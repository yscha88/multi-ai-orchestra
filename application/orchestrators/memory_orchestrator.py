# ===== application/orchestrators/memory_orchestrator.py =====
"""
기억 중심 오케스트레이터
"""

import time
from typing import List, Dict, Any
from .base_orchestrator import BaseOrchestratorImpl
from ports.memory_ports import MemoryRepository, SearchService
from core.shared.models import (
    OrchestratorResponse, SessionContext, OrchestratorType, ChatMessage, MemoryType
)


class MemoryOrchestrator(BaseOrchestratorImpl):
    """기억 중심 오케스트레이터"""

    def __init__(self, ai_providers: Dict[str, Any], memory_repository: MemoryRepository,
                 search_service: SearchService, config: Dict[str, Any]):
        super().__init__(OrchestratorType.MEMORY, config)
        self.ai_providers = ai_providers
        self.memory_repository = memory_repository
        self.search_service = search_service

    def process_request(self, user_input: str, context: SessionContext) -> OrchestratorResponse:
        """요청 처리 - 기억 중심"""
        start_time = time.time()

        try:
            # 1. 컨텍스트 검증
            if not self._validate_context(context):
                return self._prepare_error_response("잘못된 세션 컨텍스트", context)

            # 2. 관련 기억 검색
            relevant_memories = self._search_relevant_memories(user_input, context)

            # 3. 프로바이더 선택
            provider = self._select_provider()
            if not provider:
                return self._prepare_error_response("사용 가능한 AI가 없습니다", context)

            # 4. 기억을 활용한 메시지 구성
            messages = self._build_memory_enhanced_messages(user_input, context, relevant_memories)

            # 5. AI 호출
            chat_response = provider.chat(messages)

            # 6. 새로운 기억 저장
            self._save_new_memory(user_input, chat_response.content, context)

            # 7. 응답 생성
            processing_time = time.time() - start_time

            return OrchestratorResponse(
                content=chat_response.content,
                orchestrator_type=self.orchestrator_type,
                processing_time=processing_time,
                token_usage=chat_response.token_usage,
                used_providers=[provider.get_model_info().provider],
                metadata={
                    "mode": "memory_enhanced",
                    "relevant_memories_count": len(relevant_memories),
                    "memory_types_used": list(set(m.memory_type.value for m in relevant_memories)),
                    "new_memory_saved": True
                }
            )

        except Exception as e:
            processing_time = time.time() - start_time
            print(f"⚠️ MemoryOrchestrator 오류: {e}")
            return self._prepare_error_response(str(e), context)

    def get_capabilities(self) -> List[str]:
        """지원 기능 목록"""
        return [
            "memory_search", "context_continuity", "personal_adaptation",
            "conversation_history", "pattern_recognition"
        ]

    def _search_relevant_memories(self, user_input: str, context: SessionContext) -> List[Any]:
        """관련 기억 검색"""
        try:
            # 1. 키워드 기반 검색
            search_result = self.search_service.search_memories(
                query=user_input,
                memory_types=[MemoryType.CONVERSATION, MemoryType.NOTE, MemoryType.PATTERN],
                limit=5
            )

            # 2. 관련 대화 검색
            related_conversations = self.search_service.search_conversations(
                query=user_input,
                limit=2
            )

            # 3. 결과 통합
            relevant_memories = search_result.items

            # 대화 기록을 메모리 아이템으로 변환하여 추가
            from core.shared.models import MemoryItem
            from datetime import datetime

            for conv in related_conversations:
                if conv.turns:
                    last_turn = conv.turns[-1]
                    memory_item = MemoryItem(
                        content=f"이전 대화: {last_turn.user_message} -> {last_turn.assistant_message}",
                        memory_type=MemoryType.CONVERSATION,
                        timestamp=last_turn.timestamp,
                        relevance_score=0.8,
                        metadata={"conversation_id": conv.session_id, "title": conv.title}
                    )
                    relevant_memories.append(memory_item)

            # 관련성 점수로 정렬하고 상위 3개만 반환
            relevant_memories.sort(key=lambda x: x.relevance_score, reverse=True)
            return relevant_memories[:3]

        except Exception as e:
            print(f"⚠️ 기억 검색 실패: {e}")
            return []

    def _select_provider(self):
        """프로바이더 선택"""
        # 기억 중심 작업에 적합한 프로바이더 우선 선택
        preferred_order = [self.default_provider, "claude", "ollama"]

        for provider_name in preferred_order:
            provider = self.ai_providers.get(provider_name)
            if provider and provider.is_available():
                return provider

        # 사용 가능한 아무 프로바이더나
        for provider in self.ai_providers.values():
            if provider.is_available():
                return provider

        return None

    def _build_memory_enhanced_messages(self, user_input: str, context: SessionContext,
                                        relevant_memories: List[Any]) -> List[ChatMessage]:
        """기억을 활용한 메시지 구성"""
        messages = []

        # 1. 향상된 시스템 메시지
        system_content = self._build_memory_system_message(context, relevant_memories)
        messages.append(ChatMessage(role="system", content=system_content))

        # 2. 최근 대화 기록 (더 많이 포함)
        recent_turns = context.conversation_history[-4:]
        for turn in recent_turns:
            messages.append(ChatMessage(role="user", content=turn.user_message))
            messages.append(ChatMessage(role="assistant", content=turn.assistant_message))

        # 3. 현재 질문
        messages.append(ChatMessage(role="user", content=user_input))

        return messages

    def _build_memory_system_message(self, context: SessionContext, relevant_memories: List[Any]) -> str:
        """기억 기반 시스템 메시지 구성"""
        user_profile = context.user_profile

        parts = [
            f"당신은 {user_profile.name}의 개인 AI 어시스턴트입니다.",
            f"사용자 정보: {user_profile.coding_style}, 선호 언어: {', '.join(user_profile.preferred_languages)}"
        ]

        # 관련 기억 추가
        if relevant_memories:
            parts.append("\n관련 기억:")
            for i, memory in enumerate(relevant_memories, 1):
                memory_summary = memory.content[:150] + "..." if len(memory.content) > 150 else memory.content
                parts.append(f"{i}. {memory_summary}")

        parts.append("\n이전 기억을 참고하여 연속성 있는 대화를 제공해주세요.")

        return "\n".join(parts)

    def _save_new_memory(self, user_input: str, ai_response: str, context: SessionContext):
        """새로운 기억 저장"""
        try:
            # Phase 1: 간단한 기억 저장
            from core.shared.models import MemoryItem, MemoryType
            from datetime import datetime

            # 중요한 상호작용만 저장 (나중에 더 정교한 필터링 추가)
            if len(user_input) > 20 or any(keyword in user_input.lower() for keyword in
                                           ['프로젝트', '문제', '에러', '구현', '설계']):
                memory_item = MemoryItem(
                    content=f"Q: {user_input}\nA: {ai_response}",
                    memory_type=MemoryType.CONVERSATION,
                    timestamp=datetime.now(),
                    tags=self._extract_simple_tags(user_input),
                    metadata={
                        "session_id": context.session_id,
                        "orchestrator": "memory",
                        "user_id": context.user_profile.name
                    }
                )

                self.memory_repository.save_memory_item(memory_item)

        except Exception as e:
            print(f"⚠️ 새로운 기억 저장 실패: {e}")

    def _extract_simple_tags(self, text: str) -> List[str]:
        """간단한 태그 추출"""
        tags = []
        text_lower = text.lower()

        # 기술 관련 태그
        tech_keywords = {
            'python': 'python', 'javascript': 'javascript', 'java': 'java',
            'fastapi': 'fastapi', 'django': 'django', 'flask': 'flask',
            'react': 'react', 'vue': 'vue', 'angular': 'angular',
            '데이터베이스': 'database', 'db': 'database', 'sql': 'sql',
            'api': 'api', 'rest': 'rest', 'graphql': 'graphql'
        }

        for keyword, tag in tech_keywords.items():
            if keyword in text_lower:
                tags.append(tag)

        # 작업 유형 태그
        if any(word in text_lower for word in ['에러', 'error', '오류', '문제']):
            tags.append('troubleshooting')
        if any(word in text_lower for word in ['구현', 'implement', '개발', '만들기']):
            tags.append('development')
        if any(word in text_lower for word in ['설계', 'design', '아키텍처']):
            tags.append('design')

        return list(set(tags))  # 중복 제거