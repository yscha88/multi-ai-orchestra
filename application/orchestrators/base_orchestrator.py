# ===== application/orchestrators/base_orchestrator.py =====
"""
기본 오케스트레이터 구현
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
from ports.orchestrator_ports import BaseOrchestrator
from core.shared.models import (
    OrchestratorResponse, SessionContext, TaskAnalysis, OrchestratorType
)


class BaseOrchestratorImpl(BaseOrchestrator):
    """기본 오케스트레이터 구현"""

    def __init__(self, orchestrator_type: OrchestratorType, config: Dict[str, Any]):
        self.orchestrator_type = orchestrator_type
        self.config = config
        self.is_initialized = False

        # 공통 설정
        self.max_context_length = config.get('max_context_length', 4000)
        self.timeout_seconds = config.get('timeout_seconds', 120)
        self.default_provider = config.get('default_provider', 'claude')

    def get_orchestrator_type(self) -> OrchestratorType:
        """오케스트레이터 타입 반환"""
        return self.orchestrator_type

    @abstractmethod
    def process_request(self, user_input: str, context: SessionContext) -> OrchestratorResponse:
        """요청 처리 (각 오케스트레이터에서 구현)"""
        pass

    def can_handle_task(self, task_analysis: TaskAnalysis) -> bool:
        """작업 처리 가능 여부 (기본 구현)"""
        # Phase 1: 모든 오케스트레이터가 모든 작업 처리 가능
        return True

    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """지원 기능 목록"""
        pass

    def initialize(self, config: Dict[str, Any]) -> bool:
        """초기화"""
        try:
            self.config.update(config)
            self.is_initialized = True
            return True
        except Exception as e:
            print(f"⚠️ 오케스트레이터 초기화 실패: {e}")
            return False

    def cleanup(self) -> bool:
        """정리"""
        try:
            self.is_initialized = False
            return True
        except Exception as e:
            print(f"⚠️ 오케스트레이터 정리 실패: {e}")
            return False

    # ===== 공통 헬퍼 메서드들 =====

    def _validate_context(self, context: SessionContext) -> bool:
        """컨텍스트 유효성 검증"""
        return (context is not None and
                context.session_id and
                context.user_profile is not None)

    def _prepare_error_response(self, error_message: str,
                                context: SessionContext) -> OrchestratorResponse:
        """오류 응답 생성"""
        return OrchestratorResponse(
            content=f"죄송합니다. 처리 중 오류가 발생했습니다: {error_message}",
            orchestrator_type=self.orchestrator_type,
            processing_time=0.0,
            metadata={"error": True, "error_message": error_message}
        )
