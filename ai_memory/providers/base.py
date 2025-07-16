"""
AI Provider 추상 인터페이스
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class ProviderType(Enum):
    """Provider 타입"""
    CLOUD_API = "cloud_api"
    LOCAL_LLM = "local_llm"
    HYBRID = "hybrid"


@dataclass
class ModelInfo:
    """모델 정보"""
    name: str
    provider: str
    type: ProviderType
    max_tokens: int
    cost_per_1k_tokens: float = 0.0
    supports_streaming: bool = False
    supports_function_calling: bool = False
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ChatMessage:
    """채팅 메시지"""
    role: str  # "user", "assistant", "system"
    content: str
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ChatResponse:
    """채팅 응답"""
    content: str
    model_info: ModelInfo
    token_usage: Dict[str, int] = None
    cost_estimate: float = 0.0
    response_time: float = 0.0
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.token_usage is None:
            self.token_usage = {"input_tokens": 0, "output_tokens": 0}
        if self.metadata is None:
            self.metadata = {}


class BaseProvider(ABC):
    """AI Provider 추상 기본 클래스"""

    def __init__(self, model_name: str = None, **kwargs):
        self.model_name = model_name
        self.config = kwargs
        self._model_info = None

    @abstractmethod
    def chat(self, messages: List[ChatMessage], **kwargs) -> ChatResponse:
        """
        AI와 채팅

        Args:
            messages: 채팅 메시지 리스트
            **kwargs: 추가 파라미터 (max_tokens, temperature 등)

        Returns:
            ChatResponse: 응답 결과
        """
        pass

    @abstractmethod
    def get_model_info(self) -> ModelInfo:
        """모델 정보 반환"""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Provider 사용 가능 여부 확인"""
        pass

    def estimate_cost(self, messages: List[ChatMessage]) -> float:
        """비용 추정 (선택적 구현)"""
        return 0.0

    def validate_config(self) -> bool:
        """설정 유효성 검증 (선택적 구현)"""
        return True

    def get_supported_features(self) -> List[str]:
        """지원하는 기능 목록 반환"""
        return ["chat"]


class ProviderError(Exception):
    """Provider 관련 오류"""
    pass


class ProviderUnavailableError(ProviderError):
    """Provider 사용 불가 오류"""
    pass


class ProviderConfigError(ProviderError):
    """Provider 설정 오류"""
    pass