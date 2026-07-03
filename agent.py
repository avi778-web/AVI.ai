import customtkinter as ctk
import threading
import pyperclip
import requests
import time
import datetime
import random
import pygame
import os
import sys
import json
import webbrowser
from tkinter import messagebox
import ctypes
import winsound
import pyautogui
import time
import pyautogui
import pyperclip
import traceback  # 👈 Add this line

try:
    if getattr(sys, 'frozen', False):
        # If running as compiled .exe
        application_path = sys._MEIPASS
    else:
        # If running as .py script
        application_path = os.path.dirname(os.path.abspath(__file__))
    
    os.chdir(application_path)
    print(f"📂 Working Directory set to: {application_path}")
except Exception as e:
    print(f"⚠️ Could not set working directory: {e}")

def get_app_data_path():
    """Returns path to %APPDATA%/AanyaAI"""
    app_data = os.getenv('APPDATA')
    path = os.path.join(app_data, "AanyaAI")
    if not os.path.exists(path):
        os.makedirs(path)
    return path

CONFIG_FILE = os.path.join(get_app_data_path(), "user_config.json")
print(f"📂 Configuration Path: {get_app_data_path()}")


def resource_path(relative_path):

    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)


from listen import listen
from tts import speak
from actions import perform
import remote
from update_checker import check_for_update, show_progress_gui

try:
    from config import API_URL
except ImportError:
    API_URL = "https://aanya-backend.onrender.com"
    # API_URL = "http://localhost:5000"  # Local development fallback

# --- THEME SETUP ---
def setup_taskbar_icon(app_id="mycompany.myproduct.subproduct.version"):
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
    except Exception as e:
        print(f"Icon Error: {e}")

try:
    from config import  APP_VERSION
except ImportError:
    APP_VERSION = "2.6.8"
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")


alarms = []
is_running = False

last_user_interaction = time.time()
DND_MODE = False
SILENCE_LIMIT = 1200  # 10 minutes = 600 seconds


def get_smart_proactive_message():
    now = datetime.datetime.now()
    hour = now.hour
    day = now.strftime("%A")

    is_weekend = day in ["Saturday", "Sunday"]

    # 🌅 MORNING (5AM – 11AM)
    if 5 <= hour < 11:
        lines = [
            "Good morning Boss ☀️... itna chup kyun ho? Breakfast kiya?",
            "Subah ho gayi... focus mode on karein? Main help karu?",
            "Aaj ka din productive banate hain kya? Main ready hu.",
        ]

    # ☀️ AFTERNOON (11AM – 4PM)
    elif 11 <= hour < 16:
        lines = [
            "Boss... lunch break liya ya sirf kaam hi kar rahe ho?",
            "Good afternoon Boss.",
            "Main yahin hu... agar koi task pending hai toh bol do, Boss",
        ]

    # 🌆 EVENING (4PM – 9PM)
    elif 16 <= hour < 21:
        lines = [
            "Shaam ho gayi hai Boss... ",
            "Aaj ka kaam wind up karein ya thoda aur push karein?",
        ]

    # 🌙 NIGHT (9PM – 2AM)
    elif 21 <= hour or hour < 2:
        lines = [
            "It’s late Boss... rest bhi zaroori hota hai",
            "Aap chup ho... sab theek hai na? Boss",
            "Late night work kar rahe ho? Boss.. Pc lock kar du kya?",
        ]

    # 😴 DEEP NIGHT (2AM – 5AM)
    else:
        lines = [
            "Boss... abhi tak jag rahe ho? thoda so jao.",
            "Itni raat ko kaam mat karo boss... health important hai.",
            "Main yahin hu... but aapko rest lena chahiye. App bolo to pc lock kar du, Boss.",
        ]

    # Weekend softer tone
    if is_weekend:
        lines.append("Weekend hai... thoda relax bhi kar lo na 😊")

    return random.choice(lines)


