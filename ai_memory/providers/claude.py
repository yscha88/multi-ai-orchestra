"""
Anthropic Claude Provider 구현
"""

import anthropic
import os
import time
from typing import List, Dict, Any

from .base import BaseProvider, ChatMessage, ChatResponse, ModelInfo, ProviderType
from .base import ProviderError, ProviderUnavailableError, ProviderConfigError


class ClaudeProvider(BaseProvider):
    """Anthropic Claude API Provider"""

    SUPPORTED_MODELS = {
        "claude-opus-4": {
            "max_tokens": 4000,
            "cost_per_1k_input": 15.00,
            "cost_per_1k_output": 75.00,
        },
        "claude-sonnet-4": {
            "max_tokens": 8000,
            "cost_per_1k_input": 3.00,
            "cost_per_1k_output": 15.00,
        },
        "claude-sonnet-3.7": {
            "max_tokens": 8000,
            "cost_per_1k_input": 3.00,
            "cost_per_1k_output": 15.00,
        },
        "claude-sonnet-3.5-2024-10-22": {
            "max_tokens": 8000,
            "cost_per_1k_input": 0.003,
            "cost_per_1k_output": 0.015,
        },
        "claude-sonnet-3.5-2024-06-20": {
            "max_tokens": 8000,
            "cost_per_1k_input": 0.003,
            "cost_per_1k_output": 0.015,
        },
        "claude-haiku-3.5": {
            "max_tokens": 10000,
            "cost_per_1k_input": 0.00025,
            "cost_per_1k_output": 0.00125,
        },
        "claude-haiku-3": {
            "max_tokens": 10000,
            "cost_per_1k_input": 0.00025,
            "cost_per_1k_output": 0.00125,
        },
    }

    def __init__(self, api_key: str = None, model_name: str = "claude-3-5-sonnet-20241022", **kwargs):
        super().__init__(model_name, **kwargs)

        # API 키 설정
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        if not self.api_key:
            raise ProviderConfigError("ANTHROPIC_API_KEY가 설정되지 않았습니다")

        # 모델 검증
        if model_name not in self.SUPPORTED_MODELS:
            raise ProviderConfigError(f"지원하지 않는 모델: {model_name}")

        # 클라이언트 초기화
        try:
            self.client = anthropic.Anthropic(api_key=self.api_key)
        except Exception as e:
            raise ProviderConfigError(f"Claude 클라이언트 초기화 실패: {e}")

        # 모델 정보 설정
        model_config = self.SUPPORTED_MODELS[model_name]
        self._model_info = ModelInfo(
            name=model_name,
            provider="anthropic",
            type=ProviderType.CLOUD_API,
            max_tokens=model_config["max_tokens"],
            cost_per_1k_tokens=model_config["cost_per_1k_output"],
            supports_streaming=True,
            supports_function_calling=False,
            metadata={
                "cost_per_1k_input": model_config["cost_per_1k_input"],
                "cost_per_1k_output": model_config["cost_per_1k_output"]
            }
        )

    def chat(self, messages: List[ChatMessage], **kwargs) -> ChatResponse:
        """Claude와 채팅"""

        if not self.is_available():
            raise ProviderUnavailableError("Claude API가 사용 불가능합니다")

        # 메시지 형식 변환
        anthropic_messages = []
        for msg in messages:
            if msg.role in ["user", "assistant"]:
                anthropic_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })

        # API 호출 파라미터 설정
        max_tokens = kwargs.get("max_tokens", 2000)
        temperature = kwargs.get("temperature", 0.7)

        start_time = time.time()

        try:
            response = self.client.messages.create(
                model=self.model_name,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=anthropic_messages
            )

            response_time = time.time() - start_time

            # 응답 처리
            content = response.content[0].text

            # 토큰 사용량 (Claude API는 토큰 사용량을 반환하지 않으므로 추정)
            input_tokens = sum(len(msg.content.split()) for msg in messages) * 1.3  # 대략적 추정
            output_tokens = len(content.split()) * 1.3

            token_usage = {
                "input_tokens": int(input_tokens),
                "output_tokens": int(output_tokens)
            }

            # 비용 계산
            cost_estimate = self._calculate_cost(token_usage)

            return ChatResponse(
                content=content,
                model_info=self._model_info,
                token_usage=token_usage,
                cost_estimate=cost_estimate,
                response_time=response_time,
                metadata={"raw_response": response}
            )

        except anthropic.APIError as e:
            raise ProviderError(f"Claude API 오류: {e}")
        except Exception as e:
            raise ProviderError(f"예상치 못한 오류: {e}")

    def get_model_info(self) -> ModelInfo:
        """모델 정보 반환"""
        return self._model_info

    def is_available(self) -> bool:
        """Claude API 사용 가능 여부 확인"""
        try:
            # 간단한 테스트 호출
            self.client.messages.create(
                model=self.model_name,
                max_tokens=1,
                messages=[{"role": "user", "content": "test"}]
            )
            return True
        except:
            return False

    def estimate_cost(self, messages: List[ChatMessage]) -> float:
        """비용 추정"""
        input_tokens = sum(len(msg.content.split()) for msg in messages) * 1.3
        output_tokens = 100  # 예상 출력 토큰 (기본값)

        return self._calculate_cost({
            "input_tokens": int(input_tokens),
            "output_tokens": int(output_tokens)
        })

    def _calculate_cost(self, token_usage: Dict[str, int]) -> float:
        """토큰 사용량 기반 비용 계산"""
        model_config = self.SUPPORTED_MODELS[self.model_name]

        input_cost = (token_usage["input_tokens"] / 1000) * model_config["cost_per_1k_input"]
        output_cost = (token_usage["output_tokens"] / 1000) * model_config["cost_per_1k_output"]

        return input_cost + output_cost

    def validate_config(self) -> bool:
        """설정 유효성 검증"""
        if not self.api_key:
            return False

        if self.model_name not in self.SUPPORTED_MODELS:
            return False

        return True

    def get_supported_features(self) -> List[str]:
        """지원하는 기능 목록"""
        return ["chat", "streaming", "cost_estimation"]