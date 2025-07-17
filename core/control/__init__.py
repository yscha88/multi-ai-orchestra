# ===== core/control/__init__.py =====
"""
관제 도메인 구현
Phase 1: 기본적인 작업 분석 및 오케스트레이션
"""

from .task_analyzer import SimpleTaskAnalyzer
from .orchestrator_coordinator import BasicOrchestratorCoordinator

__all__ = [
    'SimpleTaskAnalyzer',
    'BasicOrchestratorCoordinator'
]



# TODO Phase 2: 고급 관제 기능들
# class AdvancedWorkflowManager(OrchestrationService):
#     """고급 워크플로우 관리자"""
#     pass
#
# class QualityController:
#     """품질 관리자"""
#     pass
#
# class ResourceOptimizer:
#     """리소스 최적화기"""
#     pass