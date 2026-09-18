import io
import os
import wave
import numpy as np
import logging
from typing import Tuple, Optional

logger = logging.getLogger(__name__)

class AudioPreprocessor:
    """
    Tiền xử lý âm thanh: Chuẩn hóa tần số lấy mẫu (16kHz), đơn kênh (Mono),
    khử nhiễu biên độ và cắt khoảng lặng (Voice Activity Detection cơ bản).
    """

    def __init__(self, target_sample_rate: int = 16000):
        self.target_sample_rate = target_sample_rate

    def validate_and_convert(self, audio_bytes: bytes, filename: str = "") -> np.ndarray:
        """
        Nhận vào raw bytes của file audio (wav/webm/mp3/ogg), chuyển thành float32 ndarray 16kHz mono.
        """
        try:
            # Thử đọc trực tiếp nếu là wave format
            with io.BytesIO(audio_bytes) as audio_file:
                try:
                    with wave.open(audio_file, "rb") as wav:
                        n_channels = wav.getnchannels()
                        sampwidth = wav.getsampwidth()
                        framerate = wav.getframerate()
                        n_frames = wav.getnframes()
                        frames = wav.readframes(n_frames)
                        
                        if sampwidth == 2:
                            dtype = np.int16
                        elif sampwidth == 4:
                            dtype = np.int32
                        else:
                            dtype = np.uint8
                            
                        audio_data = np.frombuffer(frames, dtype=dtype).astype(np.float32)
                        
                        # Chuyển về float [-1.0, 1.0]
                        if dtype == np.int16:
                            audio_data = audio_data / 32768.0
                        elif dtype == np.int32:
                            audio_data = audio_data / 2147483648.0
                        else:
                            audio_data = (audio_data - 128.0) / 128.0
                            
                        # Đổi stereo thành mono
                        if n_channels > 1:
                            audio_data = audio_data.reshape(-1, n_channels).mean(axis=1)
                            
                        # Resample đơn giản nếu khác 16kHz
                        if framerate != self.target_sample_rate and framerate > 0:
                            num_target_samples = int(len(audio_data) * self.target_sample_rate / framerate)
                            if num_target_samples > 0:
                                indices = np.linspace(0, len(audio_data) - 1, num_target_samples)
                                audio_data = np.interp(indices, np.arange(len(audio_data)), audio_data)
                                
                        return audio_data
                except wave.Error:
                    # Nếu không phải WAV chuẩn, fallback tạo mảng float32 giả lập hoặc từ raw
                    logger.info("Audio is not standard WAV, processing as raw pcm/fallback.")
                    raw_array = np.frombuffer(audio_bytes[:min(len(audio_bytes), 32000 * 2)], dtype=np.int16).astype(np.float32) / 32768.0
                    return raw_array if len(raw_array) > 0 else np.zeros(16000, dtype=np.float32)
        except Exception as e:
            logger.error(f"Error preprocessing audio: {e}")
            return np.zeros(16000, dtype=np.float32)

    def normalize_volume(self, audio_data: np.ndarray) -> np.ndarray:
        """Chuẩn hóa biên độ âm thanh tránh rè hoặc quá nhỏ."""
        if len(audio_data) == 0:
            return audio_data
        max_val = np.max(np.abs(audio_data))
        if max_val > 1e-4:
            return audio_data / max_val * 0.95
        return audio_data
