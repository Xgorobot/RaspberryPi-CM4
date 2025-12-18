import asyncio
import logging
import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import uvicorn
import audioop
import wave
import os
from datetime import datetime

# Try to import webrtcvad for better voice detection
try:
    import webrtcvad
    HAS_WEBRTCVAD = True
except ImportError:
    webrtcvad = None
    HAS_WEBRTCVAD = False

# Try to import noisereduce for professional noise reduction
try:
    import noisereduce as nr
    HAS_NOISEREDUCE = True
    logger_temp = logging.getLogger("MockVoiceServer")
except ImportError:
    nr = None
    HAS_NOISEREDUCE = False

# Try to import ChatService for CHAT mode
try:
    # Try relative import first (for module execution)
    try:
        from .chat_service import get_chat_service
    except ImportError:
        from chat_service import get_chat_service
        
    HAS_CHAT_SERVICE = True
    print("DEBUG: ChatService imported successfully")
except ImportError as e:
    HAS_CHAT_SERVICE = False
    get_chat_service = None
    print(f"DEBUG: ChatService import failed: {e}")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s.%(msecs)03d %(levelname)s:%(name)s: %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("MockVoiceServer")

# Debug: Save audio to WAV files for analysis
# Set environment variable DEBUG_SAVE_AUDIO=1 to enable
DEBUG_SAVE_AUDIO = os.environ.get('DEBUG_SAVE_AUDIO', '').lower() in ('1', 'true', 'yes')


# ... (existing imports)

# ... (existing imports)
import socket
from zeroconf import ServiceInfo
from zeroconf.asyncio import AsyncZeroconf

# ... (existing logging setup)

app = FastAPI()

# Zeroconf State
aio_zeroconf_instance = None
service_info = None

def get_local_ip():
    """
    Attempts to find the local IP address on the 192.168.x.x subnet.
    Falls back to a general internet route if not found.
    """
    try:
        # First try to find a 192.168.x.x address by inspecting interfaces (using socket hostname)
        # This is tricky without netifaces.
        # Let's try the connect method again but force a local address check?
        # Actually, let's just get the hostname and check resolved IPs.
        hostname = socket.gethostname()
        local_ips = socket.gethostbyname_ex(hostname)[2]
        for ip in local_ips:
            if ip.startswith("192.168."):
                return ip
        
        # Fallback to the connect method
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        # If all else fails, look at the ifconfig provided by user analysis: 192.168.2.192
        # As a robust fallback during this debugging session:
        return "192.168.2.192"

@app.on_event("startup")
async def startup_event():
    global aio_zeroconf_instance, service_info
    
    # Preload model if in Chat mode
    if RESPONSE_MODE == "CHAT" and HAS_CHAT_SERVICE:
        chat_service = get_chat_service() # Initialize chat service instance
        if chat_service:
            logger.info("Pre-loading Chat Model (this may take a few minutes)...")
            # Run in thread to not block event loop (though startup blocks anyway)
            import threading
            # DEBUG: Print module file
            if hasattr(chat_service, '__module__'):
                 import sys
                 mod = sys.modules.get(chat_service.__module__)
                 logger.info(f"DEBUG: ChatService module file: {getattr(mod, '__file__', 'unknown')}")
            
            threading.Thread(target=chat_service.load_model).start()
    
    local_ip = get_local_ip()
    port = 8000
    
    logger.info(f"Starting Zeroconf service on {local_ip}:{port}")
    
    # Description map
    desc = {'path': '/ws/audio'}
    
    service_info = ServiceInfo(
        "_xgo-voice._tcp.local.",
        "XGO Voice Server._xgo-voice._tcp.local.",
        addresses=[socket.inet_aton(local_ip)],
        port=port,
        properties=desc,
        server="xgo-server.local.",
    )
    
    # Use AsyncZeroconf to avoid blocking the event loop
    aio_zeroconf_instance = AsyncZeroconf()
    await aio_zeroconf_instance.async_register_service(service_info, allow_name_change=True)
    logger.info("Zeroconf service registered: _xgo-voice._tcp.local.")

