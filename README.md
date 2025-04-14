
-  RaspberryPi-CM4-main:The main program folder.
    - demos:sample program
      - expression：Emoji file
      - music：audio file
      - speechCn：Chinese Speech Recognition
      - speechEn：English Speech Recognition
      - xiaozhi：Xiaozhi real-time voice dialog
    - flacksocket：Graphic transfer and control of robots via flacksocket
    - language：Language Configuration Information
    - pics：Picture Files
    - volume：Volume Configuration Information
-  xgoMusic：The music required by the sample program.
-  xgoPicture：The pictures required by the sample program.
-  xgoVideos：Test video.
-  start1.sh：Startup script file.

- Functional Description：
  - Added graphic transfer mode for graphic transfer and robot control by means of IP access
    - ![image](https://github.com/user-attachments/assets/7f088c27-4d61-48b0-96c5-166f1bafd264)
    - ![image](https://github.com/user-attachments/assets/ca6c5c29-ac6b-427d-a51a-0a42273738b3)
  - Real-time voice conversations and added interactions via Xiaozhi
    -Usage：Long press the upper left button to record and release to return to the conversation in real time 
  - Updated and optimized speech recognition
    - Control the robot dog to complete the corresponding action through the wake-up word
    - (Note: As noise reduction and other features have not yet been realized, please operate this function in a relatively quiet environment, otherwise it may not be able to recognize the wake-up word correctly.)
  - Addition and deletion of sample functions
-  4-14 Revision Log
    -  Modified the display of battery level and network connection in main.py to detect it every 3 seconds, and then display it according to the detection result.


