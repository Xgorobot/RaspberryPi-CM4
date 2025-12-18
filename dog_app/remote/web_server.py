import os
from flask import Flask, render_template, Response, request
from flask_socketio import SocketIO, emit
import time
import logging
import cv2
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Attempt to import DogCamera and dog control functions
# Assuming this script is run when 'dog_app' is the current working directory.
try:
    from common.camera import DogCamera
    from control.xgolib import get_dog_instance, init_dog
except ImportError as e:
    logger.error(f"WebServer: Error importing DogCamera or xgolib: {e}. Server might not function correctly.")
    # Define dummies if essential for script to not crash immediately for structural checks
    DogCamera = None
    get_dog_instance = None
    init_dog = None
    logger.critical("WebServer: CRITICAL - DogCamera or xgolib import failed. Dummy objects created. Functionality will be severely limited.")


# Initialize Flask app and SocketIO
app = Flask(__name__, template_folder='templates') # Ensure Flask looks for templates in the right place
app.config['SECRET_KEY'] = 'secret_key_for_dog_app!' # Change in production
# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='gevent')

# Global instances
# These will be set by main_app.py if it's the entry point,
# or by initialize_hardware() if web_server.py is run directly.
dog_instance_ws = None # Use a distinct name to avoid confusion if run standalone
camera_instance_ws = None
action_sequencer_ws = None
skills_manager_ws = None
voice_manager_ws = None

def set_dog_instance(instance):
    """Allows main_app.py to set the dog instance."""
    global dog_instance_ws
    dog_instance_ws = instance
    print(f"WebServer: Dog instance set by external module: {type(dog_instance_ws)}")

def set_camera_instance(instance):
    """Allows main_app.py to set the camera instance if needed."""
    global camera_instance_ws
    camera_instance_ws = instance
    print(f"WebServer: Camera instance set by external module: {type(camera_instance_ws)}")

def set_action_sequencer(instance):
    """Allows main_app.py to set the action sequencer instance."""
    global action_sequencer_ws
    action_sequencer_ws = instance
    print(f"WebServer: Action Sequencer instance set: {type(action_sequencer_ws)}")

def set_skills_manager(instance):
    """Allows main_app.py to set the skills manager instance."""
    global skills_manager_ws
    skills_manager_ws = instance
    print(f"WebServer: Skills Manager instance set: {type(skills_manager_ws)}")

def set_voice_manager(instance):
    """Allows main_app.py to set the voice manager instance."""
    global voice_manager_ws
    voice_manager_ws = instance
    print(f"WebServer: Voice Manager instance set: {type(voice_manager_ws)}")

emotion_manager_ws = None
def set_emotion_manager(instance):
    global emotion_manager_ws
    emotion_manager_ws = instance
    print(f"WebServer: Emotion Manager instance set: {type(emotion_manager_ws)}")

@socketio.on('eco_mode')
def handle_eco_mode(json_data):
    """Handles toggle for Eco Mode (Fast Charge)."""
    enable = json_data.get('enable', False)
    logger.info(f"SocketIO: Eco Mode {'ENABLED' if enable else 'DISABLED'}")
    
    # 1. Handle Camera
    global camera_instance_ws
    if camera_instance_ws:
        if enable:
            camera_instance_ws.stop()
        else:
            camera_instance_ws.start()
    
    # 2. Handle Screen (EmotionManager)
    global emotion_manager_ws
    if emotion_manager_ws:
         emotion_manager_ws.set_enabled(not enable) # enable=True means EcoMode=True means ScreenEnabled=False

    # Update global state
    global eco_mode_state
    eco_mode_state = enable
    emit('eco_mode_response', {'enabled': enable}, broadcast=True)

eco_mode_state = False

@socketio.on('connect')
def handle_connect():
    global eco_mode_state
    logger.info("SocketIO: Client connected")
    emit('eco_mode_response', {'enabled': eco_mode_state})

@socketio.on('get_eco_status')
def handle_get_eco_status():
    global eco_mode_state
    logger.info("SocketIO: Client requested Eco Status")
    emit('eco_mode_response', {'enabled': eco_mode_state})



