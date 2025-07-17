# ===== ports/control_ports.py =====
"""
관제 관련 포트 인터페이스
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from core.shared.models import (
    TaskAnalysis, TaskComplexity, OrchestratorType,
    OrchestratorResponse, SessionContext
)


class TaskAnalysisService(ABC):
    """작업 분석 서비스 인터페이스"""

    @abstractmethod
    def analyze_task(self, user_input: str, context: SessionContext) -> TaskAnalysis:
        """작업 분석"""
        pass

    @abstractmethod
    def classify_complexity(self, user_input: str) -> TaskComplexity:
        """복잡도 분류"""
        pass

    @abstractmethod
    def recommend_orchestrator(self, task_analysis: TaskAnalysis) -> OrchestratorType:
        """오케스트레이터 추천"""
        pass

    # TODO Phase 2: 고급 작업 분석
    # @abstractmethod
    # def decompose_complex_task(self, task: str) -> List[str]:
    #     """복잡한 작업 분해"""
    #     pass

    # @abstractmethod
    # def estimate_resources(self, task_analysis: TaskAnalysis) -> Dict[str, Any]:
    #     """필요 리소스 추정"""
    #     pass


class OrchestrationService(ABC):
    """오케스트레이션 서비스 인터페이스"""

    @abstractmethod
    def coordinate_processing(self, user_input: str, context: SessionContext,
                              task_analysis: TaskAnalysis) -> OrchestratorResponse:
        """처리 조율"""
        pass

    @abstractmethod
    def select_optimal_provider(self, task_analysis: TaskAnalysis) -> str:
        """최적 프로바이더 선택"""
        pass

    @abstractmethod
    def monitor_processing(self, session_id: str) -> Dict[str, Any]:
        """처리 모니터링"""
        pass

    # TODO Phase 2: 고급 오케스트레이션
    # @abstractmethod
    # def coordinate_multi_ai(self, subtasks: List[str]) -> List[OrchestratorResponse]:
    #     """다중 AI 조율"""
    #     pass

    # @abstractmethod
    # def ensure_quality(self, response: OrchestratorResponse) -> OrchestratorResponse:
    #     """품질 보장"""
    #     pass