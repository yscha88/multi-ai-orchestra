# ===== application/orchestrators/simple_orchestrator.py =====
"""
단순 오케스트레이터 - 기존 방식 래핑
"""

import time
from typing import List, Dict, Any
from .base_orchestrator import BaseOrchestratorImpl
from core.shared.models import (
    OrchestratorResponse, SessionContext, OrchestratorType, ChatMessage
)


class SimpleOrchestrator(BaseOrchestratorImpl):
    """단순 오케스트레이터 (기존 방식 래핑)"""

    def __init__(self, ai_providers: Dict[str, Any], config: Dict[str, Any]):
        super().__init__(OrchestratorType.SIMPLE, config)
        self.ai_providers = ai_providers

    def process_request(self, user_input: str, context: SessionContext) -> OrchestratorResponse:
        """요청 처리 - 기존 단순 방식"""
        start_time = time.time()

        try:
            # 1. 컨텍스트 검증
            if not self._validate_context(context):
                return self._prepare_error_response("잘못된 세션 컨텍스트", context)

            # 2. 기본 프로바이더 선택
            provider_name = self.default_provider
            provider = self.ai_providers.get(provider_name)

            if not provider or not provider.is_available():
                # 사용 가능한 다른 프로바이더 찾기
                for name, prov in self.ai_providers.items():
                    if prov.is_available():
                        provider_name = name
                        provider = prov
                        break

            if not provider:
                return self._prepare_error_response("사용 가능한 AI가 없습니다", context)

            # 3. 간단한 메시지 구성
            messages = self._build_simple_messages(user_input, context)

            # 4. AI 호출
            chat_response = provider.chat(messages)

            # 5. 응답 생성
            processing_time = time.time() - start_time

            return OrchestratorResponse(
                content=chat_response.content,
                orchestrator_type=self.orchestrator_type,
                processing_time=processing_time,
                token_usage=chat_response.token_usage,
                used_providers=[provider_name],
                metadata={
                    "mode": "simple",
                    "provider": provider_name,
                    "model": provider.get_model_info().name
                }
            )

        except Exception as e:
            processing_time = time.time() - start_time
            print(f"⚠️ SimpleOrchestrator 오류: {e}")
            return self._prepare_error_response(str(e), context)

    def get_capabilities(self) -> List[str]:
        """지원 기능 목록"""
        return ["basic_chat", "quick_response", "simple_qa"]

    def can_handle_task(self, task_analysis) -> bool:
        """작업 처리 가능 여부"""
        # 단순 오케스트레이터는 모든 작업 처리 가능 (기본 옵션)
        return True

    def _build_simple_messages(self, user_input: str, context: SessionContext) -> List[ChatMessage]:
        """간단한 메시지 구성"""
        messages = []

        # 기본 시스템 메시지
        system_content = f"""당신은 {context.user_profile.name}의 AI 어시스턴트입니다.
코딩 스타일: {context.user_profile.coding_style}
선호 언어: {', '.join(context.user_profile.preferred_languages)}
간결하고 도움이 되는 답변을 제공해주세요."""

        messages.append(ChatMessage(role="system", content=system_content))

        # 최근 대화 1-2턴만 포함
        recent_turns = context.conversation_history[-2:]
        for turn in recent_turns:
            messages.append(ChatMessage(role="user", content=turn.user_message))
            messages.append(ChatMessage(role="assistant", content=turn.assistant_message))

        # 현재 질문
        messages.append(ChatMessage(role="user", content=user_input))

        return messages
