import threading
import pyaudio
import websocket # pip install websocket-client
import logging
import time

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s.%(msecs)03d %(levelname)s:%(name)s: %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("VoiceClient")
# logging.basicConfig(level=logging.INFO) # Ensure logs are visible

class VoiceStreamingClient:
    def __init__(self, server_ip, server_port, on_audio_data=None, input_device_index=7, output_device_index=7):
        self.server_url = f"ws://{server_ip}:{server_port}/ws/audio"
        self.ws = None
        self.audio = pyaudio.PyAudio()
        self.input_device_index = input_device_index
        self.output_device_index = output_device_index
        self.on_audio_data = on_audio_data
        
        # Audio Config
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 16000 # Correct rate for VAD and HW
        self.chunk = 1024 # Buffer size
        
        self.input_stream = None
        self.output_stream = None
        
        self.running = False
        self.is_playing = False # Echo Cancellation Flag
        self.capture_thread = None
        self.receive_thread = None

    def connect(self):
        try:
            # Create a long-lived connection
            self.ws = websocket.WebSocket()
            self.ws.connect(self.server_url)
            logger.info(f"Connected to {self.server_url}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to {self.server_url}: {e}")
            return False

    def send_status(self, status):
        """Sends a JSON status update to the server."""
        if self.ws and self.ws.connected:
            try:
                import json
                msg = json.dumps({"status": status})
                self.ws.send(msg)
            except Exception as e:
                logger.warning(f"Failed to send status: {e}")

    def _open_audio_streams(self):
        """Opens separate input and output streams."""
        try:
            logger.info(f"Opening audio streams (In Index: {self.input_device_index}, Out Index: {self.output_device_index})...")
            
            # DEBUG: Print all devices seen by this process
            count = self.audio.get_device_count()
            msg = f"PyAudio found {count} devices:"
            logger.info(msg)
            print("DEBUG: " + msg)
            for i in range(count):
                try:
                    info = self.audio.get_device_info_by_index(i)
                    dev_msg = f"  Device {i}: {info.get('name')} (In: {info.get('maxInputChannels')}, Out: {info.get('maxOutputChannels')}, SR: {info.get('defaultSampleRate')})"
                    logger.info(dev_msg)
                    print("DEBUG: " + dev_msg)
                except Exception: pass

            # Open Input Stream (Mic)
            self.input_stream = self.audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.rate,
                input=True,
                input_device_index=self.input_device_index,
                frames_per_buffer=self.chunk
            )

            # Open Output Stream (Speaker)
            self.output_stream = self.audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.rate,
                output=True,
                output_device_index=self.output_device_index,
                frames_per_buffer=self.chunk
            )
            logger.info("Audio streams opened successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to open audio streams: {e}")
            return False

    def _capture_loop(self):
        logger.info("Capture loop started")
        import audioop
        import math
        
        # Simple Client-Side VAD Parameters
        SILENCE_THRESHOLD_DB = 300 # Approx threshold for silence ~ 40dB ? (Need tuning)
        # However, let's use raw energy first. 
        # 16-bit audio, max 32767. 
        # Silence is usually < 500-1000.
        CLIENT_VAD_THRESHOLD = 500 

        while self.running and self.ws.connected:
            try:
                # Blocking read
                if not getattr(self, '_has_logged_read', False):
                     logger.info("Reading audio frame (first)")
                     self._has_logged_read = True
                
                data = self.input_stream.read(self.chunk, exception_on_overflow=False)
                
                # Echo Cancellation: Don't send if we are playing audio
                if self.is_playing:
                    if not getattr(self, '_has_logged_skip', False):
                        logger.info("Skipping audio (echo cancel) - playing") 
                        self.send_status("skipped_echo_cancel")
                        self._has_logged_skip = True
                    continue
                else:
                    # Reset skip log so we see it again if we toggle
                    self._has_logged_skip = False
                
                # Client-Side VAD / Energy Gating
                rms = audioop.rms(data, 2)
                if rms < CLIENT_VAD_THRESHOLD:
                    # Too quiet, don't send to save bandwidth (and reduce server load)
                    # Ideally we might want to send comfort noise or keep connection alive?
                    # For now, just skip.
                    continue

                # Periodic Logging of Volume
                if not hasattr(self, '_last_log_time'): self._last_log_time = 0
                if time.time() - self._last_log_time > 2.0:
                    logger.info(f"Mic Energy: {rms}")
                    self._last_log_time = time.time()

                # Send binary
                if not getattr(self, '_has_logged_send', False):
                     logger.info(f"Sending {len(data)} bytes (first)")
                     self.send_status("sending_audio")
                     self._has_logged_send = True
                                          
                self.ws.send_binary(data)
            except OSError as e:
                 logger.warning(f"Audio Input Overflow/Error: {e}")
                 continue
            except Exception as e:
                logger.error(f"Error in capture loop: {e}")
                self.running = False 
                break
        logger.info("Capture loop finished")

    def _receive_loop(self):
        logger.info("Receive loop started")
        
        # Buffer for accumulating audio chunks
        audio_buffer = bytearray()
        last_receive_time = None
        BUFFER_TIMEOUT = 0.2  # 200ms - if no new data for this long, play buffered audio
        
        while self.running and self.ws.connected:
            try:
                # Set a short timeout on the websocket to allow checking buffer
                self.ws.settimeout(0.1)  # 100ms receive timeout
                
                try:
                    data = self.ws.recv()
                except TimeoutError:
                    data = None
                except Exception as e:
                    if "timed out" in str(e).lower():
                        data = None
                    else:
                        raise
                
                if data is not None and isinstance(data, bytes):
                    logger.info(f"Received {len(data)} bytes from server")
                    audio_buffer.extend(data)
                    last_receive_time = time.time()
                    
                elif data is not None and isinstance(data, str):
                    logger.info(f"Received text message: {data}")
                    # Could be an "end of audio" signal?
                    if data == "END_AUDIO":
                        # Force play buffer now
                        last_receive_time = 0
                
                # Check if we should play the buffered audio
                if audio_buffer and last_receive_time is not None:
                    time_since_last = time.time() - last_receive_time
                    if time_since_last >= BUFFER_TIMEOUT:
                        # Play all buffered audio
                        buffer_size = len(audio_buffer)
                        logger.info(f"Playing buffered audio: {buffer_size} bytes (waited {time_since_last:.3f}s)")
                        print(f"DEBUG: About to play {buffer_size} bytes", flush=True)
                        
                        self.is_playing = True
                        self.send_status("playing_start")
                        
                        try:
                            t0 = time.time()
                            print(f"DEBUG: Calling output_stream.write()...", flush=True)
                            self.output_stream.write(bytes(audio_buffer))
                            dt = time.time() - t0
                            print(f"DEBUG: output_stream.write() returned after {dt:.4f}s", flush=True)
                            logger.info(f"Audio playback completed in {dt:.4f}s")
                        except Exception as e:
                            print(f"DEBUG: Audio Write EXCEPTION: {e}", flush=True)
                            logger.error(f"Audio Write Failed: {e}")
                        finally:
                            self.is_playing = False
                            self.send_status("playing_end")
                            print("DEBUG: Playback finished, buffer cleared", flush=True)
                        
                        # Clear buffer
                        audio_buffer = bytearray()
                        last_receive_time = None
                
                # Handle empty data (connection closed)
                if data is not None and not data:
                    logger.info("Connection closed by server")
                    break
                    
            except Exception as e:
                logger.error(f"Error in receive loop: {e}")
                self.running = False
                break
        
        logger.info("Receive loop finished")

    def start(self):
        if self.running: 
            return
        
        print("VoiceStreamingClient: Connecting...")
        if not self.connect():
            print("VoiceStreamingClient: Connection failed.")
            return
            
        print("VoiceStreamingClient: Opening audio streams...")
        if not self._open_audio_streams():
            print("VoiceStreamingClient: Audio Init failed.")
            self.ws.close()
            return
            
        self.running = True
        
        self.capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
        
        self.capture_thread.start()
        self.receive_thread.start()
        print("VoiceStreamingClient: Started.")

    def stop(self, terminate_audio=True):
        print("VoiceStreamingClient: Stopping...")
        self.running = False
        
        if self.ws:
            try:
                self.ws.close()
            except: pass
            self.ws = None
        
        if self.input_stream:
            try:
                self.input_stream.stop_stream()
                self.input_stream.close()
            except: pass
            self.input_stream = None
            
        if self.output_stream:
            try:
                self.output_stream.stop_stream()
                self.output_stream.close()
            except: pass
            self.output_stream = None
            
        # Only terminate PyAudio if explicitly requested (not during reconnect)
        if terminate_audio and self.audio:
            try:
                self.audio.terminate()
            except: pass
            self.audio = None
        
        if self.capture_thread:
            self.capture_thread.join(timeout=1)
            self.capture_thread = None
        if self.receive_thread:
            self.receive_thread.join(timeout=1)
            self.receive_thread = None
            
        print("VoiceStreamingClient: Stopped.")

    def start_with_reconnect(self, max_retries=None, retry_delay=3):
        """Start the client with automatic reconnection on disconnect.
        
        Args:
            max_retries: Maximum reconnect attempts (None = infinite)
            retry_delay: Seconds to wait between reconnect attempts
        """
        retries = 0
        while max_retries is None or retries < max_retries:
            print(f"\nVoiceStreamingClient: === Reconnect attempt {retries + 1} ===", flush=True)
            
            # Clean up previous connection WITHOUT terminating PyAudio
            try:
                self.stop(terminate_audio=False)
            except Exception as e:
                print(f"VoiceStreamingClient: Cleanup error: {e}", flush=True)
            
            # Create fresh PyAudio instance
            try:
                if self.audio:
                    self.audio.terminate()
            except: pass
            self.audio = pyaudio.PyAudio()
            
            # Reset state
            self.running = False
            self.ws = None
            self.input_stream = None
            self.output_stream = None
            self.is_playing = False
            self.capture_thread = None
            self.receive_thread = None
            
            print(f"VoiceStreamingClient: Attempting connection...", flush=True)
            
            # Try to start
            self.start()
            
            if self.running and self.capture_thread and self.receive_thread:
                print("VoiceStreamingClient: Connected! Monitoring threads...", flush=True)
                # Wait for EITHER thread to die (indicates connection issue)
                while self.running:
                    # Check if threads are still alive
                    capture_alive = self.capture_thread and self.capture_thread.is_alive()
                    receive_alive = self.receive_thread and self.receive_thread.is_alive()
                    if not capture_alive or not receive_alive:
                        print(f"VoiceStreamingClient: Thread died (capture={capture_alive}, receive={receive_alive})", flush=True)
                        self.running = False
                        break
                    time.sleep(0.5)
                print("VoiceStreamingClient: Connection lost!", flush=True)
            else:
                print("VoiceStreamingClient: Failed to connect.")
            
            retries += 1
            if max_retries is None or retries < max_retries:
                print(f"VoiceStreamingClient: Reconnecting in {retry_delay}s...")
                time.sleep(retry_delay)
        
        print(f"VoiceStreamingClient: Max retries ({max_retries}) reached. Giving up.")

