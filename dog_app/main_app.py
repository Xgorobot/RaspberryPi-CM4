import time
import threading
import signal # For graceful shutdown
import subprocess
import re

def get_ip_info():
    """Returns (ip, ssid) tuple."""
    ip = "N/A"
    ssid = "N/A"
    try:
        # Get IP
        ip_cmd = subprocess.check_output(['hostname', '-I'], encoding='utf-8')
        ip = ip_cmd.strip().split(' ')[0]
        
        # Get SSID
        ssid_cmd = subprocess.check_output(['iwgetid', '-r'], encoding='utf-8')
        ssid = ssid_cmd.strip()
    except Exception:
        pass
    return ip, ssid

# Module Imports
# Module Imports

# Core controls - Critical
try:
    from control.xgolib import init_dog, get_dog_instance
    from common.buttons import Button
    from common.display_utils import get_display_manager, get_main_draw_context, get_main_splash_image, lcd_draw_string, SPLASH_THEME_COLOR, font2, font3
except ImportError as e:
    print(f"MainApp: Critical Import Error (Core): {e}")
    init_dog, get_dog_instance, Button = None, None, None
    get_display_manager, get_main_draw_context, get_main_splash_image, lcd_draw_string = None, None, None, None
    SPLASH_THEME_COLOR, font2, font3 = None, None, None

# Web Server - Critical for remote
try:
    from remote.web_server import app as flask_app, socketio as flask_socketio, set_dog_instance as ws_set_dog_instance, set_camera_instance as ws_set_camera_instance, set_action_sequencer as ws_set_action_sequencer, set_skills_manager as ws_set_skills_manager, set_voice_manager as ws_set_voice_manager
    import remote.web_server as web_server # Access global vars like last_interaction_time
    from flask_socketio import emit
except ImportError as e:
    print(f"MainApp: Critical Import Error (Web): {e}")
    flask_app, flask_socketio, emit = None, None, None
    ws_set_dog_instance, ws_set_camera_instance, ws_set_action_sequencer, ws_set_skills_manager, ws_set_voice_manager = None, None, None, None, None

# Managers - Optional but important
try:
    from emotion.emotion_manager import EmotionManager, Emotion
except ImportError as e:
    print(f"MainApp: Import Error (Emotion): {e}")
    EmotionManager, Emotion = None, None

try:
    from control.action_sequencer import ActionSequencer
except ImportError as e:
    print(f"MainApp: Import Error (ActionSequencer): {e}")
    ActionSequencer = None

try:
    from voice.voice_manager import VoiceManager
except ImportError as e:
    print(f"MainApp: Import Error (Voice): {e}")
    VoiceManager = None

try:
    from skills.manager import SkillsManager
    from skills.ball_tracking import BallTrackingSkill
    from skills.voice_skill import VoiceConversationSkill
except ImportError as e:
    print(f"MainApp: Import Error (Skills): {e}")
    SkillsManager = None
    BallTrackingSkill = None
    print("MainApp: CRITICAL - One or more module imports failed. Dummy objects created. Functionality will be severely limited.")


# Global state
running = True
dog_instance = None
emotion_mgr = None
action_seq = None
action_seq = None
skills_mgr = None
voice_mgr = None
hw_buttons = None
display_mgr = None
draw_context = None
splash_image = None


