#!/bin/bash
# AI Memory 편의 실행 스크립트

# 현재 디렉토리에서 실행
cd "$(dirname "$0")"

# Python 가상환경 활성화 (있다면)
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
fi

# 메인 CLI 실행
python ai_memory_cli.py "$@"