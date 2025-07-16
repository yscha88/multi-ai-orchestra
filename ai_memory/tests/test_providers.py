#!/usr/bin/env python3
"""
Provider 테스트
"""

import sys
import os
from pathlib import Path

# 패키지 경로 추가
sys.path.insert(0, '.')

from ai_memory.providers import (
    create_provider, ChatMessage, ClaudeProvider, OllamaProvider,
    AVAILABLE_PROVIDERS, ProviderConfigError
)


def test_claude_provider():
    """Claude Provider 테스트"""
    print("\n🔵 Claude Provider 테스트")

    # API 키 확인
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        print("⚠️  ANTHROPIC_API_KEY 환경변수가 설정되지 않아 건너뜀")
        return

    try:
        # Provider 생성
        provider = create_provider('claude', api_key=api_key)

        # 모델 정보 확인
        model_info = provider.get_model_info()
        print(f"✅ 모델: {model_info.name}")
        print(f"✅ 제공자: {model_info.provider}")
        print(f"✅ 타입: {model_info.type}")

        # 간단한 채팅 테스트
        messages = [
            ChatMessage(role="user", content="안녕하세요! 간단한 테스트입니다.")
        ]

        response = provider.chat(messages)
        print(f"✅ 응답: {response.content[:50]}...")
        print(f"✅ 토큰 사용량: {response.token_usage}")
        print(f"✅ 예상 비용: ${response.cost_estimate:.4f}")
        print(f"✅ 응답 시간: {response.response_time:.2f}초")

    except Exception as e:
        print(f"❌ Claude Provider 테스트 실패: {e}")


def test_ollama_provider():
    """Ollama Provider 테스트"""
    print("\n🟡 Ollama Provider 테스트")

    try:
        # Provider 생성
        provider = create_provider('ollama')

        # 사용 가능 여부 확인
        if not provider.is_available():
            print("⚠️  Ollama 서버가 실행되지 않아 건너뜀")
            return

        # 모델 정보 확인
        model_info = provider.get_model_info()
        print(f"✅ 모델: {model_info.name}")
        print(f"✅ 제공자: {model_info.provider}")
        print(f"✅ 타입: {model_info.type}")

        # 사용 가능한 모델 목록
        if hasattr(provider, 'get_available_models'):
            models = provider.get_available_models()
            print(f"✅ 사용 가능한 모델: {models[:3]}...")

        # 간단한 채팅 테스트
        messages = [
            ChatMessage(role="user", content="Hello! This is a simple test.")
        ]

        response = provider.chat(messages, max_tokens=100)
        print(f"✅ 응답: {response.content[:50]}...")
        print(f"✅ 토큰 사용량: {response.token_usage}")
        print(f"✅ 비용: ${response.cost_estimate:.4f} (무료)")
        print(f"✅ 응답 시간: {response.response_time:.2f}초")

    except Exception as e:
        print(f"❌ Ollama Provider 테스트 실패: {e}")


def test_provider_factory():
    """Provider 팩토리 테스트"""
    print("\n🔧 Provider 팩토리 테스트")

    # 사용 가능한 Provider 목록
    print("📋 사용 가능한 Provider:")
    for name, info in AVAILABLE_PROVIDERS.items():
        print(f"   {name}: {info['description']}")

    # 잘못된 Provider 타입
    try:
        create_provider('invalid_provider')
        print("❌ 잘못된 Provider 타입이 통과됨")
    except ProviderConfigError as e:
        print(f"✅ 잘못된 Provider 타입 적절히 처리: {e}")

    # 설정 기반 생성 테스트
    config = {
        'type': 'claude',
        'claude': {
            'api_key': 'test_key',
            'model_name': 'claude-3-5-sonnet-20241022'
        }
    }

    try:
        from ai_memory.providers import create_provider_from_config
        provider = create_provider_from_config(config)
        print(f"✅ 설정 기반 Provider 생성: {provider.get_model_info().name}")
    except Exception as e:
        print(f"⚠️  설정 기반 Provider 생성 (API 키 문제): {e}")


def main():
    """메인 테스트 함수"""
    print("🧪 Provider 테스트 시작...")

    test_provider_factory()
    test_claude_provider()
    test_ollama_provider()

    print("\n🎉 Provider 테스트 완료!")


if __name__ == "__main__":
    main()