import threading
import time

class Skill:
    def __init__(self, name, dog_instance, display_manager, camera_instance=None):
        self.name = name
        self.dog = dog_instance
        self.display = display_manager
        self.camera = camera_instance
        self.running = False
        self._thread = None
        self._stop_event = threading.Event()

    def start(self):
        if self.running:
            print(f"Skill {self.name} is already running.")
            return
        
        print(f"Starting skill: {self.name}")
        self.running = True
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_wrapper, daemon=True)
        self._thread.start()

    def stop(self):
        if not self.running:
            return
        
        print(f"Stopping skill: {self.name}")
        self._stop_event.set()
        self.running = False
        if self._thread:
            self._thread.join(timeout=2.0)
            if self._thread.is_alive():
                 print(f"Skill {self.name} thread did not exit cleanly.")
        self.cleanup()

    def _run_wrapper(self):
        try:
            self.run()
        except Exception as e:
            print(f"Error in skill {self.name}: {e}")
        finally:
            self.running = False
            self.cleanup()
            print(f"Skill {self.name} finished.")

    def run(self):
        """Override this method with the skill's main loop."""
        pass

    def cleanup(self):
        """Override this to reset robot state."""
        if self.dog:
            self.dog.stop()


class SkillsManager:
    def __init__(self, dog_instance, display_manager, camera_instance=None):
        self.dog = dog_instance
        self.display = display_manager
        self.camera = camera_instance
        self.skills = {}
        self.current_skill = None

    def register_skill(self, skill_class):
        """Registers a skill class. The class is instantiated only when run?"""
        # Or instantiate them all? Let's instantiate to keep config simple.
        try:
            skill = skill_class(self.dog, self.display, self.camera)
            self.skills[skill.name] = skill
            print(f"SkillsManager: Registered skill '{skill.name}'")
        except Exception as e:
            print(f"SkillsManager: Failed to register skill {skill_class}: {e}")

    def start_skill(self, skill_name):
        if self.current_skill:
            if self.current_skill.name == skill_name and self.current_skill.running:
                print(f"Skill {skill_name} is already running.")
                return
            self.stop_current_skill()
        
        skill = self.skills.get(skill_name)
        if skill:
            self.current_skill = skill
            skill.start()
        else:
            print(f"Skill {skill_name} not found.")

    def stop_current_skill(self):
        if self.current_skill:
            self.current_skill.stop()
            self.current_skill = None
