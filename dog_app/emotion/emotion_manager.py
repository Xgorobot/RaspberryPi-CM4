import os
import time
from enum import Enum, auto
from PIL import Image

# Assuming display_utils are in dog_app.common and this script is run from dog_app directory
try:
    from common import display_utils
    from common.display_utils import get_main_draw_context, get_main_splash_image, get_display_manager
except ImportError as e:
    print(f"EmotionManager: Error importing display_utils: {e}. Display functions may not work.")
    # Define dummy functions if import fails, so the class can be instantiated
    # This helps in identifying if the issue is an import or something else downstream.
    def get_main_draw_context(): return None
    def get_main_splash_image(): return None
    def get_display_manager(): return None
    display_utils = None # So that checks like 'if display_utils:' don't cause NameError
    print("EmotionManager: CRITICAL - display_utils import failed. Dummy objects created. Display functionality will be severely limited.")


import threading
import subprocess

class Emotion(Enum):
    NEUTRAL = 1
    HAPPY = 2
    SAD = 3
    SURPRISED = 4
    ANGRY = 5
    FEAR = 6
    DISGUST = 7
    SLEEPY = 8
    # New moods
    CURIOUS = 9
    EXCITED = 10
    # Add more emotions as needed

class EmotionManager:
    def __init__(self, asset_base_path=None):
        self.current_emotion = Emotion.NEUTRAL
        self.animation_frames = []
        self.current_frame_index = 0
        self.last_frame_time = 0
        self.frame_duration = 0.1 # seconds, for animations
        self.enabled = True # For Eco Mode

        if asset_base_path is None:
            # Try to guess asset_base_path relative to this file
            # dog_app/emotion/emotion_manager.py -> dog_app/assets
            self.asset_base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'assets'))
        else:
            self.asset_base_path = asset_base_path

        print(f"EmotionManager initialized. Asset base path: {self.asset_base_path}")

        # Ensure global display objects from display_utils are ready
        self.draw_context = get_main_draw_context()
        self.splash_image = get_main_splash_image() # This is the PIL Image object to draw on
        self.display_hardware = get_display_manager()

        if not self.draw_context or not self.splash_image or not self.display_hardware:
            print("EmotionManager: Warning - Display utilities not fully initialized. UI updates may fail.")

        self.load_emotion_assets(self.current_emotion)

    def _get_expression_path(self, emotion_name_lower):
        # Corrected path to be dog_app/assets/expressions/
        return os.path.join(self.asset_base_path, "expressions", emotion_name_lower)

    def load_emotion_assets(self, emotion):
        self.animation_frames = []
        self.current_frame_index = 0
        emotion_name_lower = emotion.name.lower()

        animation_dir = self._get_expression_path(emotion_name_lower)
        # Initialize emotion_display_name with the actual emotion name for accurate logging from the start
        emotion_display_name = emotion.name

        if not os.path.exists(animation_dir) or not os.path.isdir(animation_dir):
            # Use emotion.name here for the initial "not found" message for the *requested* emotion
            print(f"Animation directory not found for {emotion.name} at {animation_dir}")
            if emotion == Emotion.NEUTRAL:
                fallback_options = ["lookaround", "eye"] # Order of preference
                loaded_fallback = False
                for fallback_name in fallback_options:
                    fallback_dir = self._get_expression_path(fallback_name)
                    if os.path.exists(fallback_dir) and os.path.isdir(fallback_dir):
                        print(f"NEUTRAL not found. Attempting to load fallback '{fallback_name}' from {fallback_dir}")
                        animation_dir = fallback_dir
                        emotion_display_name = fallback_name.upper() # For logging purposes
                        loaded_fallback = True
                        break
                if not loaded_fallback:
                    print(f"Critical: NEUTRAL and fallbacks ({', '.join(fallback_options)}) not found. No default animation available.")
                    self.animation_frames = []
                    return
            elif emotion.name != "_FALLBACK_INTERNAL_": # Avoid recursive fallback from a failed primary load
                # This logic is for when a *specific* emotion (e.g. HAPPY) fails, it tries NEUTRAL (which then tries its own fallbacks)
                print(f"Attempting to load NEUTRAL animation as fallback for {emotion.name}.")
                # Use a temporary internal marker to prevent deep recursion if NEUTRAL itself fails in a specific way
                # This is a bit complex; simpler might be to just let NEUTRAL handle its own fallbacks.
                # For now, let's assume NEUTRAL's loading (with its fallbacks) is robust.
                self.load_emotion_assets(Emotion.NEUTRAL)
                return # Return because NEUTRAL load will handle frames
            else:
                # Should not happen if NEUTRAL and its fallbacks are truly missing.
                print(f"Critical: Fallback attempt for {emotion.name} failed, and it was already a fallback process. No animation loaded.")
                self.animation_frames = []
                return

        # If we are here, animation_dir should be valid (either original or a chosen fallback for NEUTRAL)
        if not os.path.exists(animation_dir) or not os.path.isdir(animation_dir):
             # This case should ideally be caught by the logic above.
            print(f"Critical: Target animation directory {animation_dir} for {emotion_display_name} is invalid post-fallback. No animation loaded.")
            self.animation_frames = []
            return

        try:
            # Sort files numerically (1.png, 2.png, ..., 10.png)
            # Filter for .png files and ensure the filename (without extension) is a digit for robust sorting
            frame_files = sorted(
                [f for f in os.listdir(animation_dir) if f.endswith(".png") and os.path.splitext(f)[0].isdigit()],
                key=lambda x: int(os.path.splitext(x)[0])
            )
            if not frame_files: # Handles case where directory exists but contains no valid frames
                print(f"No valid .png animation frames found in {animation_dir} for emotion {emotion_display_name}")
                # If the original emotion (not NEUTRAL) had an empty dir, try NEUTRAL.
                # If NEUTRAL (or its chosen fallback like 'lookaround') itself has an empty dir, this is critical.
                if emotion != Emotion.NEUTRAL and emotion_display_name.lower() not in ["lookaround", "eye"]:
                    print(f"Attempting to load NEUTRAL animation as fallback because {emotion_display_name} frames were missing.")
                    self.load_emotion_assets(Emotion.NEUTRAL)
                else: # This means NEUTRAL or its active fallback (lookaround/eye) had no frames.
                    print(f"Critical: {emotion_display_name} animation frames not found in {animation_dir}. No fallback available.")
                return

            for frame_file in frame_files:
                frame_path = os.path.join(animation_dir, frame_file)
                self.animation_frames.append(Image.open(frame_path))
            
            if self.animation_frames:
                print(f"Loaded {len(self.animation_frames)} frames for emotion {emotion_display_name} from {animation_dir}")
            else: # Should be caught by 'if not frame_files' earlier, but as a safeguard
                print(f"No frames loaded for {emotion_display_name} despite directory existing.")
                if emotion != Emotion.NEUTRAL and emotion_display_name.lower() not in ["lookaround", "eye"]:
                    self.load_emotion_assets(Emotion.NEUTRAL)

        except Exception as e:
            print(f"Error loading animation frames for {emotion_display_name} from {animation_dir}: {e}")
            self.animation_frames = [] # Clear partial load
            # If loading a specific emotion (not NEUTRAL) fails, try NEUTRAL.
            # If loading NEUTRAL or its chosen fallback (like 'lookaround') itself fails, this is critical.
            if emotion != Emotion.NEUTRAL and emotion_display_name.lower() not in ["lookaround", "eye"]:
                print(f"Attempting to load NEUTRAL animation as fallback due to error loading {emotion_display_name}.")
                self.load_emotion_assets(Emotion.NEUTRAL)
            else:
                print(f"Critical: Error loading {emotion_display_name} animation frames from {animation_dir}. No fallback available.")


    def set_enabled(self, enabled):
        self.enabled = enabled
        if display_utils and display_utils.get_display_manager():
             disp = display_utils.get_display_manager()
             if not enabled:
                 # Eco Mode ON: Clear to Black and Backlight OFF
                 if hasattr(disp, 'clear'): disp.clear(0x00) # 0x00 is Black, 0xff is White
                 if hasattr(disp, 'bl_control'): disp.bl_control(False)
                 print("EmotionManager: Display disabled (Eco Mode).")
             else:
                 # Eco Mode OFF: Backlight ON
                 if hasattr(disp, 'bl_control'): disp.bl_control(True)
                 print("EmotionManager: Display enabled.")
                 
    def stop(self):
        """Stops the emotion manager and clears screen."""
        self.enabled = False
        print("EmotionManager: Stopped.")

    def set_emotion(self, emotion):
        if not isinstance(emotion, Emotion):
             # Try to map string to Enum
             try:
                 emotion = Emotion[emotion.upper()]
             except KeyError:
                 print(f"EmotionManager: Invalid emotion '{emotion}'. Ignoring.")
                 return

        if self.current_emotion == emotion:
            return
        
        print(f"EmotionManager: Switching emotion to {emotion.name}")
        self.current_emotion = emotion
        self.load_emotion_assets(emotion)
        self.play_sound_for_emotion(emotion)
        # Immediately update display with the first frame of the new emotion
        self.update_display(force_redraw=True)

    def set_mood(self, mood_name):
        """Sets a mood which is essentially an emotion but could be extended."""
        self.set_emotion(mood_name)

    def play_sound_for_emotion(self, emotion):
        """Plays a sound file associated with the emotion."""
        # sound_path = os.path.join(self.assets_dir, "music", f"{emotion.name.lower()}.wav")
        # Assuming assets_dir is base assets. 
        # self.assets_dir is typically ".../assets". 
        # But in __init__ it sets self.assets_dir = .../assets/expressions (inferred from usage).
        # Let's check __init__.
        # in __init__: self.assets_dir = os.path.join(base_dir, "assets", "expressions")
        
        # So for music, we should go up one level.
        music_dir = os.path.join(self.asset_base_path, "music")
        sound_path = os.path.join(music_dir, f"{emotion.name.lower()}.wav")
        
        if os.path.exists(sound_path):
            try:
                # Play sound non-blocking
                subprocess.Popen(['aplay', '-q', sound_path])
            except Exception as e:
                print(f"EmotionManager: Failed to play sound {sound_path}: {e}")
        else:
            # print(f"EmotionManager: Sound file not found: {sound_path}")
            pass

    def update_display(self, force_redraw=False):
        if not self.enabled: return

        if not self.animation_frames:
            # print(f"No frames for emotion {self.current_emotion.name}")
            # Optionally, clear the emotion area or show a default
            if self.draw_context and self.splash_image and display_utils:
                 # Example: Clear a portion of the screen
                 # Assuming emotion is displayed in a certain rectangle e.g. (0,0, 240,240) for a 240x320 screen in portrait
                 # Or full screen if splash_image is the target.
                self.draw_context.rectangle([(0,0), self.splash_image.size], fill=display_utils.SPLASH_THEME_COLOR)
                if self.display_hardware:
                    self.display_hardware.ShowImage(self.splash_image)
            return

        now = time.time()
        if force_redraw or (now - self.last_frame_time > self.frame_duration):
            if self.draw_context and self.splash_image and self.display_hardware:
                current_pil_image = self.animation_frames[self.current_frame_index]

                # Ensure image is RGB, common issue with some PNGs having alpha or being palette-based
                if current_pil_image.mode != "RGB":
                    current_pil_image = current_pil_image.convert("RGB")

                # Resize image to fit display if necessary, or expect assets to be pre-sized.
                # The LCD is 240x320. display_utils.splash is 320x240 (landscape for PIL).
                # LCD_2inch.ShowImage handles rotation if image is 320x240.
                # If emotion images are, for example, 240x240, they need to be placed on the 320x240 splash.

                # For now, let's assume images are full-screen replacements for splash_image
                # or correctly sized to be pasted onto it.
                # If they are full screen replacements (320x240):
                # self.display_hardware.ShowImage(current_pil_image)

                # If they are to be pasted onto the splash (e.g. character on a background)
                # For simplicity, let's make them replace the splash image for now
                # This means emotion images should be 320x240.

                # Check size and paste or replace
                if current_pil_image.size == self.splash_image.size:
                    self.display_hardware.ShowImage(current_pil_image)
                else:
                    # If not same size, paste it. Center it on the splash for example.
                    # This requires splash_image to be cleared first if pasting transparent images.
                    # self.draw_context.rectangle([(0,0), self.splash_image.size], fill=display_utils.SPLASH_THEME_COLOR) # Clear
                    # x_offset = (self.splash_image.width - current_pil_image.width) // 2
                    # y_offset = (self.splash_image.height - current_pil_image.height) // 2
                    # self.splash_image.paste(current_pil_image, (x_offset, y_offset))
                    # self.display_hardware.ShowImage(self.splash_image)

                    # For now, if size mismatch, try to show directly, LCD driver might handle it or crop.
                    # Or, more robustly, resize. Let's try direct show.
                    print(f"Emotion image size {current_pil_image.size} differs from splash size {self.splash_image.size}. Showing directly.")
                    self.display_hardware.ShowImage(current_pil_image)


                self.last_frame_time = now
                self.current_frame_index = (self.current_frame_index + 1) % len(self.animation_frames)
            else:
                # print("Display components not ready for EmotionManager.update_display")
                pass