def initialize_hardware(standalone_mode=False):
    """
    Initializes hardware if web_server.py is run standalone
    or if explicitly called.
    """
    global dog_instance_ws, camera_instance_ws

    if standalone_mode:
        print("WebServer: Initializing hardware in standalone mode...")
        if init_dog: # Check if import was successful
            # Initialize the dog instance (this also handles chmod for serial)
            temp_dog, _, _ = init_dog()
            if temp_dog:
                dog_instance_ws = temp_dog
                print("WebServer: Dog instance initialized (standalone).")
                dog_instance_ws.reset() # Start with a reset state
            else:
                print("WebServer: Failed to initialize dog instance (standalone).")
        else:
            print("WebServer: init_dog function not available (standalone).")

        if DogCamera: # Check if import was successful
            camera_instance_ws = DogCamera(debug=True) # Enable debug for camera init info
            if not camera_instance_ws.is_opened():
                print("WebServer: Failed to open camera (standalone).")
            else:
                print("WebServer: Camera initialized (standalone).")
        else:
            print("WebServer: DogCamera class not available (standalone).")
    else:
        print("WebServer: Running in integrated mode. Expecting instances to be set externally.")

def init_web_camera():
    """Initializes the camera for the web server's video stream."""
    global camera_instance_ws
    if camera_instance_ws is None: # Only initialize if not already set (e.g. by main_app)
        if DogCamera:
            print("WebServer: Initializing camera for video stream...")
            camera_instance_ws = DogCamera(debug=True)
            if not camera_instance_ws.is_opened():
                print("WebServer: Failed to open camera for video stream.")
            else:
                print("WebServer: Camera for video stream initialized.")
        else:
            print("WebServer: DogCamera class not available, video stream will not work.")

# Call camera initialization now that the function is defined.
init_web_camera()

import logging
import logging.handlers # For file handler

# --- Logger Setup ---
# Get a specific logger for this module
logger = logging.getLogger(__name__) # Use module's name for the logger
logger.setLevel(logging.INFO) # Set the logging level

# Create a file handler to write logs to a file
log_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'web_server.log')
file_handler = logging.FileHandler(log_file_path)
file_handler.setLevel(logging.INFO)

# Create a formatter and set it for the handler
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

# Add the handler to the logger
# Check if handlers are already present to avoid duplication if module is reloaded (though less common for web apps)
if not logger.handlers:
    logger.addHandler(file_handler)
    # Optionally, to also see logs in console if running standalone and debugging:
    # console_handler = logging.StreamHandler()
    # console_handler.setFormatter(formatter)
    # logger.addHandler(console_handler)

logger.info("WebServer logging initialized to file: %s", log_file_path)


# Global Interaction Tracker
last_interaction_time = time.time()

def update_interaction_time():
    global last_interaction_time
    last_interaction_time = time.time()

# --- HTTP Routes ---
@app.route('/')
def index():
    """Serves the main control page."""
    update_interaction_time()
    logger.info("Received request for / (index route)")
    try:
        response = render_template('index.html')
        logger.info("Successfully rendered index.html")
        return response
    except Exception as e:
        logger.error("Error rendering index.html: %s", e, exc_info=True)
        return "Error rendering page.", 500


# Pre-generate a black frame for Eco Mode
try:
    # 320x240 black image
    _black_img = np.zeros((240, 320, 3), dtype=np.uint8)
    _, _black_frame_jpeg = cv2.imencode('.jpg', _black_img)
    BLACK_FRAME_BYTES = _black_frame_jpeg.tobytes()
except Exception as e:
    logger.error(f"Failed to create black frame: {e}")
    BLACK_FRAME_BYTES = b''

