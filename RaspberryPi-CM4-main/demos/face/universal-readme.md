
# Universal Robot Eyes and Mouth Animation

This repository contains code for simulating facial expressions on a universal robot. The original code was designed for the XGO robot, but it has been adapted to be more universal and work on any system with a screen. Instead of using an LCD screen specific to the XGO robot, this version uses the Matplotlib library for displaying images, making it compatible with a wide range of devices.

![XGO Robot](https://github.com/Keyvanhardani/xgo2-robot-eye-and-mouth/blob/main/universal.png)

## Installation

Before running the script, ensure you have Python installed along with the following libraries:
- PIL (Pillow)
- Matplotlib
- Numpy

You can install these libraries using pip:

```bash
pip install Pillow matplotlib numpy
```

## Usage

To use the script, simply run the `universal-eyes-mouth.py` file. This will start the mouth and eyes animation based on the provided input.

```bash
python universal-eyes-mouth.py
```

## Modifications for Universal Compatibility

The code was modified to replace the LCD screen initialization and display commands with Matplotlib commands. The image rendering and updating mechanism were adjusted to work with Matplotlib, allowing the code to display the robot's facial expressions using Matplotlib figures instead of an LCD screen.

This adaptation makes the code suitable for a variety of platforms and removes the dependency on specific hardware components of the XGO robot.

## Contributing

Feel free to fork this repository and make your contributions. Any enhancements or bug fixes are welcome.

## License

This project is open-source and available under the [MIT License](LICENSE).
