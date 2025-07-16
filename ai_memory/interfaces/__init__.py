"""
사용자 인터페이스 관리
"""

from .base import BaseInterface
from .cli import CLIInterface
from .interactive import InteractiveInterface

__all__ = [
    'BaseInterface',
    'CLIInterface',
    'InteractiveInterface'
]

# Interface 팩토리
def create_interface(interface_type: str, memory_manager, provider, **kwargs):
    """인터페이스 생성"""

    interfaces = {
        'cli': CLIInterface,
        'interactive': InteractiveInterface,
    }

    if interface_type not in interfaces:
        available = ", ".join(interfaces.keys())
        raise ValueError(f"지원하지 않는 interface: {interface_type}. 사용 가능: {available}")

    return interfaces[interface_type](memory_manager, provider, **kwargs)