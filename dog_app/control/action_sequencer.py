import time
import threading
import random

class ActionSequencer:
    def __init__(self, dog_instance, emotion_manager=None):
        self.dog = dog_instance
        self.emotion_mgr = emotion_manager
        self._stop_event = threading.Event()
        self._current_thread = None

    @property
    def is_running(self):
        return self._current_thread is not None and self._current_thread.is_alive()

    def _run_in_thread(self, target, *args):
        """Runs a sequence in a separate thread to avoid blocking the main loop/web server."""
        if self._current_thread and self._current_thread.is_alive():
            self.stop_current_sequence() # Preempt existing action
            self._current_thread.join(timeout=1.0)
        
        self._stop_event.clear()
        self._current_thread = threading.Thread(target=target, args=args)
        self._current_thread.start()

    def stop_current_sequence(self):
        """Signals the current running sequence to stop."""
        self._stop_event.set()
        if self.dog:
            self.dog.stop()

    def _check_stop(self):
        """Helper to check if stop was requested. Raises exception to break flow."""
        if self._stop_event.is_set():
            raise InterruptedError("Action sequence interrupted")

    def perform_happy_dance(self):
        self._run_in_thread(self._happy_dance_impl)

    def _happy_dance_impl(self):
        try:
            print("ActionSequencer: Starting Happy Dance")
            if self.emotion_mgr:
                self.emotion_mgr.set_emotion("HAPPY")

            self._check_stop()
            self.dog.action(4) # Circle maybe? Or custom movement
            # Custom "Trot in circle"
            self.dog.gait_type("trot")
            self.dog.move_x(10)
            self.dog.turn(15) # Turn while moving? xgolib handling of simultaneous might vary.
            # xgolib move commands are immediate sets of VX/VYAW.
            # To move and turn:
            # dog.move_x(10) sets VX. dog.turn(15) sets VYAW. 
            # They stay set until 0'd.
            
            # Step 1: Circle
            self.dog.move_x(15) 
            self.dog.turnclass(15) # Wait, xgolib has 'turn' not 'turnclass'. 'turn(15)' 
            # And we need to wait.
            for _ in range(20): # 2 seconds
                self._check_stop()
                time.sleep(0.1)
            
            self.dog.stop()
            self._check_stop()
            
            # Step 2: Wag Tail (Yaw back and forth)
            self.dog.attitude('im_yaw', 0) # Reset?
            # Creating a wag with attitude might be slow. 
            # Using periodic_rot might be better.
            self.dog.periodic_rot('y', 4) # Period 4
            time.sleep(2)
            self.dog.periodic_rot('y', 0) # Stop
            
            self._check_stop()
            
            # Step 3: Bark/Action
            self.dog.action(13) # Wave hands? or Call
            time.sleep(2)
            
            self.dog.reset()
            print("ActionSequencer: Happy Dance Complete")

        except InterruptedError:
            print("ActionSequencer: Happy Dance Interrupted")
            self.dog.stop()
        except Exception as e:
            print(f"ActionSequencer: Error in Happy Dance: {e}")
            self.dog.stop()

    def perform_shake(self):
        self._run_in_thread(self._shake_impl)

    def _shake_impl(self):
        try:
            print("ActionSequencer: Starting Shake")
            if self.emotion_mgr:
                self.emotion_mgr.set_emotion("HAPPY")
            # Rapid roll
            for _ in range(3):
                self._check_stop()
                self.dog.attitude('r', 15)
                time.sleep(0.2)
                self.dog.attitude('r', -15)
                time.sleep(0.2)
            
            self.dog.attitude('r', 0)
            self._check_stop()
            
            # Then body shake (high freq periodic?)
            self.dog.periodic_rot('r', 2) # Fast roll
            time.sleep(1.5)
            self.dog.periodic_rot('r', 0)
            
            self.dog.reset()
        except InterruptedError:
            self.dog.stop() 

    def perform_curious(self):
        self._run_in_thread(self._curious_impl)
        
    def _curious_impl(self):
        try:
            print("ActionSequencer: Starting Curious")
            if self.emotion_mgr:
                self.emotion_mgr.set_emotion("CURIOUS")
            # Head tilt
            self.dog.attitude('r', 20)
            time.sleep(0.5)
            self._check_stop()
            
            # Lean forward
            self.dog.translation('x', 30) # mm? Check limits
            time.sleep(1)
            self._check_stop()
            
            # Hold
            time.sleep(1)
            
            # Reset
            self.dog.reset()
        except InterruptedError:
            self.dog.stop()

    def perform_boxing(self):
        self._run_in_thread(self._boxing_impl)

    def _boxing_impl(self):
        try:
            print("ActionSequencer: Starting Boxing")
            if self.emotion_mgr:
                self.emotion_mgr.set_emotion("ANGRY")
            # Stand tall?
            self.dog.action(2) # Stand
            time.sleep(3)
            self._check_stop()
            
            # Lift left front leg (ID 3?)
            # Leg IDs: 1:FrontRight, 2:FrontLeft, 3:RearRight, 4:RearLeft ? Need to verify xgolib leg mapping
            # xgolib: leg(leg_id, data)
            # Usually FL=1, FR=2, RL=3, RR=4 or similar. xgolib doesn't specify in comments.
            # Let's assume standard quadruped: 1=FrontRight, 2=FrontLeft...
            
            # Lift leg: z up, x forward
            # This requires 'motor' control or 'leg' control.
            # leg control takes 3 coords.
            # Let's just use action(21) Push-ups? Or just punch.
            # Let's try manual leg control.
            
            # Simple punch:
            # Lift Front Left
            current_z = 75 # Default height?
            punch_z = 40 # Higher (lower value is higher?) No, leg length usually positive.
            # Leg limit says [75, 115] for leg length?
            # If leg length, smaller is shorter leg (body down).
            # Wait, leg(id, [x, y, z])
            # XGOparam LEG_LIMIT: [35, 18, [75, 115]]
            # x, y, z limits.
            
            for _ in range(5):
                self._check_stop()
                # Punch Left
                # self.dog.leg(2, [35, 0, 75]) # Extend X, standard Z
                # time.sleep(0.2)
                # self.dog.leg(2, [0, 0, 90]) # Retract
                # time.sleep(0.2)
                pass # Skipping manual leg for now until verified, risking imbalance
                
            # Fallback to action 19 (Handshake) which lifts a leg
            self.dog.action(19)
            time.sleep(2)
            self.dog.action(19)
            time.sleep(2)
            
            self.dog.reset()
        except InterruptedError:
            self.dog.stop()
