# ===== application/orchestrators/control_orchestrator.py =====
"""
관제 중심 오케스트레이터
"""

import time
from typing import List, Dict, Any
from .base_orchestrator import BaseOrchestratorImpl
from core.control.task_analyzer import SimpleTaskAnalyzer
from core.control.orchestrator_coordinator import BasicOrchestratorCoordinator
from core.shared.models import (
    OrchestratorResponse, SessionContext, OrchestratorType, TaskComplexity
)


class ControlOrchestrator(BaseOrchestratorImpl):
    """관제 중심 오케스트레이터"""

    def __init__(self, ai_providers: Dict[str, Any], task_analyzer: SimpleTaskAnalyzer,
                 coordinator: BasicOrchestratorCoordinator, config: Dict[str, Any]):
        super().__init__(OrchestratorType.CONTROL, config)
        self.ai_providers = ai_providers
        self.task_analyzer = task_analyzer
        self.coordinator = coordinator

    def process_request(self, user_input: str, context: SessionContext) -> OrchestratorResponse:
        """요청 처리 - 관제 중심"""
        start_time = time.time()

        try:
            # 1. 컨텍스트 검증
            if not self._validate_context(context):
                return self._prepare_error_response("잘못된 세션 컨텍스트", context)

            # 2. 작업 분석
            task_analysis = self.task_analyzer.analyze_task(user_input, context)

            # 3. 복잡한 작업 처리 로직
            if task_analysis.complexity == TaskComplexity.COMPLEX:
                return self._handle_complex_task(user_input, context, task_analysis)
            elif task_analysis.complexity == TaskComplexity.MODERATE:
                return self._handle_moderate_task(user_input, context, task_analysis)
            else:
                return self._handle_simple_task(user_input, context, task_analysis)

        except Exception as e:
            processing_time = time.time() - start_time
            print(f"⚠️ ControlOrchestrator 오류: {e}")
            return self._prepare_error_response(str(e), context)

    def get_capabilities(self) -> List[str]:
        """지원 기능 목록"""
        return [
            "task_analysis", "complexity_assessment", "workflow_management",
            "multi_step_processing", "provider_optimization", "quality_assurance"
        ]

    def can_handle_task(self, task_analysis) -> bool:
        """작업 처리 가능 여부"""
        # 관제 오케스트레이터는 복잡한 작업에 특화
        return task_analysis.complexity in [TaskComplexity.MODERATE, TaskComplexity.COMPLEX]

    def _handle_complex_task(self, user_input: str, context: SessionContext,
                             task_analysis) -> OrchestratorResponse:
        """복잡한 작업 처리"""
        start_time = time.time()

        # 1. 단계별 분해 시뮬레이션 (Phase 1에서는 간단히)
        steps = self._decompose_complex_task(user_input)

        # 2. 고급 프로바이더 선택
        provider = self._select_advanced_provider(task_analysis)
        if not provider:
            return self._prepare_error_response("고급 AI를 사용할 수 없습니다", context)

        # 3. 관제 메시지 구성
        messages = self._build_control_messages(user_input, context, task_analysis, steps)

        # 4. AI 호출
        chat_response = provider.chat(messages)

        # 5. 결과 검증 및 향상 (Phase 1에서는 기본적으로)
        enhanced_response = self._enhance_complex_response(chat_response.content, steps)

        processing_time = time.time() - start_time

        return OrchestratorResponse(
            content=enhanced_response,
            orchestrator_type=self.orchestrator_type,
            processing_time=processing_time,
            token_usage=chat_response.token_usage,
            task_analysis=task_analysis,
            used_providers=[provider.get_model_info().provider],
            metadata={
                "mode": "complex_control",
                "complexity": task_analysis.complexity.value,
                "decomposed_steps": len(steps),
                "reasoning": task_analysis.reasoning,
                "estimated_vs_actual": {
                    "estimated": task_analysis.estimated_time,
                    "actual": processing_time
                }
            }
        )

    def _handle_moderate_task(self, user_input: str, context: SessionContext,
                              task_analysis) -> OrchestratorResponse:
        """중간 복잡도 작업 처리"""
        # 기본 조율기 사용
        return self.coordinator.coordinate_processing(user_input, context, task_analysis)

    def _handle_simple_task(self, user_input: str, context: SessionContext,
                            task_analysis) -> OrchestratorResponse:
        """단순 작업 처리 (관제 관점에서)"""
        # 분석 정보를 포함한 단순 처리
        start_time = time.time()

        provider = self._select_provider()
        if not provider:
            return self._prepare_error_response("사용 가능한 AI가 없습니다", context)

        from core.shared.models import ChatMessage
        messages = [
            ChatMessage(role="system", content=f"""당신은 효율적인 AI 어시스턴트입니다.
사용자: {context.user_profile.name}
이 질문은 단순한 작업으로 분석되었습니다: {task_analysis.reasoning}
간결하고 정확한 답변을 제공해주세요."""),
            ChatMessage(role="user", content=user_input)
        ]

        chat_response = provider.chat(messages)
        processing_time = time.time() - start_time

        return OrchestratorResponse(
            content=chat_response.content,
            orchestrator_type=self.orchestrator_type,
            processing_time=processing_time,
            token_usage=chat_response.token_usage,
            task_analysis=task_analysis,
            used_providers=[provider.get_model_info().provider],
            metadata={
                "mode": "simple_control",
                "analysis_applied": True
            }
        )

    def _decompose_complex_task(self, user_input: str) -> List[str]:
        """복잡한 작업 분해 (Phase 1 단순 버전)"""
        # Phase 1에서는 간단한 키워드 기반 분해
        steps = []

        user_input_lower = user_input.lower()

        if any(word in user_input_lower for word in ['설계', 'design', '아키텍처']):
            steps.extend([
                "요구사항 분석",
                "아키텍처 설계",
                "상세 설계",
                "구현 계획"
            ])
        elif any(word in user_input_lower for word in ['프로젝트', 'project']):
            steps.extend([
                "프로젝트 계획",
                "기술 스택 선택",
                "개발 단계별 진행",
                "테스트 및 배포"
            ])
        elif any(word in user_input_lower for word in ['구현', 'implement', '개발']):
            steps.extend([
                "요구사항 정리",
                "설계 및 구조화",
                "단계별 구현",
                "테스트 및 검증"
            ])
        else:
            steps.extend([
                "문제 분석",
                "해결 방안 모색",
                "단계별 실행"
            ])

        return steps

    def _select_advanced_provider(self, task_analysis):
        """고급 프로바이더 선택"""
        # 복잡한 작업에는 고성능 모델 우선
        if "claude" in self.ai_providers:
            claude_provider = self.ai_providers["claude"]
            if claude_provider.is_available():
                return claude_provider

        # 대안으로 사용 가능한 프로바이더
        return self._select_provider()

    def _select_provider(self):
        """일반 프로바이더 선택"""
        for provider in self.ai_providers.values():
            if provider.is_available():
                return provider
        return None

    def _build_control_messages(self, user_input: str, context: SessionContext,
                                task_analysis, steps: List[str]):
        """관제 메시지 구성"""
        from core.shared.models import ChatMessage

        messages = []

        # 고급 시스템 메시지
        system_content = f"""당신은 전문적인 AI 관제 어시스턴트입니다.
사용자: {context.user_profile.name} ({context.user_profile.coding_style})

작업 분석 결과:
- 복잡도: {task_analysis.complexity.value}
- 예상 처리 시간: {task_analysis.estimated_time:.1f}초
- 필요 기능: {', '.join(task_analysis.required_capabilities)}

단계별 접근 방법:
{chr(10).join(f'{i + 1}. {step}' for i, step in enumerate(steps))}

체계적이고 전문적인 답변을 제공해주세요."""

        messages.append(ChatMessage(role="system", content=system_content))

        # 최근 대화 (복잡한 작업일 때는 더 많은 컨텍스트)
        recent_turns = context.conversation_history[-3:]
        for turn in recent_turns:
            messages.append(ChatMessage(role="user", content=turn.user_message))
            messages.append(ChatMessage(role="assistant", content=turn.assistant_message))

        # 현재 질문
        messages.append(ChatMessage(role="user", content=user_input))

        return messages

    def _enhance_complex_response(self, response: str, steps: List[str]) -> str:
        """복잡한 응답 향상"""
        # Phase 1: 기본적인 향상
        enhanced = response

        # 단계 정보 추가
        if steps and len(enhanced) > 200:  # 충분히 상세한 응답인 경우
            enhanced += f"\n\n📋 **권장 진행 단계:**\n"
            for i, step in enumerate(steps, 1):
                enhanced += f"{i}. {step}\n"

        # 추가 지원 안내
        enhanced += "\n\n💡 각 단계에 대해 더 자세한 안내가 필요하시면 구체적으로 말씀해주세요."

        return enhanced
