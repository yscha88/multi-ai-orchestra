"""
인터페이스 기본 클래스
"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseInterface(ABC):
    """인터페이스 기본 클래스"""

    def __init__(self, memory_manager, provider, **kwargs):
        self.memory_manager = memory_manager
        self.provider = provider
        self.config = kwargs

    @abstractmethod
    def run(self):
        """인터페이스 실행"""
        pass

    def get_info(self) -> Dict[str, Any]:
        """인터페이스 정보 반환"""
        return {
            "interface": self.__class__.__name__,
            "provider": self.provider.get_model_info().name,
            "memory_path": str(self.memory_manager.base_dir)
        }