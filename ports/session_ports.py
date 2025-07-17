# ===== ports/session_ports.py =====
"""
세션 관련 포트 인터페이스
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from core.shared.models import SessionContext, UserProfile, OrchestratorType


class SessionManager(ABC):
    """세션 관리 인터페이스"""

    @abstractmethod
    def create_session(self, user_profile: UserProfile,
                       orchestrator_type: OrchestratorType = None) -> SessionContext:
        """세션 생성"""
        pass

    @abstractmethod
    def get_session(self, session_id: str) -> Optional[SessionContext]:
        """세션 조회"""
        pass

    @abstractmethod
    def update_session(self, session_context: SessionContext) -> bool:
        """세션 업데이트"""
        pass

    @abstractmethod
    def close_session(self, session_id: str) -> bool:
        """세션 종료"""
        pass

    @abstractmethod
    def get_active_sessions(self) -> List[SessionContext]:
        """활성 세션 목록"""
        pass

    # TODO Phase 2: 고급 세션 관리
    # @abstractmethod
    # def migrate_session(self, session_id: str, new_orchestrator: OrchestratorType) -> bool:
    #     """세션 마이그레이션"""
    #     pass

    # @abstractmethod
    # def backup_session(self, session_id: str) -> bool:
    #     """세션 백업"""
    #     pass