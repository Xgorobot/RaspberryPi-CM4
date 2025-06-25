import time
import threading
import signal # For graceful shutdown

# Module Imports
try:
    from control.xgolib import init_dog, get_dog_instance
    from emotion.emotion_manager import EmotionManager, Emotion
    from remote.web_server import app as flask_app, socketio as flask_socketio
    from common.buttons import Button
    from common.display_utils import get_display_manager, get_main_draw_context, get_main_splash_image, lcd_draw_string, SPLASH_THEME_COLOR, font2, font3
    # from voice.voice_interaction_manager import VoiceInteractionManager # Import when ready
except ImportError as e:
    print(f"MainApp: Error importing modules. Ensure PYTHONPATH is set correctly or run from dog_app parent. Details: {e}")
    # Fallback for direct execution from dog_app directory or if structure is slightly different
    # This assumes dog_app is the current working directory or on PYTHONPATH
    try:
        print("MainApp: Attempting fallback imports assuming dog_app is project root...")
        from dog_app.control.xgolib import init_dog, get_dog_instance
        from dog_app.emotion.emotion_manager import EmotionManager, Emotion
        from dog_app.remote.web_server import app as flask_app, socketio as flask_socketio
        from dog_app.common.buttons import Button
        from dog_app.common.display_utils import get_display_manager, get_main_draw_context, get_main_splash_image, lcd_draw_string, SPLASH_THEME_COLOR, font2, font3
        # from dog_app.voice.voice_interaction_manager import VoiceInteractionManager
        print("MainApp: Fallback imports successful.")
    except ImportError as e_fallback:
        print(f"MainApp: Fallback imports also failed. Critical error: {e_fallback}")
        # Define dummies if essential for script to not crash immediately for structural checks
        flask_app, flask_socketio, Button, EmotionManager, Emotion, init_dog, get_dog_instance = [None]*7
        get_display_manager, get_main_draw_context, get_main_splash_image, lcd_draw_string = [None]*4
        SPLASH_THEME_COLOR, font2, font3 = [None]*3


# Global state
running = True
dog_instance = None
emotion_mgr = None
# voice_mgr = None # When ready
hw_buttons = None
display_mgr = None
draw_context = None
splash_image = None


def initialize_systems():
    global dog_instance, emotion_mgr, hw_buttons, display_mgr, draw_context, splash_image

    print("MainApp: Initializing systems...")

    # Initialize Dog Control
    if init_dog:
        dog_instance, fw_info, ver_name = init_dog() # Handles chmod
        if dog_instance:
            print(f"MainApp: Dog initialized: {fw_info} ({ver_name}), Battery: {dog_instance.read_battery()}%")
            dog_instance.reset() # Ensure a known starting state
        else:
            print("MainApp: CRITICAL - Failed to initialize dog. Many functions will fail.")
    else:
        print("MainApp: CRITICAL - Dog control module (init_dog) not loaded.")

    # Initialize Display (must be after init_dog if display_utils relies on it for assets/dog info)
    # display_utils initializes its own global display, draw_context, splash_image
    if get_display_manager:
        display_mgr = get_display_manager()
        draw_context = get_main_draw_context()
        splash_image = get_main_splash_image()
        if display_mgr and draw_context and splash_image:
            print("MainApp: Display utilities initialized.")
            # Clear screen with a startup message
            draw_context.rectangle([(0,0), splash_image.size], fill=SPLASH_THEME_COLOR)
            lcd_draw_string(draw_context, 20, 100, "XGO App Starting...", color=(255,255,255), font_object=font3)
            display_mgr.ShowImage(splash_image)
        else:
            print("MainApp: Failed to get display components from display_utils.")
    else:
        print("MainApp: Display utilities not loaded.")


    # Initialize Emotion Manager
    if EmotionManager:
        emotion_mgr = EmotionManager() # Relies on display_utils being initialized
        emotion_mgr.set_emotion(Emotion.NEUTRAL) # Start with a neutral emotion
        print("MainApp: EmotionManager initialized.")
    else:
        print("MainApp: EmotionManager not loaded.")

    # Initialize Hardware Buttons
    if Button:
        try:
            hw_buttons = Button()
            print("MainApp: Hardware buttons initialized.")
        except Exception as e:
            print(f"MainApp: Failed to initialize hardware buttons (GPIO access likely failed): {e}")
            hw_buttons = None # Ensure it's None if init fails
    else:
        print("MainApp: Button class not loaded.")

    # Initialize Voice Interaction Manager (placeholder)
    # if VoiceInteractionManager:
    #     voice_config = {} # Load from a config file ideally
    #     voice_mgr = VoiceInteractionManager(dog_control_module=dog_instance,
    #                                         emotion_manager=emotion_mgr,
    #                                         config=voice_config)
    #     # voice_mgr.start_listening() # Or start based on a button/command
    #     print("MainApp: VoiceInteractionManager initialized (stub).")
    # else:
    #     print("MainApp: VoiceInteractionManager not loaded.")

    print("MainApp: All systems initialization attempt complete.")


