"""
AI Memory 핵심 컴포넌트들
"""

from .memory_manager import MemoryManager

# TODO: 다음 Phase에서 구현
# from .context_manager import ContextManager
# from .conversation_logger import ConversationLogger
# from .config_loader import ConfigLoader

__all__ = [
    'MemoryManager',
    # TODO: 다음 Phase에서 추가
    # 'ContextManager',
    # 'ConversationLogger',
    # 'ConfigLoader',
]

# 팩토리 함수
def create_memory_manager(base_dir=None):
    """MemoryManager 생성"""
    return MemoryManager(base_dir=base_dir)