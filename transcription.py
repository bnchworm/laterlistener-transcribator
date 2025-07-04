from typing import List, Dict
import whisper
from pathlib import Path

def transcribe(audio_path: str, model_size: str = "medium") -> List[Dict]:
    """
    Транскрибирует WAV 16kHz mono файл через Whisper.
    Возвращает список сегментов с таймкодами и текстом.
    """
    if not Path(audio_path).exists():
        raise FileNotFoundError(f"Аудиофайл не найден: {audio_path}")
    
    model = whisper.load_model(model_size)
    result = model.transcribe(audio_path)
    
    return [{
        "start": segment["start"],
        "end": segment["end"],
        "text": segment["text"].strip()
    } for segment in result["segments"]]

# ===== ТЕСТ =====
"""
if __name__ == "__main__":
    test_audio = "new.wav"
    try:
        segments = transcribe(test_audio, model_size="small")
        for seg in segments:
            print(f"[{seg['start']:.2f}-{seg['end']:.2f}]: {seg['text']}")
    except Exception as e:
        print(f"Ошибка: {e}")
"""
