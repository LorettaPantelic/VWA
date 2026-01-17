from pynput import keyboard
import requests
import time

SERVER = "http://127.0.0.1:5000"

def on_press(key):
    try:
        k = key.char.lower()
    except:
        return

    try:
        # BUZZER 1
        if k in ("i", "o"):
            requests.post(f"{SERVER}/buzzer/1/toggle").raise_for_status()
        elif k == "p":
            requests.post(f"{SERVER}/buzzer/1/reset").raise_for_status()

        # BUZZER 2
        elif k in ("j", "k"):
            requests.post(f"{SERVER}/buzzer/2/toggle").raise_for_status()
        elif k == "l":
            requests.post(f"{SERVER}/buzzer/2/reset").raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error sending request: {e}")

def main():
    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()

if __name__ == "__main__":
    main()
