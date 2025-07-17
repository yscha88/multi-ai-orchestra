# ===== adapters/interfaces/base_interface_adapter.py =====
"""
기본 인터페이스 어댑터
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
from ports.orchestrator_ports import BaseOrchestrator
from application.services.session_manager import SessionManagerService


class BaseInterfaceAdapter(ABC):
    """기본 인터페이스 어댑터"""

    def __init__(self, session_manager: SessionManagerService, **kwargs):
        self.session_manager = session_manager
        self.config = kwargs

    @abstractmethod
    def run(self, *args, **kwargs):
        """인터페이스 실행"""
        pass

    def get_info(self) -> Dict[str, Any]:
        """인터페이스 정보 반환"""
        return {
            "interface": self.__class__.__name__,
            "session_manager": str(self.session_manager.__class__.__name__)
        }