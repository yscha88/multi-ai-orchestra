# ===== adapters/interfaces/cli_interface_adapter.py =====
"""
CLI 인터페이스 어댑터 (기존 CLIInterface 리팩터링)
"""

import sys
from datetime import datetime
from .base_interface_adapter import BaseInterfaceAdapter
from core.shared.models import OrchestratorType, UserProfile


class CLIInterfaceAdapter(BaseInterfaceAdapter):
    """CLI 인터페이스 어댑터 (기존 CLIInterface 개선)"""

    def __init__(self, session_manager, **kwargs):
        super().__init__(session_manager, **kwargs)
        self.max_context_turns = kwargs.get('max_context_turns', 3)
        self.default_orchestrator = kwargs.get('default_orchestrator', OrchestratorType.SIMPLE)

    def run(self, query: str, orchestrator_type: OrchestratorType = None,
            user_profile: UserProfile = None) -> str:
        """단일 질문 처리 (기존 로직 + 오케스트레이터 선택)"""

        try:
            # 1. 사용자 프로필 설정
            if not user_profile:
                user_profile = UserProfile(
                    name="CLI사용자",
                    preferred_orchestrator=orchestrator_type.value if orchestrator_type else None
                )

            # 2. 오케스트레이터 타입 결정
            final_orchestrator_type = orchestrator_type or self.default_orchestrator

            # 3. 세션 생성 또는 재사용
            session = self._get_or_create_session(user_profile, final_orchestrator_type)

            # 4. 요청 처리
            response = self.session_manager.process_request(
                user_input=query,
                session_id=session.session_id,
                orchestrator_type=final_orchestrator_type
            )

            # 5. 응답 포맷팅
            formatted_response = self._format_cli_response(response)

            return formatted_response

        except Exception as e:
            error_msg = f"처리 중 오류가 발생했습니다: {e}"
            print(f"❌ {error_msg}")
            return error_msg

    def _get_or_create_session(self, user_profile: UserProfile,
                               orchestrator_type: OrchestratorType):
        """세션 가져오기 또는 생성"""
        # CLI는 보통 일회성이므로 새 세션 생성
        today = datetime.now().strftime("%Y%m%d")
        session_id = f"cli-{today}-{datetime.now().strftime('%H%M%S')}"

        session = self.session_manager.create_session(
            user_profile=user_profile,
            orchestrator_type=orchestrator_type,
            session_id=session_id
        )

        return session

    def _format_cli_response(self, response) -> str:
        """CLI 응답 포맷팅"""
        content = response.content

        # 디버그 정보 추가 (환경변수로 제어 가능)
        import os
        if os.getenv('ORCHESTRA_DEBUG', 'false').lower() == 'true':
            metadata = response.metadata or {}

            debug_info = []
            debug_info.append(f"🎼 오케스트레이터: {response.orchestrator_type.value}")
            debug_info.append(f"⏱️ 처리시간: {response.processing_time:.2f}초")

            if response.used_providers:
                debug_info.append(f"🤖 사용 AI: {', '.join(response.used_providers)}")

            if response.task_analysis:
                debug_info.append(f"📊 복잡도: {response.task_analysis.complexity.value}")

            content += f"\n\n🔍 디버그 정보:\n" + "\n".join(debug_info)

        return content
