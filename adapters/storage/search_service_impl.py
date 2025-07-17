# ===== adapters/storage/search_service_impl.py =====
"""
검색 서비스 구현 (기존 검색 로직 개선)
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


class KeywordSearchService(SearchService):
    """키워드 기반 검색 서비스 (기존 로직 개선)"""

    def __init__(self, memory_repository: MemoryRepository):
        self.memory_repository = memory_repository

    def search_memories(self, query: str, memory_types: List[MemoryType] = None,
                        limit: int = 10) -> SearchResult:
        """메모리 검색 (기존 로직 개선)"""
        start_time = time.time()

        if memory_types is None:
            memory_types = [MemoryType.CONVERSATION, MemoryType.NOTE, MemoryType.PATTERN]

        results = []

        # 대화 기록 검색
        if MemoryType.CONVERSATION in memory_types:
            conversations = self.memory_repository.load_recent_conversations(20)
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

        # 다른 메모리 타입 검색
        other_types = [mt for mt in memory_types if mt != MemoryType.CONVERSATION]
        if other_types:
            memory_items = self.memory_repository.load_memory_items(other_types)
            for item in memory_items:
                relevance = calculate_relevance(query, item.content)
                if relevance > 0.1:
                    item.relevance_score = relevance
                    results.append(item)

        # 관련성 점수로 정렬
        results.sort(key=lambda x: x.relevance_score, reverse=True)

        search_time = time.time() - start_time

        return SearchResult(
            items=results[:limit],
            query=query,
            total_found=len(results),
            search_time=search_time,
            search_strategy="keyword"
        )

    def search_conversations(self, query: str, limit: int = 5) -> List[Conversation]:
        """대화 검색"""
        conversations = self.memory_repository.load_recent_conversations(20)
        relevant_conversations = []

        for conv in conversations:
            # 제목이나 대화 내용에서 검색
            title_match = conv.title and query.lower() in conv.title.lower()
            content_match = any(
                query.lower() in turn.user_message.lower() or
                query.lower() in turn.assistant_message.lower()
                for turn in conv.turns
            )

            if title_match or content_match:
                relevant_conversations.append(conv)

        return relevant_conversations[:limit]

    def find_similar_memories(self, reference_item: MemoryItem, limit: int = 5) -> List[MemoryItem]:
        """유사한 메모리 찾기 (간단한 구현)"""
        all_items = self.memory_repository.load_memory_items()
        similar_items = []

        for item in all_items:
            if item.item_id != reference_item.item_id:
                # 태그 유사도 계산
                tag_similarity = len(set(item.tags) & set(reference_item.tags)) / \
                                 max(len(set(item.tags) | set(reference_item.tags)), 1)

                # 내용 유사도 계산
                content_similarity = calculate_relevance(reference_item.content, item.content)

                # 전체 유사도
                total_similarity = (tag_similarity * 0.3 + content_similarity * 0.7)

                if total_similarity > 0.2:  # 임계값
                    item.relevance_score = total_similarity
                    similar_items.append(item)

        similar_items.sort(key=lambda x: x.relevance_score, reverse=True)
        return similar_items[:limit]