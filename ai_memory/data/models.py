"""
Claude Memory 데이터 모델 정의
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum


class MemoryType(Enum):
    """메모리 타입 정의"""
    CONVERSATION = "conversation"
    PATTERN = "pattern"
    NOTE = "note"
    PROJECT_CONTEXT = "project_context"
    USER_PROFILE = "user_profile"


@dataclass
class ConversationTurn:
    """대화 한 턴 (질문-답변 쌍)"""
    user_message: str
    assistant_message: str
    timestamp: datetime
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class Conversation:
    """대화 세션"""
    turns: List[ConversationTurn]
    session_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    title: Optional[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    def add_turn(self, user_msg: str, assistant_msg: str):
        """새로운 대화 턴 추가"""
        turn = ConversationTurn(
            user_message=user_msg,
            assistant_message=assistant_msg,
            timestamp=datetime.now()
        )
        self.turns.append(turn)

    def get_summary(self) -> str:
        """대화 요약 생성"""
        if not self.turns:
            return "빈 대화"

        first_turn = self.turns[0]
        return f"{first_turn.user_message[:50]}..." if len(first_turn.user_message) > 50 else first_turn.user_message


@dataclass
class MemoryItem:
    """메모리 아이템"""
    content: str
    memory_type: MemoryType
    timestamp: datetime
    relevance_score: float = 0.0
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class UserProfile:
    """사용자 프로필"""
    name: str = "사용자"
    coding_style: str = "Clean Code 선호"
    preferred_languages: List[str] = None
    ide: str = "PyCharm"
    common_patterns: List[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.preferred_languages is None:
            self.preferred_languages = ["Python"]
        if self.common_patterns is None:
            self.common_patterns = []
        if self.metadata is None:
            self.metadata = {}


@dataclass
class SearchResult:
    """검색 결과"""
    items: List[MemoryItem]
    query: str
    total_found: int
    search_time: float
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}