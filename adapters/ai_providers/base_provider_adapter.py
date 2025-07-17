# ===== adapters/ai_providers/base_provider_adapter.py =====
"""
기본 Provider 어댑터 (기존 BaseProvider 리팩터링)
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
from ports.ai_ports import AIProvider
from core.shared.models import ChatMessage, ChatResponse, ModelInfo, ProviderType


class BaseProviderAdapter(AIProvider):
    """기본 Provider 어댑터 (기존 BaseProvider 개선)"""

    def __init__(self, model_name: str = None, **kwargs):
        self.model_name = model_name
        self.config = kwargs
        self._model_info = None
        self._performance_metrics = {
            "avg_response_time": 0.0,
            "success_rate": 1.0,
            "cost_efficiency": 1.0,
            "total_requests": 0
        }

    # ===== AIProvider 인터페이스 구현 =====

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

    def estimate_cost(self, messages: List[ChatMessage]) -> float:
        """비용 추정 (기본 구현)"""
        return 0.0

    def get_capabilities(self) -> List[str]:
        """지원하는 기능 목록"""
        return ["chat", "cost_estimation"]

    def get_performance_metrics(self) -> Dict[str, float]:
        """성능 메트릭"""
        return self._performance_metrics.copy()

    # ===== 성능 추적 메서드들 =====

    def _update_performance_metrics(self, response_time: float, success: bool, cost: float = 0.0):
        """성능 메트릭 업데이트"""
        self._performance_metrics["total_requests"] += 1

        # 평균 응답 시간 업데이트
        total_requests = self._performance_metrics["total_requests"]
        current_avg = self._performance_metrics["avg_response_time"]
        self._performance_metrics["avg_response_time"] = \
            (current_avg * (total_requests - 1) + response_time) / total_requests

        # 성공률 업데이트
        current_success_rate = self._performance_metrics["success_rate"]
        self._performance_metrics["success_rate"] = \
            (current_success_rate * (total_requests - 1) + (1.0 if success else 0.0)) / total_requests

    def validate_config(self) -> bool:
        """설정 유효성 검증 (기존 메서드 유지)"""
        return True