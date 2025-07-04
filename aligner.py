from typing import List, Dict

def assign_speakers(transcript: List[Dict], diarization: List[Dict]) -> List[Dict]:
    """
    Сопоставляет текст и интервалы спикеров по таймкодам и объединяет сегменты одного спикера.
    
    Возвращает список сегментов:
    [{"start": float, "end": float, "speaker": str, "text": str}]
    """
    if not transcript or not diarization:
        return []
    
    # Сортируем оба списка по времени начала
    transcript_sorted = sorted(transcript, key=lambda x: x["start"])
    diarization_sorted = sorted(diarization, key=lambda x: x["start"])
    
    aligned_segments = []
    current_speaker = None
    current_text = ""
    current_start = 0
    current_end = 0
    
    diar_idx = 0
    n_diar = len(diarization_sorted)
    
    for segment in transcript_sorted:
        seg_start = segment["start"]
        seg_end = segment["end"]
        seg_text = segment["text"]
        
        # Находим соответствующий интервал диаризации
        while diar_idx < n_diar and diarization_sorted[diar_idx]["end"] < seg_start:
            diar_idx += 1
            
        if diar_idx >= n_diar:
            # Если закончились интервалы диаризации, добавляем оставшиеся сегменты без спикера
            aligned_segments.append({
                "start": seg_start,
                "end": seg_end,
                "speaker": None,
                "text": seg_text
            })
            continue
            
        diar_segment = diarization_sorted[diar_idx]
        speaker = diar_segment["speaker"]
        
        # Проверяем, можно ли объединить с предыдущим сегментом того же спикера
        if (speaker == current_speaker and 
            abs(seg_start - current_end) < 1.0):  # Порог объединения - 1 секунда
            current_text += " " + seg_text
            current_end = seg_end
        else:
            # Добавляем предыдущий сегмент, если он есть
            if current_speaker is not None:
                aligned_segments.append({
                    "start": current_start,
                    "end": current_end,
                    "speaker": current_speaker,
                    "text": current_text.strip()
                })
            
            # Начинаем новый сегмент
            current_speaker = speaker
            current_text = seg_text
            current_start = seg_start
            current_end = seg_end
    
    # Добавляем последний сегмент
    if current_speaker is not None:
        aligned_segments.append({
            "start": current_start,
            "end": current_end,
            "speaker": current_speaker,
            "text": current_text.strip()
        })
    
    return aligned_segments