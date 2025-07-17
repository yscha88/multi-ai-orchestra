# ===== adapters/ai_providers/provider_factory.py =====
"""
Provider 팩토리 및 모델 선택기 (기존 코드 리팩터링)
"""

from typing import Dict, List, Any
from ports.ai_ports import AIProvider, ModelSelector
from core.shared.models import ModelInfo
from .claude_provider_adapter import ClaudeProviderAdapter
from .ollama_provider_adapter import OllamaProviderAdapter


class AIProviderFactory:
    """AI Provider 팩토리"""

    _providers = {
        'claude': ClaudeProviderAdapter,
        'ollama': OllamaProviderAdapter,
    }

    @classmethod
    def create_provider(cls, provider_type: str, **kwargs) -> AIProvider:
        """Provider 생성"""
        if provider_type not in cls._providers:
            available = ", ".join(cls._providers.keys())
            raise ValueError(f"지원하지 않는 provider: {provider_type}. 사용 가능: {available}")

        try:
            return cls._providers[provider_type](**kwargs)
        except Exception as e:
            raise ValueError(f"Provider 생성 실패 ({provider_type}): {e}")

    @classmethod
    def get_available_providers(cls) -> List[str]:
        """사용 가능한 Provider 목록"""
        return list(cls._providers.keys())

    @classmethod
    def register_provider(cls, provider_type: str, provider_class: type):
        """새로운 Provider 등록"""
        cls._providers[provider_type] = provider_class


class ModelSelectorImpl(ModelSelector):
    """모델 선택기 구현"""

    def __init__(self):
        self.provider_factory = AIProviderFactory()
        self.model_performance_history = {}

    def select_optimal_model(self, task_type: str, requirements: Dict[str, Any]) -> str:
        """최적 모델 선택"""
        # 기본 선택 로직
        if task_type == "coding":
            return "ollama:codellama"
        elif task_type == "reasoning":
            return "claude-3-5-sonnet-20241022"
        elif task_type == "quick_response":
            return "ollama:tinyllama"
        else:
            return "claude-3-5-sonnet-20241022"  # 기본값

    def get_available_models(self) -> List[ModelInfo]:
        """사용 가능한 모델 목록"""
        models = []

        # 각 Provider에서 모델 정보 수집
        for provider_type in self.provider_factory.get_available_providers():
            try:
                provider = self.provider_factory.create_provider(provider_type)
                if provider.is_available():
                    models.append(provider.get_model_info())
            except Exception:
                continue

        return models

    def evaluate_model_performance(self, model_name: str, task_type: str) -> float:
        """모델 성능 평가"""
        # TODO: 실제 성능 데이터 기반 평가 구현
        return 0.8  # 기본값

    def get_model_recommendations(self, context: Dict[str, Any]) -> List[str]:
        """모델 추천"""
        recommendations = []

        task_type = context.get("task_type", "general")
        user_preference = context.get("user_preference", "balanced")

        if task_type == "coding":
            recommendations = ["ollama:codellama", "claude-3-5-sonnet-20241022"]
        elif task_type == "reasoning":
            recommendations = ["claude-3-5-sonnet-20241022", "ollama:llama3.1"]
        elif user_preference == "cost_effective":
            recommendations = ["ollama:llama3.1", "ollama:tinyllama"]
        elif user_preference == "high_quality":
            recommendations = ["claude-3-5-sonnet-20241022"]
        else:
            recommendations = ["claude-3-5-sonnet-20241022", "ollama:llama3.1"]

        return recommendations