def initialize_systems():
    global dog_instance, emotion_mgr, hw_buttons, display_mgr, draw_context, splash_image, action_seq, skills_mgr, voice_mgr

    print("MainApp: Initializing systems...")

    # Initialize Dog Control
    if init_dog:
        dog_instance, fw_info, ver_name = init_dog() # Handles chmod
        if dog_instance:
            print(f"MainApp: Dog initialized: {fw_info} ({ver_name}), Battery: {dog_instance.read_battery()}%")
            dog_instance.reset() # Ensure a known starting state
            if ws_set_dog_instance:
                ws_set_dog_instance(dog_instance) # Pass dog_instance to web_server module
            else:
                print("MainApp: Web server's set_dog_instance function not available.")
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
        if web_server: # Assuming web_server module is imported as web_server
            web_server.set_emotion_manager(emotion_mgr)
    else:

        print("MainApp: EmotionManager not loaded.")

    # Initialize ActionSequencer
    if ActionSequencer and dog_instance:
        action_seq = ActionSequencer(dog_instance, emotion_mgr)
        print("MainApp: ActionSequencer initialized.")
        if ws_set_action_sequencer:
            ws_set_action_sequencer(action_seq)
    else:
        print("MainApp: ActionSequencer not loaded or Dog not ready.")

    # Initialize SkillsManager
    if SkillsManager and dog_instance:
         # Need camera instance for skills. WebServer initializes one locally if standalone, 
         # but main_app doesn't import DogCamera? 
         # Wait, main_app doesn't import DogCamera.
         # web_server creates it. 
         # But web_server runs in a thread.
         # Skills need camera.
         # I should initialize Camera in main_app and pass it to web_server AND skills_mgr.
         pass # Handled below by importing DogCamera dynamically or moving import.

    # Camera Initialization for Skills (and WebServer)
    try:
        from common.camera import DogCamera
        camera_instance = DogCamera(debug=True)
        if camera_instance.is_opened():
             print("MainApp: Camera initialized for Skills/Web.")
             if ws_set_camera_instance:
                 ws_set_camera_instance(camera_instance)
        else:
             print("MainApp: Camera failed to open.")
             camera_instance = None
    except ImportError:
        print("MainApp: Could not import DogCamera.")
        camera_instance = None

    if SkillsManager and dog_instance:
        skills_mgr = SkillsManager(dog_instance, display_mgr, camera_instance)
        skills_mgr.register_skill(BallTrackingSkill)
        skills_mgr.register_skill(VoiceConversationSkill)
        print("MainApp: SkillsManager initialized.")
        if ws_set_skills_manager:
            ws_set_skills_manager(skills_mgr)
        
        # UTILITY: Auto-start Voice Chat for testing
        print("MainApp: Auto-starting VoiceChat skill for testing...")
        skills_mgr.start_skill("VoiceChat")


    # Initialize Voice Manager
    if VoiceManager and dog_instance:
        voice_mgr = VoiceManager(dog_instance, skills_mgr, action_seq, emotion_mgr)
        print("MainApp: VoiceManager initialized.")
        if ws_set_voice_manager:
            ws_set_voice_manager(voice_mgr)
    else:
        print("MainApp: VoiceManager not loaded or Dog/Deps not ready.")

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


def status_broadcast_loop():
    """Periodically broadcasts robot status to the Web UI."""
    while True:
        try:
            status = {}
            if dog_instance:
                 try: status['battery'] = dog_instance.read_battery()
                 except: status['battery'] = "??"
                 
                 try: 
                    # Assuming these return raw values, might need formatting
                    status['roll'] = round(dog_instance.read_roll(), 2)
                    status['pitch'] = round(dog_instance.read_pitch(), 2)
                    raw_yaw = dog_instance.read_yaw()
                    status['yaw'] = round(raw_yaw % 360, 2) if raw_yaw is not None else 0
                 except: 
                    status['roll'] = status['pitch'] = status['yaw'] = 0.00
            
            if emotion_mgr:
                 status['emotion'] = emotion_mgr.current_emotion.name
            
            # Simple action status logic
            current_action = "Idle"
            if skills_mgr and skills_mgr.current_skill:
                current_action = f"Skill: {skills_mgr.current_skill.name}"
            elif action_seq and hasattr(action_seq, 'is_running') and action_seq.is_running:
                current_action = "Action Running"
            
            status['action'] = current_action

            # Log status occasionally (e.g. if battery changes or every 5s) - for now print every time for debugging
            print(f"DEBUG Status Broadcast: {status}") 
            flask_socketio.emit('status_update', status)
        except Exception as e:
            print(f"Status Loop Error: {e}")
        
        time.sleep(2)

