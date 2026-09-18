import os
import re
import json
import asyncio
import logging
from typing import Dict, Any, List, Optional, Tuple
from ..core.config import settings
from .local_llm_service import LocalLLMService
from .gemini_service import GeminiMedicalReasoningService
from .cohere_service import CohereMedicalReasoningService
from .conversational_engine import conversational_engine

logger = logging.getLogger(__name__)

class UnifiedClinicalReasoningService:
    """
    Trung tâm Điều phối Suy luận Y khoa (Unified Clinical Reasoning Coordinator):
    - Race condition giữa Google Gemini và Cohere: bên nào trả lời trước → kết quả chính.
    - Câu trả lời còn lại → alternative_answer để người dùng chuyển đổi bằng mũi tên.
    - Fallback sang Local LLM hoặc Deterministic Engine nếu cả 2 cloud thất bại.
    """

    def __init__(self):
        self.local_llm = LocalLLMService()
        self.gemini_service = GeminiMedicalReasoningService()
        self.cohere_service = CohereMedicalReasoningService()
        self.provider_mode = settings.LLM_PROVIDER.lower()

    async def _call_gemini_async(
        self,
        patient_message: str,
        predicted_diseases: List[Dict[str, Any]],
        symptoms: List[Dict[str, Any]],
        lab_indicators: Dict[str, Any],
        rag_citations: List[Dict[str, Any]],
        chat_history: Optional[List[Dict[str, str]]],
        is_emergency: bool,
        api_key: Optional[str],
        negated_symptoms: Optional[List[Dict[str, Any]]] = None,
        clarifying_questions: Optional[List[Dict[str, Any]]] = None,
        clinical_stage: str = "provisional_assumption",
    ) -> Tuple[Optional[str], str]:
        """Gọi Gemini trong thread pool để không block event loop."""
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self.gemini_service.synthesize_medical_response(
                    patient_message=patient_message,
                    predicted_diseases=predicted_diseases,
                    symptoms=symptoms,
                    lab_indicators=lab_indicators,
                    rag_citations=rag_citations,
                    chat_history=chat_history,
                    is_emergency=is_emergency,
                    api_key=api_key,
                    negated_symptoms=negated_symptoms,
                    clarifying_questions=clarifying_questions,
                    clinical_stage=clinical_stage,
                )
            )
            return (result, "cloud_gemini") if result else (None, "cloud_gemini")
        except Exception as e:
            logger.warning(f"Gemini async call failed: {e}")
            return (None, "cloud_gemini")

    async def _call_cohere_async(
        self,
        patient_message: str,
        predicted_diseases: List[Dict[str, Any]],
        symptoms: List[Dict[str, Any]],
        lab_indicators: Dict[str, Any],
        rag_citations: List[Dict[str, Any]],
        chat_history: Optional[List[Dict[str, str]]],
        is_emergency: bool,
        api_key: Optional[str],
        negated_symptoms: Optional[List[Dict[str, Any]]] = None,
        clarifying_questions: Optional[List[Dict[str, Any]]] = None,
        clinical_stage: str = "provisional_assumption",
    ) -> Tuple[Optional[str], str]:
        """Gọi Cohere trong thread pool để không block event loop."""
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self.cohere_service.synthesize_medical_response(
                    patient_message=patient_message,
                    predicted_diseases=predicted_diseases,
                    symptoms=symptoms,
                    lab_indicators=lab_indicators,
                    rag_citations=rag_citations,
                    chat_history=chat_history,
                    is_emergency=is_emergency,
                    api_key=api_key,
                    negated_symptoms=negated_symptoms,
                    clarifying_questions=clarifying_questions,
                    clinical_stage=clinical_stage,
                )
            )
            return (result, "cloud_cohere") if result else (None, "cloud_cohere")
        except Exception as e:
            logger.warning(f"Cohere async call failed: {e}")
            return (None, "cloud_cohere")

    async def generate_clinical_advice(
        self,
        patient_message: str,
        predicted_diseases: List[Dict[str, Any]],
        symptoms: List[Dict[str, Any]],
        lab_indicators: Dict[str, Any],
        rag_citations: List[Dict[str, Any]],
        chat_history: Optional[List[Dict[str, str]]] = None,
        is_emergency: bool = False,
        gemini_api_key: Optional[str] = None,
        cohere_api_key: Optional[str] = None,
        negated_symptoms: Optional[List[Dict[str, Any]]] = None,
        clarifying_questions: Optional[List[Dict[str, Any]]] = None,
        clinical_stage: str = "provisional_assumption"
    ) -> Dict[str, Any]:
        """
        Race condition giữa Gemini và Cohere:
        - Gọi song song cả 2 bằng asyncio.gather
        - Provider nào trả về trước → primary response
        - Provider còn lại → alternative_answer
        - Fallback: Local LLM → Deterministic Engine
        """
        used_provider = "rule_based"
        response_text = None
        alternative_text = None
        alternative_provider = None

        # 1. Ưu tiên Local LLM nếu cấu hình hybrid/local
        if self.provider_mode in ["local", "hybrid"]:
            try:
                response_text = await self.local_llm.generate_response(
                    patient_message=patient_message,
                    predicted_diseases=predicted_diseases,
                    symptoms=symptoms,
                    lab_indicators=lab_indicators,
                    rag_citations=rag_citations,
                    chat_history=chat_history,
                    is_emergency=is_emergency,
                    negated_symptoms=negated_symptoms,
                    clarifying_questions=clarifying_questions,
                    clinical_stage=clinical_stage,
                )
                if response_text:
                    used_provider = f"local_llm ({settings.LOCAL_LLM_MODEL})"
            except Exception as e:
                logger.warning(f"Local LLM routing failed: {e}")

        # 2. Race Gemini vs Cohere song song
        if not response_text and self.provider_mode in ["gemini", "hybrid"]:
            has_gemini = bool((gemini_api_key or os.getenv("GEMINI_API_KEY", "")).strip())
            has_cohere = bool((cohere_api_key or os.getenv("COHERE_API_KEY", "")).strip())

            if has_gemini or has_cohere:
                tasks = []

                if has_gemini:
                    tasks.append(self._call_gemini_async(
                        patient_message=patient_message,
                        predicted_diseases=predicted_diseases,
                        symptoms=symptoms,
                        lab_indicators=lab_indicators,
                        rag_citations=rag_citations,
                        chat_history=chat_history,
                        is_emergency=is_emergency,
                        api_key=gemini_api_key,
                        negated_symptoms=negated_symptoms,
                        clarifying_questions=clarifying_questions,
                        clinical_stage=clinical_stage,
                    ))
                if has_cohere:
                    tasks.append(self._call_cohere_async(
                        patient_message=patient_message,
                        predicted_diseases=predicted_diseases,
                        symptoms=symptoms,
                        lab_indicators=lab_indicators,
                        rag_citations=rag_citations,
                        chat_history=chat_history,
                        is_emergency=is_emergency,
                        api_key=cohere_api_key,
                        negated_symptoms=negated_symptoms,
                        clarifying_questions=clarifying_questions,
                        clinical_stage=clinical_stage,
                    ))

                try:
                    results = await asyncio.wait_for(
                        asyncio.gather(*tasks, return_exceptions=True),
                        timeout=4.5
                    )

                    successful = []
                    for res in results:
                        if isinstance(res, Exception):
                            continue
                        text, provider = res
                        if text:
                            successful.append((text, provider))

                    if len(successful) >= 1:
                        response_text, used_provider = successful[0]
                        logger.info(f"Primary provider: {used_provider}")

                    if len(successful) >= 2:
                        alternative_text, alternative_provider = successful[1]
                        logger.info(f"Alternative provider stored: {alternative_provider}")

                except asyncio.TimeoutError:
                    logger.warning("Cloud AI race timed out (>4.5s). Fast-failing to deterministic protocol.")
                except Exception as e:
                    logger.warning(f"Race condition gather failed: {e}")

        # 3. Fallback sang Deterministic nếu cả 2 cloud đều không trả lời
        cloud_errors = []
        gemini_err = getattr(self.gemini_service, "last_error", None)
        if gemini_err:
            cloud_errors.append(gemini_err)
        cohere_err = getattr(self.cohere_service, "last_error", None)
        if cohere_err:
            cloud_errors.append(cohere_err)

        if not response_text:
            response_text = self._build_deterministic_clinical_response(
                patient_message=patient_message,
                predicted_diseases=predicted_diseases,
                symptoms=symptoms,
                lab_indicators=lab_indicators,
                rag_citations=rag_citations,
                is_emergency=is_emergency,
                negated_symptoms=negated_symptoms,
                clarifying_questions=clarifying_questions,
                clinical_stage=clinical_stage
            )
            used_provider = "deterministic_clinical_protocol"

            # Nếu cloud AI gặp lỗi (429, 503, 404...), hiển thị rõ mã lỗi cho người dùng biết
            if cloud_errors:
                err_summary = " | ".join(cloud_errors)
                response_text += f"\n\n> ⚠️ **Mã lỗi dịch vụ Cloud AI:** `[{err_summary}]`  \n> *Hệ thống đã tự động chuyển sang Phác đồ Lâm sàng Chuẩn Bộ Y Tế để phục vụ bạn liên tục mà không bị gián đoạn.*"

        return {
            "text": response_text,
            "provider": used_provider,
            "is_emergency": is_emergency,
            "alternative_text": alternative_text,
            "alternative_provider": alternative_provider,
            "cloud_errors": cloud_errors,
        }

    def _build_deterministic_clinical_response(
        self,
        patient_message: str,
        predicted_diseases: List[Dict[str, Any]],
        symptoms: List[Dict[str, Any]],
        lab_indicators: Dict[str, Any],
        rag_citations: List[Dict[str, Any]],
        is_emergency: bool = False,
        negated_symptoms: Optional[List[Dict[str, Any]]] = None,
        clarifying_questions: Optional[List[Dict[str, Any]]] = None,
        clinical_stage: str = "provisional_assumption"
    ) -> str:
        """Sinh câu trả lời y tế linh hoạt, ân cần theo ý định qua ConversationalEngine."""
        return conversational_engine.generate_response(
            patient_message=patient_message,
            clinical_state=None,
            predicted_diseases=predicted_diseases,
            symptoms=symptoms,
            negated_symptoms=negated_symptoms or [],
            lab_indicators=lab_indicators or {},
            rag_citations=rag_citations or [],
            clarifying_questions=clarifying_questions,
            clinical_stage=clinical_stage,
            is_emergency=is_emergency
        )


clinical_reasoning_service = UnifiedClinicalReasoningService()
