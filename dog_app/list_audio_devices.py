import pyaudio

p = pyaudio.PyAudio()
print("Available Audio Devices:")
for i in range(p.get_device_count()):
    info = p.get_device_info_by_index(i)
    try:
        name = info.get('name')
        # Encode/decode to handle potential non-ascii characters if necessary, though print usually handles it
        print(f"Index {i}: {name} (In: {info.get('maxInputChannels')}, Out: {info.get('maxOutputChannels')})")
    except Exception as e:
        print(f"Index {i}: Error reading name: {e}")

print("\n--- Brute Force Probe ---")
rates = [16000, 44100, 48000]
for i in range(p.get_device_count()):
    try:
        info = p.get_device_info_by_index(i)
        name = info.get('name')
        in_ch = info.get('maxInputChannels')
        if in_ch > 0:
            print(f"\nChecking Index {i}: {name} (In: {in_ch})")
            for r in rates:
                try:
                    stream = p.open(format=pyaudio.paInt16, channels=1, rate=r, input=True, input_device_index=i, frames_per_buffer=1024)
                    print(f"  [SUCCESS] Rate {r} Hz (Mono)")
                    stream.close()
                except Exception as e:
                    pass # print(f"  [FAIL] Rate {r} Hz: {e}")
                
                if in_ch >= 2:
                    try:
                        stream = p.open(format=pyaudio.paInt16, channels=2, rate=r, input=True, input_device_index=i, frames_per_buffer=1024)
                        print(f"  [SUCCESS] Rate {r} Hz (Stereo)")
                        stream.close()
                    except Exception as e:
                        pass
    except Exception:
        pass

p.terminate()
