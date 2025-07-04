from typing import List, Dict
import whisper
import logging
from pathlib import Path

# Настройка логгирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def transcribe(audio_path: str, model_size: str = "medium") -> List[Dict]:
    """
    Транскрибирует аудиофайл в формате WAV 16kHz mono через Whisper.
    Возвращает список сегментов с таймкодами и текстом.
    
    Args:
        audio_path: путь к аудиофайлу (.wav 16kHz mono)
        model_size: размер модели (tiny, base, small, medium, large)
    
    Returns:
        [{"start": float, "end": float, "text": str}, ...]
    """
    try:
        # Проверка существования файла
        if not Path(audio_path).exists():
            logger.error(f"Файл не найден: {audio_path}")
            raise FileNotFoundError(f"Аудиофайл не найден: {audio_path}")
        
        logger.info(f"Начинаем обработку файла: {audio_path}")
        
        # Загрузка модели
        logger.info(f"Загрузка модели Whisper: {model_size}")
        model = whisper.load_model(model_size)
        
        # Транскрипция (Whisper сам проверяет параметры аудио)
        logger.info("Запуск транскрипции...")
        result = model.transcribe(audio_path)
        
        # Форматирование результата
        segments = [
            {
                "start": segment["start"],
                "end": segment["end"], 
                "text": segment["text"].strip()
            }
            for segment in result["segments"]
        ]
        
        logger.info(f"Транскрипция завершена. Получено сегментов: {len(segments)}")
        return segments
        
    except Exception as e:
        logger.error(f"Ошибка транскрипции: {e}")
        raise

# ===== ТЕСТ =====

if __name__ == "__main__":
    test_audio = "new.wav"
    try:
        segments = transcribe(test_audio, model_size="small")
        for seg in segments:
            print(f"[{seg['start']:.2f}-{seg['end']:.2f}]: {seg['text']}")
    except Exception as e:
        print(f"Ошибка: {e}")
