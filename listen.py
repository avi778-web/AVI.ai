import speech_recognition as sr

def listen():
    r = sr.Recognizer()
    
    # 🧠 UPGRADE 1: Increase pause_threshold so she doesn't cut you off when you take a breath
    r.pause_threshold = 1.5 
    
    # Optional: Adjust sensitivity to ignore background fans/AC (makes processing faster)
    r.energy_threshold = 300
    r.dynamic_energy_threshold = True

    with sr.Microphone() as source:
        # 🧠 UPGRADE 2: Quickly learn the background noise for 0.5 seconds
        r.adjust_for_ambient_noise(source, duration=0.5)
        
        print("🎙️ Listening...")
        try:
            # 🧠 UPGRADE 3: Removed phrase_time_limit! 
            # timeout=8 just means "wait up to 8 seconds for the Boss to START speaking"
            audio = r.listen(source, timeout=8) 
            
            print("⏳ Recognizing...")
            # Added 'en-IN' language code for much faster and more accurate Hinglish recognition
            text = r.recognize_google(audio, language='en-IN')
            
            print(f"🗣️ You said: {text}")
            return text.lower()
            
        except sr.WaitTimeoutError:
            return None
        except sr.UnknownValueError:
            return None
        except Exception as e:
            print(f"❌ Microphone Error: {e}")
            return None
