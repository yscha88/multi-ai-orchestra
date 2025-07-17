"""
포트 인터페이스 정의
Port-Adapter 패턴의 핵심: 먼저 인터페이스를 정의하고 나중에 구현
"""

from .memory_ports import MemoryRepository, SearchService
from .control_ports import TaskAnalysisService, OrchestrationService
from .ai_ports import AIProvider, ModelSelector

__all__ = [
    # Memory ports
    'MemoryRepository',
    'SearchService',

    # Control ports
    'TaskAnalysisService',
    'OrchestrationService',

    # AI ports
    'AIProvider',
    'ModelSelector'
]
