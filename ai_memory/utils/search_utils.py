"""
검색 관련 유틸리티 함수들
"""

import re
from typing import List, Set


def extract_keywords(text: str) -> List[str]:
    """텍스트에서 키워드 추출"""
    # 간단한 키워드 추출 (향후 개선 가능)
    words = re.findall(r'\b\w+\b', text.lower())

    # 불용어 제거
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
        '이', '그', '저', '이것', '그것', '저것', '을', '를', '이', '가', '은', '는', '에서', '에게', '에',
        '어떻게', '왜', '언제', '어디서', '무엇을', '어떤', '그런', '이런', '저런'
    }

    keywords = [word for word in words if word not in stop_words and len(word) > 2]

    return keywords


def calculate_relevance(query: str, text: str) -> float:
    """쿼리와 텍스트 간의 관련성 점수 계산"""
    query_keywords = set(extract_keywords(query))
    text_keywords = set(extract_keywords(text))

    if not query_keywords:
        return 0.0

    # 교집합 / 합집합 (Jaccard similarity)
    intersection = query_keywords.intersection(text_keywords)
    union = query_keywords.union(text_keywords)

    if not union:
        return 0.0

    jaccard_score = len(intersection) / len(union)

    # 추가 가중치 (완전 일치 키워드에 높은 점수)
    exact_matches = len(intersection)
    exact_match_bonus = exact_matches * 0.1

    return min(jaccard_score + exact_match_bonus, 1.0)