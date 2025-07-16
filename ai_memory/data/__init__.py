"""
데이터 모델 정의
"""
from datetime import datetime
from .models import (
    MemoryType,
    ConversationTurn,
    Conversation,
    MemoryItem,
    UserProfile,
    SearchResult
)


__all__ = [
    'MemoryType',
    'ConversationTurn',
    'Conversation',
    'MemoryItem',
    'UserProfile',
    'SearchResult'
]

# 팩토리 함수들
def create_conversation(session_id: str, title: str = None) -> Conversation:
    """새로운 대화 세션 생성"""
    return Conversation(
        turns=[],
        session_id=session_id,
        start_time=datetime.now(),
        title=title
    )

def create_memory_item(content: str, memory_type: MemoryType, **kwargs) -> MemoryItem:
    """새로운 메모리 아이템 생성"""
    return MemoryItem(
        content=content,
        memory_type=memory_type,
        timestamp=datetime.now(),
        **kwargs
    )