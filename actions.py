import winsound
import pyautogui
import webbrowser
import os
import time
import ctypes
import re
import datetime
import screen_brightness_control as sbc
import pywhatkit
import psutil
import shutil
import subprocess
import sys
import pygame
import tkinter as tk
from tkinter import messagebox, simpledialog
from send2trash import send2trash
import traceback
import pyperclip

# --- INITIALIZATION ---
try:
    pygame.mixer.init()
except:
    print("Audio error: Could not start Pygame mixer")

# 🔗 LINK TO YOUR NEW TTS.PY (ElevenLabs + EdgeTTS)
try:
    from tts import speak
except ImportError:
    print("⚠️ Error: tts.py not found. Voice will be disabled.")
    def speak(text): print(f"Silent Mode: {text}")

try:
    import music
except ImportError:
    music = None

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

# --- APP OPENER WRAPPER ---
try:
    from AppOpener import open as open_app_lib, close as close_app_lib # 👈 ADDED CLOSE HERE
    
    def open_app(app_name, match_closest=True, throw_error=True):
        open_app_lib(app_name, match_closest=match_closest, throw_error=throw_error)
        
    def close_app(app_name, match_closest=True, throw_error=True):
        close_app_lib(app_name, match_closest=match_closest, throw_error=throw_error)
        
except Exception as e:
    print(f"⚠️ AppOpener failed to load (Using fallback): {e}")
    def open_app(app_name, match_closest=True, throw_error=True):
        print(f"Attempting to open {app_name} via OS...")
        clean_name = app_name.strip().lower()
        try:
            subprocess.Popen(f"start {app_name}", shell=True, creationflags=0x08000000)
            time.sleep(0.1)
        except:
            pyautogui.press("win")
            time.sleep(0.1)
            pyautogui.write(clean_name)
            time.sleep(0.5)
            pyautogui.press("enter")


def safe_delete(path):
    """
    Safely deletes files. 
    BLOCKS deletion if the file is inside the Aanya App folder.
    """
    path = os.path.abspath(path)
    app_folder = os.path.dirname(os.path.abspath(__file__))
    
    # 🛑 NUCLEAR SAFETY CHECK
    if path.startswith(app_folder):
        print(f"🛑 BLOCKED: Attempted to delete app file: {path}")
        speak("Security Protocol Active. I cannot delete files inside the System Folder.")
        return

    if not os.path.exists(path):
        speak("I cannot find that file.")
        print(f"❌ Path not found: {path}")
        return

    # GUI Confirmation Popup
    root = tk.Tk()
    root.withdraw() 
    root.attributes("-topmost", True)
    
    msg = f"⚠️ CONFIRM DELETE ⚠️\n\nDo you want to send this to Recycle Bin?\n\n📂 {path}"
    confirm = messagebox.askyesno("Confirm Deletion", msg)
    root.destroy()

    if confirm:
        try:
            if 'send2trash' in sys.modules:
                send2trash(path)
                speak("Moved to Recycle Bin.")
            else:
                if os.path.isfile(path): os.remove(path)
                else: shutil.rmtree(path)
                speak("Deleted permanently.")
        except Exception as e:
            speak("Error deleting file.")
            print(e)
    else:
        speak("Cancelled.")

# --- ✨ CREATE FILE/FOLDER ---
def create_file_folder(path, is_folder=False, content=""):
    """Creates a file or folder safely"""
    try:
        path = os.path.abspath(path)
        if os.path.exists(path):
            speak("That file or folder already exists.")
            return

        if is_folder:
            os.makedirs(path)
            print(f"📂 Created Folder: {path}")
            speak("Folder created.")
        else:
            with open(path, "w") as f:
                f.write(content)
            print(f"📄 Created File: {path}")
            speak("File created.")
            
    except Exception as e:
        print(f"❌ Creation Error: {e}")
        speak("I could not create that.")

