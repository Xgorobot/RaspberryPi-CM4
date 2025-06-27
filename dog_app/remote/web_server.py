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

# Call camera initialization when module is loaded (if not already done by standalone init).
# This ensures camera is ready for web streaming when web_server is imported.
# The init_web_camera function itself checks if camera_instance_ws is None.
init_web_camera()

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

# --- HTTP Routes ---
@app.route('/')
def index():
    """Serves the main control page."""
    return render_template('index.html')

def gen_video_frames():
    """Generator function for video streaming."""
    global camera_instance_ws # Use the new global variable
    if not camera_instance_ws or not camera_instance_ws.is_opened():
        print("Video stream: Camera not available or not open.")
        # Optionally, yield a placeholder image or an error message image
        # For now, just stop if no camera.
        return

    while True:
        success, frame_bytes = camera_instance_ws.get_frame_jpeg()
        if not success or not frame_bytes:
            print("Video stream: Failed to get frame or frame_bytes is None. Trying to reconnect...")
            # Attempt to reconnect camera if frame grab fails
            if camera_instance_ws.reconnect():
                print("Video stream: Camera reconnected.")
                time.sleep(0.1) # Give it a moment
                continue
            else:
                print("Video stream: Camera reconnect failed. Stopping stream.")
                break # Exit loop if reconnect fails

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        socketio.sleep(0.03) # Limit frame rate slightly to reduce CPU, adjust as needed


@app.route('/video_feed')
def video_feed():
    """Video streaming route."""
    return Response(gen_video_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

# --- SocketIO Event Handlers ---
@socketio.on('connect')
def handle_connect():
    print('SocketIO: Client connected')
    emit('server_message', {'data': 'Connected to XGO Control Server!'})

@socketio.on('disconnect')
def handle_disconnect():
    print('SocketIO: Client disconnected')

@socketio.on('robot_command')
def handle_robot_command(json_data):
    global dog_instance_ws # Use the new global variable
    if not dog_instance_ws:
        print(f"SocketIO: Received command but dog not initialized: {json_data}")
        emit('command_response', {'status': 'Error', 'message': 'Dog not initialized.'})
        return

    command = json_data.get('command')
    value = json_data.get('value')
    print(f"SocketIO: Received command: {command}, Value: {value}")

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
        # Add more commands here:
        # e.g., translation, attitude, specific named actions
        else:
            print(f"SocketIO: Unknown command: {command}")
            emit('command_response', {'status': 'Error', 'message': f'Unknown command: {command}'})
            return

        emit('command_response', {'status': 'Success', 'command': command, 'value': value})

    except ValueError as ve:
        print(f"SocketIO: Value error for command {command}: {ve}")
        emit('command_response', {'status': 'Error', 'message': str(ve)})
    except Exception as e:
        print(f"SocketIO: Error processing command {command}: {e}")
        emit('command_response', {'status': 'Error', 'message': f'Failed to execute {command}: {str(e)}'})


if __name__ == '__main__':
    print("Starting XGO Web Control Server (Standalone Mode)...")
    initialize_hardware(standalone_mode=True) # Indicate standalone execution

    print("Hardware initialization attempt complete (standalone).")
    if dog_instance_ws:
        print(f"Dog Type: {dog_instance_ws.version}, Battery: {dog_instance_ws.read_battery()}%")
    else:
        print("Dog not available (standalone).")
    if camera_instance_ws and camera_instance_ws.is_opened():
        print("Camera is available (standalone).")
    else:
        print("Camera not available or not opened (standalone).")

    print("Starting Flask-SocketIO server on http://0.0.0.0:5000")
    # use_reloader=False is important for not running initialize_hardware twice in debug mode
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, use_reloader=False, allow_unsafe_werkzeug=True)