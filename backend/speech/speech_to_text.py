import speech_recognition as sr


def speech_to_text():
    recognizer = sr.Recognizer()

    recognizer.energy_threshold = 80
    recognizer.dynamic_energy_threshold = True
    recognizer.pause_threshold = 0.5
    recognizer.phrase_threshold = 0.0
    recognizer.non_speaking_duration = 0.2

    try:
        mic_index = None
        mic_list = sr.Microphone.list_microphone_names()

        for i, name in enumerate(mic_list):
            name_lower = name.lower()

            if "headset" in name_lower or "bluetooth" in name_lower or "boult" in name_lower:
                mic_index = i
                break

        # fallback to default mic
        if mic_index is None:
            mic_index = None

        with sr.Microphone(device_index=mic_index) as source:

            print("🎤 Speak now...")

            recognizer.adjust_for_ambient_noise(source, duration=0.3)

            audio = recognizer.listen(
                source,
                timeout=6,
                phrase_time_limit=5
            )

        text = recognizer.recognize_google(audio, language="en-US")

        print("You said:", text)

        return text.lower()

    except sr.WaitTimeoutError:
        print("⏱️ Listening timeout")
        return ""

    except sr.UnknownValueError:
        print("❌ Could not understand audio")
        return ""

    except sr.RequestError as e:
        print("❌ Google API error:", e)
        return ""

    except Exception as e:
        print("❌ Mic error:", e)
        return ""