# ===== ports/memory_ports.py =====
"""
메모리 관련 포트 인터페이스
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from core.shared.models import (
    Conversation, MemoryItem, UserProfile, SearchResult,
    MemoryType, SessionContext
)


class MemoryRepository(ABC):
    """메모리 저장소 인터페이스"""

    @abstractmethod
    def save_conversation(self, conversation: Conversation) -> bool:
        """대화 저장"""
        pass

    @abstractmethod
    def load_conversation(self, session_id: str) -> Optional[Conversation]:
        """특정 대화 로드"""
        pass

    @abstractmethod
    def load_recent_conversations(self, limit: int = 5) -> List[Conversation]:
        """최근 대화들 로드"""
        pass

    @abstractmethod
    def save_memory_item(self, item: MemoryItem) -> bool:
        """메모리 아이템 저장"""
        pass

    @abstractmethod
    def load_memory_items(self, memory_types: List[MemoryType] = None) -> List[MemoryItem]:
        """메모리 아이템들 로드"""
        pass

    @abstractmethod
    def save_user_profile(self, profile: UserProfile) -> bool:
        """사용자 프로필 저장"""
        pass

    @abstractmethod
    def load_user_profile(self, user_id: str = "default") -> UserProfile:
        """사용자 프로필 로드"""
        pass

    # TODO Phase 2: 고급 메모리 관리
    # @abstractmethod
    # def create_memory_connection(self, item1_id: str, item2_id: str, relationship: str) -> bool:
    #     """메모리 간 연결 생성"""
    #     pass

    # @abstractmethod
    # def update_memory_importance(self, item_id: str, importance: float) -> bool:
    #     """메모리 중요도 업데이트"""
    #     pass


class SearchService(ABC):
    """검색 서비스 인터페이스"""

    @abstractmethod
    def search_memories(self, query: str, memory_types: List[MemoryType] = None,
                        limit: int = 10) -> SearchResult:
        """메모리 검색"""
        pass

    @abstractmethod
    def search_conversations(self, query: str, limit: int = 5) -> List[Conversation]:
        """대화 검색"""
        pass

    @abstractmethod
    def find_similar_memories(self, reference_item: MemoryItem, limit: int = 5) -> List[MemoryItem]:
        """유사한 메모리 찾기"""
        pass

    # TODO Phase 2: 고급 검색 기능
    # @abstractmethod
    # def semantic_search(self, query: str, limit: int = 10) -> SearchResult:
    #     """의미적 검색"""
    #     pass

    # @abstractmethod
    # def concept_search(self, concepts: List[str], limit: int = 10) -> SearchResult:
    #     """개념 기반 검색"""
    #     pass