@app.on_event("shutdown")
async def shutdown_event():
    global aio_zeroconf_instance, service_info
    if aio_zeroconf_instance:
        logger.info("Unregistering Zeroconf service...")
        await aio_zeroconf_instance.async_unregister_service(service_info)
        await aio_zeroconf_instance.async_close()


# VAD Parameters
# Assuming 16kHz, 16-bit mono
CHUNK_SIZE = 1024
RATE = 16000
# Threshold for "Silence". This needs tuning.
# Noise floor seen in logs ~600-800. 
# UPDATE: Raising to 4000 to filter background noise better.
SILENCE_THRESHOLD = 4000   # Increased from 2000 to reduce false triggers
SILENCE_DURATION = 0.8     # Increased from 0.5s to require longer pause

# Response Mode: "ECHO" to echo back, "BEEP" for tone, "CHAT" for AI conversation
RESPONSE_MODE = os.environ.get('RESPONSE_MODE', 'ECHO').upper()  # ECHO, BEEP, or CHAT

# Minimum audio duration to echo (in seconds) - prevents echoing short noise bursts
MIN_ECHO_DURATION = 0.5  # At least 0.5 seconds of audio

@app.websocket("/ws/audio")
async def audio_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("DEBUG: Websocket Accepted!", flush=True)
    logger.info(f"Client connected - Response Mode: {RESPONSE_MODE}")
    
    # Send a "Welcome" beep (440Hz sine wave, 0.5s)
    # 16000 Hz sample rate
    try:
        duration = 0.5
        frequency = 440.0
        t = np.linspace(0, duration, int(RATE * duration), False)
        # Generate int16 sine wave (scale to 50% volume)
        note = (np.sin(frequency * t * 2 * np.pi) * 16000).astype(np.int16)
        # await websocket.send_bytes(note.tobytes())
        # logger.info("Sent welcome beep.")
    except Exception as e:
        logger.error(f"Failed to send beep: {e}")

    buffer = bytearray()
    silence_start_time = None
    silence_frames = 0
    
    # Initialize WebRTC VAD if available
    vad = None
    if HAS_WEBRTCVAD:
        try:
            vad = webrtcvad.Vad()
            vad.set_mode(2)  # Aggressiveness: 0-3 (2 = balanced)
            logger.info("WebRTC VAD initialized (mode=2)")
        except Exception as e:
            logger.warning(f"Failed to initialize WebRTC VAD: {e}")
            vad = None
    
    try:
        while True:
            # Receive generic message to handle both Text (Status) and Binary (Audio)
            message = await websocket.receive()
            
            if message["type"] == "websocket.disconnect":
                logger.info(f"Client disconnected event.")
                break
                
            if "text" in message:
                # Log Client Status Update
                try:
                    # Try to parse as JSON if possible, or just log raw
                    # import json # make sure json is imported or just log string
                    logger.info(f"======> CLIENT STATE: {message['text']}")
                except Exception as e:
                     logger.warning(f"Failed to log text message: {e}")
                continue
            
            if "bytes" not in message:
                continue

            data = message["bytes"]
            
            if not data:
                break
            
            # Voice Activity Detection
            is_speech = False
            
            if HAS_WEBRTCVAD and vad is not None:
                # WebRTC VAD requires specific frame sizes: 10, 20, or 30ms
                # At 16kHz, 20ms = 320 samples = 640 bytes
                # Process in 20ms chunks for webrtcvad
                frame_duration_ms = 20
                frame_bytes = int(RATE * frame_duration_ms / 1000 * 2)  # 640 bytes
                
                # Check each 20ms frame in the data
                pos = 0
                speech_frames = 0
                total_frames = 0
                while pos + frame_bytes <= len(data):
                    frame = data[pos:pos + frame_bytes]
                    try:
                        if vad.is_speech(frame, RATE):
                            speech_frames += 1
                    except Exception:
                        pass  # Skip invalid frames
                    total_frames += 1
                    pos += frame_bytes
                
                # Consider it speech if >50% of frames have speech
                if total_frames > 0 and speech_frames / total_frames > 0.5:
                    is_speech = True
                    
            else:
                # Fallback to energy-based VAD
                energy = audioop.rms(data, 2)
                is_speech = energy > SILENCE_THRESHOLD
            
            # Check Max Duration (10 seconds = 500 chunks of 20ms)
            MAX_CHUNKS = int(10 * 1000 / 20)
            current_recording_chunks = len(buffer) / (RATE * 0.02 * 2) 
            
            if is_speech:
                # Voice detected - ADD TO BUFFER (only record speech, not silence)
                buffer.extend(data)
                if silence_start_time is not None:
                    logger.info(f"VAD: Voice Activity Detected. Recording...")
                silence_start_time = None
                silence_frames = 0
            else:
                # Silence detected
                silence_frames += 1
                if silence_start_time is None:
                    silence_start_time = asyncio.get_event_loop().time()
                    logger.info("Silence started...")
            
            # FORCE RETURN if buffer is too big (Check GLOBAL buffer size)
            if len(buffer) > 10 * RATE * 2: # 10 seconds
                 # Only if we haven't already decided to process (i.e. silence duration not yet met)
                 # We force it by overriding silence detection state
                 if silence_start_time is None or (asyncio.get_event_loop().time() - silence_start_time) <= SILENCE_DURATION:
                     logger.info("Max speech duration reached (10s). Forcing processing.")
                     silence_start_time = asyncio.get_event_loop().time() - (SILENCE_DURATION + 1.0) # Fake long silence
            
            # Check if silence has persisted long enough
            # Use current time OR forced time
            current_time = asyncio.get_event_loop().time()
            if silence_start_time is not None and (current_time - silence_start_time) > SILENCE_DURATION:
                    # Only respond if we have gathered enough audio (not just noise)
                    min_buffer_size = int(RATE * 2 * MIN_ECHO_DURATION)  # bytes = rate * 2 (16-bit) * duration
                    if len(buffer) > min_buffer_size: 
                        logger.info(f"Silence detected ({SILENCE_DURATION}s). Sending {RESPONSE_MODE} response.")
                        
                        # Choose response based on mode
                        response_data = None
                        
                        if RESPONSE_MODE == "ECHO":
                            # Ensure buffer is byte-aligned (16-bit = 2 bytes per sample)
                            buffer_bytes = bytes(buffer)
                            if len(buffer_bytes) % 2 != 0:
                                buffer_bytes = buffer_bytes[:-1]  # Remove last byte if odd
                                logger.warning("Fixed odd buffer length for byte alignment")
                            
                            # Debug: Save raw audio to WAV file
                            if DEBUG_SAVE_AUDIO:
                                try:
                                    timestamp = datetime.now().strftime("%H%M%S")
                                    wav_path = f"debug_audio_{timestamp}.wav"
                                    with wave.open(wav_path, 'wb') as wf:
                                        wf.setnchannels(1)
                                        wf.setsampwidth(2)  # 16-bit
                                        wf.setframerate(RATE)
                                        wf.writeframes(buffer_bytes)
                                    logger.info(f"DEBUG: Saved raw audio to {wav_path}")
                                except Exception as e:
                                    logger.error(f"Failed to save debug audio: {e}")
                            
                            # Convert to numpy for processing
                            audio_array = np.frombuffer(buffer_bytes, dtype=np.int16).astype(np.float32)
                            
                            # ========== REMOVE START SPIKE ==========
                            # Trim first 150ms to remove mic initialization artifact
                            trim_samples = int(RATE * 0.15)  # 150ms (was 100ms)
                            if len(audio_array) > trim_samples * 2:
                                audio_array = audio_array[trim_samples:]
                                logger.info(f"Trimmed first {trim_samples} samples (150ms)")
                            
                            # Apply 80ms fade-in to smooth any remaining start spike
                            fade_samples = int(RATE * 0.08)  # 80ms (was 50ms)
                            if len(audio_array) > fade_samples:
                                fade_in = np.linspace(0, 1, fade_samples)
                                audio_array[:fade_samples] *= fade_in
                            
                            # ========== NOISE REDUCTION ==========
                            if HAS_NOISEREDUCE:
                                try:
                                    audio_reduced = nr.reduce_noise(
                                        y=audio_array, 
                                        sr=RATE,
                                        stationary=True,
                                        prop_decrease=1.0,  # 100% noise reduction
                                        n_fft=512,
                                        win_length=400,
                                        hop_length=100
                                    )
                                    audio_array = audio_reduced
                                    logger.info("Applied noisereduce noise reduction")
                                except Exception as e:
                                    logger.warning(f"noisereduce failed: {e}")
                            
                            # Normalize and soft clip
                            max_val = np.max(np.abs(audio_array))
                            if max_val > 0:
                                audio_array = audio_array / max_val
                                audio_array = np.tanh(audio_array * 1.5)
                                audio_array = audio_array * 22937
                            
                            response_data = audio_array.astype(np.int16).tobytes()
                            logger.info(f"Echoing {len(response_data)} bytes (noise-reduced)")

                        elif RESPONSE_MODE == "CHAT":
                            # CHAT mode: Streaming
                            if HAS_CHAT_SERVICE:
                                try:
                                    logger.info("Processing with ChatService...")
                                    chat_service = get_chat_service()
                                    response_gen = chat_service.process_audio(buffer)
                                    
                                    sent_bytes = 0
                                    chunk_count = 0
                                    # Streaming loop
                                    for chunk in response_gen:
                                        if chunk:
                                            await websocket.send_bytes(chunk)
                                            sent_bytes += len(chunk)
                                            chunk_count += 1
                                    
                                    logger.info(f"ChatService streaming complete. Sent {sent_bytes} bytes.")
                                    response_data = None # Already sent

                                except Exception as e:
                                    logger.error(f"ChatService error: {e}")
                                    import traceback
                                    traceback.print_exc()
                                    # Fallback to beep
                                    duration = 0.5
                                    frequency = 880.0
                                    t = np.linspace(0, duration, int(RATE * duration), False)
                                    response_data = (np.sin(frequency * t * 2 * np.pi) * 16000).astype(np.int16).tobytes()
                            else:
                                logger.warning("ChatService not available, falling back to ECHO")
                                response_data = buffer

                        else:
                            # BEEP mode
                            duration = 1.0
                            frequency = 440.0
                            t = np.linspace(0, duration, int(RATE * duration), False)
                            response_data = (np.sin(frequency * t * 2 * np.pi) * 16000).astype(np.int16).tobytes()
                            logger.info(f"Generated beep: {len(response_data)} bytes")

                        # Send response_data if not already sent (non-streaming modes or fallback)
                        if response_data:
                            chunk_size = 4096
                            sent_bytes = 0
                            chunk_count = 0
                            for i in range(0, len(response_data), chunk_size):
                                chunk = response_data[i:i+chunk_size]
                                await websocket.send_bytes(chunk)
                                sent_bytes += len(chunk)
                                chunk_count += 1
                                await asyncio.sleep(0.05)
                            logger.info(f"Response sent. ({sent_bytes} bytes).")
                        
                        # Clear buffer after processing
                        buffer = bytearray()
                        silence_start_time = None
                    else:
                        pass
                         # Buffer too small, maybe just brief noise, keep waiting or clear if too old?
            
    except WebSocketDisconnect:
        logger.info(f"Client disconnected. Final Buffer Size: {len(buffer)}")
    except Exception as e:
        logger.error(f"Error in connection handler: {e}")
        
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