def main_loop():
    global running, emotion_mgr, hw_buttons, web_server # Ensure web_server is global
 
    emotion_cycle = [Emotion.NEUTRAL, Emotion.HAPPY, Emotion.SAD, Emotion.SURPRISED, Emotion.SLEEPY]
    current_emotion_idx = 0

    if emotion_mgr:
        emotion_mgr.set_emotion(emotion_cycle[current_emotion_idx])

    last_button_check_time = time.time()
    last_auto_check_time = time.time()
    
    # Track state to avoid spamming set_emotion
    is_sleepy = False
    is_low_battery = False
    show_ip_info = False # Toggle for IP display

    last_status_time = 0

    while running:
        # Update Display (Emotion or IP Info)
        if show_ip_info:
            if display_mgr and draw_context and splash_image:
                 # Clear screen
                 draw_context.rectangle([(0,0), splash_image.size], fill=SPLASH_THEME_COLOR)
                 
                 # Draw Info
                 ip, ssid = get_ip_info()
                 lcd_draw_string(draw_context, 10, 80, f"WiFi: {ssid}", color=(255,255,255), font_object=font3)
                 lcd_draw_string(draw_context, 10, 130, f"IP: {ip}", color=(255,255,255), font_object=font3)
                 lcd_draw_string(draw_context, 10, 200, "Press 'C' to Hide", color=(100,100,100), font_object=font2)
                 
                 display_mgr.ShowImage(splash_image)
        elif emotion_mgr:
            emotion_mgr.update_display()

        now = time.time()

        # --- Status Broadcast (every 2s) ---
        if now - last_status_time > 2.0:
            last_status_time = now
            try:
                status = {}
                # 1. Hardware Status (Synchronous read)
                if dog_instance:
                    try: 
                        status['battery'] = dog_instance.read_battery()
                    except: 
                        status['battery'] = 0
                    
                    try: 
                        status['roll'] = round(dog_instance.read_roll(), 2)
                        status['pitch'] = round(dog_instance.read_pitch(), 2)
                        raw_yaw = dog_instance.read_yaw()
                        status['yaw'] = round(raw_yaw % 360, 2) if raw_yaw is not None else 0
                    except: 
                         status['roll'] = status['pitch'] = status['yaw'] = 0.00
                
                # 2. Software Status
                if emotion_mgr:
                    status['emotion'] = emotion_mgr.current_emotion.name
                
                current_action = "Idle"
                if skills_mgr and skills_mgr.current_skill:
                    current_action = f"Skill: {skills_mgr.current_skill.name}"
                elif action_seq and hasattr(action_seq, 'is_running') and action_seq.is_running:
                     current_action = "Action Running"
                status['action'] = current_action

                # print(f"DEBUG Status Broadcast: {status}") 
                flask_socketio.emit('status_update', status)
            except Exception as e:
                print(f"Status Error: {e}")

        # --- Auto Emotion Logic (every 1s) ---
        if emotion_mgr and (now - last_auto_check_time > 1.0):
            last_auto_check_time = now
            
            # 1. Check Battery
            bat = 0
            if dog_instance:
                 try: bat = dog_instance.read_battery()
                 except: bat = 100 
            
            if bat < 20 and bat > 0: # Low battery
                if not is_low_battery:
                    print(f"MainApp: Low Battery ({bat}%) -> SAD")
                    emotion_mgr.set_emotion(Emotion.SAD)
                    is_low_battery = True
            else:
                if is_low_battery: is_low_battery = False
            
            # 2. Check Idle
            time_since_interaction = now - web_server.last_interaction_time
            if not is_low_battery:
                if time_since_interaction > 60:
                    if not is_sleepy and emotion_mgr.current_emotion != Emotion.SLEEPY:
                        print("MainApp: System Idle -> SLEEPY")
                        emotion_mgr.set_emotion(Emotion.SLEEPY)
                        is_sleepy = True
                else: 
                    if is_sleepy: 
                        emotion_mgr.set_emotion(Emotion.NEUTRAL)
                        is_sleepy = False

        # Hardware Button Handling
        if hw_buttons and now - last_button_check_time > 0.1:
            if hw_buttons.press_lower_right(): # 'A' button 
                print("MainApp: Button A (Lower Right) pressed - Cycle Emotion")
                if emotion_mgr:
                    current_emotion_idx = (current_emotion_idx + 1) % len(emotion_cycle)
                    emotion_mgr.set_emotion(emotion_cycle[current_emotion_idx])
                    web_server.update_interaction_time() 

            if hw_buttons.press_upper_left(): # 'C' button
                print("MainApp: Button C (Upper Left) pressed - Toggle IP Display")
                show_ip_info = not show_ip_info
                # Force immediate update if turning on to avoid lag
                if show_ip_info:
                     if display_mgr and draw_context and splash_image:
                         draw_context.rectangle([(0,0), splash_image.size], fill=SPLASH_THEME_COLOR)
                         lcd_draw_string(draw_context, 20, 100, "Loading Network Info...", color=(255,255,255), font_object=font2)
                         display_mgr.ShowImage(splash_image)

            if hw_buttons.press_lower_left(): # 'B' button 
                print("MainApp: Button B (Lower Left) pressed - Shutdown Request")
                running = False 

            last_button_check_time = now

        time.sleep(0.05) # Main loop tick rate

    # Cleanup outside loop
    if dog_instance:
        dog_instance.stop()
    if emotion_mgr:
        emotion_mgr.stop()
    print("MainApp: Loop finished.")

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
