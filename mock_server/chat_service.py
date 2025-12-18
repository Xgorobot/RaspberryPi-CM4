"""
MiniCPM-o 2.6 Chat Service
Provides voice-to-voice conversation capabilities using MiniCPM-o model.
Adapted for Apple Silicon (MPS) support.
"""

import os
import sys
import io
import logging
import numpy as np
import librosa
import soundfile
import torch
import wave
import threading
import os

# Setup logging
logger = logging.getLogger("ChatService")

# Add minicpm_o directory to path for vad_utils
MINICPM_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(MINICPM_DIR, "minicpm_o"))

try:
    import vad_utils
    HAS_VAD = True
except ImportError:
    logger.warning("vad_utils not available, using simple VAD")
    HAS_VAD = False


class ChatService:
    """Simple chat service using MiniCPM-o for voice conversations."""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        """Singleton pattern - only one instance of the model."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if ChatService._initialized:
            return
        
        logger.info("Initializing ChatService...")
        import threading
        # self.load_lock = threading.Lock() # Lock is failing, using manual flag
        self._is_loading = False
        
        # Determine device
        if torch.backends.mps.is_available():
            # MPS is crashing with BFloat16 and Float16 (NaN). Float32 OOMs.
            # Fallback to CPU for stability.
            self.device = 'cpu' 
            self.dtype = torch.float32
            logger.info("Using CPU device (MPS unstable for this model)")
        elif torch.cuda.is_available():
            self.device = 'cuda:0'
            self.dtype = torch.bfloat16
            logger.info("Using CUDA device")
        else:
            self.device = 'cpu'
            self.dtype = torch.float32
            logger.info("Using CPU device")
        
        # Model configuration
        self.model_path = os.environ.get('MINICPM_MODEL', 'openbmb/MiniCPM-o-2_6')
        self.model = None
        self.tokenizer = None
        self.session_id = 0
        
        # Audio settings
        self.sample_rate = 16000
        
        # Reference audio for voice cloning (optional)
        self.ref_audio_path = os.path.join(
            MINICPM_DIR, "minicpm_o", "assets", "ref_audios", "default.wav"
        )
        
        ChatService._initialized = True
        logger.info(f"ChatService initialized (id={id(self)})")
            
    def load_model(self):
        """Load the MiniCPM-o model. Thread-safe(ish)."""
        logger.info(f"load_model called on instance {id(self)}")
        
        # 1. Check if loaded
        if self.model is not None:
             return True

        # 2. Check if loading (Manual Lock)
        if self._is_loading:
             logger.info(f"[PID:{os.getpid()} TID:{threading.get_ident()}] Model is loading by another thread. Waiting...")
             while self._is_loading:
                 import time
                 time.sleep(1)
                 if self.model is not None:
                     return True
             return True

        self._is_loading = True
        try:
             # Double-check
             if self.model is not None:
                 return True
                 
             logger.info(f"[PID:{os.getpid()} TID:{threading.get_ident()}] Loading MiniCPM-o model from {self.model_path}...")
             logger.info("This may take a while on first run (downloading ~16GB)...")
            
             from transformers import AutoModel, AutoTokenizer
             
             # Use local var to prevent race conditions (partial loading)
             model_instance = None
             
             with torch.no_grad():
                logger.info("Calling AutoModel.from_pretrained...")
                model_instance = AutoModel.from_pretrained(
                    self.model_path,
                    trust_remote_code=True,
                    torch_dtype=self.dtype,
                    attn_implementation='sdpa' if self.device != 'mps' else 'eager'
                )
             logger.info("Model object created.")
            
             self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_path,
                trust_remote_code=True
             )
             logger.info("Tokenizer loaded.")
            
             # Initialize TTS
             logger.info("Initializing TTS...")
             model_instance.init_tts()
             logger.info("TTS initialized.")
            
             # Move to device
             logger.info(f"Moving model to {self.device}...")
             if self.device == 'mps':
                try:
                    model_instance.to(self.device).eval()
                except Exception as e:
                    logger.warning(f"Failed to move to MPS: {e}, using CPU")
                    self.device = 'cpu'
                    model_instance.to(self.device).eval()
             else:
                model_instance.to(self.device).eval()
            
             # FINAL ASSIGNMENT
             self.model = model_instance
             logger.info(f"Model loaded successfully on {self.device}")
             return True
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            self._is_loading = False
    
    def process_audio(self, audio_bytes: bytes):
        """
        Process audio input and generate a voice response.
        """
        if self.model is None:
            if not self.load_model():
                yield self._generate_error_audio()
                return
        
        # DEBUG: Save input audio
        import time
        import wave
        timestamp = int(time.time())
        in_filename = f"debug_in_{timestamp}.wav"
        try:
            with wave.open(in_filename, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2) # 16-bit
                wf.setframerate(self.sample_rate)
                wf.writeframes(audio_bytes)
            logger.info(f"Saved input audio to {in_filename}")
        except Exception as e:
            logger.error(f"Failed to save input audio: {e}")

        try:
            # Convert bytes to numpy array
            audio_np = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
            
            # Ensure 16kHz sample rate
            if len(audio_np) == 0:
                logger.warning("Empty audio input")
                yield self._generate_error_audio()
                return
            
            logger.info(f"Processing audio: {len(audio_np)} samples ({len(audio_np)/self.sample_rate:.2f}s)")
            
            # Prepare messages for the model
            # Initialize with voice style if available
            if os.path.exists(self.ref_audio_path):
                ref_audio, _ = librosa.load(self.ref_audio_path, sr=self.sample_rate, mono=True)
                voice_prompt = "Use the voice in the audio prompt to synthesize new content."
                assistant_prompt = "You are a helpful assistant with the above voice style."
                sys_msg = {
                    'role': 'user',
                    'content': [voice_prompt + "\n", ref_audio, "\n" + assistant_prompt]
                }
                
                with torch.no_grad():
                    logger.info("Executing streaming_prefill (system prompt)...")
                    self.model.streaming_prefill(
                        session_id=str(self.session_id),
                        msgs=[sys_msg],
                        tokenizer=self.tokenizer,
                    )
                    logger.info("System prompt prefilled.")
            
            # Send user audio
            user_msg = {'role': 'user', 'content': [audio_np]}
            
            with torch.no_grad():
                logger.info("Executing streaming_prefill (user audio)...")
                self.model.streaming_prefill(
                    session_id=str(self.session_id),
                    msgs=[user_msg],
                    tokenizer=self.tokenizer,
                )
                logger.info("User audio prefilled.")
            
            # Generate response
            response_text = ""
            import soundfile as sf
            import io
            
            logger.info("Starting streaming_generate...")
            
            # Open debug output file
            import time
            timestamp = int(time.time())
            out_filename = f"debug_out_{timestamp}.pcm"
            
            with open(out_filename, 'wb') as out_f:
                with torch.inference_mode():
                    self.model.config.stream_input = True
                    
                    for r in self.model.streaming_generate(
                        session_id=str(self.session_id),
                        tokenizer=self.tokenizer,
                        generate_audio=True,
                    ):
                        audio_np = r.get("audio_wav")
                        text = r.get("text", "")
                        
                        if audio_np is not None:
                            # MiniCPM-o outputs raw float32/float16 audio at 24000Hz (usually) or 16000Hz?
                            # We need to ensure it's 16kHz int16 for the client.
                            sr = r.get("sampling_rate", self.sample_rate)
                            
                            # Convert to int16
                            audio_int16 = (audio_np * 32767).astype(np.int16)
                            audio_bytes = audio_int16.tobytes()
                            
                            # Save to debug file
                            out_f.write(audio_bytes)
                            
                            # Yield to client
                            yield audio_bytes
                            
                        if text:
                            response_text += text
                            # logger.info(f"Received text chunk: {text}")

            logger.info(f"Generation complete. Text: {response_text[:100]}...")
            logger.info(f"Saved output audio to {out_filename}")
            
        except Exception as e:
            logger.error(f"Error processing audio: {e}")
            import traceback
            traceback.print_exc()
            yield self._generate_error_audio()
    
    def _generate_error_audio(self) -> bytes:
        """Generate a simple beep to indicate an error."""
        duration = 0.5
        frequency = 880  # Higher pitch for error
        t = np.linspace(0, duration, int(self.sample_rate * duration), False)
        audio = (np.sin(frequency * t * 2 * np.pi) * 16000).astype(np.int16)
        return audio.tobytes()


# Singleton instance
_chat_service = None

def get_chat_service() -> ChatService:
    """Get the singleton ChatService instance."""
    global _chat_service
    if _chat_service is None:
        _chat_service = ChatService()
    return _chat_service
