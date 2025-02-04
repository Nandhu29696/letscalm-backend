import speech_recognition as sr

def transcribe_audio(file_path: str):
    recognizer = sr.Recognizer()
    with sr.AudioFile(file_path) as source:
        audio_data = recognizer.record(source)
        try:
            transcription = recognizer.recognize_sphinx(audio_data)
            return transcription
        except sr.UnknownValueError:
            return "Could not understand the audio."
        except sr.RequestError as e:
            return f"Sphinx error: {str(e)}"
