import threading
import time
import re

class VoiceManager:
    def __init__(self, dog_instance, skills_manager, action_sequencer, emotion_manager):
        self.dog = dog_instance
        self.skills_mgr = skills_manager
        self.action_seq = action_sequencer
        self.emotion_mgr = emotion_manager
        self.is_listening = False
        self._stop_event = threading.Event()
        self._thread = None

        # Command Mappings
        self.command_map = {
            r"\b(sit|sit down)\b": lambda: self.dog.action(12),
            r"\b(stand|stand up)\b": lambda: self.dog.action(2),
            r"\b(lie|lie down)\b": lambda: self.dog.action(1),
            r"\b(handshake|shake hand|hand)\b": lambda: self.dog.action(19),
            r"\b(push up|pushups)\b": lambda: self.dog.action(21),
            r"\b(happy|dance)\b": lambda: self.perform_custom("happy_dance"),
            r"\b(shake|shake it)\b": lambda: self.perform_custom("shake"),
            r"\b(curious)\b": lambda: self.perform_custom("curious"),
            r"\b(box|boxing|fight)\b": lambda: self.perform_custom("boxing"),
            r"\b(ball|track ball)\b": lambda: self.perform_skill("BallTracking"),
            r"\b(stop|halt|quiet)\b": lambda: self.stop_all(),
            r"\b(bark)\b": lambda: self.dog.action(130), # Placeholder for bark or specialized action
        }

    def perform_custom(self, name):
        if self.action_seq:
            if name == "happy_dance": self.action_seq.perform_happy_dance()
            elif name == "shake": self.action_seq.perform_shake()
            elif name == "curious": self.action_seq.perform_curious()
            elif name == "boxing": self.action_seq.perform_boxing()

    def perform_skill(self, name):
        if self.skills_mgr:
            self.skills_mgr.start_skill(name)

    def stop_all(self):
        print("VoiceManager: Stopping all activities.")
        self.dog.reset()
        if self.skills_mgr:
            self.skills_mgr.stop_current_skill()
        if self.action_seq:
            self.action_seq.stop_current_sequence()

    def process_command(self, text):
        """Processes a text command and triggers the corresponding action."""
        if not text: return False
        text = text.lower().strip()
        print(f"VoiceManager: Received command '{text}'")
        
        matched = False
        for pattern, func in self.command_map.items():
            if re.search(pattern, text):
                print(f"VoiceManager: Matched pattern '{pattern}'")
                # Stop previous skill/action if distinct?
                # For now, let's assume actions override each other or user says "stop"
                func()
                matched = True
                # Don't return immediately if we want to support "sit and bark"? 
                # For now, first match wins.
                if self.emotion_mgr:
                     # self.emotion_mgr.set_emotion("active") # If implemented
                     pass
                return True
        
        if not matched:
            print("VoiceManager: No match found.")
            pass
            
        return matched

    def start_listening(self):
        """Stub for actual audio listening."""
        if self.is_listening: return
        self.is_listening = True
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()
        print("VoiceManager: Listening thread started (Simulation Mode).")

    def stop_listening(self):
        self.is_listening = False
        self._stop_event.set()
        if self._thread:
            # self._thread.join() # Don't block
            pass
        print("VoiceManager: Listening stopped.")

    def _listen_loop(self):
        """
        Placeholder loop. In a real implementation with local STT, 
        this would capture audio and call process_command.
        """
        while self.is_listening and not self._stop_event.is_set():
            # time.sleep(1)
            # Check for generic 'pyaudio' if we decide to implement wake word later
            time.sleep(1)
