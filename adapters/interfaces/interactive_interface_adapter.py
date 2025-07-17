# ===== adapters/interfaces/interactive_interface_adapter.py =====
"""
대화형 인터페이스 어댑터 (기존 InteractiveInterface 리팩터링)
"""

import sys
import os
from datetime import datetime
from .base_interface_adapter import BaseInterfaceAdapter
from core.shared.models import OrchestratorType, UserProfile


class InteractiveInterfaceAdapter(BaseInterfaceAdapter):
    """대화형 인터페이스 어댑터 (기존 InteractiveInterface 개선)"""

    def __init__(self, session_manager, **kwargs):
        super().__init__(session_manager, **kwargs)
        self.max_context_turns = kwargs.get('max_context_turns', 5)
        self.current_session = None
        self.available_orchestrators = [
            OrchestratorType.SIMPLE,
            OrchestratorType.MEMORY,
            OrchestratorType.CONTROL
        ]

    def run(self, user_profile: UserProfile = None,
            orchestrator_type: OrchestratorType = None):
        """대화형 세션 시작 (기존 로직 + 오케스트레이터 선택)"""

        # 1. 초기 설정
        self._initialize_session(user_profile, orchestrator_type)

        # 2. 환영 메시지
        self._print_welcome()

        # 3. 메인 대화 루프
        while True:
            try:
                user_input = input("\n👤 You: ").strip()

                if not user_input:
                    continue

                # 명령어 처리
                if self._handle_command(user_input):
                    continue

                # AI와 대화
                response = self._process_user_message(user_input)
                self._print_ai_response(response)

            except KeyboardInterrupt:
                print("\n\n🛑 Ctrl+C가 감지되었습니다.")
                self._handle_quit()
                break
            except EOFError:
                print("\n\n👋 세션을 종료합니다.")
                self._handle_quit()
                break
            except Exception as e:
                print(f"\n❌ 오류 발생: {e}")
                continue

    def _initialize_session(self, user_profile: UserProfile = None,
                            orchestrator_type: OrchestratorType = None):
        """세션 초기화"""
        # 기본 사용자 프로필
        if not user_profile:
            user_profile = UserProfile(
                name="대화형사용자",
                interaction_style="balanced"
            )

        # 기본 오케스트레이터
        if not orchestrator_type:
            orchestrator_type = OrchestratorType.SIMPLE

        # 세션 생성
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_id = f"interactive-{timestamp}"

        self.current_session = self.session_manager.create_session(
            user_profile=user_profile,
            orchestrator_type=orchestrator_type,
            session_id=session_id
        )

    def _print_welcome(self):
        """환영 메시지 출력 (기존 + 오케스트레이터 정보)"""
        session_context = self.session_manager.get_session(self.current_session.session_id)

        print("🎼 Multi-AI Orchestra - 대화형 세션")
        print("=" * 60)
        print(f"🎭 현재 오케스트레이터: {session_context.current_orchestrator.value}")
        print(f"👤 사용자: {session_context.user_profile.name}")
        print(f"📝 상호작용 스타일: {session_context.user_profile.interaction_style}")
        print("=" * 60)
        print("💡 명령어:")
        print("  /quit, /exit          - 세션 종료")
        print("  /save                - 현재 세션 저장")
        print("  /clear               - 세션 기록 초기화")
        print("  /switch              - 오케스트레이터 변경 🎛️")
        print("  /stats               - 세션 통계")
        print("  /help                - 도움말")
        print("  /debug on/off        - 디버그 모드 토글")
        print("=" * 60)

    def _handle_command(self, user_input: str) -> bool:
        """명령어 처리 (기존 + 새로운 명령어)"""
        command = user_input.lower()

        if command in ['/quit', '/exit']:
            self._handle_quit()
            return True
        elif command == '/save':
            self._handle_save()
            return True
        elif command == '/clear':
            self._handle_clear()
            return True
        elif command == '/switch':
            self._handle_switch_orchestrator()
            return True
        elif command == '/stats':
            self._handle_stats()
            return True
        elif command == '/help':
            self._handle_help()
            return True
        elif command.startswith('/debug'):
            self._handle_debug(command)
            return True

        return False

    def _process_user_message(self, user_input: str):
        """사용자 메시지 처리"""
        try:
            response = self.session_manager.process_request(
                user_input=user_input,
                session_id=self.current_session.session_id
            )
            return response
        except Exception as e:
            print(f"❌ 메시지 처리 실패: {e}")
            return None

    def _print_ai_response(self, response):
        """AI 응답 출력"""
        if not response:
            return

        # 오케스트레이터 정보 표시
        orchestrator_emoji = {
            OrchestratorType.SIMPLE: "🤖",
            OrchestratorType.MEMORY: "🧠",
            OrchestratorType.CONTROL: "🎛️"
        }

        emoji = orchestrator_emoji.get(response.orchestrator_type, "🤖")
        print(f"\n{emoji} AI ({response.orchestrator_type.value}): {response.content}")

        # 디버그 정보 (활성화된 경우)
        if os.getenv('ORCHESTRA_DEBUG', 'false').lower() == 'true':
            self._print_debug_info(response)

    def _print_debug_info(self, response):
        """디버그 정보 출력"""
        print(f"   ⏱️ {response.processing_time:.2f}초", end="")

        if response.used_providers:
            print(f" | 🤖 {', '.join(response.used_providers)}", end="")

        if response.task_analysis:
            print(f" | 📊 {response.task_analysis.complexity.value}", end="")

        print()  # 줄바꿈

    def _handle_quit(self):
        """세션 종료 (기존 로직 유지)"""
        if self.current_session:
            session_context = self.session_manager.get_session(self.current_session.session_id)
            if session_context and len(session_context.conversation_history) > 0:
                save_choice = input("💾 현재 세션을 저장하시겠습니까? (y/N): ").lower()
                if save_choice in ['y', 'yes', '예']:
                    self.session_manager.save_session(self.current_session.session_id)
                    print("💾 세션이 저장되었습니다.")

        print("👋 Multi-AI Orchestra 세션이 종료되었습니다.")

    def _handle_save(self):
        """세션 저장"""
        if self.current_session:
            self.session_manager.save_session(self.current_session.session_id)
            print("💾 세션이 저장되었습니다.")
        else:
            print("💭 저장할 세션이 없습니다.")

    def _handle_clear(self):
        """세션 기록 초기화"""
        if self.current_session:
            session_context = self.session_manager.get_session(self.current_session.session_id)
            if session_context:
                session_context.conversation_history.clear()
                session_context.total_interactions = 0
                print("🗑️ 현재 세션 기록이 초기화되었습니다.")

    def _handle_switch_orchestrator(self):
        """오케스트레이터 변경 (새로운 기능)"""
        current_session_context = self.session_manager.get_session(self.current_session.session_id)
        current_orchestrator = current_session_context.current_orchestrator

        print(f"\n🎛️ 현재 오케스트레이터: {current_orchestrator.value}")
        print("\n📋 사용 가능한 오케스트레이터:")

        for i, orchestrator_type in enumerate(self.available_orchestrators, 1):
            status = "✅ 현재" if orchestrator_type == current_orchestrator else "🔹 사용 가능"
            description = self._get_orchestrator_description(orchestrator_type)
            print(f"   {i}. {orchestrator_type.value} - {description} ({status})")

        print("   0. 취소")

        try:
            choice = input("\n선택하세요 (번호): ").strip()

            if choice == '0' or choice.lower() == 'cancel':
                print("🚫 오케스트레이터 변경이 취소되었습니다.")
                return

            choice_num = int(choice) - 1
            if 0 <= choice_num < len(self.available_orchestrators):
                selected_orchestrator = self.available_orchestrators[choice_num]

                if selected_orchestrator == current_orchestrator:
                    print("⚠️ 이미 현재 오케스트레이터입니다.")
                    return

                # 오케스트레이터 변경
                success = self.session_manager.switch_orchestrator(
                    self.current_session.session_id,
                    selected_orchestrator
                )

                if success:
                    print(f"✅ 오케스트레이터가 변경되었습니다: {selected_orchestrator.value}")
                else:
                    print("❌ 오케스트레이터 변경에 실패했습니다.")
            else:
                print("❌ 잘못된 선택입니다.")

        except ValueError:
            print("❌ 숫자를 입력해주세요.")
        except KeyboardInterrupt:
            print("\n🚫 오케스트레이터 변경이 취소되었습니다.")

    def _handle_stats(self):
        """세션 통계 표시 (새로운 기능)"""
        if not self.current_session:
            print("📊 활성 세션이 없습니다.")
            return

        session_context = self.session_manager.get_session(self.current_session.session_id)

        print("\n📊 세션 통계:")
        print(f"   세션 ID: {session_context.session_id}")
        print(f"   오케스트레이터: {session_context.current_orchestrator.value}")
        print(f"   총 상호작용: {session_context.total_interactions}회")
        print(f"   세션 시작: {session_context.start_time.strftime('%Y-%m-%d %H:%M:%S')}")

        if session_context.conversation_history:
            print(f"   대화 기록: {len(session_context.conversation_history)}개 턴")

        if session_context.relevant_memories:
            print(f"   관련 기억: {len(session_context.relevant_memories)}개")

    def _handle_debug(self, command: str):
        """디버그 모드 토글"""
        parts = command.split()
        if len(parts) > 1:
            mode = parts[1].lower()
            if mode == 'on':
                os.environ['ORCHESTRA_DEBUG'] = 'true'
                print("🔍 디버그 모드가 활성화되었습니다.")
            elif mode == 'off':
                os.environ['ORCHESTRA_DEBUG'] = 'false'
                print("🔍 디버그 모드가 비활성화되었습니다.")
            else:
                print("❌ 사용법: /debug on 또는 /debug off")
        else:
            current_status = os.getenv('ORCHESTRA_DEBUG', 'false')
            print(f"🔍 현재 디버그 모드: {'활성화' if current_status == 'true' else '비활성화'}")

    def _handle_help(self):
        """도움말 표시 (기존 + 새로운 기능)"""
        print("""
🎼 Multi-AI Orchestra 명령어:

대화 관련:
  - 일반 텍스트: AI와 대화
  - 연속 대화가 자동으로 기억됩니다

세션 관리:
  /save         - 현재 세션을 저장
  /clear        - 현재 세션 기록 초기화
  /quit         - 세션 종료 (저장 여부 선택)

오케스트레이터 관리:
  /switch       - 오케스트레이터 변경 🎛️
  /stats        - 세션 통계 표시

디버그 및 정보:
  /debug on/off - 디버그 정보 표시 토글
  /help         - 이 도움말

🎭 오케스트레이터 타입:
  • simple   - 기본 AI (빠른 응답)
  • memory   - 기억 중심 (연속성 강화)
  • control  - 관제 중심 (복잡한 작업)

💡 팁:
  - 복잡한 작업: control 오케스트레이터 추천
  - 이전 대화 참조: memory 오케스트레이터 추천
  - 빠른 질답: simple 오케스트레이터 추천
""")

    def _get_orchestrator_description(self, orchestrator_type: OrchestratorType) -> str:
        """오케스트레이터 설명"""
        descriptions = {
            OrchestratorType.SIMPLE: "기본 AI 채팅",
            OrchestratorType.MEMORY: "기억 기반 연속 대화",
            OrchestratorType.CONTROL: "복잡한 작업 관제"
        }
        return descriptions.get(orchestrator_type, "설명 없음")
