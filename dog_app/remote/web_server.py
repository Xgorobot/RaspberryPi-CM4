import os
from flask import Flask, render_template, Response
from flask_socketio import SocketIO, emit
import time

# Attempt to import DogCamera and dog control functions
# Assuming this script is run when 'dog_app' is the current working directory.
try:
    from common.camera import DogCamera
    from control.xgolib import get_dog_instance, init_dog
except ImportError as e:
    print(f"WebServer: Error importing DogCamera or xgolib: {e}. Server might not function correctly.")
    # Define dummies if essential for script to not crash immediately for structural checks
    DogCamera = None
    get_dog_instance = None
    init_dog = None
    print("WebServer: CRITICAL - DogCamera or xgolib import failed. Dummy objects created. Functionality will be severely limited.")


# Initialize Flask app and SocketIO
app = Flask(__name__, template_folder='templates') # Ensure Flask looks for templates in the right place
app.config['SECRET_KEY'] = 'secret_key_for_dog_app!' # Change in production
socketio = SocketIO(app)

# Global instances
# These will be set by main_app.py if it's the entry point,
# or by initialize_hardware() if web_server.py is run directly.
dog_instance_ws = None # Use a distinct name to avoid confusion if run standalone
camera_instance_ws = None

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


# --- HTTP Routes ---
@app.route('/')
def index():
    """Serves the main control page."""
    logger.info("Received request for / (index route)")
    try:
        response = render_template('index.html')
        logger.info("Successfully rendered index.html")
        return response
    except Exception as e:
        logger.error("Error rendering index.html: %s", e, exc_info=True)
        return "Error rendering page.", 500


def gen_video_frames():
    """Generator function for video streaming."""
    global camera_instance_ws # Use the new global variable
    logger.info("gen_video_frames called for /video_feed")
    if not camera_instance_ws:
        logger.warning("Video stream requested, but camera_instance_ws is None.")
        return
    if not camera_instance_ws.is_opened():
        logger.warning("Video stream requested, but camera is not open. Camera status: %s", camera_instance_ws.get_status())
        # Optionally, attempt to open camera here if it makes sense for your design
        # For now, just stop if no camera.
        return

    logger.info("Starting video frame generation loop.")
    while True:
        try:
            success, frame_bytes = camera_instance_ws.get_frame_jpeg()
            if not success or not frame_bytes:
                logger.warning("Video stream: Failed to get frame or frame_bytes is None. Trying to reconnect...")
                # Attempt to reconnect camera if frame grab fails
                if camera_instance_ws.reconnect():
                    logger.info("Video stream: Camera reconnected.")
                    time.sleep(0.1) # Give it a moment
                    continue
                else:
                    logger.warning("Video stream: Camera reconnect failed. Stopping stream.")
                    break # Exit loop if reconnect fails

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
    global dog_instance_ws # Use the new global variable
    logger.info("SocketIO: Received robot_command: %s", json_data)

    if not dog_instance_ws:
        logger.error("SocketIO: Received command %s but dog_instance_ws is None.", json_data.get('command'))
        emit('command_response', {'status': 'Error', 'message': 'Dog not initialized on server.'})
        return

    logger.info("SocketIO: dog_instance_ws type: %s", type(dog_instance_ws))

    command = json_data.get('command')
    value = json_data.get('value')
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
            # Or, specific methods like dog_instance_ws.translate_left(speed)
            dog_instance_ws.translate('y', -int(value) if value is not None else -15) # Example: negative y for left
            logger.info("Executed translate_left with speed: %s", value)
        elif command == 'translate_right':
            dog_instance_ws.translate('y', int(value) if value is not None else 15)  # Example: positive y for right
            logger.info("Executed translate_right with speed: %s", value)
        elif command == 'pitch_up': # Rear down / Front up
            # Assuming dog_instance_ws.attitude('p', angle_or_step)
            dog_instance_ws.attitude('p', int(value) if value is not None else 5) # Example: positive pitch for front up
            logger.info("Executed pitch_up with value: %s", value)
        elif command == 'pitch_down': # Front down / Rear up
            dog_instance_ws.attitude('p', -int(value) if value is not None else -5) # Example: negative pitch for front down
            logger.info("Executed pitch_down with value: %s", value)
        elif command == 'roll_left': # Left down
            dog_instance_ws.attitude('r', -int(value) if value is not None else -5) # Example: negative roll for left down
            logger.info("Executed roll_left with value: %s", value)
        elif command == 'roll_right': # Right down
            dog_instance_ws.attitude('r', int(value) if value is not None else 5) # Example: positive roll for right down
            logger.info("Executed roll_right with value: %s", value)
        elif command == 'emergency_stop':
            dog_instance_ws.stop() # Or a more immediate stop if available e.g. dog_instance_ws.imu_stop(True)
            logger.info("Executed emergency_stop")
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

@socketio.on('request_status')
def handle_request_status():
    """Handles request from client to send current status."""
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

    logger.info("Starting Flask-SocketIO server on http://0.0.0.0:5000")
    # use_reloader=False is important for not running initialize_hardware twice in debug mode
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, use_reloader=False, allow_unsafe_werkzeug=True)