def monitor_activity():
    """Runs in background to check alarms and health reminders"""
    print("✅ System Monitor Started...")

    mp3_path = resource_path("alarm.mp3")
    print(f"🔎 DEBUG: Looking for alarm at: {mp3_path}")
    if os.path.exists(mp3_path):
        print("✅ Alarm file FOUND.")
    else:
        print("❌ Alarm file NOT FOUND. Please ensure 'alarm.mp3' is in the same folder as agent.py")

    start_usage_time = time.time()
    last_hour_check = int(datetime.datetime.now().strftime("%H"))
    warning_2hr_given = False
    
    try: 
        pygame.mixer.init()
    except Exception as e: 
        print(f"⚠️ Audio Init Error: {e}")

    while True:
        try:
            current_time = datetime.datetime.now()

            # --- 1. ALARM CHECK ---
            for alarm in alarms[:]:
                if current_time >= alarm['time']:
                    print(f"⏰ ALARM TRIGGERED! (Scheduled: {alarm['time'].strftime('%I:%M %p')})") 
                    speak("Alarm ka time ho gaya hai boss.")
                    
                    # Recalculate path just in case
                    sound_file = resource_path("alarm.mp3")
                    
                    if os.path.exists(sound_file):
                        try:
                            print(f"🎵 Alarm...")
                            pygame.mixer.music.load(sound_file)
                            pygame.mixer.music.play()
                            time.sleep(15) 

                            pygame.mixer.music.stop()
                        except Exception as e:
                            print(f"❌ Playback Error: {e}")
                            speak("Time is up. Time is up.")
                    else:
                        print(f"⚠️ File missing at runtime: {sound_file}")
                        speak("Time is up. I cannot find the ringtone file.")
                    
                    if alarm in alarms:
                        alarms.remove(alarm)

            # --- 2. HEALTH CHECK (2 Hours) ---
            elapsed = time.time() - start_usage_time
            if elapsed >= 7200 and not warning_2hr_given:
                msgs = ["Boss, please take a break.", "Time to stretch, Boss.", "You have been working for 2 hours."]
                speak(random.choice(msgs))
                warning_2hr_given = True

            # --- 3. HOURLY REMINDER ---
            current_hour = int(current_time.strftime("%H"))
            if current_hour != last_hour_check:
                if current_hour >= 23 or current_hour < 4:
                    speak("It is getting late. You should sleep now.")
                else:
                    speak(f"Time check: {current_time.strftime('%I:%M %p')}")
                
                last_hour_check = current_hour
                warning_2hr_given = False 

            global last_user_interaction, DND_MODE

            if not DND_MODE:
                silent_time = time.time() - last_user_interaction

                if silent_time >= SILENCE_LIMIT:
                    message = get_smart_proactive_message()
                    speak(message)

                    # Reset timer after speaking
                    last_user_interaction = time.time()

            time.sleep(1)
            
        except Exception as e:
            print(f"❌ Monitor Thread Error: {e}")
            time.sleep(5) # Wait before retrying to prevent crash loop


class AanyaProfessionalApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        setup_taskbar_icon("shaurya.aanya.ai.v1")
        self.title("AANYA AI")
        self.geometry("650x650")
        self.resizable(False, False)
        
        try:
            icon_path = resource_path("aanya-logo.ico")
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
                # This line forces Windows to refresh the taskbar icon
                self.after(200, lambda: self.iconbitmap(icon_path))
        except:
            pass

        # self.chat_history = self.load_chat_history()

        try:
            self.iconbitmap(resource_path("aanya-logo.ico"))
        except:
            pass


        self.api_key = ""
        self.groq_key = ""
        self.email = ""
        self.device_id = "Desktop-Main"
        self.terms_accepted = ctk.BooleanVar(value=False)

        # --- UPDATE CHECK ---
        self.check_app_update()

        if self.load_local_config():
            self.show_main_interface()
        else:
            self.show_disclaimer()

    def check_app_update(self):
            def _background_check():
                try:
                    update = check_for_update()
                    if update and update.get("update"):
                        self.after(0, lambda: self.prompt_update(update))
                except Exception as e:
                    print(f"Update Check Error: {e}")

            threading.Thread(target=_background_check, daemon=True).start()

    def prompt_update(self, update):
            if messagebox.askyesno("Update Available", f"Version {update['latest']} available. Update now?"):
                show_progress_gui(update["url"], update["latest"])
                self.destroy()


    def load_local_config(self):
        if os.path.exists(CONFIG_FILE):  # Use global constant
            try:
                with open(CONFIG_FILE, "r") as f:
                    data = json.load(f)
                    self.api_key = data.get("api_key", "")
                    self.groq_key = data.get("groq_key", "")
                    self.email = data.get("email", "")
                    if self.api_key and self.groq_key:
                        return True
            except:
                return False
        return False

    def save_local_config(self):
        data = {
            "api_key": self.api_key,
            "groq_key": self.groq_key,
            "email": self.email
        }
        try:
            with open(CONFIG_FILE, "w") as f:  # Use global constant
                json.dump(data, f)
            print(f"✅ Config saved to {CONFIG_FILE}")
        except Exception as e:
            print(f"❌ Config Save Error: {e}")


    def add_global_buttons(self, parent_frame):
        nav_frame = ctk.CTkFrame(parent_frame, fg_color="transparent")
        nav_frame.pack(side="bottom", pady=20)

        ctk.CTkButton(nav_frame, text="🌐  WEBSITE", width=120, height=30,
                      fg_color="#222", hover_color="#333",
                      command=lambda: webbrowser.open("https://your-website.com")).pack(side="left", padx=10)

        ctk.CTkButton(nav_frame, text="🔗  LINKEDIN", width=120, height=30,
                      fg_color="#0077b5", hover_color="#005582",
                      command=lambda: webbrowser.open("https://linkedin.com/in/your-profile")).pack(side="left", padx=10)

    def show_disclaimer(self):
        self.clear_frame()
        frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        frame.pack(fill="both", expand=True)

        content = ctk.CTkFrame(frame, corner_radius=20, fg_color="#101010")
        content.pack(pady=50, padx=40, fill="both", expand=True)

        ctk.CTkLabel(content, text="ACCESS PROTOCOL", font=("Orbitron", 26, "bold"), text_color="#00E5FF").pack(pady=(40, 10))

        terms = (
            "⚠️ SYSTEM ACCESS WARNING ⚠️\n\n"
            "1. AUTOMATION: Aanya will control files, settings, and browsers.\n"
            "2. PRIVACY: Data is encrypted locally. No personal uploads.\n"
            "3. SECURITY: Use with standard privileges.\n"
            "4. LIABILITY: You are responsible for issued commands.\n"
            "5. SAFE: Your groq api key is only used for AI processing, never shared or stored on our servers.\n\n"
            "6. UPDATES: The app will check for updates on launch. Always use the latest version for best performance and security.\n\n"
        )
        
        textbox = ctk.CTkTextbox(content, width=500, height=150, font=("Consolas", 14), 
                                 fg_color="#050505", text_color="#aaaaaa", corner_radius=10)
        textbox.insert("0.0", terms)
        textbox.configure(state="disabled")
        textbox.pack(pady=20)

        chk = ctk.CTkCheckBox(content, text="I accept the security protocols.", 
                              variable=self.terms_accepted, command=self.toggle_next_btn,
                              fg_color="#00E5FF", hover_color="#00B8D4")
        chk.pack(pady=10)

        self.btn_next = ctk.CTkButton(content, text="PROCEED TO SETUP  ➡️", state="disabled", 
                                      command=self.show_api_setup, height=50, width=250,
                                      font=("Orbitron", 14, "bold"), fg_color="#222")
        self.btn_next.pack(pady=20)
        self.add_global_buttons(content)

    def toggle_next_btn(self):
        if self.terms_accepted.get():
            self.btn_next.configure(state="normal", fg_color="#00E5FF", text_color="black")
        else:
            self.btn_next.configure(state="disabled", fg_color="#222", text_color="gray")


    def show_api_setup(self):
        self.clear_frame()
        frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        frame.pack(fill="both", expand=True)

        content = ctk.CTkFrame(frame, corner_radius=20, fg_color="#101010")
        content.pack(pady=40, padx=40, fill="both", expand=True)

        ctk.CTkLabel(content, text="SYSTEM INITIALIZATION", font=("Orbitron", 24, "bold"), text_color="#00E5FF").pack(pady=(30, 5))
        ctk.CTkLabel(content, text="Enter credentials to link neural core", font=("Roboto", 12), text_color="gray").pack(pady=(0, 20))

        # UPDATED: Label changed to USER NAME as requested
        self.entry_email = self.create_input(content, "USER NAME", "Enter your name...")
        self.entry_aanya = self.create_input(content, "AANYA API KEY", "Enter backend key...")
        self.entry_groq = self.create_input(content, "GROQ AI KEY", "gsk_...")

        self.lbl_error = ctk.CTkLabel(content, text="", text_color="#FF3D00", font=("Roboto", 12, "bold"))
        self.lbl_error.pack(pady=5)

        ctk.CTkButton(content, text="ESTABLISH CONNECTION  ⚡", command=self.validate_and_connect, 
                      height=50, width=280, font=("Orbitron", 14, "bold"), 
                      fg_color="#00E5FF", text_color="black", hover_color="#00B8D4").pack(pady=20)

        self.add_global_buttons(content)

    def create_input(self, parent, label, placeholder):
        ctk.CTkLabel(parent, text=label, anchor="w", font=("Consolas", 12, "bold"), text_color="#00E5FF").pack(fill="x", padx=60, pady=(10, 0))
        entry = ctk.CTkEntry(parent, placeholder_text=placeholder, height=40, fg_color="#050505", border_color="#333")
        entry.pack(fill="x", padx=60, pady=(5, 0))
        return entry

    def validate_and_connect(self):
        email = self.entry_email.get().strip()
        a_key = self.entry_aanya.get().strip()
        g_key = self.entry_groq.get().strip()

        if not email or not a_key or not g_key:
            self.lbl_error.configure(text="❌ ERROR: All fields are required.", text_color="#FF3D00")
            return
        
        if len(a_key) < 5 or len(g_key) < 5:
            self.lbl_error.configure(text="❌ ERROR: Invalid API Key format.", text_color="#FF3D00")
            return

        self.lbl_error.configure(text="⏳ Verifying keys with server...", text_color="#00E5FF")
        self.update()

        try:
            test_payload = {"command": "ping", "name": email, "deviceId": "Setup-Check", "groqKey": g_key}
            headers = {"x-api-key": a_key, "Content-Type": "application/json"}
            response = requests.post(f"{API_URL}/command", json=test_payload, headers=headers, timeout=15)

            if response.status_code in [401, 403]:
                self.lbl_error.configure(text="❌ ERROR: API Key rejected by server.", text_color="#FF3D00")
                return
            elif response.status_code >= 500:
                self.lbl_error.configure(text="❌ ERROR: Server error. Try again.", text_color="#FF3D00")
                return

        except requests.exceptions.ConnectionError:
             self.lbl_error.configure(text="❌ ERROR: Cannot reach server.", text_color="#FF3D00")
             return
        except Exception as e:
             self.lbl_error.configure(text=f"❌ ERROR: Connection Failed", text_color="#FF3D00")
             return

        self.email = email
        self.api_key = a_key
        self.groq_key = g_key
        self.save_local_config()
        self.show_main_interface()

    def show_main_interface(self):
        self.clear_frame()
        self.configure(fg_color="#050505")
        
        # Header
        header = ctk.CTkFrame(self, height=80, fg_color="transparent")
        header.pack(fill="x", padx=30, pady=(20, 10))
        
        ctk.CTkLabel(header, text="AANYA", font=("Orbitron", 36, "bold"), text_color="#00E5FF").pack(side="left")
        ctk.CTkLabel(header, text=f" / {self.email}", font=("Consolas", 12), text_color="#00E5FF").pack(side="left", pady=(18,0), padx=5)
        
        # --- ⚙️ NEW SETTINGS BUTTON ---
        ctk.CTkButton(header, text="⋮  Settings", width=100, height=30,
                      fg_color="#222", hover_color="#333", border_width=1, border_color="#444",
                      command=self.open_settings_window).pack(side="right", padx=10, pady=10)
                # --- 🔕 DND BUTTON ---
        self.btn_dnd = ctk.CTkButton(
            header,
            text="🔔 Proactive: ON",
            width=150,
            height=30,
            fg_color="#1a1a1a",
            hover_color="#333",
            border_width=1,
            border_color="#00E5FF",
            text_color="#00E5FF",
            command=self.toggle_dnd_mode
        )
        self.btn_dnd.pack(side="right", padx=10, pady=10)

        self.status_badge = ctk.CTkButton(header, text="STANDBY", font=("Roboto", 12, "bold"), 
                                        fg_color="#1a1a1a", width=100, height=30, hover=False, text_color="gray")
        self.status_badge.pack(side="right", pady=10)

        # Log
        log_container = ctk.CTkFrame(self, fg_color="#0a0a0a", corner_radius=15, border_width=1, border_color="#222")
        log_container.pack(fill="both", expand=True, padx=30, pady=10)

        self.log_box = ctk.CTkTextbox(log_container, font=("Consolas", 14), fg_color="transparent", text_color="#cfcfcf", wrap="word")
        self.log_box.pack(fill="both", expand=True, padx=15, pady=15)
        
        self.log_message(f"System Online. Memory Core Active.", "SYS")
        self.log_box.configure(state="disabled")

