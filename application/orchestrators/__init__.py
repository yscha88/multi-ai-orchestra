# ===== application/orchestrators/__init__.py =====
"""
오케스트레이터 구현들
Phase 1: 기본적인 오케스트레이터들
"""

from .base_orchestrator import BaseOrchestratorImpl
from .simple_orchestrator import SimpleOrchestrator
from .memory_orchestrator import MemoryOrchestrator
from .control_orchestrator import ControlOrchestrator
from .orchestrator_factory import OrchestratorFactoryImpl

__all__ = [
    'BaseOrchestratorImpl',
    'SimpleOrchestrator',
    'MemoryOrchestrator',
    'ControlOrchestrator',
    'OrchestratorFactoryImpl'
]

# TODO Phase 2: 고급 오케스트레이터들
# class PersonalityOrchestrator(BaseOrchestratorImpl):
#     """통합 관제인격 오케스트레이터"""
#     pass
#
# class CollaborationOrchestrator(BaseOrchestratorImpl):
#     """협업 중심 오케스트레이터"""
#     pass