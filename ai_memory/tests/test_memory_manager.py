#!/usr/bin/env python3
"""
MemoryManager 테스트
"""

import sys
from pathlib import Path
from datetime import datetime

# 패키지 경로 추가
sys.path.insert(0, '.')

from ai_memory.core import MemoryManager
from ai_memory.data import Conversation, UserProfile, MemoryType


def test_memory_manager():
    """MemoryManager 기본 기능 테스트"""
    print("🧪 MemoryManager 테스트 시작...")

    # 테스트용 디렉토리
    test_dir = Path("test_memory")
    memory_manager = MemoryManager(base_dir=test_dir)

    # 1. 사용자 프로필 테스트
    print("\n1. 사용자 프로필 테스트")
    profile = UserProfile(
        name="테스트 사용자",
        coding_style="TDD 선호",
        preferred_languages=["Python", "TypeScript"],
        ide="PyCharm"
    )

    memory_manager.save_user_profile(profile)
    loaded_profile = memory_manager.load_user_profile()

    print(f"✅ 프로필 저장/로드: {loaded_profile.name}")

    # 2. 대화 저장 테스트
    print("\n2. 대화 저장 테스트")
    conversation = Conversation(
        turns=[],
        session_id="test-session-1",
        start_time=datetime.now(),
        title="테스트 대화"
    )

    conversation.add_turn(
        "FastAPI 프로젝트 어떻게 시작하지?",
        "FastAPI 프로젝트를 시작하려면 먼저 가상환경을 만들고..."
    )

    conversation.add_turn(
        "데이터베이스 연결은 어떻게 해?",
        "SQLAlchemy를 사용해서 데이터베이스 연결을 설정할 수 있습니다..."
    )

    memory_manager.save_conversation(conversation)
    print("✅ 대화 저장 완료")

    # 3. 최근 대화 로드 테스트
    print("\n3. 최근 대화 로드 테스트")
    recent_convs = memory_manager.load_recent_conversations(limit=5)

    if recent_convs:
        print(f"✅ 최근 대화 {len(recent_convs)}개 로드")
        for i, conv in enumerate(recent_convs, 1):
            print(f"   {i}. {conv.title} - {len(conv.turns)}개 턴")
    else:
        print("❌ 최근 대화 없음")

    # 4. 검색 테스트
    print("\n4. 검색 테스트")
    search_result = memory_manager.search_memory("FastAPI")

    print(f"✅ 검색 결과: {search_result.total_found}개 발견")
    for item in search_result.items[:3]:
        print(f"   - {item.content[:50]}... (점수: {item.relevance_score:.2f})")

    # 5. 메모리 통계
    print("\n5. 메모리 통계")
    stats = memory_manager.get_memory_stats()
    print(f"✅ 총 대화: {stats['total_conversations']}개")
    print(f"✅ 총 턴: {stats['total_turns']}개")
    print(f"✅ 저장 경로: {stats['storage_path']}")

    print("\n🎉 모든 테스트 완료!")


if __name__ == "__main__":
    test_memory_manager()