def gen_video_frames():
    """Generator function for video streaming."""
    global camera_instance_ws # Use the new global variable
    logger.info("gen_video_frames called for /video_feed")
    if not camera_instance_ws:
        logger.warning("Video stream requested, but camera_instance_ws is None.")
        return
    if not camera_instance_ws.is_opened():
        # If not opened, check if it's due to Eco Mode. If so, stream black.
        pass 
        #logger.warning("Video stream requested, but camera is not open. Camera status: %s", camera_instance_ws.get_status())
        #return

    logger.info("Starting video frame generation loop.")
    while True:
        # Check global Eco Mode check
        if eco_mode_state:
            time.sleep(1.0) # Sleep to save CPU
            if BLACK_FRAME_BYTES:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + BLACK_FRAME_BYTES + b'\r\n')
            continue       # Skip frame fetching

        try:
            if not camera_instance_ws.is_opened():
                # logic to handle closed camera (wait for it to open or exit)
                time.sleep(0.5)
                continue 
            
            success, frame_bytes = camera_instance_ws.get_frame_jpeg()
            if not success or not frame_bytes:
                # Double check Eco Mode before reconnecting (race condition)
                if eco_mode_state: continue
                
                logger.warning("Video stream: Failed to get frame. Reconnecting...")
                if camera_instance_ws.reconnect():
                    logger.info("Camera reconnected.")
                    continue
                else:
                    break

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            socketio.sleep(0.03) # Limit frame rate slightly to reduce CPU, adjust as needed
        except Exception as e:
            logger.error("Error in video frame generation loop: %s", e, exc_info=True)
            break # Exit loop on error


