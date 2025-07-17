# ===== core/control/orchestrator_coordinator.py =====
"""
오케스트레이터 조율기 - Phase 1 기본 구현
"""

import time
from typing import Dict, Any
from ports.control_ports import OrchestrationService
from ports.ai_ports import AIProvider, ModelSelector
from core.shared.models import (
    TaskAnalysis, OrchestratorResponse, SessionContext, OrchestratorType
)


class BasicOrchestratorCoordinator(OrchestrationService):
    """기본 오케스트레이션 서비스 (Phase 1)"""

    def __init__(self, ai_providers: Dict[str, AIProvider], model_selector: ModelSelector):
        self.ai_providers = ai_providers
        self.model_selector = model_selector
        self.processing_sessions = {}  # session_id -> processing_info

    def coordinate_processing(self, user_input: str, context: SessionContext,
                              task_analysis: TaskAnalysis) -> OrchestratorResponse:
        """처리 조율 (Phase 1: 기본 구현)"""
        start_time = time.time()

        # 1. 최적 프로바이더 선택
        provider_name = self.select_optimal_provider(task_analysis)
        provider = self.ai_providers.get(provider_name)

        if not provider:
            raise RuntimeError(f"Provider '{provider_name}'를 찾을 수 없습니다")

        # 2. 처리 모니터링 시작
        self._start_monitoring(context.session_id, task_analysis, provider_name)

        try:
            # 3. 컨텍스트 기반 메시지 구성
            messages = self._build_context_messages(user_input, context, task_analysis)

            # 4. AI 호출
            chat_response = provider.chat(messages)

            # 5. 응답 후처리
            processed_response = self._post_process_response(
                chat_response, task_analysis, context
            )

            processing_time = time.time() - start_time

            # 6. 오케스트레이터 응답 생성
            orchestrator_response = OrchestratorResponse(
                content=processed_response,
                orchestrator_type=task_analysis.recommended_orchestrator,
                processing_time=processing_time,
                token_usage=chat_response.token_usage,
                task_analysis=task_analysis,
                used_providers=[provider_name],
                metadata={
                    "provider_info": provider.get_model_info().name,
                    "complexity": task_analysis.complexity.value,
                    "estimated_vs_actual_time": {
                        "estimated": task_analysis.estimated_time,
                        "actual": processing_time
                    }
                }
            )

            # 7. 모니터링 완료
            self._complete_monitoring(context.session_id, True, orchestrator_response)

            return orchestrator_response

        except Exception as e:
            processing_time = time.time() - start_time
            self._complete_monitoring(context.session_id, False, None)
            raise RuntimeError(f"처리 중 오류 발생: {e}")

    def select_optimal_provider(self, task_analysis: TaskAnalysis) -> str:
        """최적 프로바이더 선택"""
        # Phase 1: 간단한 선택 로직

        # 복잡도 기반 선택
        if task_analysis.complexity == TaskComplexity.COMPLEX:
            # 복잡한 작업은 고성능 모델 (Claude)
            return "claude"

        # 필요 기능 기반 선택
        if "code_generation" in task_analysis.required_capabilities:
            # 코드 생성은 CodeLlama 우선
            if "ollama" in self.ai_providers:
                ollama_provider = self.ai_providers["ollama"]
                if hasattr(ollama_provider, 'get_model_names'):
                    available_models = ollama_provider.get_model_names()
                    if any("codellama" in model.lower() for model in available_models):
                        return "ollama"

        # 기본값: 사용 가능한 첫 번째 프로바이더
        for provider_name, provider in self.ai_providers.items():
            if provider.is_available():
                return provider_name

        raise RuntimeError("사용 가능한 AI Provider가 없습니다")

    def monitor_processing(self, session_id: str) -> Dict[str, Any]:
        """처리 모니터링"""
        if session_id not in self.processing_sessions:
            return {"status": "not_found"}

        session_info = self.processing_sessions[session_id]
        current_time = time.time()
        elapsed_time = current_time - session_info["start_time"]

        return {
            "status": session_info["status"],
            "elapsed_time": elapsed_time,
            "estimated_time": session_info["estimated_time"],
            "progress": min(elapsed_time / session_info["estimated_time"], 1.0),
            "provider": session_info["provider"],
            "complexity": session_info["complexity"]
        }

    # ===== 헬퍼 메서드들 =====

    def _build_context_messages(self, user_input: str, context: SessionContext,
                                task_analysis: TaskAnalysis) -> List[Any]:
        """컨텍스트 기반 메시지 구성"""
        from core.shared.models import ChatMessage

        messages = []

        # 1. 시스템 메시지 (오케스트레이터 타입에 따라)
        system_message = self._build_system_message(context, task_analysis)
        if system_message:
            messages.append(ChatMessage(role="system", content=system_message))

        # 2. 최근 대화 기록 (제한적으로)
        recent_turns = context.conversation_history[-3:]  # 최근 3턴만
        for turn in recent_turns:
            messages.append(ChatMessage(role="user", content=turn.user_message))
            messages.append(ChatMessage(role="assistant", content=turn.assistant_message))

        # 3. 관련 기억 (있다면)
        if context.relevant_memories:
            memory_context = self._build_memory_context(context.relevant_memories)
            if memory_context:
                messages.append(ChatMessage(role="system", content=f"관련 기억: {memory_context}"))

        # 4. 현재 사용자 입력
        messages.append(ChatMessage(role="user", content=user_input))

        return messages

    def _build_system_message(self, context: SessionContext, task_analysis: TaskAnalysis) -> str:
        """시스템 메시지 구성"""
        user_profile = context.user_profile

        parts = [
            "당신은 사용자의 개인 AI 어시스턴트입니다.",
            f"사용자 정보: {user_profile.name}, {user_profile.coding_style}, 선호 언어: {', '.join(user_profile.preferred_languages)}"
        ]

        # 작업 복잡도에 따른 지침
        if task_analysis.complexity == TaskComplexity.COMPLEX:
            parts.append("복잡한 작업이므로 체계적이고 단계별로 접근해주세요.")
        elif task_analysis.complexity == TaskComplexity.MODERATE:
            parts.append("적당한 복잡도의 작업이므로 실용적인 해결책을 제시해주세요.")
        else:
            parts.append("간단한 질문이므로 명확하고 간결하게 답변해주세요.")

        # 사용자 상호작용 스타일 반영
        if user_profile.interaction_style == "brief":
            parts.append("사용자는 간결한 답변을 선호합니다.")
        elif user_profile.interaction_style == "detailed":
            parts.append("사용자는 상세한 설명을 선호합니다.")

        return " ".join(parts)

    def _build_memory_context(self, memories: List[Any]) -> str:
        """기억 컨텍스트 구성"""
        if not memories:
            return ""

        memory_summaries = []
        for memory in memories[:2]:  # 최대 2개만
            summary = memory.content[:100] + "..." if len(memory.content) > 100 else memory.content
            memory_summaries.append(summary)

        return " | ".join(memory_summaries)

    def _post_process_response(self, chat_response: Any, task_analysis: TaskAnalysis,
                               context: SessionContext) -> str:
        """응답 후처리"""
        response_content = chat_response.content

        # Phase 1: 기본적인 후처리만

        # 1. 사용자 스타일에 따른 조정
        if context.user_profile.interaction_style == "brief":
            # 너무 긴 응답은 요약 제안
            if len(response_content) > 500:
                response_content += "\n\n💡 더 간단한 설명이 필요하시면 '간단히 설명해줘'라고 말씀해주세요."

        # 2. 복잡한 작업의 경우 다음 단계 제안
        if task_analysis.complexity == TaskComplexity.COMPLEX:
            response_content += "\n\n🔄 추가로 궁금한 부분이나 구체적으로 진행하고 싶은 단계가 있으면 말씀해주세요."

        return response_content

    def _start_monitoring(self, session_id: str, task_analysis: TaskAnalysis, provider_name: str):
        """모니터링 시작"""
        self.processing_sessions[session_id] = {
            "status": "processing",
            "start_time": time.time(),
            "estimated_time": task_analysis.estimated_time,
            "provider": provider_name,
            "complexity": task_analysis.complexity.value
        }

    def _complete_monitoring(self, session_id: str, success: bool, response: Any):
        """모니터링 완료"""
        if session_id in self.processing_sessions:
            self.processing_sessions[session_id]["status"] = "completed" if success else "failed"
            self.processing_sessions[session_id]["end_time"] = time.time()

            # 일정 시간 후 정리 (메모리 절약)
            # TODO: 백그라운드 정리 작업 구현