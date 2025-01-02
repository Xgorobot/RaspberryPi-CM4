
# XGO2 Robot Eye and Mouth

This repository contains the open-source code for eye and mouth animations of the XGO2 robot. The code includes algorithms for controlling eye movements and mouth animations based on spoken words, enhancing the robot's ability to communicate and interact.

![XGO Robot](https://github.com/Keyvanhardani/xgo2-robot-eye-and-mouth/blob/main/Xgo.png)

## Features

- Eye blinking and movement animations
- Mouth movement synchronized with spoken words
- Customizable parameters for scaling and timing
- Easy integration with XGO robot components

## Installation

To use this code with your XGO2 robot, follow these steps:

### Clone the repository:
```
git clone https://github.com/Keyvanhardani/xgo2-robot-eye-and-mouth.git
```
### Navigate to the cloned directory:
```
cd xgo2-robot-eye-and-mouth
```
Ensure you have all required dependencies installed. (List any necessary dependencies here.)

## Usage

To start the eye and mouth animations, use the following functions:

```python
from eye_mouth_controller import start_speaking, stop_speaking

# To start the animation
start_speaking("Your text here")

# To stop the animation
stop_speaking()
 
OR 

thread = start_speaking("Your text here")
stop_speaking(thread)

```

## Customization

You can customize the eye and mouth animations by modifying the scale factors and image paths in the `eye_mouth_controller.py` file.

## Contributing

Contributions to this project are welcome. Please fork the repository and submit a pull request with your proposed changes.

## License

This project is licensed under the MIT License - see the LICENSE file for details.



## Acknowledgments

- Thanks to the XGO2 Robot team for their support and collaboration.
- Special thanks to all contributors and the open-source community.


---
Created by Keyvan Hardani 10.2023
