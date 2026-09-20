import re
import uuid
import time
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import os
import sys

# Ensure ai_engine is in python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "ai_engine")))
from src.classification.clarification_engine import ClarificationEngine

import hashlib
from ..core.redis import redis_manager
from ..core.config import settings

from .triage_service import triage_service
from .rag_service import rag_service
from .gemini_service import gemini_service
from .clinical_reasoning_service import clinical_reasoning_service
from .dialogue_state_service import dialogue_state_service, resolve_question_topic, SLOT_TOPIC_MAP

logger = logging.getLogger(__name__)
clarification_engine = ClarificationEngine()

class ChatService:
    def __init__(self):
        self._triage_cache: Dict[str, Any] = {}

    async def _analyze_triage_with_cache(
        self,
        text: str,
        audio_bytes: Optional[bytes] = None,
        audio_filename: str = "",
        document_bytes: Optional[bytes] = None,
        document_filename: str = ""
    ) -> Dict[str, Any]:
        """Phân tích triệu chứng có tích hợp bộ nhớ đệm phân tán Redis (hoặc memory fallback)."""
        if not audio_bytes and not document_bytes:
            clean_q = (text or "").strip().lower()
            cache_key = f"triage_cache:{hashlib.md5(clean_q.encode('utf-8')).hexdigest()}"
            cached = await redis_manager.get_json(cache_key)
            if cached:
                return cached
            res = triage_service.analyze(
                text=text,
                audio_bytes=audio_bytes,
                audio_filename=audio_filename,
                document_bytes=document_bytes,
                document_filename=document_filename
            )
            await redis_manager.set_json(cache_key, res, ex=settings.CACHE_TTL_TRIAGE)
            return res
        return triage_service.analyze(
            text=text,
            audio_bytes=audio_bytes,
            audio_filename=audio_filename,
            document_bytes=document_bytes,
            document_filename=document_filename
        )

    def _handle_general_medical_intent(self, user_message: str) -> Optional[str]:
        """
        Nhận diện và định tuyến thông minh các lượt hội thoại:
        1. Câu hỏi kiến thức y tế chuẩn (Oresol, Paracetamol, Kháng sinh, Cách hạ sốt...) -> Phản hồi chuẩn mực tức thì.
        2. Chào hỏi, gọi trợ lý, giao tiếp xã giao (Greetings, Chitchat) -> Phản hồi thân thiện, KHÔNG TRUY VẤN RAG/TRIAGE.
        3. Lời cảm ơn, tạm biệt -> Phản hồi lịch sự, KHÔNG TRUY VẤN RAG/TRIAGE.
        4. Giới thiệu chức năng / Danh tính trợ lý -> Trả lời chức năng, KHÔNG TRUY VẤN RAG/TRIAGE.
        5. Câu hỏi ngoài lĩnh vực y tế (Out-of-Domain Guardrail: code, toán, thời tiết, giải trí...) -> Lịch sự từ chối, KHÔNG TRUY VẤN RAG/TRIAGE.
        """
        msg = user_message.lower().strip()
        if not msg:
            return None

        # 1. Danh mục từ khóa & dấu hiệu y tế / triệu chứng lâm sàng toàn diện
        clinical_keywords = [
            # Triệu chứng cơ năng & thực thể
            "sốt", "nóng", "rét", "lạnh", "ớn lạnh", "ho", "đau", "nhức", "mỏi", "tức", "rát",
            "ngứa", "viêm", "sưng", "phù", "nôn", "ói", "tiêu chảy", "táo bón", "chóng mặt",
            "buồn nôn", "phát ban", "khó thở", "thở gấp", "thở dốc", "hụt hơi", "co giật", "méo miệng",
            "liệt", "sụt cân", "giảm cân", "phù nề", "vết thương", "lở loét", "đờm", "kinh nguyệt",
            "tiểu", "đại tiện", "khát nước", "mệt mỏi", "mệt", "uể oải", "khàn tiếng", "mất tiếng",
            "sổ mũi", "ngạt mũi", "nghẹt mũi", "chảy nước mũi", "hắt hơi", "ợ chua", "ợ hơi",
            "trào ngược", "đầy bụng", "chướng bụng", "khó tiêu", "buốt", "rắt", "bí tiểu", "chảy máu",
            "xuất huyết", "bầm tím", "ngất", "choáng", "xây xẩm", "hoa mắt", "mất ngủ", "chán ăn",
            "biếng ăn", "khó nuốt", "nuốt vướng", "mẩn đỏ", "dị ứng", "mề đay", "mụn", "khối u", "u bướu", "hạch",
            "tê bì", "chuột rút", "co cứng", "khó chịu", "không khỏe", "ốm", "yếu",
            # Cơ quan giải phẫu
            "ngực", "bụng", "đầu", "họng", "mắt", "tai", "mũi", "da", "miệng", "môi", "lưỡi",
            "răng", "nướu", "lợi", "cổ", "vai", "gáy", "lưng", "sườn", "eo", "hông", "tay",
            "chân", "đùi", "gối", "khớp", "xương", "cơ", "tim", "phổi", "gan", "thận", "dạ dày",
            "bao tử", "ruột", "tá tràng", "đại tràng", "trực tràng", "mật", "tụy", "bàng quang",
            "não", "mạch máu", "niệu",
            # Dược phẩm, xét nghiệm, y khoa chuyên biệt
            "máu", "xét nghiệm", "ocr", "thuốc", "kháng sinh", "paracetamol", "panadol", "efferalgan",
            "oresol", "aspirin", "ibuprofen", "kháng viêm", "huyết áp", "nhịp tim", "đường huyết",
            "sp02", "cấp cứu", "115", "điều trị", "phác đồ", "triệu chứng", "bệnh án", "ung thư",
            "uống thuốc", "liều dùng", "viên nén", "khám bệnh", "tiêm vắc xin", "vắc xin", "chích ngừa",
            "truyền dịch", "nội soi", "siêu âm", "x-quang", "chụp ct", "mri", "chỉ số", "kết quả",
            "tai biến", "đột quỵ", "nhồi máu", "dịch bệnh", "nhiễm trùng", "nhiễm khuẩn", "vi khuẩn", "virus",
            "covid", "sốt xuất huyết", "tay chân miệng", "sởi", "thủy đậu", "gout", "tiểu đường",
            "đái tháo đường", "men gan", "mỡ máu", "acid uric", "bạch cầu", "hồng cầu", "tiểu cầu",
            "wbc", "rbc", "plt", "glucose", "ast", "alt", "creatinine", "ure", "mang thai", "có thai", "bầu"
        ]
        # Khớp từ khóa lâm sàng theo ranh giới từ ngữ (Word boundary) để tránh nhận diện nhầm từ tiếng Anh / từ ghép
        clinical_pattern = r'(?:^|[^\wÀ-ỹ])(' + '|'.join(re.escape(k) for k in sorted(clinical_keywords, key=len, reverse=True)) + r')(?=[^\wÀ-ỹ]|$)'
        has_clinical_keyword = bool(re.search(clinical_pattern, msg, re.IGNORECASE))

        # 1. Giới thiệu chức năng & Danh tính MediBot AI
        is_identity_or_help = bool(re.search(
            r'(?:bạn là ai|bạn tên là gì|bạn tên gì|ai tạo ra bạn|ai phát triển bạn|bạn ở đâu|bạn làm được gì|bạn có thể làm gì|hướng dẫn|chức năng|giới thiệu|bạn giúp được gì|cách sử dụng|tính năng)',
            msg
        ))
        if is_identity_or_help:
            return (
                "Chào bạn! Tôi là **Trợ Lý Y Tế AI Đa Phương Thức (MediBot AI)** được chuẩn hóa theo danh mục bệnh học & ICD-10 của Bộ Y Tế Việt Nam. Tôi có thể hỗ trợ bạn:\n\n"
                "🩺 **1. Khám & Phân Tầng Triệu Chứng:** Tiếp nhận mô tả bệnh qua văn bản hoặc giọng nói tiếng Việt, tự động bóc tách thực thể triệu chứng (NER) và phân tầng nhóm bệnh nguy cơ cao nhất.\n\n"
                "🧪 **2. Bóc Tách Phiếu Xét Nghiệm Máu (OCR):** Đọc tự động các chỉ số sinh hóa máu (WBC, RBC, Glucose, AST, ALT, Bilirubin, Ure...) và cảnh báo chỉ số bất thường.\n\n"
                "🚨 **3. Báo Động Đỏ Cấp Cứu 115 (Red Flags):** Phát hiện tức thì các dấu hiệu nguy kịch đe dọa sinh mạng (FAST Đột quỵ, Nhồi máu cơ tim, Sốc sốt xuất huyết, Bí tiểu cấp).\n\n"
                "📚 **4. Tra Cứu Tri Thức Y Khoa & Phác Đồ Bộ Y Tế (RAG):** Trích dẫn chính xác hướng dẫn chăm sóc, chế độ ăn uống và phác đồ điều trị ngoại trú.\n\n"
                "📋 **5. Lập Bệnh Án Ngoại Trú Điện Tử & Xuất PDF:** Tự động tổng hợp toàn bộ diễn biến ca khám thành hồ sơ bệnh án đa bệnh lý và in/tải file PDF chuẩn bệnh viện.\n\n"
                "👉 Hiện tại bạn đang cảm thấy khó chịu ở đâu hay cần tư vấn về vấn đề sức khỏe nào? Hãy chia sẻ cho tôi nhé!"
            )

        # 2. Lời chào, hỏi thăm & Giao tiếp xã giao (Greetings / Chitchat)
        is_greeting = bool(re.search(
            r'(?:^(?:xin chào|chào|hello|hi|hey|alo|hé lô|hế lô|hế lo|good morning|good afternoon|good evening)\b|'
            r'(?:chào bạn|chào bác sĩ|chào bs|chào bot|chào ad|chào em|chào anh|chào chị|chào nha|chào mọi người|chào buổi sáng|chào buổi chiều|chào buổi tối)|'
            r'^(?:bạn ơi|bot ơi|bác sĩ ơi|bs ơi|ad ơi|ê bot|alo bạn ơi|alo bot|alo ad)\b|'
            r'(?:có ai không|có ai ở đây không|có ai trực không|bạn có đó không)|'
            r'(?:bạn khỏe không|dạo này thế nào|khỏe không bot|bạn có mệt không))',
            msg
        ))
        if is_greeting and not has_clinical_keyword:
            return (
                "Xin chào bạn! Tôi là **Trợ Lý Y Tế AI (MediBot)** được chuẩn hóa theo danh mục bệnh học & ICD-10 của Bộ Y Tế Việt Nam.\n\n"
                "Tôi có thể hỗ trợ bạn:\n"
                "- 🩺 **Đánh giá triệu chứng lâm sàng** & phân tầng nhóm bệnh nguy cơ\n"
                "- 🧪 **Đọc & bóc tách chỉ số phiếu xét nghiệm máu (OCR)**\n"
                "- 🚨 **Cảnh báo dấu hiệu nguy hiểm cấp cứu Red Flag 115**\n"
                "- 📚 **Tra cứu phác đồ điều trị & hướng dẫn chăm sóc ngoại trú**\n\n"
                "Hiện tại bạn đang cảm thấy không khỏe ở đâu hoặc cần tư vấn về vấn đề sức khỏe nào? Hãy chia sẻ cho tôi nhé!"
            )

        # 3. Lời cảm ơn (Thanks & Gratitude)
        is_thanks = bool(re.search(
            r'(?:^(?:cảm ơn|cám ơn|thank you|thanks|cảm ơn bạn|cảm ơn bác sĩ|rất cảm ơn|ok cảm ơn|tuyệt vời|tốt lắm|được rồi cảm ơn|cảm ơn nhiều|cảm ơn bot)\b|'
            r'(?:cảm ơn bạn nhé|cảm ơn bác sĩ nhiều|cảm ơn nhiều nhé))',
            msg
        ))
        if is_thanks and not has_clinical_keyword:
            return (
                "Dạ không có gì ạ! Rất vui vì được đồng hành và hỗ trợ bạn. 🩺\n\n"
                "Nếu bạn có thêm bất kỳ triệu chứng bất thường nào hoặc có kết quả xét nghiệm mới cần phân tích, hãy nhắn cho tôi bất cứ lúc nào nhé. Chúc bạn luôn dồi dào sức khỏe!"
            )

        # 4. Tạm biệt (Farewells)
        is_farewell = bool(re.search(
            r'(?:^(?:tạm biệt|bye|goodbye|hẹn gặp lại|chúc ngủ ngon|ngủ ngon|gặp lại sau)\b|'
            r'(?:tạm biệt bot|chào tạm biệt))',
            msg
        ))
        if is_farewell and not has_clinical_keyword:
            return (
                "Tạm biệt bạn! Hãy chú ý nghỉ ngơi điều độ và theo dõi sức khỏe nhé. Chúc bạn một ngày an lành!"
            )

        # 5. Rõ ràng ngoài phạm vi y tế (Out-of-Domain: code, toán, bóng đá, thời tiết)
        is_explicit_out_of_domain = bool(re.search(
            r'(?:viết code|lập trình|python|javascript|giải phương trình|tính tích phân|thời tiết hôm nay|dự báo thời tiết|kết quả bóng đá|tỷ giá|chứng khoán|đầu tư bitcoin)',
            msg
        ))
        if is_explicit_out_of_domain and not has_clinical_keyword:
            return (
                "Xin lỗi bạn, tôi là **MediBot AI** - Hệ thống trợ lý chuyên sâu và độc quyền trong lĩnh vực **Y Tế & Chăm Sóc Sức Khỏe** (chuẩn hóa theo ICD-10 & Phác đồ Bộ Y Tế Việt Nam).\n\n"
                "Tôi chỉ có thể hỗ trợ giải đáp các vấn đề chuyên môn y khoa:\n"
                "- 🩺 **Tiếp nhận & phân tầng nguy cơ** từ các triệu chứng bệnh lý cơ thể\n"
                "- 🧪 **Bóc tách & giải thích chỉ số** xét nghiệm máu, phiếu cận lâm sàng\n"
                "- 🚨 **Cảnh báo & hướng dẫn sơ cứu** các dấu hiệu cấp cứu Red Flag 115\n"
                "- 💊 **Tư vấn hướng dẫn dùng thuốc** & phác đồ điều trị an toàn chuẩn Bộ Y Tế\n\n"
                "Rất tiếc tôi **không tiếp nhận các câu hỏi nằm ngoài lĩnh vực y tế**. Nếu bạn đang gặp phải bất kỳ triệu chứng khó chịu nào, hãy chia sẻ để tôi hỗ trợ nhé!"
            )

        return None

    def _extract_all_session_problems(self, chat_history: Optional[List[Dict[str, Any]]], current_message: str) -> List[Dict[str, Any]]:
        """
        Quét toàn bộ lịch sử phiên khám để bóc tách TẤT CẢ các vấn đề bệnh lý độc lập mà bệnh nhân đã trao đổi.
        """
        all_user_turns = []
        if chat_history:
            for item in chat_history:
                if item.get("sender") == "user":
                    c = item.get("content") or item.get("text") or ""
                    if c and not re.search(r'^(?:trả lời|chọn|đáp án)[:\s"]+', c, flags=re.IGNORECASE):
                        all_user_turns.append(c)
        if current_message and not re.search(r'^(?:trả lời|chọn|đáp án)[:\s"]+', current_message, flags=re.IGNORECASE):
            all_user_turns.append(current_message)

        problems_map = {}
        for turn in all_user_turns:
            if self._handle_general_medical_intent(turn):
                continue
            # In-memory cache lookup to avoid redundant O(N) pipeline re-evaluation
            cache_key = hashlib.md5(turn.strip().lower().encode('utf-8')).hexdigest()
            t = self._triage_cache.get(cache_key)
            if not t:
                t = triage_service.analyze(text=turn)
                self._triage_cache[cache_key] = t

            syms = t.get("extracted_entities", {}).get("symptoms", [])
            preds = t.get("triage_results", [])
            if syms and preds:
                primary = dict(preds[0])
                icd = primary.get("icd_code")
                if icd not in problems_map:
                    primary["symptoms"] = [s.get("standard_term") for s in syms]
                    primary["symptom_entities"] = syms
                    problems_map[icd] = primary
                else:
                    for s in syms:
                        st = s.get("standard_term")
                        if st and st not in problems_map[icd]["symptoms"]:
                            problems_map[icd]["symptoms"].append(st)
                            problems_map[icd]["symptom_entities"].append(s)

        res = []
        for idx, item in enumerate(problems_map.values(), 1):
            item["rank"] = idx
            res.append(item)
        return res

    def _parse_clarification_response(self, msg: str) -> str:
        """
        Bóc tách câu trả lời thực tế của người dùng từ chuỗi làm rõ (Clarification Response).
        Loại bỏ các tiêu đề câu hỏi (như 'Thân nhiệt...: Không sốt') để tránh các từ khóa trong câu hỏi
        như 'cơn sốt', 'xuất huyết' gây ô nhiễm vào NER và làm sai lệch phân tầng bệnh.
        """
        clean = msg.strip()
        clean = re.sub(
            r'^(?:trả lời câu hỏi làm rõ|trả lời|chọn|đáp án|tôi xin bổ sung thông tin lâm sàng|bổ sung thông tin lâm sàng|tôi xin bổ sung|bổ sung thông tin|tôi có các dấu hiệu)[:\s"]+',
            '',
            clean,
            flags=re.IGNORECASE
        ).strip('"\';. ')

        clean = re.sub(
            r'^(?:tôi xin bổ sung thông tin lâm sàng|bổ sung thông tin lâm sàng|thông tin lâm sàng)[:\s"]+',
            '',
            clean,
            flags=re.IGNORECASE
        ).strip('"\';. ')

        parts = clean.split('|')
        user_answers = []
        for p in parts:
            p = p.strip('"\';. ')
            if not p:
                continue
            if ':' in p:
                _, a_part = p.rsplit(':', 1)
                a_part = a_part.strip('"\';. ')
                if a_part:
                    user_answers.append(a_part)
            elif '?' in p:
                _, a_part = p.rsplit('?', 1)
                a_part = a_part.strip('"\';. ')
                if a_part:
                    user_answers.append(a_part)
            else:
                user_answers.append(p)

        return " . ".join(user_answers) if user_answers else clean

    async def _extract_cumulative_session_context(
        self,
        chat_history: Optional[List[Dict[str, Any]]],
        current_user_message: str
    ) -> Dict[str, Any]:
        """
        Trích xuất và tích lũy toàn bộ bối cảnh lâm sàng qua TẤT CẢ các lượt hội thoại:
        1. Duyệt tất cả các tin nhắn người dùng (chính thức & câu trả lời làm rõ).
        2. Tích lũy danh sách triệu chứng khẳng định (cumulative_symptoms).
        3. Tích lũy danh sách triệu chứng loại trừ (cumulative_negated).
        4. Tự động loại bỏ mâu thuẫn (nếu lượt sau khẳng định 'không sốt' thì gạch bỏ 'sốt').
        5. Trích xuất danh sách các câu hỏi trợ lý đã từng hỏi (already_asked_questions) để tránh trùng lặp.
        6. Đếm số lượt trả lời làm rõ (clarification_turns_count).
        """
        cumulative_symptoms: Dict[str, Dict[str, Any]] = {}
        cumulative_negated: Dict[str, Dict[str, Any]] = {}
        clinical_utterances: List[str] = []
        already_asked_texts: List[str] = []
        clarification_turns_count = 0

        # Quét các câu hỏi trợ lý đã từng hỏi trong lịch sử
        if chat_history:
            for item in chat_history:
                if item.get("sender") == "assistant":
                    content = item.get("content") or item.get("text") or ""
                    for line in content.split("\n"):
                        line_s = line.strip()
                        if (line_s.startswith("**") or line_s.startswith("- **")) and "?" in line_s:
                            clean_q = re.sub(r'^(?:[\-\*]+\s*)?(?:\d+\.|\-)?\s*', '', line_s).split("?")[0] + "?"
                            clean_q = clean_q.strip("* \t-")
                            if len(clean_q) > 8:
                                already_asked_texts.append(clean_q)

        # Gom tất cả các lượt người dùng
        user_turns: List[str] = []
        if chat_history:
            for item in chat_history:
                if item.get("sender") == "user":
                    c = (item.get("content") or item.get("text") or "").strip()
                    if c:
                        user_turns.append(c)
        if current_user_message.strip():
            user_turns.append(current_user_message.strip())

        for turn in user_turns:
            is_clarif = bool(
                re.search(r'^(?:trả lời câu hỏi làm rõ|trả lời|chọn|đáp án|tôi xin bổ sung|bổ sung thông tin|tôi có các dấu hiệu)[:\s"]+', turn, flags=re.IGNORECASE)
                or "câu hỏi làm rõ" in turn.lower()
            )
            if is_clarif:
                clarification_turns_count += 1
                clean_t = self._parse_clarification_response(turn)
            else:
                clean_t = turn

            if self._handle_general_medical_intent(clean_t):
                continue

            clinical_utterances.append(clean_t)
            t = await self._analyze_triage_with_cache(text=clean_t)

            # Khẳng định
            syms = t.get("extracted_entities", {}).get("symptoms", [])
            for s in syms:
                st = s.get("standard_term")
                if st:
                    cumulative_symptoms[st] = s

            # Phủ định
            negs = t.get("extracted_entities", {}).get("negated_symptoms", []) or t.get("negated_symptoms", [])
            for n in negs:
                nt = n.get("standard_term")
                if nt:
                    cumulative_negated[nt] = n

        # Loại trừ các triệu chứng khẳng định nếu đã bị phủ định ở các lượt làm rõ sau đó
        for nt in list(cumulative_negated.keys()):
            if nt in cumulative_symptoms:
                del cumulative_symptoms[nt]

        combined_text = " . ".join(clinical_utterances) if clinical_utterances else current_user_message

        return {
            "cumulative_symptoms": list(cumulative_symptoms.values()),
            "cumulative_negated": list(cumulative_negated.values()),
            "combined_text": combined_text,
            "already_asked_texts": already_asked_texts,
            "clarification_turns_count": clarification_turns_count
        }

    def _classify_conversational_intent(
        self,
        user_message: str,
        is_emergency: bool,
        top_preds: List[Dict[str, Any]],
        symptoms: List[Dict[str, Any]],
        clinical_stage: str,
        dst_state: Any
    ) -> Optional[str]:
        """
        Phân loại ý định hội thoại nâng cao (Tầng 4: Conversational Intent Handler):
        1. INQUIRY_EMERGENCY_NEED: Hỏi có cần đi viện / cấp cứu / có nguy hiểm không.
        2. INQUIRY_MEDICATION: Hỏi về thuốc điều trị, mua thuốc gì.
        3. INQUIRY_SYMPTOM_MEANING: Hỏi nguyên nhân, thế là bị bệnh gì.
        4. INQUIRY_NUTRITION: Chế độ ăn uống, kiêng gì, nên ăn gì.
        5. INQUIRY_PROGNOSIS: Tiên lượng bệnh, bao lâu khỏi, có tự khỏi không.
        """
        msg_lower = user_message.lower().strip()
        top_disease = top_preds[0].get("disease_name_vi", "tình trạng sức khỏe hiện tại") if top_preds else "tình trạng của bạn"
        symptom_names = [s.get("standard_term", "") for s in symptoms if isinstance(s, dict)]
        sym_str = ", ".join(symptom_names[:3]) if symptom_names else "các dấu hiệu bạn mô tả"

        # 1. INQUIRY_EMERGENCY_NEED
        if re.search(r'(?:có cần.*(?:đi viện|vào viện|cấp cứu|đi khám)|có phải.*(?:đi viện|vào viện|cấp cứu|đi khám)|khi nào.*(?:cần|phải).*(?:đi viện|vào viện|cấp cứu)|có nguy hiểm không|nguy hiểm lắm không|có sao không)', msg_lower):
            if is_emergency:
                return (
                    f"⚠️ **ĐÁNH GIÁ MỨC ĐỘ KHẨN CẤP: BẮT BUỘC ĐI VIỆN NGAY!**\n\n"
                    f"Dựa trên các dấu hiệu lâm sàng ({sym_str}), tình trạng của bạn đang ở mức **Báo động đỏ khẩn cấp** có nguy cơ đe dọa đường thở hoặc tuần hoàn. "
                    f"Bạn **CẦN ĐẾN KHOA CẤP CỨU GẦN NHẤT HOẶC GỌI 115 NGAY**, không nên chần chừ hay tự theo dõi tại nhà!"
                )
            else:
                return (
                    f"🩺 **ĐÁNH GIÁ MỨC ĐỘ NGUY HIỂM & CHỈ ĐỊNH NHẬP VIỆN:**\n\n"
                    f"Hiện tại, hệ thống chưa phát hiện dấu hiệu đe dọa tính mạng tức thì từ các triệu chứng ({sym_str}). Tuy nhiên, bạn **CẦN ĐI VIỆN HOẶC GỌI CẤP CỨU NGAY** nếu xuất hiện bất kỳ 'dấu hiệu cờ đỏ' (Red Flags) sau:\n"
                    f"- Cảm giác khó thở, thở rít, tức nghẹn cổ họng hoặc tím tái môi/đầu chi.\n"
                    f"- Đau thắt ngực dữ dội, vã mồ hôi lạnh, choáng váng hoặc ngất xỉu.\n"
                    f"- Sốt cao liên tục trên 39°C không hạ sau khi dùng thuốc hạ sốt, li bì hoặc co giật.\n"
                    f"- Nôn liên tục không uống được nước hoặc xuất huyết dưới da/chảy máu cam/chảy máu chân răng.\n\n"
                    f"Nếu không có các dấu hiệu nguy cấp trên, bạn nên đến cơ sở y tế chuyên khoa để được bác sĩ thăm khám trực tiếp trong vòng 24 - 48 giờ."
                )

        # 2. INQUIRY_MEDICATION
        if re.search(r'(?:uống thuốc gì|dùng thuốc gì|mua thuốc gì|thuốc gì.*đỡ|thuốc gì.*hết|có thuốc gì|uống gì cho đỡ|uống gì để hạ)', msg_lower):
            return (
                f"💊 **HƯỚNG DẪN XỬ TRÍ & DÙNG THUỐC AN TOÀN:**\n\n"
                f"Đối với nghi vấn liên quan đến **{top_disease}** ({sym_str}):\n"
                f"- **Nguyên tắc an toàn:** Tuyệt đối không tự ý mua thuốc kháng sinh hoặc thuốc chứa Corticoid (như Medrol, Dexamethasone...) mà chưa có chỉ định của bác sĩ.\n"
                f"- **Xử trí ban đầu thông thường:**\n"
                f"  + Nếu sốt trên 38.5°C hoặc đau nhức nhiều: Có thể dùng Paracetamol (10-15 mg/kg mỗi lần, cách nhau 4-6 giờ; người lớn 500mg/lần, không quá 3g/ngày).\n"
                f"  + Nếu ngứa, dị ứng da: Uống nhiều nước, có thể dùng dung dịch nước muối sinh lý làm sạch, tránh cào gãi làm xước da nhiễm trùng.\n"
                f"  + Nếu cảm cúm/viêm mũi họng: Súc họng nước muối sinh lý ấm, bổ sung vitamin C.\n"
                f"- **Lưu ý quan trọng:** Hãy đến gặp bác sĩ hoặc dược sĩ chuyên môn để được kê đơn thuốc đúng liều lượng và phù hợp với cơ địa của bạn."
            )

        # 3. INQUIRY_SYMPTOM_MEANING
        if re.search(r'(?:thế là bị.*(?:gì|sao|bệnh gì)|bị bệnh gì|nghĩa là gì|dấu hiệu của bệnh gì|tại sao lại bị|là bệnh gì vậy)', msg_lower):
            prob_percent = int(top_preds[0].get("probability", 0.0) * 100) if top_preds else 50
            return (
                f"🔍 **PHÂN TÍCH NGUYÊN NHÂN & TRIỆU CHỨNG LÂM SÀNG:**\n\n"
                f"Dựa trên các dấu hiệu ({sym_str}), hệ thống nhận định khả năng cao nhất là **{top_disease}** (Độ tin cậy ước tính: **{prob_percent}%**).\n\n"
                f"**Cơ chế bệnh sinh thường gặp:**\n"
                f"- Các triệu chứng của bạn phản ánh phản ứng viêm hoặc kích ứng tại cơ quan đích.\n"
                f"- Phân tầng lâm sàng hiện tại: **{clinical_stage}**.\n"
                f"- Để chẩn đoán xác định, bác sĩ có thể cần thực hiện thêm các xét nghiệm cận lâm sàng hoặc nội soi chuyên sâu."
            )

        # 4. INQUIRY_NUTRITION
        if re.search(r'(?:ăn gì|kiêng gì|ăn uống.*thế nào|chế độ ăn|thực đơn|uống nước gì|có được ăn.*không)', msg_lower):
            allergen = dst_state.clinical_slots.get("allergen_trigger") if (hasattr(dst_state, "clinical_slots") and isinstance(dst_state.clinical_slots, dict)) else ""
            allergy_advice = f"\n- **Kiêng tuyệt đối:** Không ăn lại món nghi ngờ dị ứng ({allergen or 'hải sản, tôm, cua, đồ tanh, đậu phộng'}) và hạn chế đồ uống có cồn/bia rượu." if ("dị ứng" in top_disease.lower() or "mày đay" in top_disease.lower() or allergen) else ""
            return (
                f"🥗 **CHẾ ĐỘ DINH DƯỠNG & CHĂM SÓC:**\n\n"
                f"Đối với tình trạng **{top_disease}** hiện tại:\n"
                f"- **Nên bổ sung:**\n"
                f"  + Uống đủ nước (2 - 2.5 lít/ngày), ưu tiên nước lọc, nước oresol (nếu sốt/tiêu chảy), nước ép trái cây giàu vitamin C.\n"
                f"  + Ăn thức ăn mềm, dễ tiêu hóa, chia nhỏ thành nhiều bữa trong ngày (cháo, súp, canh).\n"
                f"- **Cần kiêng cữ:**{allergy_advice}\n"
                f"  + Hạn chế đồ ăn cay nóng, dầu mỡ nhiều, nước có ga và các chất kích thích."
            )

        # 5. INQUIRY_PROGNOSIS
        if re.search(r'(?:bao lâu.*(?:khỏi|hết|đỡ)|có tự khỏi không|có lâu không|tiên lượng|khi nào thì khỏi)', msg_lower):
            return (
                f"⏱️ **TIÊN LƯỢNG & DIỄN BIẾN HỒI PHỤC:**\n\n"
                f"- Đối với tình trạng **{top_disease}**:\n"
                f"  + Nếu là phản ứng kích ứng hoặc viêm cấp tính nhẹ, triệu chứng thường cải thiện sau **2 - 5 ngày** khi được chăm sóc đúng cách và loại bỏ nguyên nhân gây kích thích.\n"
                f"  + Nếu sau **3 ngày** triệu chứng không có dấu hiệu thuyên giảm hoặc có xu hướng trầm trọng hơn, bạn cần tái khám bác sĩ ngay để điều chỉnh phác đồ."
            )

        return None

    async def process_patient_message(
        self,
        session_id: str,
        user_message: str,
        chat_history: Optional[List[Dict[str, Any]]] = None,
        audio_bytes: Optional[bytes] = None,
        audio_filename: str = "",
        document_bytes: Optional[bytes] = None,
        document_filename: str = "",
        gemini_api_key: Optional[str] = None,
        cohere_api_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Xử lý tin nhắn của bệnh nhân kèm ngữ cảnh đa lượt (Multi-turn Cumulative Context):
        1. Nhận diện các câu hỏi thường gặp (Kháng sinh, khả năng hệ thống, hạ sốt) để phản hồi Fast-Path chuẩn mực.
        2. Tích lũy toàn bộ triệu chứng từ TẤT CẢ các lượt trước và duy trì Sổ theo dõi Đa bệnh lý.
        3. Phân tầng theo 3 cấp độ: Sàng lọc ban đầu -> Chẩn đoán giả định (bắt buộc hỏi phân biệt) -> Kết luận xác định.
        4. RAG retrieval kiến thức y khoa chuyên sâu từ ICD-10 & Phác đồ Bộ Y Tế.
        5. Dùng Unified Clinical Reasoning (Local LLM / Gemini / Rule-based) để suy luận lâm sàng.
        """
        pipeline_start = time.time()
        # 1. Kiểm tra Fast-Path General Medical Intent (Kháng sinh, Hỏi chức năng, Cách hạ sốt...)
        general_intent_answer = self._handle_general_medical_intent(user_message)
        if general_intent_answer and not (audio_bytes or document_bytes):
            fast_lat_ms = max(int((time.time() - pipeline_start) * 1000), 4)
            fast_breakdown = {"intent_filter_ms": fast_lat_ms, "total_ms": fast_lat_ms}
            return {
                "message_id": str(uuid.uuid4()),
                "session_id": session_id,
                "sender": "assistant",
                "text_content": general_intent_answer,
                "created_at": datetime.utcnow().isoformat(),
                "latency_ms": fast_lat_ms,
                "pipeline_breakdown": fast_breakdown,
                "telemetry": {
                    "is_emergency": False,
                    "red_flag": {},
                    "symptoms": [],
                    "negated_symptoms": [],
                    "lab_indicators": {},
                    "top_predictions": [],
                    "clarification": {"needs_clarification": False, "clinical_stage": "intent_handled", "questions": []},
                    "rag_citations": [],
                    "latency_ms": fast_lat_ms,
                    "pipeline_breakdown": fast_breakdown
                }
            }

        is_summary_query = bool(re.search(
            r'(?:tôi đang bị những gì|tôi bị những bệnh gì|bị những gì|tổng hợp|tóm tắt|có những bệnh gì|các bệnh tôi bị|còn.*nữa mà|còn bệnh|tất cả các bệnh)',
            user_message,
            flags=re.IGNORECASE
        ))

        # Trích xuất toàn bộ các vấn đề bệnh lý đã phát hiện trong cả phiên khám
        session_problems = self._extract_all_session_problems(chat_history, user_message)

        # 2. TÍCH LŨY TOÀN BỘ NGỮ CẢNH ĐA LƯỢT VÀ BỆNH ÁN ĐỘNG (DST)
        t_ner_start = time.time()
        dst_state = await dialogue_state_service.get_state(session_id)
        
        session_context = await self._extract_cumulative_session_context(chat_history, user_message)
        cumulative_symptoms = session_context["cumulative_symptoms"]
        cumulative_negated = session_context["cumulative_negated"]
        active_text = session_context["combined_text"]
        already_asked_texts = session_context["already_asked_texts"]
        clarification_turns_count = session_context["clarification_turns_count"]

        # Phân tích nguy cơ bệnh học với bối cảnh lũy kế toàn diện
        triage_data = await self._analyze_triage_with_cache(
            text=active_text,
            audio_bytes=audio_bytes,
            audio_filename=audio_filename,
            document_bytes=document_bytes,
            document_filename=document_filename
        )
        ner_ms = max(int((time.time() - t_ner_start) * 1000), 1)

        # Hợp nhất danh sách triệu chứng khẳng định
        current_extracted = triage_data.get("extracted_entities", {}).get("symptoms", [])
        
        # Cập nhật slot filling vào DST
        dst_state = dialogue_state_service.fill_slots_from_utterance(
            state=dst_state,
            user_message=user_message,
            extracted_symptoms=current_extracted,
            negated_symptoms=cumulative_negated
        )

        seen_terms = {s.get("standard_term"): s for s in cumulative_symptoms if s.get("standard_term")}
        for s in current_extracted:
            st = s.get("standard_term")
            if st and st not in seen_terms:
                seen_terms[st] = s
        for st, s in dst_state.confirmed_symptoms.items():
            if st not in seen_terms:
                seen_terms[st] = s
        symptoms = list(seen_terms.values())

        # Loại bỏ các triệu chứng đã bị phủ định
        neg_terms = {s.get("standard_term") for s in cumulative_negated if s.get("standard_term")}
        symptoms = [s for s in symptoms if s.get("standard_term") not in neg_terms]

        is_emergency = triage_data.get("is_emergency", False)
        lab_indicators = triage_data.get("lab_indicators", {})
        top_preds = triage_data.get("triage_results", [])
        top_prob = top_preds[0].get("probability", 0.0) if top_preds else 0.0

        # Tầng 1: Tăng độ tin cậy (Confidence Boost) nếu slot dị nguyên đã được người bệnh xác nhận
        allergen_slot = dst_state.clinical_slots.get("allergen_trigger", "")
        if allergen_slot and allergen_slot not in ["không rõ dị nguyên tiếp xúc"]:
            if top_preds:
                primary_code = str(top_preds[0].get("icd_code", ""))
                if any(primary_code.startswith(pfx) for pfx in ["L20", "L50", "T78", "Z91"]):
                    top_prob = min(0.95, round(top_prob + 0.15, 3))
                    top_preds[0]["probability"] = top_prob

        # 3. XÁC ĐỊNH PHÂN TẦNG LÂM SÀNG (3-Tier Clinical Confidence Stage)
        clinical_stage = clarification_engine.determine_clinical_stage(
            top_probability=top_prob,
            symptom_count=len(symptoms),
            clarification_turns_count=clarification_turns_count,
            is_emergency=is_emergency
        )

        # Kiểm tra nếu người dùng đang hỏi trực tiếp về điều trị / cấp cứu / giải thích triệu chứng
        is_asking_followup = bool(re.search(
            r'(?:uống thuốc gì|dùng thuốc gì|thuốc gì|hạ sốt.*thế nào|uống gì|ăn uống thế nào|ăn gì|chế độ ăn|cách hạ sốt|cấp cứu|nhập viện|vào viện|khi nào.*(?:viện|cấp cứu)|dấu hiệu nào.*(?:viện|cấp cứu)|bắt buộc phải.*(?:viện|cấp cứu)|nguy hiểm|thế là.*(?:gì|dấu hiệu gì)|dấu hiệu gì|nghĩa là gì)',
            user_message,
            re.IGNORECASE
        ))

        # Đảm bảo tiến trình lâm sàng tăng tiến có kiểm soát:
        # Chỉ chuyển sang 'definitive_conclusion' khi ĐÃ QUA ÍT NHẤT 1 LƯỢT LÀM RÕ (clarification_turns_count >= 1)
        # HOẶC số triệu chứng nhiều (>= 4) và xác suất rất cao (>= 0.85).
        # Ở lượt đầu tiên (clarification_turns_count == 0), duy trì 'provisional_assumption' hoặc 'initial_screening'
        # để luôn đặt câu hỏi làm rõ phân biệt cho bệnh nhân trả lời.
        if clarification_turns_count >= 1 and len(symptoms) >= 3 and top_prob >= 0.70:
            clinical_stage = "definitive_conclusion"
        elif len(symptoms) >= 4 and top_prob >= 0.85 and not is_asking_followup:
            clinical_stage = "definitive_conclusion"
        else:
            if clinical_stage == "definitive_conclusion" and clarification_turns_count == 0:
                clinical_stage = "provisional_assumption"
            elif len(symptoms) >= 2 or clarification_turns_count >= 1 or is_asking_followup:
                if clinical_stage == "initial_screening":
                    clinical_stage = "provisional_assumption"

        clarification = {
            "needs_clarification": (clinical_stage != "definitive_conclusion" and not is_asking_followup),
            "clinical_stage": clinical_stage,
            "confidence_score": round(top_prob, 3),
            "questions": []
        }

        # Sinh câu hỏi làm rõ phân biệt nếu chưa đạt kết luận sơ bộ xác định và không phải đang hỏi xử trí
        if clinical_stage != "definitive_conclusion" and not is_asking_followup:
            top_codes = [p.get("icd_code") for p in top_preds if p.get("icd_code")]
            generated_qs = clarification_engine.generate_context_aware_questions(
                user_text=active_text,
                detected_symptoms=[s.get("standard_term", "") if isinstance(s, dict) else str(s) for s in symptoms],
                top_disease_codes=top_codes,
                already_asked_texts=already_asked_texts
            )
            # Lọc bỏ các câu hỏi mà topic tương ứng đã có trong bệnh án động DST
            filtered_qs = []
            for q in generated_qs:
                q_top = resolve_question_topic(q)
                if f"answered_{q_top}" in dst_state.clinical_slots:
                    continue
                if q_top == "allergen_trigger" and dst_state.clinical_slots.get("allergen_trigger"):
                    continue
                if q_top == "fever_pattern" and dst_state.clinical_slots.get("fever_pattern"):
                    continue
                filtered_qs.append(q)
            clarification["questions"] = filtered_qs

        if clarification.get("questions"):
            q0 = dict(clarification.get("questions")[0])
            q0["topic"] = resolve_question_topic(q0)
            dst_state.pending_question = q0
        dst_state.is_emergency = is_emergency
        dst_state.active_hypotheses = top_preds
        await dialogue_state_service.save_state(dst_state)

        # 4. RAG Knowledge Retrieval (Redis Cached)
        t_rag_start = time.time()
        primary_code = top_preds[0].get("icd_code") if top_preds else None
        top_name = top_preds[0].get("disease_name_vi", "") if top_preds else ""
        sym_text = " ".join([s.get("standard_term", "") for s in symptoms[:3] if isinstance(s, dict) and s.get("standard_term")])
        
        # Tạo truy vấn RAG tập trung vào mặt bệnh và triệu chứng cốt lõi, tránh bị nhiễu bởi các option làm rõ
        if top_name and sym_text:
            rag_query = f"{top_name} {sym_text}"
        elif top_name:
            rag_query = f"{top_name} {user_message}"
        elif sym_text:
            rag_query = f"{sym_text} {user_message}"
        else:
            rag_query = user_message

        raw_rag_docs = await rag_service.a_retrieve_medical_knowledge(rag_query, disease_code=primary_code)

        # Lọc bỏ phác đồ lạc đề giải phẫu (ví dụ: đang khám Mắt tuyệt đối không đưa phụ khoa/âm đạo/tiết niệu)
        has_eye = any("mắt" in s.get("standard_term", "").lower() for s in symptoms if isinstance(s, dict)) or (primary_code and primary_code.startswith("H")) or any(k in user_message.lower() for k in ["mắt", "nhìn mờ", "thị lực", "mỏi mắt", "cộm mắt"])
        rag_docs = []
        for doc in raw_rag_docs:
            dept = doc.get("department", "").lower()
            title = doc.get("title", "").lower()
            content = doc.get("content", "").lower()
            
            # Nếu đang có triệu chứng mắt, loại trừ tài liệu sinh dục, phụ khoa, tiết niệu
            if has_eye:
                if any(x in dept or x in title or x in content for x in ["âm đạo", "sinh dục", "phụ khoa", "tiền liệt tuyến", "vỡ lách", "kinh nguyệt"]):
                    continue
            rag_docs.append(doc)
            
        if not rag_docs:
            rag_docs = raw_rag_docs[:2]
        rag_ms = max(int((time.time() - t_rag_start) * 1000), 1)

        # 5. Suy luận lâm sàng đa tầng (Local LLM -> Cloud Gemini -> Deterministic Template)
        t_llm_start = time.time()
        clinical_advice = await clinical_reasoning_service.generate_clinical_advice(
            patient_message=user_message,
            predicted_diseases=top_preds,
            symptoms=symptoms,
            lab_indicators=lab_indicators,
            rag_citations=rag_docs,
            chat_history=chat_history,
            is_emergency=is_emergency,
            gemini_api_key=gemini_api_key,
            cohere_api_key=cohere_api_key,
            negated_symptoms=cumulative_negated,
            clarifying_questions=clarification.get("questions"),
            clinical_stage=clinical_stage
        )
        llm_ms = max(int((time.time() - t_llm_start) * 1000), 1)
        ai_response_text = clinical_advice.get("text", "")

        # Tầng 4: Đánh giá ý định người bệnh (Intent Classification)
        intent_response = self._classify_conversational_intent(
            user_message=user_message,
            is_emergency=is_emergency,
            top_preds=top_preds,
            symptoms=symptoms,
            clinical_stage=clinical_stage,
            dst_state=dst_state
        )

        response_text = ""

        if is_emergency:
            rf = triage_data.get("red_flag_details", {}).get("triggered_flags", [{}])[0]
            action = rf.get("action_vi", "Cần gọi cấp cứu 115 ngay!")
            response_text = f"🚨 **BÁO ĐỘNG ĐỎ CẤP CỨU Y TẾ** 🚨\n\n{action}\n\n**Khuyến cáo khẩn cấp:**\n- Giữ người bệnh ở tư thế an toàn, không tự ý di chuyển hoặc vận động mạnh.\n- Chuẩn bị sẵn sổ khám bệnh và các đơn thuốc đang dùng.\n- Hệ thống đã kích hoạt cửa sổ cấp cứu 115 trên màn hình của bạn."
            if intent_response:
                response_text += f"\n\n{intent_response}"
        elif ai_response_text:
            response_text = ai_response_text
        elif intent_response:
            response_text = intent_response
        elif is_summary_query and len(session_problems) > 1:
            # Phản hồi tổng kết đa bệnh lý hoàn chỉnh
            response_text = f"Chào bạn, tôi đã ghi nhớ và tổng hợp toàn bộ các vấn đề bạn đã chia sẻ từ đầu buổi khám. Hiện tại bạn đang có **{len(session_problems)} vấn đề sức khỏe độc lập** cần lưu ý:\n\n"
            all_rag_docs = []
            for idx, p in enumerate(session_problems, 1):
                sym_str = ", ".join(p["symptoms"])
                response_text += f"🩺 **Vấn đề {idx}: {p['disease_name_vi']} (Mã ICD-10: `{p['icd_code']}`)**\n"
                response_text += f"- **Triệu chứng ghi nhận:** {sym_str}\n"
                response_text += f"- **Độ tin cậy ước tính:** **{p['probability_percentage']}**\n"
                response_text += f"- **Lời khuyên xử trí:** {p['recommendation']}\n\n"
                docs = await rag_service.a_retrieve_medical_knowledge(p["disease_name_vi"], disease_code=p["icd_code"])
                if docs:
                    all_rag_docs.extend(docs[:1])

            if all_rag_docs:
                response_text += "📚 **Trích dẫn Tri Thức Y Khoa & Phác Đồ Bộ Y Tế (RAG Knowledge):**\n"
                for doc in all_rag_docs:
                    response_text += f"- **{doc.get('title')}**\n"
                    response_text += f"  _{doc.get('content')}_\n"
                    response_text += f"  *(Nguồn trích dẫn: {doc.get('source')})*\n"
                response_text += "\n"

            response_text += "💡 **Lời khuyên phối hợp:** Hai tình trạng trên thuộc hai chuyên khoa khác nhau. Bạn nên đi khám chuyên khoa Nam khoa/Tiết niệu trước để làm xét nghiệm dịch niệu đạo, đồng thời khám Da liễu để được kê đơn thuốc bôi/uống an toàn."
            rag_docs = all_rag_docs
        else:
            # Fallback Clinical Reasoning cho từng lượt thông thường
            is_lab_upload_message = bool(re.search(r'(?:phiếu xét nghiệm|kết quả xét nghiệm|chỉ số sinh hóa|tài liệu xét nghiệm|kết quả máu|xét nghiệm máu)', user_message, flags=re.IGNORECASE))
            
            if not has_clinical_evidence:
                if is_lab_upload_message:
                    response_text = (
                        "Chào bạn! Tôi đã tiếp nhận tài liệu / hình ảnh phiếu xét nghiệm bạn vừa tải lên.\n\n"
                        "Để tôi có thể đối chiếu chính xác nhất kết quả cận lâm sàng này với thể trạng của bạn, vui lòng chia sẻ thêm:\n"
                        "- Bạn đang cảm thấy mệt mỏi, khó chịu hoặc có triệu chứng bất thường nào không (ví dụ: sốt, đau bụng, sụt cân)?\n"
                        "- Hoặc bạn có thể gõ nhanh một vài chỉ số in trên phiếu (như *WBC*, *Tiểu cầu*, *Đường huyết*, *Men gan*) để tôi đánh giá tức thì!"
                    )
                else:
                    response_text = (
                        "Chào bạn! Tôi chưa nhận thấy thông tin cụ thể về triệu chứng bệnh lý của bạn.\n\n"
                        "Để tôi có thể tư vấn và đánh giá chính xác nhất, bạn vui lòng mô tả chi tiết:\n"
                        "- Bạn đang cảm thấy khó chịu hoặc đau ở vị trí nào?\n"
                        "- Triệu chứng xuất hiện từ khi nào và có kèm theo sốt hay biểu hiện bất thường nào khác không?\n\n"
                        "Hoặc bạn có thể bấm chọn nhanh các gợi ý trắc nghiệm phía dưới."
                    )
            else:
                sym_names = [s.get("standard_term", "") for s in symptoms]
                sym_str = ", ".join(sym_names) if sym_names else "các biểu hiện bạn đã chia sẻ"
                
                if is_clarification_turn:
                    response_text = f"Chào bạn, tôi đã ghi nhận thêm thông tin **'{clean_user_message}'** cho tình trạng **{sym_str}**.\n\n"
                else:
                    response_text = f"Chào bạn, tôi đã tiếp nhận và ghi nhớ toàn bộ thông tin về triệu chứng **{sym_str}**.\n\n"

                # Phân tích kết quả xét nghiệm nếu có
                if lab_indicators:
                    response_text += "📊 **Đánh giá chỉ số xét nghiệm (OCR):**\n"
                    for test, info in lab_indicators.items():
                        val = info.get("value")
                        unit = info.get("unit", "")
                        status = info.get("status", "NORMAL")
                        msg = info.get("message", "")
                        response_text += f"- **{test}**: `{val} {unit}` ({msg})\n"
                    response_text += "\n"

                # Kết luận chẩn đoán phân biệt
                if top_preds:
                    primary = top_preds[0]
                    response_text += f"🔍 **Đánh giá nhóm bệnh nguy cơ cao nhất:** **{primary.get('disease_name_vi')}** (Mã ICD-10: `{primary.get('icd_code')}`) với độ tin cậy ước tính **{primary.get('probability_percentage')}**.\n"
                    response_text += f"💡 **Lời khuyên xử trí:** {primary.get('recommendation')}\n\n"

                # Trích xuất tri thức y khoa từ RAG
                if rag_docs:
                    response_text += "📚 **Trích dẫn Tri Thức Y Khoa & Phác Đồ Bộ Y Tế (RAG Knowledge):**\n"
                    for doc in rag_docs:
                        response_text += f"- **{doc.get('title')}**\n"
                        response_text += f"  _{doc.get('content')}_\n"
                        response_text += f"  *(Nguồn trích dẫn: {doc.get('source')})*\n"
                    response_text += "\n"

                # Nếu cần làm rõ thêm
                if clarification.get("needs_clarification"):
                    response_text += f"❓ **Để chẩn đoán chính xác hơn:** Vui lòng trả lời nhanh các câu hỏi trắc nghiệm ở bảng bên dưới hoặc phản hồi thêm cho tôi nhé."

        total_ms = max(int((time.time() - pipeline_start) * 1000), 12)
        pipeline_breakdown = {
            "ner_ms": ner_ms,
            "rag_ms": rag_ms,
            "llm_ms": llm_ms,
            "total_ms": total_ms
        }

        # Telemetry payload cho Side Dashboard & Kiểm toán
        alt_text = clinical_advice.get("alternative_text")
        alt_provider = clinical_advice.get("alternative_provider")
        alternative_answers = []
        if alt_text:
            alternative_answers = [{"text": alt_text, "provider": alt_provider or "unknown"}]

        telemetry = {
            "is_emergency": is_emergency,
            "red_flag": triage_data.get("red_flag_details", {}),
            "symptoms": symptoms,
            "negated_symptoms": cumulative_negated,
            "lab_indicators": lab_indicators,
            "top_predictions": top_preds,
            "clarification": clarification,
            "rag_citations": rag_docs,
            "latency_ms": total_ms,
            "pipeline_breakdown": pipeline_breakdown,
            "provider": clinical_advice.get("provider", "unknown"),
        }

        return {
            "message_id": str(uuid.uuid4()),
            "session_id": session_id,
            "sender": "assistant",
            "text_content": response_text,
            "created_at": datetime.utcnow().isoformat(),
            "latency_ms": total_ms,
            "pipeline_breakdown": pipeline_breakdown,
            "telemetry": telemetry,
            "alternative_answers": alternative_answers,
        }

    def generate_medical_record(
        self,
        session_id: str,
        chat_history: List[Dict[str, Any]],
        telemetry: Optional[Dict[str, Any]] = None,
        gemini_api_key: Optional[str] = None
    ) -> str:
        """
        Tổng hợp toàn bộ buổi khám thành một BỆNH ÁN HOÀN CHỈNH ĐA BỆNH LÝ.
        """
        telem = telemetry or {}
        session_problems = self._extract_all_session_problems(chat_history, "")
        all_diseases = session_problems if session_problems else telem.get("top_predictions", [])
        
        all_symptoms = []
        seen = set()
        for p in session_problems:
            for s in p.get("symptoms", []):
                if s not in seen:
                    all_symptoms.append({"standard_term": s})
                    seen.add(s)
        if not all_symptoms:
            all_symptoms = telem.get("symptoms", [])

        return gemini_service.generate_comprehensive_medical_record(
            session_id=session_id,
            chat_history=chat_history,
            predicted_diseases=all_diseases,
            symptoms=all_symptoms,
            lab_indicators=telem.get("lab_indicators", {}),
            rag_citations=telem.get("rag_citations", []),
            api_key=gemini_api_key
        )

    def process_patient_message_sync(self, *args, **kwargs) -> Dict[str, Any]:
        """Wrapper đồng bộ phục vụ kiểm thử và gọi từ luồng đồng bộ."""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    return pool.submit(asyncio.run, self.process_patient_message(*args, **kwargs)).result()
            return loop.run_until_complete(self.process_patient_message(*args, **kwargs))
        except RuntimeError:
            return asyncio.run(self.process_patient_message(*args, **kwargs))

chat_service = ChatService()