# --- 🧠 SMART PRINT (Code Typing) ---
def smart_print(*args):
    """
    If text looks like code -> TYPE IT (pyautogui).
    If text looks like chat -> SPEAK IT (tts).
    """
    text = " ".join(map(str, args))
    print(f"🖨️ AI Output: {text}")

    # Code Indicators
    code_signals = ["<html", "<!DOCTYPE", "import ", "def ", "class ", "print(", "return", "<div>", "<body>", "{", "}"]
    is_code = any(sig in text for sig in code_signals) or len(text) > 150

    if is_code:
        speak("I am typing the code now. Please click where you want it.")
        time.sleep(2)
        try:
            pyautogui.write(text, interval=0.001) 
        except Exception as e:
            print(f"Typing Error: {e}")
            speak("I could not type the text.")
    else:
        speak(text)

def smart_input(prompt_text):
    """Shows a stable Popup Window for user input"""
    try:
        # Instead of creating a new Tk every time, use the existing one if possible
        root = tk.Toplevel() 
        root.withdraw()
        root.attributes("-topmost", True)
        
        speak(prompt_text) 
        user_input = simpledialog.askstring("Aanya Needs Input", prompt_text, parent=root)
        
        root.destroy()
        return user_input if user_input else ""
    except:
        return ""

# --- ⚡ MAIN PERFORM FUNCTION ---
def perform(intent, alarm_list=None):
    if not intent:
        return

    t = intent.get("type")
    a = intent.get("action")
    p = intent.get("payload")
    ad_free = intent.get("adFree", False)

    if a in ["OPEN_APP", "CLOSE_APP", "OPEN_URL"]:
            t = "APP"
    elif a == "CMD_EXEC":
            t = "SYSTEM"

    print(f"⚙️ Action: {a} | Payload: {p}")
    print(f"⚡ Executing: {t} -> {p}")

# --- 1. PYTHON EXECUTION ---
    if t == "PYTHON_EXEC":
        try:
            safe_alarm_path = resource_path("alarm.mp3")
            if not os.path.exists(safe_alarm_path):
                print(f"⚠️ WARNING: Alarm file missing at {safe_alarm_path}")

            exec_globals = {
                'os': os, 'sys': sys, 'shutil': shutil, 'subprocess': subprocess,
                'webbrowser': webbrowser, 'pyautogui': pyautogui, 'time': time,
                'datetime': datetime, 'ctypes': ctypes, 
                'print': smart_print,  # 👈 OVERRIDE PRINT
                'speak': speak, 'psutil': psutil, 'winsound': winsound,
                'input': smart_input,  # 👈 OVERRIDE INPUT
                'ALARM_PATH': safe_alarm_path, 'pygame': pygame,
                'safe_delete': safe_delete, 
                'create_file_folder': create_file_folder, 
                'secure_delete': safe_delete ,
                'pyperclip': pyperclip,
            }

            clean_payload = p
            if "os.remove" in p or "shutil.rmtree" in p:
                clean_payload = p.replace("os.remove", "safe_delete").replace("shutil.rmtree", "safe_delete")

            # Execute the AI's code
            exec(clean_payload, exec_globals)
            
            # If it succeeds, return success
            return {"status": "success"}
            
        except Exception as e:
            # 🧠 CAPTURE THE FULL ERROR TRACEBACK
            error_log = traceback.format_exc() 
            print(f"❌ Execution Error Caught for ReAct Loop: {e}")
            
            # 🔄 SEND THE ERROR BACK TO AGENT.PY
            return {"status": "error", "error_msg": error_log}

