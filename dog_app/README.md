# XGO Refactored Application (dog_app)

This application is a refactored version of the original XGO robot control software,
organized into a modular structure.

## Modules

The application is divided into the following main modules:

-   `dog_app/control/`: Core robot control logic (interfacing with `xgolib.py`).
-   `dog_app/emotion/`: Manages the robot's emotional state and visual/auditory feedback.
-   `dog_app/remote/`: Provides a web-based remote control interface (Flask + SocketIO).
-   `dog_app/voice/`: (Placeholder) Intended for voice interaction capabilities.
-   `dog_app/common/`: Shared utilities for display, buttons, camera, language, etc.
-   `dog_app/assets/`: Contains static assets like images, expression animations, sounds, and fonts.
-   `dog_app/language/`: Contains language files for localization.

## Setup and Running

### 1. Prerequisites (Manual Steps - CRITICAL)

Before running the application, several manual steps are required due to limitations in automated refactoring of asset paths and system-specific files:

**a. Move Asset Directories:**

The following directories and their contents need to be moved from the original project structure into the `dog_app` structure:

-   Move original `RaspberryPi-CM4-main/demos/expression/` to `dog_app/assets/expressions/`
    ```bash
    # Example: Assuming you are in the parent directory of dog_app and RaspberryPi-CM4-main
    mv RaspberryPi-CM4-main/demos/expression dog_app/assets/expressions
    ```
-   Move original `xgoMusic/` to `dog_app/assets/sounds/emotion_sounds/`
    ```bash
    # Example:
    # mkdir -p dog_app/assets/sounds/emotion_sounds
    # cp -r xgoMusic/* dog_app/assets/sounds/emotion_sounds/
    # rm -rf xgoMusic
    ```
-   Move original `RaspberryPi-CM4-main/language/` to `dog_app/language/`
    ```bash
    # Example:
    mv RaspberryPi-CM4-main/language dog_app/language
    ```

**b. Font File:**

-   Place the `msyh.ttc` font file (Microsoft YaHei) into the `dog_app/assets/fonts/` directory.
-   The original project referenced this font at `/home/jinliang/model/msyh.ttc`. You may need to obtain this font from the original system or use a suitable alternative. If not found, a default PIL font will be used, but visuals might differ.

**c. Permissions:**

-   The application interacts with hardware (serial port for motor control, GPIO for buttons, camera, SPI for LCD). You will likely need to run the main application with `sudo`.
    ```bash
    sudo python3 -m dog_app.main_app
    ```
    (Or `cd dog_app; sudo python3 main_app.py`)
-   The control module attempts `sudo chmod 777 /dev/ttyAMA0`. For a long-term solution, consider adding your user to the `dialout`, `gpio`, and `video` groups, or setting up udev rules.

### 2. Install Dependencies

Install the required Python packages using the provided `requirements.txt` file (located in `dog_app/`).

```bash
pip install -r dog_app/requirements.txt
```
It's recommended to do this in a virtual environment.
Note: `spidev` might require system-level installation on Raspberry Pi (e.g., `sudo apt-get install python3-spidev`).

### 3. Running the Application

Navigate to the parent directory of `dog_app` and run the main application as a module:

```bash
sudo python3 -m dog_app.main_app
```

Or, navigate into the `dog_app` directory and run:

```bash
cd dog_app
sudo python3 main_app.py
```

The web server for remote control should then be accessible at `http://<your_pi_ip>:5000`.
The robot should display a startup message and then a default emotion on its LCD.
Hardware buttons can be used to cycle emotions (default: Lower Right) or trigger shutdown (default: Lower Left).

## Development Notes

-   **Asset Paths:** Code in `dog_app/common/display_utils.py` and `dog_app/emotion/emotion_manager.py` expects assets to be in the new `dog_app/assets/` structure.
-   **Main Entry Point:** `dog_app/main_app.py` initializes and coordinates all modules.
-   **Web Interface:** Access via `http://<raspberry_pi_ip>:5000`. Video streaming is on `/video_feed`. Commands are sent via SocketIO.
-   **Hardware Initialization:** Done in `dog_app/main_app.py` via `initialize_systems()`, which calls `init_dog()` from the control module (handling serial port permissions) and sets up other components.
```
