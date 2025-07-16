"""
대화형 인터페이스 - 모델 선택 기능 추가
"""

import sys
import os
from datetime import datetime
from .base import BaseInterface
from ..providers.base import ChatMessage
from ..providers import create_provider, AVAILABLE_PROVIDERS, ProviderConfigError
from ..data.models import Conversation

class InteractiveInterface(BaseInterface):
    """대화형 인터페이스 - 모델 선택 기능 추가"""

    def __init__(self, memory_manager, provider, **kwargs):
        super().__init__(memory_manager, provider, **kwargs)
        self.session_conversation = None
        self.max_context_turns = kwargs.get('max_context_turns', 5)
        self.available_providers = {}  # 사용 가능한 Provider 캐시

    def run(self):
        """대화형 세션 시작"""

        # 세션 초기화
        self._initialize_session()

        # 시작 메시지
        self._print_welcome()

        # 메인 루프
        while True:
            try:
                user_input = input("\n👤 You: ").strip()

                if not user_input:
                    continue

                # 명령어 처리
                if user_input.lower() in ['/quit', '/exit']:
                    self._handle_quit()
                    break
                elif user_input.lower() == '/save':
                    self._handle_save()
                    continue
                elif user_input.lower() == '/clear':
                    self._handle_clear()
                    continue
                elif user_input.lower() == '/switch':
                    self._handle_switch_provider()
                    continue
                elif user_input.lower() == '/model':
                    self._handle_change_model()
                    continue
                elif user_input.lower() == '/help':
                    self._handle_help()
                    continue
                elif user_input.lower() == '/stats':
                    self._handle_stats()
                    continue
                elif user_input.lower() == '/providers':
                    self._handle_list_providers()
                    continue
                elif user_input.lower() == '/models':
                    self._handle_list_models()
                    continue

                # AI와 대화
                response = self._process_message(user_input)
                model_name = self.provider.get_model_info().name
                print(f"\n🤖 {model_name}: {response}")

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

    def _initialize_session(self):
        """세션 초기화"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_id = f"interactive-{timestamp}"

        self.session_conversation = Conversation(
            turns=[],
            session_id=session_id,
            start_time=datetime.now(),
            title=f"Interactive Session {timestamp}"
        )

    def _print_welcome(self):
        """환영 메시지 출력"""
        model_info = self.provider.get_model_info()
        user_profile = self.memory_manager.load_user_profile()

        print("🧠 Claude Memory - 대화형 세션")
        print("=" * 50)
        print(f"🤖 AI Provider: {model_info.name} ({model_info.provider})")
        print(f"👤 사용자: {user_profile.name}")
        print(f"💾 메모리 경로: {self.memory_manager.base_dir}")
        print("=" * 50)
        print("💡 명령어:")
        print("  /quit 또는 /exit - 세션 종료")
        print("  /save - 현재 세션 저장")
        print("  /clear - 세션 기록 초기화")
        print("  /switch - Provider 변경 🔄")
        print("  /model - 현재 Provider 내 모델 변경 🎯")
        print("  /models - 사용 가능한 모델 목록")
        print("  /providers - 사용 가능한 Provider 목록")
        print("  /stats - 메모리 통계")
        print("  /help - 도움말")
        print("=" * 50)

    def _process_message(self, user_message: str) -> str:
        """메시지 처리"""

        # 1. 관련 메모리 검색
        search_result = self.memory_manager.search_memory(user_message, limit=3)

        # 2. 최근 대화 기록 로드
        recent_conversations = self.memory_manager.load_recent_conversations(limit=2)

        # 3. 사용자 프로필 로드
        user_profile = self.memory_manager.load_user_profile()

        # 4. 현재 세션 컨텍스트 구성
        messages = self._build_messages(
            user_message, search_result, recent_conversations,
            user_profile, self.session_conversation
        )

        # 5. AI 호출
        response = self.provider.chat(messages)

        # 6. 세션에 기록
        self.session_conversation.add_turn(user_message, response.content)

        return response.content

    def _build_messages(self, user_message, search_result, recent_conversations,
                       user_profile, current_session):
        """메시지 구성"""

        messages = []

        # 시스템 메시지 (첫 번째 메시지에만)
        if not current_session.turns:
            system_content = self._build_system_message(
                search_result, recent_conversations, user_profile
            )
            messages.append(ChatMessage(role="system", content=system_content))

        # 현재 세션의 이전 대화들
        for turn in current_session.turns[-self.max_context_turns:]:
            messages.append(ChatMessage(role="user", content=turn.user_message))
            messages.append(ChatMessage(role="assistant", content=turn.assistant_message))

        # 현재 메시지
        messages.append(ChatMessage(role="user", content=user_message))

        return messages

    def _build_system_message(self, search_result, recent_conversations, user_profile):
        """시스템 메시지 구성"""

        parts = [
            "당신은 사용자의 개인 개발 비서입니다.",
            "아래의 정보를 참고하여 연속성 있는 대화를 제공해주세요.",
            "",
            f"# 사용자 프로필",
            f"- 이름: {user_profile.name}",
            f"- 코딩 스타일: {user_profile.coding_style}",
            f"- 선호 언어: {', '.join(user_profile.preferred_languages)}",
            f"- IDE: {user_profile.ide}"
        ]

        # 관련 메모리
        if search_result.items:
            parts.append("\n# 관련 기억")
            for i, item in enumerate(search_result.items[:1], 1):
                parts.append(f"- {item.content[:150]}...")

        # 최근 대화
        if recent_conversations:
            parts.append("\n# 최근 대화 요약")
            for conv in recent_conversations[:1]:
                if conv.turns:
                    last_turn = conv.turns[-1]
                    parts.append(f"- {last_turn.user_message[:100]}...")

        return "\n".join(parts)

    def _handle_quit(self):
        """세션 종료"""
        if self.session_conversation.turns:
            save_choice = input("💾 현재 세션을 저장하시겠습니까? (y/N): ").lower()
            if save_choice in ['y', 'yes', '예']:
                self.memory_manager.save_conversation(self.session_conversation)
                print("💾 세션이 저장되었습니다.")

        print("👋 Claude Memory 세션이 종료되었습니다.")

    def _handle_save(self):
        """세션 저장"""
        if self.session_conversation.turns:
            self.memory_manager.save_conversation(self.session_conversation)
            print("💾 세션이 저장되었습니다.")
        else:
            print("💭 저장할 대화가 없습니다.")

    def _handle_clear(self):
        """세션 기록 초기화"""
        self.session_conversation.turns.clear()
        print("🗑️ 현재 세션 기록이 초기화되었습니다.")

    def _handle_switch_provider(self):
        """Provider 변경 (모델 선택 포함)"""
        current_provider = self.provider.get_model_info()

        print(f"\n🔄 현재 Provider: {current_provider.name} ({current_provider.provider})")
        print("\n📋 사용 가능한 Provider:")

        providers = list(AVAILABLE_PROVIDERS.keys())
        for i, (name, info) in enumerate(AVAILABLE_PROVIDERS.items(), 1):
            status = "✅ 현재" if name == current_provider.provider else "🔹 사용 가능"
            print(f"   {i}. {name} - {info['description']} ({status})")

        print("   0. 취소")

        try:
            choice = input("\n선택하세요 (번호): ").strip()

            if choice == '0' or choice.lower() == 'cancel':
                print("🚫 Provider 변경이 취소되었습니다.")
                return

            choice_num = int(choice) - 1
            if 0 <= choice_num < len(providers):
                selected_provider = providers[choice_num]

                if selected_provider == current_provider.provider:
                    print("⚠️ 이미 현재 Provider입니다.")
                    # 같은 Provider 내에서 모델 변경 제안
                    if selected_provider == 'ollama':
                        model_change = input("🎯 다른 모델로 변경하시겠습니까? (y/N): ").lower()
                        if model_change in ['y', 'yes', '예']:
                            self._handle_change_model()
                    return

                # 새 Provider 생성 시도
                success = self._switch_to_provider(selected_provider)
                if success:
                    new_info = self.provider.get_model_info()
                    print(f"✅ Provider 변경 완료: {new_info.name} ({new_info.provider})")

                    # 세션 메타데이터에 Provider 변경 기록
                    self.session_conversation.metadata['provider_changes'] = \
                        self.session_conversation.metadata.get('provider_changes', [])
                    self.session_conversation.metadata['provider_changes'].append({
                        'timestamp': datetime.now().isoformat(),
                        'from': f"{current_provider.name} ({current_provider.provider})",
                        'to': f"{new_info.name} ({new_info.provider})"
                    })
                else:
                    print("❌ Provider 변경에 실패했습니다.")
            else:
                print("❌ 잘못된 선택입니다.")

        except ValueError:
            print("❌ 숫자를 입력해주세요.")
        except KeyboardInterrupt:
            print("\n🚫 Provider 변경이 취소되었습니다.")

    def _handle_change_model(self):
        """현재 Provider 내에서 모델 변경"""
        current_provider = self.provider.get_model_info()

        print(f"\n🎯 현재 모델: {current_provider.name} ({current_provider.provider})")

        if current_provider.provider == 'ollama':
            # Ollama 모델 목록 가져오기
            try:
                if hasattr(self.provider, 'get_available_models'):
                    models = self.provider.get_available_models()
                    if not models:
                        print("❌ 사용 가능한 모델을 찾을 수 없습니다.")
                        print("   ollama list 명령으로 설치된 모델을 확인하세요.")
                        return

                    print("\n📋 사용 가능한 Ollama 모델:")
                    for i, model in enumerate(models, 1):
                        status = "✅ 현재" if model == current_provider.name else "🔹 사용 가능"

                        # 모델 특성 표시
                        model_info = self._get_model_characteristics(model)
                        print(f"   {i}. {model} - {model_info} ({status})")

                    print("   0. 취소")

                    try:
                        choice = input("\n선택하세요 (번호): ").strip()

                        if choice == '0' or choice.lower() == 'cancel':
                            print("🚫 모델 변경이 취소되었습니다.")
                            return

                        choice_num = int(choice) - 1
                        if 0 <= choice_num < len(models):
                            selected_model = models[choice_num]

                            if selected_model == current_provider.name:
                                print("⚠️ 이미 현재 모델입니다.")
                                return

                            # 새 모델로 변경
                            success = self._switch_to_model(selected_model)
                            if success:
                                new_info = self.provider.get_model_info()
                                print(f"✅ 모델 변경 완료: {new_info.name}")

                                # 세션 메타데이터에 모델 변경 기록
                                self.session_conversation.metadata['model_changes'] = \
                                    self.session_conversation.metadata.get('model_changes', [])
                                self.session_conversation.metadata['model_changes'].append({
                                    'timestamp': datetime.now().isoformat(),
                                    'from': current_provider.name,
                                    'to': selected_model
                                })
                            else:
                                print("❌ 모델 변경에 실패했습니다.")
                        else:
                            print("❌ 잘못된 선택입니다.")

                    except ValueError:
                        print("❌ 숫자를 입력해주세요.")
                    except KeyboardInterrupt:
                        print("\n🚫 모델 변경이 취소되었습니다.")

                else:
                    print("❌ 현재 Provider는 모델 목록 조회를 지원하지 않습니다.")

            except Exception as e:
                print(f"❌ 모델 목록 조회 실패: {e}")

        elif current_provider.provider == 'claude':
            # Claude 모델 목록 (하드코딩)
            claude_models = [
                ("claude-3-5-sonnet-20241022", "고성능 범용 모델"),
                ("claude-3-haiku-20240307", "빠르고 경제적인 모델")
            ]

            print("\n📋 사용 가능한 Claude 모델:")
            for i, (model, desc) in enumerate(claude_models, 1):
                status = "✅ 현재" if model == current_provider.name else "🔹 사용 가능"
                print(f"   {i}. {model} - {desc} ({status})")

            print("   0. 취소")

            try:
                choice = input("\n선택하세요 (번호): ").strip()

                if choice == '0' or choice.lower() == 'cancel':
                    print("🚫 모델 변경이 취소되었습니다.")
                    return

                choice_num = int(choice) - 1
                if 0 <= choice_num < len(claude_models):
                    selected_model = claude_models[choice_num][0]

                    if selected_model == current_provider.name:
                        print("⚠️ 이미 현재 모델입니다.")
                        return

                    # 새 모델로 변경
                    success = self._switch_to_model(selected_model)
                    if success:
                        new_info = self.provider.get_model_info()
                        print(f"✅ 모델 변경 완료: {new_info.name}")
                else:
                    print("❌ 잘못된 선택입니다.")

            except ValueError:
                print("❌ 숫자를 입력해주세요.")
            except KeyboardInterrupt:
                print("\n🚫 모델 변경이 취소되었습니다.")

        else:
            print(f"❌ {current_provider.provider} Provider는 모델 변경을 지원하지 않습니다.")

    def _get_model_characteristics(self, model_name: str) -> str:
        """모델 특성 정보 반환"""
        characteristics = {
            'llama3.1:8b': '범용 모델 (8B 파라미터)',
            'codellama:latest': '코드 특화 모델 🔧',
            'phi4:latest': '고성능 소형 모델 ⚡',
            'tinyllama:latest': '초경량 모델 🪶',
            'mistral:latest': '고성능 범용 모델',
            'neural-chat:latest': '대화 특화 모델 💬',
            'dolphin-mixtral:latest': '창의적 작업 특화 🐬'
        }
        return characteristics.get(model_name, '범용 모델')

    def _switch_to_model(self, model_name: str) -> bool:
        """같은 Provider 내에서 모델 변경"""
        try:
            current_provider_type = self.provider.get_model_info().provider

            # 현재 Provider 설정 유지하면서 모델만 변경
            provider_kwargs = {'model_name': model_name}

            if current_provider_type == 'claude':
                api_key = os.getenv('ANTHROPIC_API_KEY')
                if not api_key:
                    print("❌ ANTHROPIC_API_KEY가 설정되지 않았습니다.")
                    return False
                provider_kwargs['api_key'] = api_key

            # 새 Provider 생성
            new_provider = create_provider(current_provider_type, **provider_kwargs)

            # 사용 가능 여부 확인
            if not new_provider.is_available():
                print(f"❌ {model_name} 모델을 사용할 수 없습니다.")
                return False

            # Provider 교체
            self.provider = new_provider
            return True

        except Exception as e:
            print(f"❌ 모델 변경 실패: {e}")
            return False

    def _switch_to_provider(self, provider_name: str) -> bool:
        """실제 Provider 변경 수행"""
        try:
            # Provider별 설정 준비
            provider_kwargs = {}

            if provider_name == 'claude':
                # Claude API 키 확인
                api_key = os.getenv('ANTHROPIC_API_KEY')
                if not api_key:
                    print("❌ ANTHROPIC_API_KEY가 설정되지 않았습니다.")
                    print("   claude_memory/config/.env 파일을 확인하세요.")
                    return False
                provider_kwargs['api_key'] = api_key

            elif provider_name == 'ollama':
                # Ollama 서버 확인은 create_provider에서 is_available()로 처리
                pass

            # 새 Provider 생성
            new_provider = create_provider(provider_name, **provider_kwargs)

            # 사용 가능 여부 확인
            if not new_provider.is_available():
                if provider_name == 'claude':
                    print("❌ Claude API를 사용할 수 없습니다. API 키를 확인하세요.")
                elif provider_name == 'ollama':
                    print("❌ Ollama 서버를 사용할 수 없습니다.")
                    print("   다음 명령으로 Ollama를 시작하세요: ollama serve")
                return False

            # Provider 교체
            self.provider = new_provider
            return True

        except ProviderConfigError as e:
            print(f"❌ Provider 설정 오류: {e}")
            return False
        except Exception as e:
            print(f"❌ Provider 변경 실패: {e}")
            return False

    def _handle_list_models(self):
        """현재 Provider의 사용 가능한 모델 목록 표시"""
        current_provider = self.provider.get_model_info()

        print(f"\n🎯 {current_provider.provider.upper()} 모델 목록:")

        if current_provider.provider == 'ollama':
            try:
                if hasattr(self.provider, 'get_available_models'):
                    models = self.provider.get_available_models()
                    if models:
                        for model in models:
                            status = "✅ 현재" if model == current_provider.name else "🔹 사용 가능"
                            characteristics = self._get_model_characteristics(model)
                            print(f"   {model} - {characteristics} ({status})")
                    else:
                        print("   사용 가능한 모델이 없습니다.")
                else:
                    print("   모델 목록 조회를 지원하지 않습니다.")
            except Exception as e:
                print(f"   모델 목록 조회 실패: {e}")

        elif current_provider.provider == 'claude':
            claude_models = [
                ("claude-3-5-sonnet-20241022", "고성능 범용 모델"),
                ("claude-3-haiku-20240307", "빠르고 경제적인 모델")
            ]

            for model, desc in claude_models:
                status = "✅ 현재" if model == current_provider.name else "🔹 사용 가능"
                print(f"   {model} - {desc} ({status})")

    def _handle_list_providers(self):
        """사용 가능한 Provider 목록 표시"""
        current_provider = self.provider.get_model_info()

        print("\n📋 사용 가능한 Provider 상세 정보:")
        for name, info in AVAILABLE_PROVIDERS.items():
            status = "✅ 현재 사용 중" if name == current_provider.provider else "🔹 사용 가능"
            print(f"\n{name.upper()}:")
            print(f"   상태: {status}")
            print(f"   설명: {info['description']}")
            print(f"   타입: {info['type'].value}")
            print(f"   비용: {info['cost']}")
            print(f"   요구사항: {', '.join(info['requires'])}")

    def _handle_stats(self):
        """메모리 통계 표시"""
        stats = self.memory_manager.get_memory_stats()
        model_info = self.provider.get_model_info()

        print("\n📊 메모리 통계:")
        print(f"   총 대화: {stats['total_conversations']}개")
        print(f"   총 턴: {stats['total_turns']}개")
        print(f"   현재 세션: {len(self.session_conversation.turns)}개 턴")
        print(f"   AI 모델: {model_info.name} ({model_info.provider})")
        print(f"   저장 경로: {stats['storage_path']}")

        # Provider/모델 변경 기록 표시
        provider_changes = self.session_conversation.metadata.get('provider_changes', [])
        model_changes = self.session_conversation.metadata.get('model_changes', [])

        if provider_changes:
            print(f"   Provider 변경: {len(provider_changes)}회")
            for change in provider_changes[-3:]:  # 최근 3회만 표시
                print(f"     {change['from']} → {change['to']}")

        if model_changes:
            print(f"   모델 변경: {len(model_changes)}회")
            for change in model_changes[-3:]:  # 최근 3회만 표시
                print(f"     {change['from']} → {change['to']}")

    def _handle_help(self):
        """도움말 표시"""
        print("""
🧠 Claude Memory 명령어:

대화 관련:
  - 일반 텍스트: AI와 대화
  - 연속 대화가 자동으로 기억됩니다

세션 관리:
  /save   - 현재 세션을 저장
  /clear  - 현재 세션 기록 초기화
  /quit   - 세션 종료 (저장 여부 선택)

AI 모델 관리:
  /switch    - Provider 변경 🔄 (Claude ↔ Ollama)
  /model     - 현재 Provider 내 모델 변경 🎯
  /models    - 현재 Provider의 사용 가능한 모델 목록
  /providers - 사용 가능한 Provider 목록

정보:
  /stats  - 메모리 통계 표시
  /help   - 이 도움말

💡 팁:
  - 대화 중에 언제든 Provider/모델 변경 가능
  - codellama로 코딩, phi4로 일반 대화 등 용도별 선택
  - 변경 기록은 세션에 자동 저장됩니다
  - Ctrl+C로 언제든 안전하게 종료 가능
""")