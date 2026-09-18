import numpy as np
import logging
from typing import Dict, Any, Tuple

logger = logging.getLogger(__name__)

class HybridLateFusionLayer:
    """
    Late Fusion tổng hợp điểm xác suất từ 2 nhánh:
    P_final = alpha * P_tabular + (1 - alpha) * P_text

    Trọng số alpha điều chỉnh động:
    - Khi có xét nghiệm máu (Lab indicators): alpha = 0.65
    - Khi chỉ có triệu chứng text: alpha = 0.15 (chỉ dựa vào binary symptom vector)
    """

    def __init__(self, default_alpha: float = 0.65):
        self.default_alpha = default_alpha

    def fuse(self, prob_tabular: np.ndarray, prob_text: np.ndarray, has_lab_data: bool = False) -> Tuple[np.ndarray, float]:
        """
        Thực hiện Late Fusion và trả về (P_final, alpha_used).
        """
        # Chỉ kích hoạt trọng số Tabular khi thực sự có chỉ số cận lâm sàng (Lab indicators)
        alpha = self.default_alpha if has_lab_data else 0.0

        # Đảm bảo shape tương thích
        if len(prob_tabular) != len(prob_text):
            logger.warning("Probabilities dimension mismatch. Reshaping to match tabular classes.")
            min_len = min(len(prob_tabular), len(prob_text))
            prob_tabular = prob_tabular[:min_len]
            prob_text = prob_text[:min_len]

        p_final = alpha * prob_tabular + (1.0 - alpha) * prob_text
        # Chuẩn hóa tổng = 1.0
        sum_p = np.sum(p_final)
        if sum_p > 0:
            p_final = p_final / sum_p

        return p_final, alpha
