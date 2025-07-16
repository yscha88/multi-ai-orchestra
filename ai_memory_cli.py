#!/usr/bin/env python3
"""
AI Memory CLI - 메인 실행 파일 (수정된 버전)
"""

import sys
import os
import argparse
from pathlib import Path

# 패키지 경로 추가
sys.path.insert(0, '.')

# .env 파일 로드 (python-dotenv 사용)
try:
    from dotenv import load_dotenv

    # 여러 경로에서 .env 파일 찾기
    env_paths = [
        Path('../multi-ai-orchestra/ai_memory/config/.env'),
        Path('.ai_memory/config/.env'),
        Path('.env'),
        Path('./.env')
    ]

    env_loaded = False
    for env_path in env_paths:
        if env_path.exists():
            load_dotenv(env_path)
            print(f"✅ .env 파일 로드됨: {env_path}")
            env_loaded = True
            break

    if not env_loaded:
        print("⚠️  .env 파일을 찾을 수 없습니다.")
        print("   다음 경로들을 확인했습니다:")
        for path in env_paths:
            print(f"   - {path}")

except ImportError:
    print("⚠️  python-dotenv가 설치되지 않았습니다.")
    print("   설치 명령: pip install python-dotenv")
    print("   .env 파일 대신 환경변수를 사용하세요.")

from ai_memory.core import MemoryManager
from ai_memory.providers import create_provider, AVAILABLE_PROVIDERS
from ai_memory.interfaces import create_interface


