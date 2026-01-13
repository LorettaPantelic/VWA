from pynput import keyboard
import requests
import time

SERVER = "http://127.0.0.1:5000"

def on_press(key):
    try:
        k = key.char.lower()
    except:
        return

    if k == "i":
        requests.post(f"{SERVER}/buzzer_stopwatch/toggle")
    elif k == "o":
        requests.post(f"{SERVER}/buzzer_stopwatch/toggle")
    elif k == "p":
        requests.post(f"{SERVER}/buzzer_stopwatch/reset")

def main():
    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()

if __name__ == "__main__":
    main()
