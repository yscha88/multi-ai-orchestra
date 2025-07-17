# ===== ports/ai_ports.py =====
"""
AI 관련 포트 인터페이스
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from core.shared.models import ChatMessage, ChatResponse, ModelInfo


class AIProvider(ABC):
    """AI 제공자 인터페이스 (기존 BaseProvider 개선)"""

    @abstractmethod
    def chat(self, messages: List[ChatMessage], **kwargs) -> ChatResponse:
        """AI와 채팅"""
        pass

    @abstractmethod
    def get_model_info(self) -> ModelInfo:
        """모델 정보 반환"""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """사용 가능 여부 확인"""
        pass

    @abstractmethod
    def estimate_cost(self, messages: List[ChatMessage]) -> float:
        """비용 추정"""
        pass

    # Phase 1 추가 메서드
    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """지원하는 기능 목록"""
        pass

    @abstractmethod
    def get_performance_metrics(self) -> Dict[str, float]:
        """성능 메트릭"""
        pass

    # TODO Phase 2: 고급 AI 기능
    # @abstractmethod
    # def stream_chat(self, messages: List[ChatMessage]) -> Iterator[str]:
    #     """스트리밍 채팅"""
    #     pass

    # @abstractmethod
    # def function_call(self, function_name: str, parameters: Dict[str, Any]) -> Any:
    #     """함수 호출"""
    #     pass


class ModelSelector(ABC):
    """모델 선택 인터페이스"""

    @abstractmethod
    def select_optimal_model(self, task_type: str, requirements: Dict[str, Any]) -> str:
        """최적 모델 선택"""
        pass

    @abstractmethod
    def get_available_models(self) -> List[ModelInfo]:
        """사용 가능한 모델 목록"""
        pass

    @abstractmethod
    def evaluate_model_performance(self, model_name: str, task_type: str) -> float:
        """모델 성능 평가"""
        pass

    @abstractmethod
    def get_model_recommendations(self, context: Dict[str, Any]) -> List[str]:
        """모델 추천"""
        pass

    # TODO Phase 2: 고급 모델 선택
    # @abstractmethod
    # def adaptive_model_selection(self, user_feedback: Dict[str, Any]) -> str:
    #     """적응형 모델 선택"""
    #     pass

    # @abstractmethod
    # def multi_model_strategy(self, complex_task: str) -> Dict[str, str]:
    #     """다중 모델 전략"""
    #     pass