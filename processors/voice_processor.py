import os
import whisper


class VoiceProcessor:
    def __init__(self):
        self.model = whisper.load_model("small")
        print("Whisper model loaded")

    def transcribe(self, audio_path):
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        result = self.model.transcribe(audio_path)
        return result["text"]