# Control Dock
        dock = ctk.CTkFrame(self, height=120, fg_color="#101010", corner_radius=20)
        dock.pack(fill="x", padx=30, pady=20)

        # Make the listen button a bit smaller to fit the text box
        self.btn_listen = ctk.CTkButton(dock, text="🎙️ VOICE", width=120,
                                        command=self.toggle_listening, 
                                        height=60, font=("Orbitron", 14, "bold"),
                                        fg_color="#00E5FF", text_color="black", hover_color="#00B8D4", corner_radius=10)
        self.btn_listen.pack(side="left", padx=20, pady=20)

        # Add the new Text Input Box
        self.entry_command = ctk.CTkEntry(dock, placeholder_text="Type a command and press Enter...", 
                                          height=60, font=("Consolas", 14), 
                                          fg_color="#050505", border_color="#333", corner_radius=10)
        self.entry_command.pack(side="left", fill="x", expand=True, padx=(0, 20), pady=20)
        
        # Make the 'Enter' key trigger our new function
        self.entry_command.bind("<Return>", self.handle_text_input)

        self.add_global_buttons(self)

        if not any(t.name == "MonitorThread" for t in threading.enumerate()):
            t = threading.Thread(target=monitor_activity, daemon=True, name="MonitorThread")
            t.start()
            threading.Thread(target=lambda: speak("System online."), daemon=True).start()
        # START REMOTE CONTROL THREAD
        if not any(t.name == "RemoteThread" for t in threading.enumerate()):
            remote_t = threading.Thread(
                target=remote.start_remote_listener,
                args=(self.api_key, API_URL, lambda cmd: self.process_text_command(cmd, source="PHONE")),
                daemon=True,
                name="RemoteThread"
            )
            remote_t.start()


    def handle_text_input(self, event=None):
            command = self.entry_command.get().strip()
            if not command:
                return  

            self.entry_command.delete(0, 'end')

            global last_user_interaction
            last_user_interaction = time.time()

            self.log_message(f"You: {command}", "TEXT")
