"""
메모리 관리 중앙 시스템
"""

from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime, timedelta
import time

from ai_memory.data.models import (
    Conversation, ConversationTurn, MemoryItem, MemoryType,
    UserProfile, SearchResult
)
from ai_memory.utils.file_utils import ensure_directory, load_json_file, save_json_file
from ai_memory.utils.search_utils import extract_keywords, calculate_relevance


class MemoryManager:
    """메모리 저장, 검색, 관리를 담당하는 중앙 클래스"""

    def __init__(self, base_dir: Path = None):
        """
        Args:
            base_dir: 메모리 저장 기본 디렉토리 (기본값: ./claude_memory)
        """
        self.base_dir = base_dir or Path("claude_memory")
        self.personal_dir = self.base_dir / "personal"
        self.shared_dir = self.base_dir / "shared"

        # 하위 디렉토리
        self.sessions_dir = self.personal_dir / "work-sessions"
        self.notes_dir = self.personal_dir / "my-notes"
        self.patterns_dir = self.personal_dir / "personal-patterns"
        self.profile_file = self.personal_dir / "user-profile.json"

        # 디렉토리 생성
        self._ensure_directories()

        # 캐시
        self._user_profile_cache = None
        self._recent_conversations_cache = None
        self._cache_timestamp = None
        self._cache_ttl = 300  # 5분

    def _ensure_directories(self):
        """필요한 디렉토리들 생성"""
        directories = [
            self.sessions_dir,
            self.notes_dir,
            self.patterns_dir,
            self.shared_dir / "project-context",
            self.shared_dir / "coding-patterns",
            self.shared_dir / "common-issues",
            self.shared_dir / "team-decisions"
        ]

        for directory in directories:
            ensure_directory(directory)

    def _is_cache_valid(self) -> bool:
        """캐시가 유효한지 확인"""
        if self._cache_timestamp is None:
            return False

        return (datetime.now() - self._cache_timestamp).seconds < self._cache_ttl

    def _clear_cache(self):
        """캐시 초기화"""
        self._user_profile_cache = None
        self._recent_conversations_cache = None
        self._cache_timestamp = None

    # === 대화 관련 메서드들 ===

    def save_conversation(self, conversation: Conversation):
        """대화 세션 저장"""
        date_str = conversation.start_time.strftime("%Y-%m-%d")
        time_str = conversation.start_time.strftime("%H-%M-%S")

        filename = f"{date_str}-{time_str}-{conversation.session_id}.json"
        filepath = self.sessions_dir / filename

        # Conversation을 JSON 직렬화 가능한 형태로 변환
        conversation_data = {
            "session_id": conversation.session_id,
            "title": conversation.title,
            "start_time": conversation.start_time.isoformat(),
            "end_time": conversation.end_time.isoformat() if conversation.end_time else None,
            "turns": [
                {
                    "user_message": turn.user_message,
                    "assistant_message": turn.assistant_message,
                    "timestamp": turn.timestamp.isoformat(),
                    "metadata": turn.metadata
                }
                for turn in conversation.turns
            ],
            "metadata": conversation.metadata
        }

        save_json_file(filepath, conversation_data)
        self._clear_cache()  # 캐시 초기화

    def load_recent_conversations(self, limit: int = 5) -> List[Conversation]:
        """최근 대화 기록 로드 - 인코딩 문제 해결"""
        if self._is_cache_valid() and self._recent_conversations_cache:
            return self._recent_conversations_cache[:limit]

        conversations = []

        # 최근 세션 파일들 가져오기
        session_files = []
        try:
            session_files = sorted(
                [f for f in self.sessions_dir.glob("*.json") if f.is_file()],
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )[:limit * 2]  # 여유있게 더 많이 가져와서 오류 대비
        except Exception as e:
            print(f"⚠️ 세션 파일 목록 조회 실패: {e}")
            return []

        for session_file in session_files:
            try:
                # 파일 무결성 확인
                if session_file.stat().st_size == 0:
                    print(f"⚠️ 빈 파일 건너뛰기: {session_file}")
                    continue

                # JSON 파일 로드 (인코딩 문제 해결된 함수 사용)
                data = load_json_file(session_file)

                if not data:  # 빈 딕셔너리인 경우
                    print(f"⚠️ 빈 데이터 건너뛰기: {session_file}")
                    continue

                # 필수 필드 확인
                required_fields = ['session_id', 'start_time', 'turns']
                if not all(field in data for field in required_fields):
                    print(f"⚠️ 필수 필드 누락: {session_file}")
                    continue

                # JSON 데이터를 Conversation 객체로 변환
                turns = []
                for turn_data in data.get("turns", []):
                    try:
                        turn = ConversationTurn(
                            user_message=turn_data.get("user_message", ""),
                            assistant_message=turn_data.get("assistant_message", ""),
                            timestamp=datetime.fromisoformat(turn_data.get("timestamp", datetime.now().isoformat())),
                            metadata=turn_data.get("metadata", {})
                        )
                        turns.append(turn)
                    except Exception as e:
                        print(f"⚠️ 대화 턴 변환 실패: {e}")
                        continue

                conversation = Conversation(
                    turns=turns,
                    session_id=data.get("session_id", "unknown"),
                    start_time=datetime.fromisoformat(data.get("start_time", datetime.now().isoformat())),
                    end_time=datetime.fromisoformat(data["end_time"]) if data.get("end_time") else None,
                    title=data.get("title"),
                    metadata=data.get("metadata", {})
                )

                conversations.append(conversation)

                # 원하는 개수만큼 모았으면 중단
                if len(conversations) >= limit:
                    break

            except Exception as e:
                print(f"⚠️ 세션 파일 로드 실패 {session_file}: {e}")
                # 손상된 파일 백업
                try:
                    from ..utils.file_utils import backup_corrupted_file
                    backup_corrupted_file(session_file)
                except Exception:
                    pass
                continue

        self._recent_conversations_cache = conversations
        self._cache_timestamp = datetime.now()

        return conversations

    # === 사용자 프로필 관련 메서드들 ===

    def load_user_profile(self) -> UserProfile:
        """사용자 프로필 로드 - 인코딩 문제 해결"""
        if self._is_cache_valid() and self._user_profile_cache:
            return self._user_profile_cache

        profile = UserProfile()  # 기본 프로필

        if self.profile_file.exists():
            try:
                data = load_json_file(self.profile_file)

                if data:  # 빈 딕셔너리가 아닌 경우만
                    profile = UserProfile(
                        name=data.get("name", "사용자"),
                        coding_style=data.get("coding_style", "Clean Code 선호"),
                        preferred_languages=data.get("preferred_languages", ["Python", "JavaScript"]),
                        ide=data.get("ide", "PyCharm"),
                        common_patterns=data.get("common_patterns", []),
                        metadata=data.get("metadata", {})
                    )

            except Exception as e:
                print(f"⚠️ 프로필 로드 실패: {e}")
                # 기본 프로필 사용
                profile = UserProfile()

        self._user_profile_cache = profile
        self._cache_timestamp = datetime.now()

        return profile

    def save_user_profile(self, profile: UserProfile):
        """사용자 프로필 저장"""
        profile_data = {
            "name": profile.name,
            "coding_style": profile.coding_style,
            "preferred_languages": profile.preferred_languages,
            "ide": profile.ide,
            "common_patterns": profile.common_patterns,
            "metadata": profile.metadata
        }

        save_json_file(self.profile_file, profile_data)
        self._user_profile_cache = profile
        self._cache_timestamp = datetime.now()

    # === 검색 관련 메서드들 ===

    def search_memory(self, query: str, memory_types: List[MemoryType] = None,
                      limit: int = 10) -> SearchResult:
        """메모리 검색"""
        start_time = time.time()

        if memory_types is None:
            memory_types = [MemoryType.CONVERSATION, MemoryType.NOTE, MemoryType.PATTERN]

        results = []

        # 대화 기록 검색
        if MemoryType.CONVERSATION in memory_types:
            conversations = self.load_recent_conversations(20)  # 더 많이 로드해서 검색
            for conv in conversations:
                for turn in conv.turns:
                    relevance = calculate_relevance(query, turn.user_message + " " + turn.assistant_message)
                    if relevance > 0.1:  # 임계값
                        results.append(MemoryItem(
                            content=f"User: {turn.user_message}\nAssistant: {turn.assistant_message}",
                            memory_type=MemoryType.CONVERSATION,
                            timestamp=turn.timestamp,
                            relevance_score=relevance,
                            metadata={"session_id": conv.session_id, "title": conv.title}
                        ))

        # 노트 검색
        if MemoryType.NOTE in memory_types:
            # TODO: 노트 검색 로직 구현
            pass

        # 패턴 검색
        if MemoryType.PATTERN in memory_types:
            # TODO: 패턴 검색 로직 구현
            pass

        # 관련성 점수로 정렬
        results.sort(key=lambda x: x.relevance_score, reverse=True)

        search_time = time.time() - start_time

        return SearchResult(
            items=results[:limit],
            query=query,
            total_found=len(results),
            search_time=search_time
        )

    # === 편의 메서드들 ===

    def get_memory_stats(self) -> Dict[str, Any]:
        """메모리 통계 정보"""
        conversations = self.load_recent_conversations(100)

        total_turns = sum(len(conv.turns) for conv in conversations)
        total_sessions = len(conversations)

        if conversations:
            oldest_date = min(conv.start_time for conv in conversations)
            newest_date = max(conv.start_time for conv in conversations)
        else:
            oldest_date = newest_date = datetime.now()

        return {
            "total_conversations": total_sessions,
            "total_turns": total_turns,
            "oldest_conversation": oldest_date.isoformat(),
            "newest_conversation": newest_date.isoformat(),
            "storage_path": str(self.base_dir)
        }

    def cleanup_old_conversations(self, days_old: int = 30):
        """오래된 대화 기록 정리"""
        cutoff_date = datetime.now() - timedelta(days=days_old)

        deleted_count = 0
        for session_file in self.sessions_dir.glob("*.json"):
            try:
                data = load_json_file(session_file)
                start_time = datetime.fromisoformat(data["start_time"])

                if start_time < cutoff_date:
                    session_file.unlink()
                    deleted_count += 1

            except Exception as e:
                print(f"⚠️ 파일 정리 실패 {session_file}: {e}")

        if deleted_count > 0:
            self._clear_cache()

        return deleted_count