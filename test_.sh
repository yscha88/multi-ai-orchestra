#!/bin/bash
echo "🧪 AI Memory 통합 테스트 시작..."

# 1. 사용 가능한 Provider 확인
echo "1. Provider 목록"
python ai_memory_cli.py --list-providers

# 2. 메모리 통계
echo "2. 메모리 통계"
python ai_memory_cli.py --stats

# 3. CLI 모드 테스트 (Ollama)
echo "3. CLI 모드 테스트"
python ai_memory_cli.py --provider ollama "안녕하세요! 간단한 테스트입니다."

# 4. 대화형 모드는 수동으로 테스트
echo "4. 대화형 모드 테스트는 수동으로 실행:"
echo "   python ai_memory_cli.py --interactive --provider ollama"

echo "🎉 통합 테스트 완료!"