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


class Emotion(Enum):
    NEUTRAL = auto()
    HAPPY = auto()
    SAD = auto()
    ANGRY = auto()
    SURPRISED = auto()
    SLEEPY = auto()
    # Add more emotions as needed

class EmotionManager:
    def __init__(self, asset_base_path=None):
        self.current_emotion = Emotion.NEUTRAL
        self.animation_frames = []
        self.current_frame_index = 0
        self.last_frame_time = 0
        self.frame_duration = 0.1 # seconds, for animations

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

        if not os.path.exists(animation_dir) or not os.path.isdir(animation_dir):
            print(f"Animation directory not found for {emotion.name} at {animation_dir}")
            if emotion != Emotion.NEUTRAL:
                print(f"Attempting to load NEUTRAL animation as fallback.")
                self.load_emotion_assets(Emotion.NEUTRAL) # Fallback to NEUTRAL animation
            else:
                # This means NEUTRAL animation itself is missing or failed to load
                print(f"Critical: NEUTRAL animation not found at {animation_dir}. No fallback available.")
            return

        try:
            # Sort files numerically (1.png, 2.png, ..., 10.png)
            # Filter for .png files and ensure the filename (without extension) is a digit for robust sorting
            frame_files = sorted(
                [f for f in os.listdir(animation_dir) if f.endswith(".png") and os.path.splitext(f)[0].isdigit()],
                key=lambda x: int(os.path.splitext(x)[0])
            )
            if not frame_files: # Handles case where directory exists but contains no valid frames
                print(f"No valid .png animation frames found in {animation_dir} for emotion {emotion.name}")
                if emotion != Emotion.NEUTRAL:
                    print(f"Attempting to load NEUTRAL animation as fallback.")
                    self.load_emotion_assets(Emotion.NEUTRAL)
                else:
                    print(f"Critical: NEUTRAL animation frames not found in {animation_dir}. No fallback available.")
                return

            for frame_file in frame_files:
                frame_path = os.path.join(animation_dir, frame_file)
                self.animation_frames.append(Image.open(frame_path))
            
            if self.animation_frames:
                print(f"Loaded {len(self.animation_frames)} frames for emotion {emotion.name} from {animation_dir}")
            else: # Should be caught by 'if not frame_files' earlier, but as a safeguard
                print(f"No frames loaded for {emotion.name} despite directory existing.")
                if emotion != Emotion.NEUTRAL:
                    self.load_emotion_assets(Emotion.NEUTRAL)

        except Exception as e:
            print(f"Error loading animation frames for {emotion.name} from {animation_dir}: {e}")
            self.animation_frames = [] # Clear partial load
            if emotion != Emotion.NEUTRAL:
                print(f"Attempting to load NEUTRAL animation as fallback due to error.")
                self.load_emotion_assets(Emotion.NEUTRAL)
            else:
                print(f"Critical: Error loading NEUTRAL animation frames from {animation_dir}. No fallback available.")


    def set_emotion(self, new_emotion: Emotion):
        if self.current_emotion != new_emotion:
            print(f"Changing emotion from {self.current_emotion.name} to {new_emotion.name}")
            self.current_emotion = new_emotion
            self.load_emotion_assets(new_emotion)
            # Immediately update display with the first frame of the new emotion
            self.update_display(force_redraw=True)

    def update_display(self, force_redraw=False):
        # --- Sound Playing (Placeholder) ---
        # TODO: Consider if sound should be triggered once on emotion change, or looped, etc.
        # self.play_current_emotion_sound()

        if not self.animation_frames:
            # print(f"No frames for emotion {self.current_emotion.name}")
            # Optionally, clear the emotion area or show a default
            if self.draw_context and self.splash_image and display_utils:
                 # Example: Clear a portion of the screen
                 # Assuming emotion is displayed in a certain rectangle e.g. (0,0, 240,240) for a 240x320 screen in portrait
                 # Or full screen if splash_image is the target.
                 # For now, let's assume the emotion takes over the main splash image.
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
