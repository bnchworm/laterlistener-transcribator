from openai import OpenAI
from typing import Dict, List


def transcription(audio_path: str) -> List[Dict]:
    client = OpenAI()
    audio_file = open("audio.wav", "rb")

    transcription_obj = client.audio.transcriptions.create(
        file=audio_file,
        model="whisper-1",
        response_format="verbose_json",
        timestamp_granularities=["word"]
    )

    return transcription_obj.dict()['words']
