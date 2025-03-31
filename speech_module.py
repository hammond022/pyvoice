import speech_recognition as sr

def recognize_speech(speech_queue):
    recognizer = sr.Recognizer()
    mic = sr.Microphone()
    with mic as source:
        recognizer.adjust_for_ambient_noise(source)
    
    while True:
        with mic as source:
            try:
                audio = recognizer.listen(source)
                text = recognizer.recognize_google(audio).lower()
                speech_queue.put(text)
            except sr.UnknownValueError:
                continue
            except sr.RequestError:
                speech_queue.put("Speech Recognition API unavailable")
                break