import os
from flask import Flask, render_template, Response
from flask_socketio import SocketIO, emit
import time

# Attempt to import DogCamera and dog control functions
try:
    from ..common.camera import DogCamera
    from ..control.xgolib import get_dog_instance, init_dog
except ImportError:
    print("WebServer: Could not import common.camera or control.xgolib via relative imports.")
    # Fallback for different execution context (e.g. if web_server.py is run directly for testing)
    try:
        import sys
        CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
        # Assuming dog_app is the project root directory containing common/, control/, remote/
        PROJECT_ROOT_TEMP = os.path.abspath(os.path.join(CURRENT_DIR, '..', '..'))
        if PROJECT_ROOT_TEMP not in sys.path:
            sys.path.append(PROJECT_ROOT_TEMP)
        from dog_app.common.camera import DogCamera
        from dog_app.control.xgolib import get_dog_instance, init_dog
        print("WebServer: Successfully imported camera and xgolib via sys.path modification.")
    except ImportError as e:
        print(f"WebServer: Critical error importing modules: {e}. Server might not function correctly.")
        DogCamera = None
        get_dog_instance = None
        init_dog = None


# Initialize Flask app and SocketIO
app = Flask(__name__, template_folder='templates') # Ensure Flask looks for templates in the right place
app.config['SECRET_KEY'] = 'secret_key_for_dog_app!' # Change in production
socketio = SocketIO(app)

# Global instances
dog = None
camera = None

def initialize_hardware():
    global dog, camera
    print("WebServer: Initializing hardware...")
    if init_dog: # Check if import was successful
        # Initialize the dog instance (this also handles chmod for serial)
        dog_instance, _, _ = init_dog()
        if dog_instance:
            dog = dog_instance
            print("WebServer: Dog instance initialized.")
            dog.reset() # Start with a reset state
        else:
            print("WebServer: Failed to initialize dog instance.")
            dog = None # Ensure dog is None if init fails
    else:
        print("WebServer: init_dog function not available.")
        dog = None

    if DogCamera: # Check if import was successful
        camera = DogCamera(debug=True) # Enable debug for camera init info
        if not camera.is_opened():
            print("WebServer: Failed to open camera.")
            # camera object will exist but camera.is_opened() will be false
        else:
            print("WebServer: Camera initialized.")
    else:
        print("WebServer: DogCamera class not available.")
        camera = None


# --- HTTP Routes ---
@app.route('/')
def index():
    """Serves the main control page."""
    return render_template('index.html')

def gen_video_frames():
    """Generator function for video streaming."""
    global camera
    if not camera or not camera.is_opened():
        print("Video stream: Camera not available or not open.")
        # Optionally, yield a placeholder image or an error message image
        # For now, just stop if no camera.
        return

    while True:
        success, frame_bytes = camera.get_frame_jpeg()
        if not success or not frame_bytes:
            print("Video stream: Failed to get frame or frame_bytes is None. Trying to reconnect...")
            # Attempt to reconnect camera if frame grab fails
            if camera.reconnect():
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
    global dog
    if not dog:
        print(f"SocketIO: Received command but dog not initialized: {json_data}")
        emit('command_response', {'status': 'Error', 'message': 'Dog not initialized.'})
        return

    command = json_data.get('command')
    value = json_data.get('value')
    print(f"SocketIO: Received command: {command}, Value: {value}")

    try:
        if command == 'forward':
            dog.forward(int(value) if value is not None else 15) # Default speed 15
        elif command == 'backward':
            dog.back(int(value) if value is not None else 15)
        elif command == 'turn_left':
            dog.turnleft(int(value) if value is not None else 30) # Default angle/speed 30
        elif command == 'turn_right':
            dog.turnright(int(value) if value is not None else 30)
        elif command == 'stop_move':
            dog.stop()
        elif command == 'action':
            if value is not None:
                action_id = int(value)
                if 0 <= action_id <= 255: # Action 255 is reset/stop
                    dog.action(action_id, wait=False) # wait=False for responsiveness
                    if action_id == 255: dog.stop() # Ensure full stop for reset action
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
    print("Starting XGO Web Control Server...")
    initialize_hardware()

    print("Hardware initialization attempt complete.")
    if dog:
        print(f"Dog Type: {dog.version}, Battery: {dog.read_battery()}%")
    else:
        print("Dog not available.")
    if camera and camera.is_opened():
        print("Camera is available.")
    else:
        print("Camera not available or not opened.")

    print("Starting Flask-SocketIO server on http://0.0.0.0:5000")
    # use_reloader=False is important for not running initialize_hardware twice in debug mode
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, use_reloader=False, allow_unsafe_werkzeug=True)

```
