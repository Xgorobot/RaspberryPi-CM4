#RaspberryPi-CM4
RaspberryPi-CM4 AI module code

## About this repository

This repository contains the following components:

- [app/](https://github.com/Xgorobot/RaspberryPi-CM4/tree/main/app) -- Raspberry Pi server for controlling a xgo2 using a mobile application.
- [demos/](https://github.com/Xgorobot/RaspberryPi-CM4/tree/main/demos) -- Officially created demos that can be run directly.
- [extra_demos/](https://github.com/Xgorobot/RaspberryPi-CM4/tree/main/extra_demos) -- Some immature demo programs are provided for learning and reference purposes only. There is no guarantee that they will function properly.
- [pics/](https://github.com/Xgorobot/RaspberryPi-CM4/tree/main/pics) -- Image resources used in the built-in program..
- [tools/](https://github.com/Xgorobot/RaspberryPi-CM4/tree/main/tools) --
- [volume/](https://github.com/Xgorobot/RaspberryPi-CM4/tree/main/volume) -- Volume configuration file.
Some testing and compilation tools.

If you want to upgrade xgo-pythonlib,please run these two commands:

```
pip install --upgrade xgo-pythonlib
sudo pip install --upgrade xgo-pythonlib
```

[Xgorobot/XGO-PythonLib(github.com)](https://github.com/Xgorobot/XGO-PythonLib)

## ChangeLog
### [xgo0627] - 2023-6-27

#### Fixed
- English language keywords have been revised.
- Unifying the interaction logic of 5G SSID and volume.
- Upgraded the bin firmware for mini and lite.
### [1.0.1] - 2023-6-25

#### Fixed

- Fixed the bug where the app and speech would get stuck and unable to exit when not connected to the network.
- Fixed the bug that the sound demo would get stuck and unable to exit.
- Fixed the bug that the speech demo can't be run correct.

### [1.0.0] - 2023-6-20 

### The stable version of the image file has been released.

#### Added

- Added a language switching feature for Chinese, English, and Japanese languages.
- The current version number is displayed on the main page.
