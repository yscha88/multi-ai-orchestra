"""
설정 관리

AI Memory의 설정을 관리합니다.
"""

from pathlib import Path
import os

# 기본 경로 설정
DEFAULT_CONFIG_DIR = Path(".ai-memory/config")
DEFAULT_CONFIG_FILE = DEFAULT_CONFIG_DIR / "ai-memory.yaml"

# 환경변수 지원
def get_config_path():
    """환경변수 또는 기본 경로에서 설정 파일 경로 반환"""
    return os.getenv('AI_MEMORY_CONFIG', DEFAULT_CONFIG_FILE)

# TODO: Phase B에서 구현
# from .settings import Settings, load_settings, save_settings

__all__ = [
    'DEFAULT_CONFIG_DIR',
    'DEFAULT_CONFIG_FILE',
    'get_config_path',
    # TODO: Phase B에서 추가
    # 'Settings',
    # 'load_settings',
    # 'save_settings',
]