def run_web_server():
    if flask_app and flask_socketio:
        print("MainApp: Starting Flask-SocketIO web server on a new thread...")
        # Set use_reloader=False to prevent Flask from running initialization twice
        # allow_unsafe_werkzeug for newer versions if debug=True
        flask_socketio.run(flask_app, host='0.0.0.0', port=5000, debug=False, use_reloader=False, allow_unsafe_werkzeug=True)
    else:
        print("MainApp: Flask app or SocketIO not loaded. Web server cannot start.")

def handle_shutdown_signal(signum, frame):
    global running
    print(f"\nMainApp: Received shutdown signal ({signum}). Cleaning up...")
    running = False

def cleanup_systems():
    print("MainApp: Cleaning up systems...")
    # if voice_mgr:
    #     voice_mgr.stop_listening()
    #     print("MainApp: Voice manager stopped.")

    if dog_instance:
        print("MainApp: Resetting dog position...")
        dog_instance.reset()
        # Consider other cleanup like unloading motors if necessary

    # Display a shutdown message
    if display_mgr and draw_context and splash_image:
        try:
            draw_context.rectangle([(0,0), splash_image.size], fill=SPLASH_THEME_COLOR)
            lcd_draw_string(draw_context, 60, 100, "Shutting Down...", color=(255,255,255), font_object=font3)
            display_mgr.ShowImage(splash_image)
        except Exception as e:
            print(f"MainApp: Error showing shutdown message on display: {e}")

    if hasattr(hw_buttons, 'GPIO') and hw_buttons.GPIO: # If RPi.GPIO was used
        hw_buttons.GPIO.cleanup()
        print("MainApp: GPIO cleanup done.")

    print("MainApp: Cleanup complete. Exiting.")


def main_loop():
    global running, emotion_mgr, hw_buttons

    emotion_cycle = [Emotion.NEUTRAL, Emotion.HAPPY, Emotion.SAD, Emotion.SURPRISED, Emotion.SLEEPY]
    current_emotion_idx = 0

    if emotion_mgr:
        emotion_mgr.set_emotion(emotion_cycle[current_emotion_idx])

    last_button_check_time = time.time()

    while running:
        # Update EmotionManager (for animations, etc.)
        if emotion_mgr:
            emotion_mgr.update_display()

        # Hardware Button Handling (example)
        if hw_buttons and time.time() - last_button_check_time > 0.1: # Poll every 100ms
            if hw_buttons.press_lower_right(): # 'A' button in original mapping
                print("MainApp: Button A (Lower Right) pressed - Cycle Emotion")
                if emotion_mgr:
                    current_emotion_idx = (current_emotion_idx + 1) % len(emotion_cycle)
                    emotion_mgr.set_emotion(emotion_cycle[current_emotion_idx])

            if hw_buttons.press_upper_left(): # 'C' button
                print("MainApp: Button C (Upper Left) pressed - Placeholder")
                # Example: Toggle voice listening
                # if voice_mgr:
                #     if voice_mgr.is_listening: voice_mgr.stop_listening()
                #     else: voice_mgr.start_listening()

            if hw_buttons.press_lower_left(): # 'B' button - often used for exit/back
                print("MainApp: Button B (Lower Left) pressed - Shutdown Request")
                running = False # Signal shutdown

            last_button_check_time = time.time()

        time.sleep(0.05) # Main loop tick rate

if __name__ == "__main__":
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, handle_shutdown_signal)  # Ctrl+C
    signal.signal(signal.SIGTERM, handle_shutdown_signal) # kill command

    initialize_systems()

    if flask_app: # Only start web server if Flask loaded
        web_thread = threading.Thread(target=run_web_server, daemon=True)
        web_thread.start()
    else:
        print("MainApp: Web server thread not started as Flask app is not available.")

    try:
        main_loop()
    except Exception as e:
        print(f"MainApp: Unhandled exception in main loop: {e}")
    finally:
        cleanup_systems()
