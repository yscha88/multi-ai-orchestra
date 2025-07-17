# ===== ports/orchestrator_ports.py =====
"""
오케스트레이터 관련 포트 인터페이스
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
from core.shared.models import (
    OrchestratorResponse, SessionContext, TaskAnalysis, OrchestratorType
)


class BaseOrchestrator(ABC):
    """기본 오케스트레이터 인터페이스"""

    @abstractmethod
    def get_orchestrator_type(self) -> OrchestratorType:
        """오케스트레이터 타입 반환"""
        pass

    @abstractmethod
    def process_request(self, user_input: str, context: SessionContext) -> OrchestratorResponse:
        """요청 처리"""
        pass

    @abstractmethod
    def can_handle_task(self, task_analysis: TaskAnalysis) -> bool:
        """작업 처리 가능 여부"""
        pass

    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """지원 기능 목록"""
        pass

    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> bool:
        """초기화"""
        pass

    @abstractmethod
    def cleanup(self) -> bool:
        """정리"""
        pass

    # TODO Phase 2: 고급 오케스트레이터 기능
    # @abstractmethod
    # def learn_from_interaction(self, user_input: str, response: OrchestratorResponse,
    #                           feedback: Dict[str, Any]) -> bool:
    #     """상호작용에서 학습"""
    #     pass

    # @abstractmethod
    # def adapt_to_user(self, user_context: Dict[str, Any]) -> bool:
    #     """사용자에게 적응"""
    #     pass


class OrchestratorFactory(ABC):
    """오케스트레이터 팩토리 인터페이스"""

    @abstractmethod
    def create_orchestrator(self, orchestrator_type: OrchestratorType,
                            config: Dict[str, Any]) -> BaseOrchestrator:
        """오케스트레이터 생성"""
        pass

    @abstractmethod
    def get_available_orchestrators(self) -> List[OrchestratorType]:
        """사용 가능한 오케스트레이터 목록"""
        pass

    @abstractmethod
    def register_orchestrator(self, orchestrator_type: OrchestratorType,
                              orchestrator_class: type) -> bool:
        """오케스트레이터 등록"""
        pass