if __name__ == "__main__":
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(description="Voice Streaming Client")
    parser.add_argument("--ip", default="localhost", help="Server IP address")
    parser.add_argument("--port", type=int, default=8000, help="Server Port")
    parser.add_argument("--in-dev", type=int, default=None, help="Input Device Index (auto-detect if not set)")
    parser.add_argument("--out-dev", type=int, default=None, help="Output Device Index (auto-detect if not set)")
    
    args = parser.parse_args()
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s.%(msecs)03d %(levelname)s:%(name)s: %(message)s',
        datefmt='%H:%M:%S'
    )
    logger.info(f"Starting Client -> {args.ip}:{args.port}")
    
    # Auto-detect audio device with fallback chain
    p = pyaudio.PyAudio()
    
    input_device_index = args.in_dev
    output_device_index = args.out_dev
    
    # Priority order for device selection
    # 1. wm8960 (hardware codec on XGO)
    # 2. pulse (PulseAudio - usually works)
    # 3. default
    count = p.get_device_count()
    
    wm8960_idx = None
    pulse_idx = None
    default_idx = None
    
    for i in range(count):
        try:
            info = p.get_device_info_by_index(i)
            name = info.get('name', '')
            max_in = info.get('maxInputChannels', 0)
            max_out = info.get('maxOutputChannels', 0)
            
            if "wm8960" in name.lower() and max_in > 0 and max_out > 0:
                wm8960_idx = i
                logger.info(f"Found WM8960 at index {i}: {name}")
            elif "pulse" in name.lower() and max_in > 0 and max_out > 0:
                pulse_idx = i
                logger.info(f"Found Pulse at index {i}: {name}")
            elif name.lower() == "default" and max_in > 0 and max_out > 0:
                default_idx = i
                logger.info(f"Found Default at index {i}: {name}")
        except: pass
    
    # Select best device
    if input_device_index is None:
        if wm8960_idx is not None:
            input_device_index = wm8960_idx
            logger.info(f"Using WM8960 for input: index {wm8960_idx}")
        elif pulse_idx is not None:
            input_device_index = pulse_idx
            logger.info(f"Using Pulse for input: index {pulse_idx}")
        elif default_idx is not None:
            input_device_index = default_idx
            logger.info(f"Using Default for input: index {default_idx}")
        else:
            logger.error("No suitable input device found!")
            sys.exit(1)
    
    if output_device_index is None:
        if wm8960_idx is not None:
            output_device_index = wm8960_idx
            logger.info(f"Using WM8960 for output: index {wm8960_idx}")
        elif pulse_idx is not None:
            output_device_index = pulse_idx
            logger.info(f"Using Pulse for output: index {pulse_idx}")
        elif default_idx is not None:
            output_device_index = default_idx
            logger.info(f"Using Default for output: index {default_idx}")
        else:
            logger.error("No suitable output device found!")
            sys.exit(1)
    
    logger.info(f"Final device selection: Input={input_device_index}, Output={output_device_index}")
    p.terminate()

    try:
        client = VoiceStreamingClient(
            server_ip=args.ip, 
            server_port=args.port,
            input_device_index=input_device_index,
            output_device_index=output_device_index
        )
        client.start()
        
        while client.running:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Interrupted")
        if 'client' in locals():
            client.stop()
    except Exception as e:
        logger.error(f"Fatal Error: {e}")
