import os
import time
from enum import Enum, auto
from PIL import Image

# Assuming display_utils are in dog_app.common
# Adjust import path if necessary based on how the project is run
try:
    from ..common import display_utils
    from ..common.display_utils import get_main_draw_context, get_main_splash_image, get_display_manager
except ImportError:
    print("EmotionManager: Could not import common.display_utils. Relative import failed.")
    # Fallback for direct execution or different project structure
    try:
        import sys
        # Temporarily add project root if running this file directly for testing
        # This is a hack for development, not for production structure
        CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
        PROJECT_ROOT_TEMP = os.path.abspath(os.path.join(CURRENT_DIR, '..', '..')) # Guessing project root is two levels up
        if PROJECT_ROOT_TEMP not in sys.path:
            sys.path.append(PROJECT_ROOT_TEMP)
        from dog_app.common import display_utils
        from dog_app.common.display_utils import get_main_draw_context, get_main_splash_image, get_display_manager
        print("EmotionManager: Successfully imported display_utils via sys.path modification.")
    except ImportError as e:
        print(f"EmotionManager: Critical error importing display_utils: {e}. Display functions will not work.")
        # Define dummy functions if import fails, so the class can be instantiated
        def get_main_draw_context(): return None
        def get_main_splash_image(): return None
        def get_display_manager(): return None
        display_utils = None


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

    def _get_static_emotion_image_path(self, emotion_name_lower):
        # Corrected path for static images
        return os.path.join(self.asset_base_path, "images", "static_emotions", f"{emotion_name_lower}.png") # Assuming png, original was jpg

    def load_emotion_assets(self, emotion):
        self.animation_frames = []
        self.current_frame_index = 0
        emotion_name_lower = emotion.name.lower()

        # Try loading animation first
        animation_dir = self._get_expression_path(emotion_name_lower)

        # Check if the main "expressions" directory exists, as asset moving was problematic
        if not os.path.exists(os.path.join(self.asset_base_path, "expressions")):
            print(f"Warning: Main expressions directory not found at {os.path.join(self.asset_base_path, 'expressions')}")
            # Try static image as fallback immediately
            static_image_path = self._get_static_emotion_image_path(emotion_name_lower)
            if os.path.exists(static_image_path):
                try:
                    print(f"Loading static image: {static_image_path}")
                    self.animation_frames = [Image.open(static_image_path)]
                except Exception as e:
                    print(f"Error loading static image {static_image_path}: {e}")
            else:
                print(f"Warning: Static emotion image not found: {static_image_path}")
            return

        if os.path.isdir(animation_dir):
            try:
                # Sort files numerically (1.png, 2.png, ..., 10.png)
                frame_files = sorted(
                    [f for f in os.listdir(animation_dir) if f.endswith(".png")],
                    key=lambda x: int(os.path.splitext(x)[0])
                )
                for frame_file in frame_files:
                    frame_path = os.path.join(animation_dir, frame_file)
                    self.animation_frames.append(Image.open(frame_path))
                if self.animation_frames:
                    print(f"Loaded {len(self.animation_frames)} frames for emotion {emotion.name} from {animation_dir}")
                    return # Successfully loaded animation
            except Exception as e:
                print(f"Error loading animation frames for {emotion.name} from {animation_dir}: {e}")
                self.animation_frames = [] # Clear partial load

        # Fallback to static image if animation failed or not found
        static_image_path = self._get_static_emotion_image_path(emotion_name_lower)
        # Try original jpg extension as well from xgoPictures
        if not os.path.exists(static_image_path):
            static_image_path_jpg = os.path.join(self.asset_base_path, "images", "static_emotions", f"{emotion_name_lower}.jpg")
            if os.path.exists(static_image_path_jpg):
                static_image_path = static_image_path_jpg # Use jpg if png not found

        if os.path.exists(static_image_path):
            try:
                print(f"Loading static image as fallback: {static_image_path}")
                self.animation_frames = [Image.open(static_image_path)]
            except Exception as e:
                print(f"Error loading static fallback image {static_image_path}: {e}")
        else:
            print(f"Warning: No animation or static image found for emotion {emotion.name}")
            # Consider loading a default "neutral" or "unknown" image here
            # For now, if NEUTRAL also fails, it will show nothing.
            if emotion != Emotion.NEUTRAL: # Avoid infinite recursion if NEUTRAL fails
                self.load_emotion_assets(Emotion.NEUTRAL)


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

    if not os.path.exists(os.path.join(DUMMY_ASSET_BASE, "images", "static_emotions")):
         os.makedirs(os.path.join(DUMMY_ASSET_BASE, "images", "static_emotions"))
         try:
            img_neutral = Image.new("RGB", (320,240), "grey")
            draw_n = ImageDraw.Draw(img_neutral)
            if display_utils: draw_n.text((10,10), "NEUTRAL FACE", fill="black", font=display_utils.font3)
            img_neutral.save(os.path.join(DUMMY_ASSET_BASE, "images", "static_emotions", "neutral.png"))
         except Exception as e:
            print(f"Error creating dummy neutral image: {e}")


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

```