# --- 2. ALARM SYSTEM ---
    elif t == "ALARM" or a == "ALARM_SET":
        if p and alarm_list is not None:
            try:
                command = p.lower()
                target_time = None
                now = datetime.datetime.now()

                numbers = re.findall(r'\d+', command)
                if numbers:
                    amount = int(numbers[0])
                    if "hour" in command: target_time = now + datetime.timedelta(hours=amount)
                    elif "minute" in command: target_time = now + datetime.timedelta(minutes=amount)
                    elif "second" in command: target_time = now + datetime.timedelta(seconds=amount)
                
                if not target_time and (":" in command or "am" in command or "pm" in command):
                    time_match = re.search(r'(\d{1,2})(:(\d{2}))?', command)
                    if time_match:
                        hour = int(time_match.group(1))
                        minute = int(time_match.group(3)) if time_match.group(3) else 0
                        if "pm" in command and hour != 12: hour += 12
                        if "am" in command and hour == 12: hour = 0
                        target_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                        if target_time < now: target_time += datetime.timedelta(days=1)

                if target_time:
                    alarm_list.append({'time': target_time, 'active': True})
                    print(f"⏰ Alarm set for {target_time}")
                    return {"status": "success"} # 👈 FIXED: Tell agent.py it worked!
                else:
                    print("❌ Could not parse alarm time.")
                    return {"status": "error", "error_msg": "Boss, aapne time nahi bataya. Pucho kitne baje ka alarm lagau?"}
            except Exception as e:
                return {"status": "error", "error_msg": str(e)}


