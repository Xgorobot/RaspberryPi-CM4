from skills.manager import Skill
import time
import socket
from voice.streaming_client import VoiceStreamingClient
try:
    from common.discovery import ServiceDiscoverer
except ImportError:
    ServiceDiscoverer = None

class VoiceConversationSkill(Skill):
    def __init__(self, dog_instance, display_manager, camera_instance=None):
        super().__init__("VoiceChat", dog_instance, display_manager, camera_instance)
        
        # Default to auto-discovery
        self.server_url = "auto"
        self.resolved_url = None
        
        self.client = None

    def set_server_url(self, url):
        self.server_url = url

    def _discover_server(self):
        if ServiceDiscoverer:
            print("VoiceConversationSkill: Attempting to discover XGO Voice Server...")
            discoverer = ServiceDiscoverer()
            result = discoverer.discover(timeout=3.0)
            if result:
                # Construct URL
                # Use property 'path' if available, else default
                path = '/ws/audio'
                if result.get('properties'):
                     # properties keys are bytes, values are bytes
                     raw_path = result['properties'].get(b'path')
                     if raw_path:
                         path = raw_path.decode('utf-8')
                
                url = f"ws://{result['host']}:{result['port']}{path}"
                print(f"VoiceConversationSkill: Discovered server at {url}")
                return url
            else:
                print("VoiceConversationSkill: Discovery failed. No server found.")
        return None

    def run(self):
        # Resolve URL if needed
        if self.server_url == "auto":
             discovered = self._discover_server()
             if discovered:
                 self.resolved_url = discovered
             else:
                 # Fallback
                 # HARDCODED FOR RELIABILITY
                 self.resolved_url = "ws://192.168.2.192:8000/ws/audio"
                 print(f"VoiceConversationSkill: Discovery failed. Falling back to HARDCODED IP: {self.resolved_url}")
        else:
            self.resolved_url = self.server_url
            
        print(f"VoiceConversationSkill: Connecting to {self.resolved_url}...")
        
        # Auto-detect audio device (prioritize wm8960 hardware)
        import pyaudio
        p = pyaudio.PyAudio()
        target_index = None
        
        for i in range(p.get_device_count()):
            try:
                info = p.get_device_info_by_index(i)
                name = info.get('name', '')
                max_in = info.get('maxInputChannels', 0)
                max_out = info.get('maxOutputChannels', 0)
                
                # Prefer wm8960 (hardware codec)
                if "wm8960" in name.lower() and max_in > 0 and max_out > 0:
                    target_index = i
                    print(f"VoiceConversationSkill: Found WM8960 at index {i}")
                    break
                # Fallback to pulse if no wm8960 found yet
                elif target_index is None and "pulse" in name.lower() and max_in > 0 and max_out > 0:
                    target_index = i
                    print(f"VoiceConversationSkill: Found Pulse at index {i} (fallback)")
            except: pass
        
        p.terminate()
        
        if target_index is None:
            target_index = 7  # Ultimate fallback
            print(f"VoiceConversationSkill: No suitable device found, using fallback index {target_index}")
        
        print(f"VoiceConversationSkill: Using audio device index {target_index}")
        
        # Parse resolved_url into server_ip and server_port
        try:
            from urllib.parse import urlparse
            parsed_url = urlparse(self.resolved_url)
            server_ip = parsed_url.hostname
            server_port = parsed_url.port
        except Exception as e:
            print(f"VoiceConversationSkill: Error parsing URL {self.resolved_url}: {e}. Using defaults.")
            server_ip = "127.0.0.1" # Fallback
            server_port = 8000 # Fallback

        self.client = VoiceStreamingClient(
            server_ip=server_ip,
            server_port=server_port,
            on_audio_data=None, # Internal playback handled by client
            input_device_index=target_index,
            output_device_index=target_index
        )
        
        # Start the client with auto-reconnect (handles server restarts)
        # This blocks until the skill is stopped or max retries reached
        import threading
        
        def reconnect_loop():
            self.client.start_with_reconnect(max_retries=None, retry_delay=3)
        
        self.reconnect_thread = threading.Thread(target=reconnect_loop, daemon=True)
        self.reconnect_thread.start()
        
        # Wait a moment for initial connection
        time.sleep(2)
        
        if not self.client.running:
             print("VoiceConversationSkill: Initial connection failed, but will keep retrying in background.")

        print("VoiceConversationSkill: Client running (with auto-reconnect).")

        # Main Loop for the Skill - just wait for stop signal
        while not self._stop_event.is_set():
            time.sleep(0.5)
            
        self.client.stop()
        print("VoiceConversationSkill: Finished.")

    def cleanup(self):
        if self.client:
            self.client.stop()
        super().cleanup()
