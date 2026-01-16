from pynput import keyboard
import requests
import time

SERVER = "http://127.0.0.1:5000"

def on_press(key):
    try:
        k = key.char.lower()
    except:
        return

    # BUZZER 1
    if k == "i" or k == "o":
        requests.post(f"{SERVER}/buzzer/1/toggle")
    elif k == "p":
        requests.post(f"{SERVER}/buzzer/1/reset")

    # BUZZER 2
    elif k == "j" or k == "k":
        requests.post(f"{SERVER}/buzzer/2/toggle")
    elif k == "l":
        requests.post(f"{SERVER}/buzzer/2/reset")

def main():
    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()

if __name__ == "__main__":
    main()