@app.route('/video_feed')
def video_feed():
    """Video streaming route."""
    return Response(gen_video_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

# --- SocketIO Event Handlers ---
@socketio.on('connect')
def handle_connect():
    logger.info('SocketIO: Client connected')
    emit('server_message', {'data': 'Connected to XGO Control Server!'})

@socketio.on('disconnect')
def handle_disconnect():
    logger.info('SocketIO: Client disconnected')

@socketio.on('robot_command')
def handle_robot_command(json_data):
    """
    Handles generic robot commands.
    """
    global dog_instance_ws
    logger.info(f"SocketIO: Received robot_command: {json_data}")
    if not dog_instance_ws: return

    try:
        cmd = json_data.get('command')
        val = json_data.get('value')
        if cmd == 'action':
            dog_instance_ws.action(int(val))
        elif cmd == 'height':
             dog_instance_ws.translation('z', int(val))
    except Exception as e:
        logger.error(f"Error in robot_command: {e}")

@socketio.on('motor_command')
def handle_motor_command(data):
    """Handles motor load/unload commands."""
    update_interaction_time()
    global dog_instance_ws
    if not dog_instance_ws:
        logger.error("Motor command received but dog_instance_ws is None.")
        emit('command_response', {'status': 'Error', 'message': 'Dog not initialized on server.'})
        return

    action = data.get('action')
    logger.info(f"Received Motor Command: {action}")
    
    if action == 'load':
        logger.info("Executing Load Motors...")
        print(">>> DEBUG: Executing Load Motors") # Direct stdout debug
        if dog_instance_ws:
            print(">>> DEBUG: Dog Instance Found. Sending Load.")
            logger.info("Sending load_allmotor()...")
            dog_instance_ws.load_allmotor()
            
            import time
            logger.info("Waiting 1.0s...")
            time.sleep(1.0) 
            
            logger.info("Sending reset() to clear state...")
            dog_instance_ws.reset()
            time.sleep(0.5)

            logger.info("Sending action(2) [Stand]...")
            dog_instance_ws.action(2) 
            
            logger.info("Load Sequence Complete.")
        
        emit('command_response', {'status': 'Success', 'message': 'Motors loaded and reset.'})
        return

    elif action == 'unload':
         def soft_unload_task():
             try:
                 logger.info("Soft Unload Task Started")
                 if dog_instance_ws:
                     # Strategy: Custom Lie Down Pose
                     flat_pose = [-73.0, 91.75, 7.42, -69.94, 88.01, 6.93, -73.0, 86.76, 9.6, -73.0, 93.0, 1.82, 0.76, 50.0, -71.76]
                     
                     has_motors = hasattr(dog_instance_ws, 'motors')
                     logger.info(f"Using Custom Pose... (Has motors method: {has_motors})")
                     
                     if has_motors:
                         dog_instance_ws.motors(flat_pose)
                         import time
                         time.sleep(3.0) # Thread safe sleep
                     else:
                         logger.warning("xgolib missing 'motors' method, falling back to action(1)")
                         dog_instance_ws.action(1)
                         import time
                         time.sleep(2.0)

                     logger.info("Soft Unload: Unloading motors NOW")
                     if dog_instance_ws:
                         dog_instance_ws.unload_allmotor()
             except Exception as e:
                 logger.error(f"Soft Unload Exception: {e}")
                 # Emergency unload fallback
                 if dog_instance_ws: dog_instance_ws.unload_allmotor()

         # Use threading.Thread for immediate execution
         import threading
         t = threading.Thread(target=soft_unload_task)
         t.daemon = True
         t.start()
         emit('command_response', {'status': 'Success', 'message': 'Soft Unload started.'})
         return

    logger.info("SocketIO: dog_instance_ws type: %s", type(dog_instance_ws))

    command = data.get('command')
    value = data.get('value')
    logger.info("SocketIO: Processing command: %s, Value: %s", command, value)

    try:
        if command == 'forward':
            dog_instance_ws.forward(int(value) if value is not None else 15) # Default speed 15
        elif command == 'backward':
            dog_instance_ws.back(int(value) if value is not None else 15)
        elif command == 'turn_left':
            dog_instance_ws.turnleft(int(value) if value is not None else 30) # Default angle/speed 30
        elif command == 'turn_right':
            dog_instance_ws.turnright(int(value) if value is not None else 30)
        elif command == 'stop_move':
            dog_instance_ws.stop()
        elif command == 'action':
            if value is not None:
                action_id = int(value)
                if 0 <= action_id <= 255: # Action 255 is reset/stop
                    dog_instance_ws.action(action_id, wait=False) # wait=False for responsiveness
                    if action_id == 255: dog_instance_ws.stop() # Ensure full stop for reset action
                else:
                    raise ValueError("Action ID out of range (0-255)")
            else:
                raise ValueError("Action ID not provided")
        elif command == 'translate_left':
            # Assuming dog_instance_ws has a method like translate('y', speed)
            # The value from joystick is speed. Negative for left, Positive for right if using a single translate y.
            # Or, specific methods like dog_instance_ws.left(speed)
            # xgolib.left() calls move_y(positive_value), xgolib.right() calls move_y(negative_value)
            # So, for JS 'translate_left', we want dog.left(), which is move_y(positive_value)
            dog_instance_ws.move_y(int(value) if value is not None else 15)
            logger.info("Executed translate_left (move_y positive) with speed: %s", value)
        elif command == 'translate_right':
            # For JS 'translate_right', we want dog.right(), which is move_y(negative_value)
            dog_instance_ws.move_y(-int(value) if value is not None else -15)
            logger.info("Executed translate_right (move_y negative) with speed: %s", value)
        elif command == 'pitch_up': # Rear down / Front up
            # Assuming dog_instance_ws.attitude('p', angle_or_step)
            # Positive value for pitch up (front of dog raises)
            dog_instance_ws.attitude('p', int(value) if value is not None else 5)
            logger.info("Executed pitch_up with value: %s", value)
        elif command == 'pitch_down': # Front down / Rear up
            # Negative value for pitch down (front of dog lowers)
            dog_instance_ws.attitude('p', -int(value) if value is not None else -5)
            logger.info("Executed pitch_down with value: %s", value)
        elif command == 'roll_left': # Left side down, right side up
            # Negative value for roll left
            dog_instance_ws.attitude('r', -int(value) if value is not None else -5)
            logger.info("Executed roll_left with value: %s", value)
        elif command == 'roll_right': # Right side down, left side up
            # Positive value for roll right
            dog_instance_ws.attitude('r', int(value) if value is not None else 5)
            logger.info("Executed roll_right with value: %s", value)
        elif command == 'emergency_stop':
            dog_instance_ws.stop() # Or a more immediate stop if available e.g. dog_instance_ws.imu_stop(True)
            logger.info("Executed emergency_stop")
        elif command == 'turn_left_by_angle':
            angle = int(value) if value is not None else 30
            dog_instance_ws.turn_by(-angle) # Negative angle for left turn
            logger.info("Executed turn_left_by_angle with angle: %s", angle)
        elif command == 'turn_right_by_angle':
            angle = int(value) if value is not None else 30
            dog_instance_ws.turn_by(angle)  # Positive angle for right turn
            logger.info("Executed turn_right_by_angle with angle: %s", angle)
        elif command == 'set_gait':
            gait_name = str(value).lower() # Ensure lowercase, e.g., "walk" or "trot"
            if hasattr(dog_instance_ws, 'gait_type'):
                dog_instance_ws.gait_type(gait_name)
                logger.info("Executed set_gait with type: %s", gait_name)
                # Optionally, set pace based on gait, or allow separate pace control
                if gait_name == "trot":
                    if hasattr(dog_instance_ws, 'pace'):
                        dog_instance_ws.pace("high") # Example: trot uses high pace
                        logger.info("Set pace to high for trot.")
                elif gait_name == "walk":
                     if hasattr(dog_instance_ws, 'pace'):
                        dog_instance_ws.pace("normal") # Example: walk uses normal pace
                        logger.info("Set pace to normal for walk.")
            else:
                logger.warning("dog_instance_ws does not have gait_type method.")
                emit('command_response', {'status': 'Error', 'message': 'Gait control not available.'})
                return
        elif command == 'custom_action':
            action_name = str(value)
            logger.info("SocketIO: Received custom_action: %s", action_name)
            if action_sequencer_ws:
                if action_name == 'happy_dance':
                    action_sequencer_ws.perform_happy_dance()
                elif action_name == 'shake':
                    action_sequencer_ws.perform_shake()
                elif action_name == 'curious':
                    action_sequencer_ws.perform_curious()
                elif action_name == 'boxing':
                    action_sequencer_ws.perform_boxing()
                else:
                    logger.warning(f"Unknown custom action: {action_name}")
                    emit('command_response', {'status': 'Error', 'message': f'Unknown custom action: {action_name}'})
                    return
                emit('command_response', {'status': 'Success', 'command': command, 'value': value})
            else:
                logger.warning("Action Sequencer not available via WebServer.")
                emit('command_response', {'status': 'Error', 'message': 'Action Sequencer not available.'})
                return

        elif command == 'skill_command':
            skill_name = str(value)
            action = json_data.get('action', 'start') # 'start' or 'stop'
            logger.info("SocketIO: Received skill_command: %s, Action: %s", skill_name, action)
            
            if skills_manager_ws:
                if action == 'start':
                    skills_manager_ws.start_skill(skill_name)
                    emit('command_response', {'status': 'Success', 'message': f'Started skill: {skill_name}'})
                elif action == 'stop':
                    skills_manager_ws.stop_current_skill()
                    emit('command_response', {'status': 'Success', 'message': 'Stopped current skill'})
                else:
                    emit('command_response', {'status': 'Error', 'message': f'Unknown skill action: {action}'})
            else:
                 logger.warning("Skills Manager not available via WebServer.")
                 emit('command_response', {'status': 'Error', 'message': 'Skills Manager not available.'})


                 logger.warning("Skills Manager not available via WebServer.")
                 emit('command_response', {'status': 'Error', 'message': 'Skills Manager not available.'})

        elif command == 'voice_command':
            text_command = str(value)
            logger.info("SocketIO: Received voice_command: %s", text_command)
            if voice_manager_ws:
                success = voice_manager_ws.process_command(text_command)
                status = 'Success' if success else 'Failed (No Match)'
                emit('command_response', {'status': status, 'message': f'Processed: {text_command}'})
            else:
                logger.warning("Voice Manager not available via WebServer.")
                emit('command_response', {'status': 'Error', 'message': 'Voice Manager not available.'})

        # Add more commands here:
        # e.g., specific named actions
        else:
            logger.warning("SocketIO: Unknown command: %s", command)
            emit('command_response', {'status': 'Error', 'message': f'Unknown command: {command}'})
            return

        logger.info("SocketIO: Command %s executed successfully.", command)
        emit('command_response', {'status': 'Success', 'command': command, 'value': value})

    except ValueError as ve:
        logger.error("SocketIO: Value error for command %s with value %s: %s", command, value, ve, exc_info=True)
        emit('command_response', {'status': 'Error', 'message': str(ve)})
    except Exception as e:
        logger.error("SocketIO: General error processing command %s with value %s: %s", command, value, e, exc_info=True)
        emit('command_response', {'status': 'Error', 'message': f'Failed to execute {command}: {str(e)}'})

@socketio.on('move_command')
def handle_move_command(json_data):
    """Handles movement command from joystick."""
    update_interaction_time()
    global dog_instance_ws
    if not dog_instance_ws:
        return
    
    try:
        x = float(json_data.get('x', 0))
        y = float(json_data.get('y', 0))
        # xgolib usually expects int step/speed, but might handle float. 
        # Casting to int to be safe as per original 'move_x' usage pattern.
        # But for smooth control, maybe keep logic:
        # move_x(step): step is speed/distance.
        
        dog_instance_ws.move_x(int(x))
        dog_instance_ws.move_y(int(y))
        
    except Exception as e:
        logger.error(f"Error in handle_move_command: {e}")

@socketio.on('turn_command')
def handle_turn_command(json_data):
    """Handles continuous turning from joystick."""
    update_interaction_time()
    global dog_instance_ws
    if not dog_instance_ws:
        return

    try:
        speed = float(json_data.get('speed', 0))
        dog_instance_ws.turn(int(speed)) 
    except Exception as e:
        logger.error(f"Error in handle_turn_command: {e}")

@socketio.on('custom_action')
def handle_custom_action_event(json_data):
    """Handles custom actions sent via specific event."""
    update_interaction_time()
    global action_sequencer_ws
    logger.info(f"SocketIO: Received custom_action event: {json_data}")
    
    if not action_sequencer_ws:
        emit('command_response', {'status': 'Error', 'message': 'Action Sequencer not available.'})
        return

    action_name = json_data.get('value')
    if action_name == 'happy_dance':
        action_sequencer_ws.perform_happy_dance()
    elif action_name == 'shake':
        action_sequencer_ws.perform_shake()
    elif action_name == 'curious':
        action_sequencer_ws.perform_curious()
    elif action_name == 'boxing':
        action_sequencer_ws.perform_boxing()
    else:
        emit('command_response', {'status': 'Error', 'message': f'Unknown custom action: {action_name}'})

@socketio.on('pitch_command')
def handle_pitch_command(json_data):
    """Handles continuous pitch from joystick."""
    update_interaction_time()
    global dog_instance_ws
    if not dog_instance_ws:
        return

    try:
        value = float(json_data.get('value', 0))
        # attitude('p', value) sets the pitch angle. 
        # Joystick sends continuous stream? Or absolute position?
        # Joystick sends value centered at 0.
        # If we just set attitude to this value, it will track the stick.
        # Max pitch usually around 15-20 degrees.
        # Stick value (y * 15) gives -15 to +15. This seems appropriate for direct mapping.
        dog_instance_ws.attitude('p', value)
    except Exception as e:
        logger.error(f"Error in handle_pitch_command: {e}")

@socketio.on('skill_command')
def handle_skill_command_event(json_data):
    """Handles skill commands."""
    update_interaction_time()
    global skills_manager_ws
    
    command = json_data.get('command') # Redundant if event is skill_command
    skill_name = json_data.get('value')
    action = json_data.get('action')

    logger.info(f"SocketIO: Received skill_command: {skill_name}, action: {action}")

    if not skills_manager_ws:
         emit('command_response', {'status': 'Error', 'message': 'Skills Manager not available.'})
         return

    if action == 'start':
        skills_manager_ws.start_skill(skill_name)
    elif action == 'stop':
        skills_manager_ws.stop_current_skill()

@socketio.on('client_log')
def handle_client_log(json_data):
    """Logs messages from the client."""
    update_interaction_time()
    msg = json_data.get('msg', '')
    logger.info(f"CLIENT_LOG: {msg}")

@socketio.on('request_status')
def handle_request_status():
    """Handles request from client to send current status."""
    # Status update is periodic, but client can request immediate update
    # Here we don't necessarily update interaction time as this is automatic polling usually?
    # If it's used for heartbeat, updating it prevents sleep.
    # Let's assume manual request or heartbeat keeps it awake. 
    # If we want auto-sleep, we should distinguish "passive" vs "active".
    # But usually request_status is not frequent or sent by user action.
    # Let's NOT update for status request to allow sleep if user is just watching video.
    pass

    global dog_instance_ws
    logger.info("SocketIO: Received request_status")

    battery_level = None
    wifi_strength = None
    dog_status = "Unknown"

    if dog_instance_ws:
        try:
            battery_level = dog_instance_ws.read_battery()
            # Assuming a method like dog_instance_ws.get_status() or similar might exist
            # For now, using a generic status if specific one isn't available.
            if hasattr(dog_instance_ws, 'get_current_mode'): # Example attribute
                 dog_status = dog_instance_ws.get_current_mode()
            elif hasattr(dog_instance_ws, 'is_standing'): # another example
                 dog_status = "Standing" if dog_instance_ws.is_standing() else "Not Standing"
            else:
                 dog_status = "Operating" # Generic status
            logger.info(f"Dog instance available: Battery={battery_level}, Status={dog_status}")
        except Exception as e:
            logger.error(f"Error querying dog instance for status: {e}")
            dog_status = "Error"
    else:
        logger.warning("Dog instance not available for status query.")
        dog_status = "Not Connected"

    try:
        # Placeholder for WiFi signal strength - this is platform specific
        # You'll need to implement get_wifi_signal_strength() based on your OS/hardware
        wifi_strength = get_wifi_signal_strength()
        if wifi_strength is None:
             wifi_strength = "N/A"
    except NameError: # Function not defined
        logger.warning("get_wifi_signal_strength() function is not defined. WiFi strength will be N/A.")
        wifi_strength = "N/A"
    except Exception as e:
        logger.error(f"Error getting WiFi signal strength: {e}")
        wifi_strength = "Error"

    status_data = {
        'battery': battery_level,
        'wifi_strength': wifi_strength,
        'dog_status': dog_status
    }
    logger.info(f"Sending status_update: {status_data}")
    emit('status_update', status_data)

def get_wifi_signal_strength():
    """
    Placeholder function to get WiFi signal strength.
    This needs to be implemented based on the specific operating system and hardware.
    Example for Linux using iwconfig (requires wireless-tools to be installed):
    """
    # import subprocess
    # try:
    #     output = subprocess.check_output(['iwconfig', 'wlan0'], text=True) # Replace wlan0 with your interface
    #     for line in output.split('\n'):
    #         if 'Signal level=' in line:
    #             # Example: Signal level=-50 dBm
    #             signal = line.split('Signal level=')[1].split(' ')[0]
    #             return signal # Returns something like "-50"
    #         elif 'Link Quality=' in line:
    #             # Example: Link Quality=70/70
    #             quality = line.split('Link Quality=')[1].split(' ')[0]
    #             return quality # Returns something like "70/70"
    # except FileNotFoundError:
    #     logger.warning("iwconfig command not found. Cannot get WiFi signal strength.")
    #     return None
    # except Exception as e:
    #     logger.error(f"Error executing iwconfig: {e}")
    #     return None
    logger.info("get_wifi_signal_strength: Placeholder function called. Returning None.")
    return None # Return None if not implemented or error


if __name__ == '__main__':
    # Note: The logger for the module is already configured with a FileHandler.
    # If running standalone, messages will go to web_server.log.
    # If you also want console output for standalone, uncomment the console_handler lines in logger setup.
    logger.info("Starting XGO Web Control Server (Standalone Mode)...")
    initialize_hardware(standalone_mode=True) # Indicate standalone execution

    logger.info("Hardware initialization attempt complete (standalone).")
    if dog_instance_ws:
        logger.info("Dog Type: %s, Battery: %s%%", dog_instance_ws.version, dog_instance_ws.read_battery())
    else:
        logger.warning("Dog not available (standalone).")
    if camera_instance_ws and camera_instance_ws.is_opened():
        logger.info("Camera is available (standalone).")
    else:
        logger.warning("Camera not available or not opened (standalone).")

    # use_reloader=False is important for not running initialize_hardware twice in debug mode
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, use_reloader=False, allow_unsafe_werkzeug=True)

import subprocess

@socketio.on('volume_command')
def handle_volume_command(json_data):
    """Handles system volume control."""
    update_interaction_time()
    try:
        volume = int(json_data.get('value', 50))
        # Clamp between 0 and 100
        volume = max(0, min(100, volume))
        
        logger.info(f"Setting System Volume to {volume}%")
        
        # Using amixer to set Master volume
        # 'amixer set Master 50%' works on most ALSA setups
        subprocess.run(['amixer', 'set', 'Master', f'{volume}%'], check=False)
        
        # Some systems might use 'PCM' or 'Headphone' if Master doesn't exist
        # We can try setting PCM as well just in case
        subprocess.run(['amixer', 'set', 'PCM', f'{volume}%'], check=False)
        
    except Exception as e:
        logger.error(f"Error setting volume: {e}")