# --- 3. SYSTEM CONTROL (IMPROVED) ---
    elif t == "SYSTEM":
            if a in ["SYSTEM_REPORT", "BATTERY_CHECK"]:
                try:
                    battery = psutil.sensors_battery()
                    percent = battery.percent if battery else "Unknown"
                    plugged = "charging pe hai" if battery and battery.power_plugged else "plugged in nahi hai"
                    cpu = psutil.cpu_percent(interval=0.1)
                    ram = psutil.virtual_memory().percent
                    report = f"Boss, battery {percent}% hai aur {plugged}. CPU usage {cpu}% aur RAM {ram}% hai."
                    print(f"📊 {report}")
                    speak(report) 
                    return {"status": "success"}
                except Exception as e:
                    return {"status": "error", "error_msg": str(e)}

            elif a == "CMD_EXEC" and p:
                if "import " in p or "print(" in p:
                    return {"status": "error", "error_msg": "Sent Python to CMD_EXEC."}
                try:
                    subprocess.Popen(f'cmd /k {p}', creationflags=subprocess.CREATE_NEW_CONSOLE)
                    return {"status": "success"}
                except Exception as e:
                    return {"status": "error", "error_msg": str(e)}

            elif a == "TYPE" and p:
                clean_code = p.replace("```python", "").replace("```", "")
                if "\\n" in clean_code: clean_code = clean_code.encode('utf-8').decode('unicode_escape')
                clean_code = clean_code.strip('\r\n')
                pyperclip.copy(clean_code)
                time.sleep(0.3)
                pyautogui.hotkey('ctrl', 'v')
                return {"status": "success"}

            # 👇 MOVED VOLUME, BRIGHTNESS & PRESS INTO THE SYSTEM BLOCK 👇
            elif a == "VOLUME_UP":
                pyautogui.press('volumeup', presses=5)
                return {"status": "success"}
            elif a == "VOLUME_DOWN":
                pyautogui.press('volumedown', presses=5)
                return {"status": "success"}
            elif a == "VOLUME_MAX":
                pyautogui.press('volumeup', presses=50) 
                return {"status": "success"}
            elif a in ["MUTE", "MUTED", "VOLUME_MUTE", "UNMUTE", "VOLUME_UNMUTE"]:
                pyautogui.press("volumemute")
                return {"status": "success"}
            elif a == "VOLUME_SET" and p:
                try:
                    clean_val = re.sub(r'[^0-9]', '', str(p))
                    target = int(clean_val)
                    pyautogui.press("volumemute")
                    for _ in range(50): pyautogui.press("volumedown") # Ensure 0
                    presses = int(target / 2)
                    for _ in range(presses): pyautogui.press("volumeup")
                    return {"status": "success"}
                except: pass

            elif "BRIGHTNESS" in a:
                try:
                    current = sbc.get_brightness()
                    current = current[0] if current else 50
                    if a == "BRIGHTNESS_UP": sbc.set_brightness(min(current + 10, 100))
                    elif a == "BRIGHTNESS_DOWN": sbc.set_brightness(max(current - 10, 0))
                    elif a == "BRIGHTNESS_MAX": sbc.set_brightness(100)
                    elif a == "BRIGHTNESS_MIN": sbc.set_brightness(0)
                    elif a == "BRIGHTNESS_SET" and p:
                        clean_val = re.sub(r'[^0-9]', '', str(p))
                        sbc.set_brightness(int(clean_val))
                    return {"status": "success"}
                except Exception as e:
                    print(f"Brightness Error: {e}")

            elif a == "LOCK": 
                ctypes.windll.user32.LockWorkStation()
                return {"status": "success"}
            elif a == "SCREENSHOT": 
                pyautogui.screenshot("screenshot.png")
                return {"status": "success"}
            elif a == "MINIMIZE": 
                pyautogui.hotkey('win', 'd')
                return {"status": "success"}
            elif a == "ABORT": 
                os.system("shutdown /a")
                return {"status": "success"}

            elif a == "PRESS" and p:
                key = p.replace("window", "win").replace("control", "ctrl").replace("escape", "esc").replace("alt", "alt").strip().lower()
                if "+" in key: pyautogui.hotkey(*[k.strip() for k in key.split("+")])
                else: pyautogui.press(key)
                return {"status": "success"}


    # --- 4. APP CONTROL ---
    elif t == "APP" or a in ["OPEN_APP", "CLOSE_APP", "OPEN_URL"]:
        if a == "OPEN_URL":
            webbrowser.open_new_tab(p)
            return {"status": "success"}
            
        elif a == "OPEN_APP":
            clean_name = str(p).lower().strip()
            try:
                open_app_lib(clean_name, match_closest=True, throw_error=True)
                return {"status": "success"}
            except Exception as e:
                return {"status": "error", "error_msg": f"Boss, mujhe '{clean_name}' nahi mila."}

        elif a == "CLOSE_APP":
            clean_name = str(p).lower().strip()
            if any(x in clean_name for x in ["explorer", "manager", "folder"]):
                os.system('powershell -c "(New-Object -comObject Shell.Application).Windows() | foreach-object {$_.quit()}"')
                return {"status": "success"}
            try:
                close_app_lib(clean_name, match_closest=True, throw_error=True)
                return {"status": "success"}
            except Exception as e:
                return {"status": "error", "error_msg": f"'{clean_name}' open nahi hai."}


    # --- 5. MUSIC ---
    elif t == "MUSIC":
        if a == "PLAY_YT":
            pywhatkit.playonyt(p)
        
        elif a == "PLAY_SPECIFIC":
            link = None
            if music:
                try:
                    mashups = list(music.mashups[0].values()) if isinstance(music.mashups, tuple) else list(music.mashups.values())
                    playlists = list(music.Playlists[0].values()) if isinstance(music.Playlists, tuple) else list(music.Playlists.values())

                    if p == "rahat": link = mashups[3] if ad_free else mashups[0]
                    elif p == "best": link = mashups[4] if ad_free else mashups[1]
                    elif p == "trip": link = mashups[5] if ad_free else mashups[2]
                    elif p == "phonk": link = playlists[2] if ad_free else playlists[0]
                    elif p == "hindi": link = playlists[3] if ad_free else playlists[1]
                    elif p == "english": link = "https://www.youtube.com/watch?v=36YnV9STBqc&list=PLMC9KNkIncKvYin_USF1qoJQnIyMAfRxl" 

                except Exception as e:
                    print(f"Music Lookup Error: {e}")

            if link:
                webbrowser.open(link)
            else:
                print(f"⚠️ Playlist '{p}' not found in library. Searching YouTube...")
                pywhatkit.playonyt(f"{p} songs playlist")
