"""
AI Provider 관리 및 팩토리
"""

from .base import BaseProvider, ChatMessage, ChatResponse, ModelInfo, ProviderType
from .base import ProviderError, ProviderUnavailableError, ProviderConfigError
from .claude import ClaudeProvider
from .ollama import OllamaProvider

# Provider 팩토리
def create_provider(provider_type: str, **kwargs) -> BaseProvider:
    """Provider 타입에 따라 적절한 Provider 인스턴스 생성"""

    providers = {
        'claude': ClaudeProvider,
        'ollama': OllamaProvider,
    }

    if provider_type not in providers:
        available = ", ".join(providers.keys())
        raise ProviderConfigError(f"지원하지 않는 provider: {provider_type}. 사용 가능: {available}")

    try:
        return providers[provider_type](**kwargs)
    except Exception as e:
        raise ProviderConfigError(f"Provider 생성 실패 ({provider_type}): {e}")

# 설정 기반 Provider 생성
def create_provider_from_config(config: dict) -> BaseProvider:
    """설정 딕셔너리를 기반으로 Provider 생성"""

    provider_type = config.get('type')
    if not provider_type:
        raise ProviderConfigError("Provider 타입이 설정되지 않았습니다")

    # 타입별 설정 추출
    provider_config = config.get(provider_type, {})

    return create_provider(provider_type, **provider_config)

# 사용 가능한 Provider 목록
AVAILABLE_PROVIDERS = {
    'claude': {
        'name': 'Anthropic Claude',
        'type': ProviderType.CLOUD_API,
        'description': 'Claude API를 통한 고품질 AI 어시스턴트',
        'requires': ['api_key'],
        'cost': 'paid'
    },
    'ollama': {
        'name': 'Ollama',
        'type': ProviderType.LOCAL_LLM,
        'description': '로컬 실행 오픈소스 LLM',
        'requires': ['ollama_server'],
        'cost': 'free'
    }
}

__all__ = [
    # Base classes
    'BaseProvider',
    'ChatMessage',
    'ChatResponse',
    'ModelInfo',
    'ProviderType',

    # Exceptions
    'ProviderError',
    'ProviderUnavailableError',
    'ProviderConfigError',

    # Providers
    'ClaudeProvider',
    'OllamaProvider',

    # Factory functions
    'create_provider',
    'create_provider_from_config',

    # Constants
    'AVAILABLE_PROVIDERS',
]