# 🧠 SMART SELECTION INTERCEPTOR
            command_lower = command.lower()
            if "code" in command_lower or "fix" in command_lower or "selected" in command_lower:
                
                self.log_message("Auto-copying selected text...", "SYS")
                
                # 1. Aanya presses Ctrl+C for you!
                pyautogui.hotkey('ctrl', 'c')
                time.sleep(0.2) # Give Windows a split second to update the clipboard
                
                # 2. Grab the fresh text
                clipboard_content = pyperclip.paste()
                
                if clipboard_content and len(clipboard_content) > 3 and clipboard_content.strip() != command.strip():
                    self.log_message("📋 Grabbed selected code successfully!", "SYS")
                    command = f"{command}\n\nHere is the broken code I have selected. Please analyze it, explain the bug, and use the TYPE action to output the fixed code:\n\n```python\n{clipboard_content}\n```"
                else:
                    self.log_message("⚠️ No text was selected.", "ERR")
            threading.Thread(target=self.process_text_command, args=(command, "TEXT"), daemon=True).start()
            
    # --- HELPER FUNCTIONS ---
    
    def toggle_dnd_mode(self):
        global DND_MODE

        DND_MODE = not DND_MODE

        if DND_MODE:
            self.btn_dnd.configure(
                text="🔕 Proactive: OFF",
                border_color="#FF3D00",
                text_color="#FF3D00"
            )
            self.log_message("Proactive mode disabled.", "SYS")
        else:
            self.btn_dnd.configure(
                text="🔔 Proactive: ON",
                border_color="#00E5FF",
                text_color="#00E5FF"
            )
            self.log_message("Proactive mode enabled.", "SYS")
    def clear_frame(self):
        for widget in self.winfo_children():
            widget.destroy()
    def open_settings_window(self):
                """Opens a popup window to manage Settings"""
                window = ctk.CTkToplevel(self)
                window.title("Settings")
                window.geometry("400x600")
                window.configure(fg_color="#050505")
                window.resizable(False, False)
                
                # --- ✅ FIX: ADD ICON TO SETTINGS WINDOW ---
                try:
                    # We use 'after' to ensure the window is initialized before setting the icon
                    window.after(200, lambda: window.iconbitmap(resource_path("aanya-logo.ico")))
                except Exception as e:
                    print(f"Settings Icon Error: {e}")

                window.attributes("-topmost", True) # Keep on top

                ctk.CTkLabel(window, text="SYSTEM CONFIGURATION", font=("Orbitron", 18, "bold"), text_color="#00E5FF").pack(pady=20)
                ctk.CTkLabel(window, text="1. API KEYS", font=("Arial", 12, "bold"), anchor="w", text_color="#00E5FF").pack(fill="x", padx=30, pady=(10, 5))
                
                ctk.CTkLabel(window, text="Aanya API Key", anchor="w", text_color="gray").pack(fill="x", padx=30)
                entry_aanya = ctk.CTkEntry(window, fg_color="#101010", border_color="#333")
                entry_aanya.pack(fill="x", padx=30, pady=(0, 10))
                entry_aanya.insert(0, self.api_key)

                ctk.CTkLabel(window, text="Groq AI Key", anchor="w", text_color="gray").pack(fill="x", padx=30)
                entry_groq = ctk.CTkEntry(window, fg_color="#101010", border_color="#333")
                entry_groq.pack(fill="x", padx=30, pady=(0, 10))
                entry_groq.insert(0, self.groq_key)

                # --- SECTION 2: GENERAL ---
                ctk.CTkLabel(window, text="2. GENERAL", font=("Arial", 12, "bold"), anchor="w", text_color="#00E5FF").pack(fill="x", padx=30, pady=(15, 5))
                
                ctk.CTkLabel(window, text="User Name / Email", anchor="w", text_color="gray").pack(fill="x", padx=30)
                entry_name = ctk.CTkEntry(window, fg_color="#101010", border_color="#333")
                entry_name.pack(fill="x", padx=30, pady=(0, 10))
                entry_name.insert(0, self.email)

                # --- SECTION 3: WEBSITE ---
                ctk.CTkLabel(window, text="3. WEBSITE", font=("Arial", 12, "bold"), anchor="w", text_color="#00E5FF").pack(fill="x", padx=30, pady=(15, 5))
                
                ctk.CTkButton(window, text="🌐 Get API Keys (Website)", fg_color="transparent", 
                            border_width=1, border_color="#00E5FF", text_color="#00E5FF",
                            command=lambda: webbrowser.open("https://your-website.com/dashboard")).pack(pady=5)

                # --- SAVE FUNCTION ---
                def save_and_close():
                    new_name = entry_name.get().strip()
                    new_aanya = entry_aanya.get().strip()
                    new_groq = entry_groq.get().strip()

                    if not new_name or not new_aanya or not new_groq:
                        messagebox.showerror("Error", "All fields are required!")
                        window.lift() # Bring window back to top
                        return

                    # Update Variables
                    self.email = new_name
                    self.api_key = new_aanya
                    self.groq_key = new_groq
                    
                    # Save to File
                    self.save_local_config()
                    
                    # Refresh Main UI to show new name immediately
                    self.show_main_interface()
                    
                    messagebox.showinfo("Success", "Settings Saved!")
                    window.destroy()

                # --- SAVE BUTTON ---
                ctk.CTkButton(window, text="💾 SAVE CHANGES", height=45, 
                            fg_color="#00E5FF", text_color="black", hover_color="#00B8D4",
                            font=("Orbitron", 14, "bold"),
                            command=save_and_close).pack(side="bottom", pady=30, padx=30, fill="x")

    def log_message(self, text, tag="LOG"):
        self.log_box.configure(state="normal")
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        colors = {"ERR": "🔴", "SYS": "🔵", "MIC": "🎙️", "PHONE": "📱", "AI": "🟣", "EXE": "⚡", "AUTH": "🟢", "TEXT": "⌨️"}
        icon = colors.get(tag, "⚪")
        self.log_box.insert("end", f"{icon} [{timestamp}] {text}\n\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def toggle_listening(self):
        global is_running
        if is_running:
            is_running = False
            self.btn_listen.configure(text="🎙️ ACTIVATE VOICE", fg_color="#00E5FF", text_color="black")
            self.status_badge.configure(text="STANDBY", fg_color="#1a1a1a", text_color="gray")
        else:
            is_running = True
            self.btn_listen.configure(text="🛑 ABORT LISTENING", fg_color="#FF3D00", text_color="white")
            self.status_badge.configure(text="LISTENING", fg_color="#00E5FF", text_color="black")
            threading.Thread(target=self.run_voice_loop, daemon=True).start()
    def handle_text_input(self, event=None):
            command = self.entry_command.get().strip()
            if not command:
                return  

            self.entry_command.delete(0, 'end')

            global last_user_interaction
            last_user_interaction = time.time()

            self.log_message(f"You: {command}", "TEXT")

# 🧠 SMART SELECTION INTERCEPTOR (TEXT MODE)
            command_lower = command.lower()
            triggers = ["fix code", "fix selected", "analyze code", "broken code", "copy karo", "copy karke", "check karo", "fix"]
            
            if any(word in command_lower for word in triggers):
                # 🧹 CLEAR CLIPBOARD FIRST to prevent reading old data!
                pyperclip.copy("") 
                
                pyautogui.hotkey('alt', 'tab')
                time.sleep(0.4) 

                pyautogui.hotkey('ctrl', 'c')
                time.sleep(0.3) 
                
                clipboard_content = pyperclip.paste()

                if clipboard_content and len(clipboard_content.strip()) > 3:
                    command = f"The user said: '{command}'. Here is the code from their clipboard:\n\n```python\n{clipboard_content}\n```\n\nPlease find the bug, explain it in the 'reply' field, and use the TYPE action to output the fully fixed code."
                else:
                    self.log_message("⚠️ No text was selected.", "ERR")
                    speak("Boss, aapne koi text select nahi kiya hai.")
                    return # Stop here so it doesn't send empty data to the AI


            threading.Thread(target=self.process_text_command, args=(command, "TEXT"), daemon=True).start()

    def run_voice_loop(self):
        global is_running
        while is_running:
            self.log_message("Listening...", "MIC")
            command = listen()

            if not command:
                continue

            global last_user_interaction
            last_user_interaction = time.time()
            self.log_message(f"You: {command}", "MIC")

# 🧠 SMART SELECTION INTERCEPTOR (VOICE MODE)
            command_lower = command.lower()
            triggers = ["fix code", "fix selected", "analyze code", "broken code", "copy karo", "copy karke", "check karo", "fix"]

            if any(word in command_lower for word in triggers):
                # 🧹 CLEAR CLIPBOARD FIRST to prevent reading old data!
                pyperclip.copy("")
                
                pyautogui.hotkey('ctrl', 'c')
                time.sleep(0.3) 
                
                clipboard_content = pyperclip.paste()
                
                if clipboard_content and len(clipboard_content.strip()) > 3:
                    command = f"The user said: '{command}'. Here is the code from their clipboard:\n\n```python\n{clipboard_content}\n```\n\nPlease find the bug, explain it in the 'reply' field, and use the TYPE action to output the fully fixed code."
                else:
                    self.log_message("⚠️ No text was selected.", "ERR")
                    speak("Boss, aapne koi text select nahi kiya hai.")
                    continue # Skip sending to server

            # DIRECT CALL - Voice loop is already a thread, so we don't start a new one!
            self.process_text_command(command, source="MIC")

    def process_text_command(self, command, source="MIC", retry_count=0): 
        try:
            if source == "PHONE":
                self.log_message(f"Phone: {command}", "PHONE")
            elif source == "SYS_RETRY":
                self.log_message(f"Self-Correcting... Attempt {retry_count}", "SYS")
            payload = {
                "command": command,
                "email": self.email,
                "deviceId": self.device_id,
                "groqKey": self.groq_key,
                "isRetry": source == "SYS_RETRY"
            }
            headers = {"x-api-key": self.api_key, "Content-Type": "application/json"}

            if source != "SYS_RETRY":
                self.log_message("Processing...", "SYS")
                
            response = requests.post(f"{API_URL}/command", json=payload, headers=headers, timeout=60)

            if response.status_code == 200:
                data = response.json()
                reply = data.get("reply")
                intents = data.get("intents") or []
                
                if not isinstance(intents, list): intents = [intents]
                if not intents and data.get("intent"): intents = [data.get("intent")]

                if reply:
                    self.log_message(f"Aanya: {reply}", "AI")
                    speak(reply)

                for item in intents:
                    if isinstance(item, list):
                        for sub in item:
                            if isinstance(sub, dict): self.execute_action(sub, retry_count)
                    elif isinstance(item, dict):
                        self.execute_action(item, retry_count)

                return reply 

            elif response.status_code == 429:
                self.log_message("Daily Limit Exceeded.", "ERR")
                speak("Daily limit reached.")
                return "Daily limit exceeded."
                
            elif response.status_code in [401, 403]:
                self.log_message("Auth Error. Keys invalid.", "ERR")
                self.api_key = ""
                self.groq_key = ""
                if os.path.exists("user_config.json"): os.remove("user_config.json")
                global is_running
                is_running = False
                self.toggle_listening()
                messagebox.showerror("Auth Error", "API Key Invalid. Please restart app.")
                sys.exit()
                return "Auth Error."
            else:
                self.log_message(f"Server Error: {response.status_code}", "ERR")
                return "Server Error."

        except requests.exceptions.Timeout:
            self.log_message("Server Timeout...", "ERR")
            return "Server Timeout."
        except Exception as e:
            self.log_message(f"Error: {e}", "ERR")
            return f"PC Error occurred."
    def execute_action(self, intent, retry_count=0):
        try:
            # 1. Map the keys from the AI's JSON
            action_type = intent.get('type', 'Unknown')   
            action_name = intent.get('action', 'Unknown') 
            payload = intent.get('payload', 'No payload')

            self.log_message(f"Executing: {action_name}", "EXE")
            
            # 2. Run the logic in actions.py
            result = perform(intent, alarm_list=alarms) 

            # 3. Process the Result
            if isinstance(result, dict) and result.get("status") == "error":
                error_msg = result.get("error_msg", "Unknown error")
                
                # If it's not a Python coding task, just report and stop
                if action_type != "PYTHON_EXEC":
                    self.log_message(f"Action Failed: {error_msg}", "ERR")
                    speak(error_msg)
                    return 

                # If it's a Python crash, try the Self-Correction loop
                if retry_count < 3: 
                    self.log_message(f"Code Error. Attempting auto-fix...", "SYS")

                    hidden_prompt = (
                        f"SYSTEM AUTO-RETRY: The code failed with this error:\n{error_msg}\n\n"
                        "Please fix the code and run it again using PYTHON_EXEC. "
                        "Do not use TYPE. Keep the reply very short."
                    )
                    self.process_text_command(hidden_prompt, source="SYS_RETRY", retry_count=retry_count + 1)
                else:
                    self.log_message("Max retries reached. Fix manually.", "ERR")
                    speak("Boss, main is error ko auto-fix nahi kar payi.")
            
            # ✅ SUCCESS: If no error, the function ends quietly here.

        except Exception as e:
            # 🛑 The traceback now works because of the import!
            full_error = traceback.format_exc()
            self.log_message(f"Critical System Error!", "ERR")
            print(full_error) # Prints to your terminal for debugging

if __name__ == "__main__":
    app = AanyaProfessionalApp()
    app.mainloop()