def parse_arguments():
    """명령줄 인자 파싱"""
    parser = argparse.ArgumentParser(
        description="Claude Memory - 기억을 가진 AI 어시스턴트",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  python ai_memory_cli.py "FastAPI 프로젝트 어떻게 시작하지?"
  python ai_memory_cli.py --interactive
  python ai_memory_cli.py --provider ollama "로컬 LLM으로 질문"
  python ai_memory_cli.py --interactive --provider claude
        """
    )

    parser.add_argument(
        'query',
        nargs='?',
        help='질문 (대화형 모드가 아닌 경우 필수)'
    )

    parser.add_argument(
        '--interactive', '-i',
        action='store_true',
        help='대화형 모드 시작'
    )

    parser.add_argument(
        '--provider', '-p',
        choices=list(AVAILABLE_PROVIDERS.keys()),
        default='claude',
        help='AI Provider 선택 (기본값: claude)'
    )

    parser.add_argument(
        '--memory-dir', '-m',
        type=Path,
        default=Path('../multi-ai-orchestra/claude_memory'),
        help='메모리 저장 디렉토리 (기본값: ./claude_memory)'
    )

    parser.add_argument(
        '--model',
        help='사용할 모델 이름 (Provider별 기본값 사용)'
    )

    parser.add_argument(
        '--max-context',
        type=int,
        default=5,
        help='최대 컨텍스트 턴 수 (기본값: 5)'
    )

    parser.add_argument(
        '--list-providers',
        action='store_true',
        help='사용 가능한 Provider 목록 표시'
    )

    parser.add_argument(
        '--stats',
        action='store_true',
        help='메모리 통계 표시'
    )

    parser.add_argument(
        '--check-env',
        action='store_true',
        help='환경변수 설정 상태 확인'
    )

    return parser.parse_args()


def check_environment():
    """환경변수 설정 상태 확인"""
    print("🔍 환경변수 확인:")
    print()

    # ANTHROPIC_API_KEY 확인
    anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')

    if anthropic_api_key:
        # 보안을 위해 앞 4자리와 뒤 4자리만 표시
        masked_key = f"{anthropic_api_key[:4]}...{anthropic_api_key[-4:]}" if len(anthropic_api_key) > 8 else "****"
        print(f"✅ ANTHROPIC_API_KEY: {masked_key}")
    else:
        print("❌ ANTHROPIC_API_KEY: 설정되지 않음")
        print("   해결방법:")
        print("   1. ai_memory/config/.env 파일에 추가")
        print("   2. 또는 export ANTHROPIC_API_KEY='your-key-here'")

    print()

    # .env 파일 존재 확인
    env_files = [
        Path('../multi-ai-orchestra/ai_memory/config/.env'),
        Path('.ai_memory/config/.env'),
        Path('.env')
    ]

    print("📄 .env 파일 상태:")
    for env_file in env_files:
        if env_file.exists():
            print(f"✅ {env_file} (존재)")
        else:
            print(f"❌ {env_file} (없음)")

    print()

    # python-dotenv 설치 확인
    try:
        import dotenv
        print("✅ python-dotenv: 설치됨")
    except ImportError:
        print("❌ python-dotenv: 설치되지 않음")
        print("   설치 명령: pip install python-dotenv")


def list_providers():
    """사용 가능한 Provider 목록 표시"""
    print("📋 사용 가능한 AI Provider:")
    print()

    for name, info in AVAILABLE_PROVIDERS.items():
        print(f"🔹 {name}")
        print(f"   설명: {info['description']}")
        print(f"   타입: {info['type'].value}")
        print(f"   비용: {info['cost']}")
        print(f"   요구사항: {', '.join(info['requires'])}")
        print()


def show_stats(memory_manager):
    """메모리 통계 표시"""
    stats = memory_manager.get_memory_stats()

    print("📊 Claude Memory 통계:")
    print(f"   총 대화: {stats['total_conversations']}개")
    print(f"   총 턴: {stats['total_turns']}개")
    print(f"   최근 대화: {stats['newest_conversation']}")
    print(f"   저장 경로: {stats['storage_path']}")


def create_components(args):
    """메모리 매니저와 프로바이더 생성"""

    # 메모리 매니저 생성
    memory_manager = MemoryManager(base_dir=args.memory_dir)

    # 프로바이더 생성
    provider_kwargs = {}
    if args.model:
        provider_kwargs['model_name'] = args.model

    # Claude의 경우 API 키 확인
    if args.provider == 'claude':
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            print("❌ ANTHROPIC_API_KEY가 설정되지 않았습니다.")
            print()
            print("해결방법:")
            print("1. ai_memory/config/.env 파일에 추가:")
            print("   ANTHROPIC_API_KEY=your-api-key-here")
            print()
            print("2. 또는 환경변수로 설정:")
            print("   export ANTHROPIC_API_KEY='your-api-key-here'")
            print()
            print("3. 환경변수 확인:")
            print("   python ai_memory_cli.py --check-env")
            sys.exit(1)
        provider_kwargs['api_key'] = api_key
    elif args.provider == 'openai':
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            print("❌ OPENAI_API_KEY 설정되지 않았습니다.")
            print()
            print("해결방법:")
            print("1. ai_memory/config/.env 파일에 추가:")
            print("   OPENAI_API_KEY=your-api-key-here")
            print()
            print("2. 또는 환경변수로 설정:")
            print("   export OPENAI_API_KEY='your-api-key-here'")
            print()
            print("3. 환경변수 확인:")
            print("   python ai_memory_cli.py --check-env")
            sys.exit(1)
        provider_kwargs['api_key'] = api_key

    try:
        provider = create_provider(args.provider, **provider_kwargs)

        # Provider 사용 가능 여부 확인
        if not provider.is_available():
            print(f"❌ {args.provider} Provider를 사용할 수 없습니다.")
            if args.provider == 'ollama':
                print("   Ollama 서버가 실행 중인지 확인하세요:")
                print("   ollama serve")
            elif args.provider == 'claude':
                print("   API 키가 올바른지 확인하세요:")
                print("   python ai_memory_cli.py --check-env")
            sys.exit(1)

        return memory_manager, provider

    except Exception as e:
        print(f"❌ Provider 생성 실패: {e}")
        if args.provider == 'claude':
            print("   API 키 확인: python ai_memory_cli.py --check-env")
        sys.exit(1)


def main():
    """메인 함수"""
    args = parse_arguments()

    # 특별한 명령어 처리
    if args.check_env:
        check_environment()
        return

    if args.list_providers:
        list_providers()
        return

    # 컴포넌트 생성
    memory_manager, provider = create_components(args)

    # 통계 표시
    if args.stats:
        show_stats(memory_manager)
        return

    # 인터페이스 모드 결정
    if args.interactive:
        # 대화형 모드
        interface = create_interface(
            'interactive',
            memory_manager,
            provider,
            max_context_turns=args.max_context
        )
        interface.run()
    else:
        # CLI 모드
        if not args.query:
            print("❌ 질문을 입력하거나 --interactive 옵션을 사용하세요.")
            print("   도움말: python ai_memory_cli.py --help")
            sys.exit(1)

        interface = create_interface(
            'cli',
            memory_manager,
            provider,
            max_context_turns=args.max_context
        )

        response = interface.run(args.query)
        print(response)


if __name__ == "__main__":
    main()