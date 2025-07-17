# ===== application/orchestrators/orchestrator_factory.py =====
"""
오케스트레이터 팩토리 구현
"""

from typing import Dict, Any, List
from ports.orchestrator_ports import OrchestratorFactory, BaseOrchestrator
from core.shared.models import OrchestratorType
from .simple_orchestrator import SimpleOrchestrator
from .memory_orchestrator import MemoryOrchestrator
from .control_orchestrator import ControlOrchestrator


class OrchestratorFactoryImpl(OrchestratorFactory):
    """오케스트레이터 팩토리 구현"""

    def __init__(self, ai_providers: Dict[str, Any], memory_repository=None,
                 search_service=None, task_analyzer=None, coordinator=None):
        self.ai_providers = ai_providers
        self.memory_repository = memory_repository
        self.search_service = search_service
        self.task_analyzer = task_analyzer
        self.coordinator = coordinator

        # 등록된 오케스트레이터들
        self._orchestrators = {
            OrchestratorType.SIMPLE: SimpleOrchestrator,
            OrchestratorType.MEMORY: MemoryOrchestrator,
            OrchestratorType.CONTROL: ControlOrchestrator
        }

    def create_orchestrator(self, orchestrator_type: OrchestratorType,
                            config: Dict[str, Any]) -> BaseOrchestrator:
        """오케스트레이터 생성"""
        if orchestrator_type not in self._orchestrators:
            available = ", ".join([ot.value for ot in self._orchestrators.keys()])
            raise ValueError(f"지원하지 않는 오케스트레이터: {orchestrator_type.value}. 사용 가능: {available}")

        orchestrator_class = self._orchestrators[orchestrator_type]

        try:
            if orchestrator_type == OrchestratorType.SIMPLE:
                return orchestrator_class(self.ai_providers, config)
            elif orchestrator_type == OrchestratorType.MEMORY:
                if not self.memory_repository or not self.search_service:
                    raise ValueError("Memory orchestrator requires memory_repository and search_service")
                return orchestrator_class(self.ai_providers, self.memory_repository,
                                          self.search_service, config)
            elif orchestrator_type == OrchestratorType.CONTROL:
                if not self.task_analyzer or not self.coordinator:
                    raise ValueError("Control orchestrator requires task_analyzer and coordinator")
                return orchestrator_class(self.ai_providers, self.task_analyzer,
                                          self.coordinator, config)
            else:
                raise ValueError(f"구현되지 않은 오케스트레이터: {orchestrator_type.value}")

        except Exception as e:
            raise ValueError(f"오케스트레이터 생성 실패 ({orchestrator_type.value}): {e}")

    def get_available_orchestrators(self) -> List[OrchestratorType]:
        """사용 가능한 오케스트레이터 목록"""
        return list(self._orchestrators.keys())

    def register_orchestrator(self, orchestrator_type: OrchestratorType,
                              orchestrator_class: type) -> bool:
        """새로운 오케스트레이터 등록"""
        try:
            self._orchestrators[orchestrator_type] = orchestrator_class
            return True
        except Exception as e:
            print(f"⚠️ 오케스트레이터 등록 실패: {e}")
            return False
