# ===== adapters/storage/memory_repository_impl.py =====
"""
메모리 저장소 구현 (기존 MemoryManager 리팩터링)
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import time

from ports.memory_ports import MemoryRepository, SearchService
from core.shared.models import (
    Conversation, ConversationTurn, MemoryItem, MemoryType,
    UserProfile, SearchResult
)
from infrastructure.utils.file_utils import ensure_directory, load_json_file, save_json_file
from infrastructure.utils.search_utils import extract_keywords, calculate_relevance


class FileBasedMemoryRepository(MemoryRepository):
    """파일 기반 메모리 저장소 (기존 MemoryManager 리팩터링)"""

    def __init__(self, base_dir: Path = None):
        """
        Args:
            base_dir: 메모리 저장 기본 디렉토리 (기본값: ./orchestra_memory)
        """
        self.base_dir = base_dir or Path("orchestra_memory")
        self.personal_dir = self.base_dir / "personal"
        self.shared_dir = self.base_dir / "shared"

        # 하위 디렉토리
        self.sessions_dir = self.personal_dir / "work-sessions"
        self.notes_dir = self.personal_dir / "my-notes"
        self.patterns_dir = self.personal_dir / "personal-patterns"
        self.profile_file = self.personal_dir / "user-profile.json"

        # 디렉토리 생성
        self._ensure_directories()

        # 캐시 (기존 코드 유지)
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

    # ===== MemoryRepository 인터페이스 구현 =====

    def save_conversation(self, conversation: Conversation) -> bool:
        """대화 세션 저장 (기존 로직 유지)"""
        try:
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
                "orchestrator_type": conversation.orchestrator_type,  # Phase 1 추가
                "task_complexity": conversation.task_complexity,      # Phase 1 추가
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
            return True
        except Exception as e:
            print(f"⚠️ 대화 저장 실패: {e}")
            return False

    def load_conversation(self, session_id: str) -> Optional[Conversation]:
        """특정 대화 로드"""
        try:
            # 세션 ID로 파일 찾기
            for session_file in self.sessions_dir.glob("*.json"):
                try:
                    data = load_json_file(session_file)
                    if data.get("session_id") == session_id:
                        return self._json_to_conversation(data)
                except Exception:
                    continue
            return None
        except Exception as e:
            print(f"⚠️ 대화 로드 실패: {e}")
            return None

    def load_recent_conversations(self, limit: int = 5) -> List[Conversation]:
        """최근 대화 기록 로드 (기존 로직 개선)"""
        if self._is_cache_valid() and self._recent_conversations_cache:
            return self._recent_conversations_cache[:limit]

        conversations = []

        try:
            # 최근 세션 파일들 가져오기
            session_files = sorted(
                [f for f in self.sessions_dir.glob("*.json") if f.is_file()],
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )[:limit * 2]  # 여유있게 더 많이 가져와서 오류 대비

            for session_file in session_files:
                try:
                    if session_file.stat().st_size == 0:
                        continue

                    data = load_json_file(session_file)
                    if not data:
                        continue

                    conversation = self._json_to_conversation(data)
                    if conversation:
                        conversations.append(conversation)

                    if len(conversations) >= limit:
                        break

                except Exception as e:
                    print(f"⚠️ 세션 파일 로드 실패 {session_file}: {e}")
                    continue

        except Exception as e:
            print(f"⚠️ 세션 파일 목록 조회 실패: {e}")

        self._recent_conversations_cache = conversations
        self._cache_timestamp = datetime.now()
        return conversations

    def save_memory_item(self, item: MemoryItem) -> bool:
        """메모리 아이템 저장 (신규)"""
        try:
            # 메모리 타입별 디렉토리 선택
            if item.memory_type == MemoryType.NOTE:
                target_dir = self.notes_dir
            elif item.memory_type == MemoryType.PATTERN:
                target_dir = self.patterns_dir
            else:
                target_dir = self.personal_dir / "misc"
                ensure_directory(target_dir)

            # 파일명 생성
            timestamp = item.timestamp.strftime("%Y%m%d_%H%M%S")
            filename = f"{item.memory_type.value}_{timestamp}_{item.item_id[:8]}.json"
            filepath = target_dir / filename

            # JSON 데이터 생성
            item_data = {
                "item_id": item.item_id,
                "content": item.content,
                "memory_type": item.memory_type.value,
                "timestamp": item.timestamp.isoformat(),
                "relevance_score": item.relevance_score,
                "tags": item.tags,
                "metadata": item.metadata
            }

            save_json_file(filepath, item_data)
            return True
        except Exception as e:
            print(f"⚠️ 메모리 아이템 저장 실패: {e}")
            return False

    def load_memory_items(self, memory_types: List[MemoryType] = None) -> List[MemoryItem]:
        """메모리 아이템들 로드 (신규)"""
        items = []
        try:
            # 검색할 디렉토리들 결정
            search_dirs = []
            if not memory_types:
                search_dirs = [self.notes_dir, self.patterns_dir, self.personal_dir / "misc"]
            else:
                for memory_type in memory_types:
                    if memory_type == MemoryType.NOTE:
                        search_dirs.append(self.notes_dir)
                    elif memory_type == MemoryType.PATTERN:
                        search_dirs.append(self.patterns_dir)

            # 각 디렉토리에서 아이템들 로드
            for search_dir in search_dirs:
                if search_dir.exists():
                    for item_file in search_dir.glob("*.json"):
                        try:
                            data = load_json_file(item_file)
                            item = self._json_to_memory_item(data)
                            if item:
                                items.append(item)
                        except Exception:
                            continue

        except Exception as e:
            print(f"⚠️ 메모리 아이템 로드 실패: {e}")

        return items

    def save_user_profile(self, profile: UserProfile) -> bool:
        """사용자 프로필 저장 (기존 로직 유지)"""
        try:
            profile_data = {
                "name": profile.name,
                "coding_style": profile.coding_style,
                "preferred_languages": profile.preferred_languages,
                "ide": profile.ide,
                "common_patterns": profile.common_patterns,
                # Phase 1 추가
                "preferred_orchestrator": profile.preferred_orchestrator,
                "interaction_style": profile.interaction_style,
                "metadata": profile.metadata
            }

            save_json_file(self.profile_file, profile_data)
            self._user_profile_cache = profile
            self._cache_timestamp = datetime.now()
            return True
        except Exception as e:
            print(f"⚠️ 프로필 저장 실패: {e}")
            return False

    def load_user_profile(self, user_id: str = "default") -> UserProfile:
        """사용자 프로필 로드 (기존 로직 개선)"""
        if self._is_cache_valid() and self._user_profile_cache:
            return self._user_profile_cache

        profile = UserProfile()  # 기본 프로필

        if self.profile_file.exists():
            try:
                data = load_json_file(self.profile_file)

                if data:
                    profile = UserProfile(
                        name=data.get("name", "사용자"),
                        coding_style=data.get("coding_style", "Clean Code 선호"),
                        preferred_languages=data.get("preferred_languages", ["Python"]),
                        ide=data.get("ide", "PyCharm"),
                        common_patterns=data.get("common_patterns", []),
                        # Phase 1 추가
                        preferred_orchestrator=data.get("preferred_orchestrator"),
                        interaction_style=data.get("interaction_style", "balanced"),
                        metadata=data.get("metadata", {})
                    )

            except Exception as e:
                print(f"⚠️ 프로필 로드 실패: {e}")
                profile = UserProfile()

        self._user_profile_cache = profile
        self._cache_timestamp = datetime.now()
        return profile

    # ===== 헬퍼 메서드들 =====

    def _json_to_conversation(self, data: Dict[str, Any]) -> Optional[Conversation]:
        """JSON 데이터를 Conversation 객체로 변환"""
        try:
            turns = []
            for turn_data in data.get("turns", []):
                turn = ConversationTurn(
                    user_message=turn_data.get("user_message", ""),
                    assistant_message=turn_data.get("assistant_message", ""),
                    timestamp=datetime.fromisoformat(turn_data.get("timestamp", datetime.now().isoformat())),
                    metadata=turn_data.get("metadata", {})
                )
                turns.append(turn)

            conversation = Conversation(
                turns=turns,
                session_id=data.get("session_id", "unknown"),
                start_time=datetime.fromisoformat(data.get("start_time", datetime.now().isoformat())),
                end_time=datetime.fromisoformat(data["end_time"]) if data.get("end_time") else None,
                title=data.get("title"),
                # Phase 1 추가
                orchestrator_type=data.get("orchestrator_type"),
                task_complexity=data.get("task_complexity"),
                metadata=data.get("metadata", {})
            )

            return conversation
        except Exception as e:
            print(f"⚠️ Conversation 변환 실패: {e}")
            return None

    def _json_to_memory_item(self, data: Dict[str, Any]) -> Optional[MemoryItem]:
        """JSON 데이터를 MemoryItem 객체로 변환"""
        try:
            return MemoryItem(
                item_id=data.get("item_id", ""),
                content=data.get("content", ""),
                memory_type=MemoryType(data.get("memory_type", MemoryType.NOTE.value)),
                timestamp=datetime.fromisoformat(data.get("timestamp", datetime.now().isoformat())),
                relevance_score=data.get("relevance_score", 0.0),
                tags=data.get("tags", []),
                metadata=data.get("metadata", {})
            )
        except Exception as e:
            print(f"⚠️ MemoryItem 변환 실패: {e}")
            return None

    # ===== 편의 메서드들 (기존 MemoryManager에서 이동) =====

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

    def cleanup_old_conversations(self, days_old: int = 30) -> int:
        """오래된 대화 기록 정리"""
        cutoff_date = datetime.now() - timedelta(days=days_old)
        deleted_count = 0

        try:
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

        except Exception as e:
            print(f"⚠️ 정리 작업 실패: {e}")

        return deleted_count