if __name__ == '__main__':
    print("EmotionManager Test")
    # This test requires assets to be in the expected locations relative to this file,
    # e.g., ../assets/expressions/happy/1.png, etc.
    # And display hardware to be connected.

    # Create dummy asset structure for testing if they don't exist from problematic move step
    DUMMY_ASSET_BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'assets'))
    if not os.path.exists(os.path.join(DUMMY_ASSET_BASE, "expressions")):
        os.makedirs(os.path.join(DUMMY_ASSET_BASE, "expressions", "happy"))
        os.makedirs(os.path.join(DUMMY_ASSET_BASE, "expressions", "sad"))
        # Create dummy 320x240 images for testing
        try:
            img_happy = Image.new("RGB", (320, 240), "yellow")
            draw_h = ImageDraw.Draw(img_happy)
            if display_utils: draw_h.text((10,10), "HAPPY FACE", fill="black", font=display_utils.font3)
            img_happy.save(os.path.join(DUMMY_ASSET_BASE, "expressions", "happy", "1.png"))
            img_happy.save(os.path.join(DUMMY_ASSET_BASE, "expressions", "happy", "2.png"))

            img_sad = Image.new("RGB", (320, 240), "blue")
            draw_s = ImageDraw.Draw(img_sad)
            if display_utils: draw_s.text((10,10), "SAD FACE", fill="white", font=display_utils.font3)
            img_sad.save(os.path.join(DUMMY_ASSET_BASE, "expressions", "sad", "1.png"))
        except Exception as e:
            print(f"Error creating dummy images: {e}")

    emotion_mgr = EmotionManager(asset_base_path=DUMMY_ASSET_BASE)

    if not emotion_mgr.display_hardware:
        print("Display hardware not available, cannot run full visual test.")
    else:
        print("Starting emotion display cycle...")
        emotions_to_cycle = [Emotion.HAPPY, Emotion.SAD, Emotion.NEUTRAL]
        try:
            for i in range(2): # Cycle a few times
                for emotion_state in emotions_to_cycle:
                    emotion_mgr.set_emotion(emotion_state)
                    # Let animation run for a bit
                    for _ in range(20): # Show ~2 seconds of animation (20 frames * 0.1s/frame)
                        emotion_mgr.update_display()
                        time.sleep(emotion_mgr.frame_duration)

            emotion_mgr.set_emotion(Emotion.NEUTRAL) # Return to neutral
            print("Emotion display cycle test complete.")

        except KeyboardInterrupt:
            print("Emotion test interrupted.")
        finally:
            # Clear screen or show neutral face
            if display_utils and emotion_mgr.draw_context and emotion_mgr.splash_image and emotion_mgr.display_hardware:
                emotion_mgr.draw_context.rectangle([(0,0), emotion_mgr.splash_image.size], fill=display_utils.SPLASH_THEME_COLOR)
                display_utils.lcd_draw_string(emotion_mgr.draw_context, 50, 100, "Test End", font_object=display_utils.font3)
                emotion_mgr.display_hardware.ShowImage(emotion_mgr.splash_image)
            print("Cleaned up display.")

    # Clean up dummy assets if they were created by this test script
    # This is a bit risky if real assets had these names, but for isolated test:
    # (Consider more robust cleanup or manual cleanup)
    # For now, this script is illustrative.
    print("EmotionManager test script finished.")
