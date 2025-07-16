"""
스냅스를 가진 AI 어시스턴트
"""

__version__ = "0.1.0"
__author__ = "차요셉"
__description__ = "AI Assistant with Persistent Memory"

# Phase B 완료 - 핵심 컴포넌트
from .core import MemoryManager
from .data import Conversation, ConversationTurn, MemoryItem, MemoryType, UserProfile

# Phase C 완료 - Provider 시스템
from .providers import (
    create_provider, BaseProvider, ChatMessage, ChatResponse,
    ClaudeProvider, OllamaProvider, AVAILABLE_PROVIDERS
)

# TODO: 향후 구현 예정
# from .interfaces import CLIInterface, InteractiveInterface
# from .factory import create_ai_memory, create_interactive_session

__all__ = [
    # Core components (Phase B)
    'MemoryManager',
    'Conversation',
    'ConversationTurn',
    'MemoryItem',
    'MemoryType',
    'UserProfile',

    # Provider system (Phase C)
    'create_provider',
    'BaseProvider',
    'ChatMessage',
    'ChatResponse',
    'ClaudeProvider',
    'OllamaProvider',
    'AVAILABLE_PROVIDERS',

    # TODO: 향후 추가 예정
    # 'create_ai_memory',
    # 'create_interactive_session',
]

# 패키지 정보 업데이트
PACKAGE_INFO = {
    "name": "multi-ai-orchestra",
    "version": __version__,
    "description": __description__,
    "phases": {
        "A": "✅ Directory Structure & __init__.py",
        "B": "✅ MemoryManager Separation",
        "C": "✅ BaseProvider Interface",
        "D": "⏳ Interface Layer",
        "E": "⏳ Factory Functions & CLI Integration"
    }
}

def get_package_info():
    """패키지 정보 출력"""
    return PACKAGE_INFO