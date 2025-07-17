# ===== adapters/interfaces/__init__.py =====
"""
사용자 인터페이스 어댑터들 (기존 코드 리팩터링)
"""

from .cli_interface_adapter import CLIInterfaceAdapter
from .interactive_interface_adapter import InteractiveInterfaceAdapter
from .interface_factory import InterfaceFactory

__all__ = [
    'CLIInterfaceAdapter',
    'InteractiveInterfaceAdapter',
    'InterfaceFactory'
]

# TODO Phase 2: 추가 인터페이스
# class WebInterfaceAdapter(BaseInterfaceAdapter):
#     """웹 인터페이스 어댑터"""
#     pass
#
# class APIInterfaceAdapter(BaseInterfaceAdapter):
#     """API 인터페이스 어댑터"""
#     pass
