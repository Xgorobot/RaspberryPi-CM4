import socketio
import time
import sys

sio = socketio.Client()

@sio.event
def connect():
    print("TestClient: Connected to server")

@sio.event
def connect_error(data):
    print(f"TestClient: The connection failed: {data}")

@sio.event
def disconnect():
    print("TestClient: Disconnected from server")

@sio.on('command_response')
def on_response(data):
    print(f"TestClient: Received response: {data}")

@sio.on('status_update')
def on_status(data):
    # Just print one to verify subscription, then ignore to avoid spam
    pass

def test_events():
    try:
        sio.connect('http://localhost:5000')
        time.sleep(1)
        
        # Test 1: Custom Action (Shake)
        print("\n--- Testing Custom Action: Shake ---")
        sio.emit('custom_action', {'command': 'custom_action', 'value': 'shake'})
        time.sleep(2) # Wait for response

        # Test 2: Move Command
        print("\n--- Testing Move Command ---")
        sio.emit('move_command', {'x': 10, 'y': 0, 'turn': 0})
        time.sleep(1)
        sio.emit('move_command', {'x': 0, 'y': 0, 'turn': 0}) # Stop

        # Test 3: Turn Command
        print("\n--- Testing Turn Command ---")
        sio.emit('turn_command', {'speed': 10})
        time.sleep(1)
        sio.emit('turn_command', {'speed': 0}) # Stop

        print("\n--- Tests Sent. Checking logs... ---")
        sio.disconnect()
        
    except Exception as e:
        print(f"TestClient: Error: {e}")

if __name__ == "__main__":
    test_events()
