# ===== adapters/interfaces/interface_factory.py =====
"""
인터페이스 팩토리
"""

from typing import Dict, Any
from .cli_interface_adapter import CLIInterfaceAdapter
from .interactive_interface_adapter import InteractiveInterfaceAdapter


class InterfaceFactory:
    """인터페이스 팩토리"""

    _interfaces = {
        'cli': CLIInterfaceAdapter,
        'interactive': InteractiveInterfaceAdapter,
    }

    @classmethod
    def create_interface(cls, interface_type: str, session_manager, **kwargs):
        """인터페이스 생성"""
        if interface_type not in cls._interfaces:
            available = ", ".join(cls._interfaces.keys())
            raise ValueError(f"지원하지 않는 interface: {interface_type}. 사용 가능: {available}")

        try:
            return cls._interfaces[interface_type](session_manager, **kwargs)
        except Exception as e:
            raise ValueError(f"인터페이스 생성 실패 ({interface_type}): {e}")

    @classmethod
    def get_available_interfaces(cls):
        """사용 가능한 인터페이스 목록"""
        return list(cls._interfaces.keys())

    @classmethod
    def register_interface(cls, interface_type: str, interface_class: type):
        """새로운 인터페이스 등록"""
        cls._interfaces[interface_type] = interface_class

