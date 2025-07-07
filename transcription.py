from openai import OpenAI
from typing import Dict, List
import os


def transcription(audio_path: str) -> List[Dict]:
    client = OpenAI(api_key=os.getenv("OPENAI_KEY"))
    audio_file = open(audio_path, "rb")

    transcription_obj = client.audio.transcriptions.create(
        file=audio_file,
        model="whisper-1",
        response_format="verbose_json",
        timestamp_granularities=["word"]
    )

    return transcription_obj.dict()['words']
