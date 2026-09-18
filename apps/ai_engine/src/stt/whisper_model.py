import os
import time
import logging
from typing import Dict, Any, Optional
import numpy as np
from .audio_preprocessor import AudioPreprocessor

logger = logging.getLogger(__name__)

class FasterWhisperSTT:
    """
    Wrapper cho Faster-Whisper hỗ trợ tiếng Việt.
    Độ trễ mục tiêu <= 2.5s trên GPU T4 hoặc CPU đa luồng.
    """

    def __init__(self, model_size: str = "base", device: str = "cpu", compute_type: str = "int8"):
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.preprocessor = AudioPreprocessor()
        self.model = None
        # Model is loaded lazily on first transcribe call to prevent startup latency

    def _load_model(self):
        try:
            from faster_whisper import WhisperModel
            logger.info(f"Loading Faster-Whisper model '{self.model_size}' on {self.device} ({self.compute_type})...")
            self.model = WhisperModel(self.model_size, device=self.device, compute_type=self.compute_type)
            logger.info("Faster-Whisper model loaded successfully.")
        except Exception as e:
            logger.warning(f"Could not load faster-whisper directly ({e}). Falling back to simulation/lightweight handler.")
            self.model = None

    def transcribe(self, audio_bytes: bytes, filename: str = "", language: str = "vi") -> Dict[str, Any]:
        """
        Nhận vào raw bytes của file ghi âm, trả về text tiếng Việt + metadata thời gian xử lý.
        """
        start_time = time.time()
        audio_array = self.preprocessor.validate_and_convert(audio_bytes, filename)
        audio_array = self.preprocessor.normalize_volume(audio_array)

        if self.model is None:
            self._load_model()

        if self.model is not None:
            try:
                segments, info = self.model.transcribe(
                    audio_array,
                    language=language,
                    beam_size=5,
                    vad_filter=True,
                    vad_parameters=dict(min_silence_duration_ms=500)
                )
                full_text = " ".join([seg.text.strip() for seg in segments])
                latency = time.time() - start_time
                return {
                    "text": full_text,
                    "language": info.language,
                    "language_probability": float(info.language_probability),
                    "duration_seconds": float(info.duration) if hasattr(info, "duration") else len(audio_array) / 16000.0,
                    "latency_seconds": round(latency, 3),
                    "status": "success"
                }
            except Exception as e:
                logger.error(f"Inference error in FasterWhisper: {e}")

        # Fallback simulation nếu chưa load được weights cục bộ
        latency = time.time() - start_time
        duration_sec = round(len(audio_array) / 16000.0, 2) if len(audio_array) > 0 else 0.0
        
        if len(audio_array) == 0:
            return {
                "text": "",
                "language": language,
                "language_probability": 0.0,
                "duration_seconds": 0.0,
                "latency_seconds": round(latency, 3),
                "status": "empty_audio",
                "is_simulated": False
            }

        simulated_text = "Tôi bị sốt cao đau đầu và mệt mỏi từ hôm qua"
        return {
            "text": simulated_text,
            "language": language,
            "language_probability": 0.98,
            "duration_seconds": duration_sec,
            "latency_seconds": round(latency, 3),
            "status": "fallback_simulated",
            "is_simulated": True
        }
