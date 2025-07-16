"""
CLI 인터페이스 - 단일 질문 처리
"""

import sys
from datetime import datetime
from .base import BaseInterface
from ..providers.base import ChatMessage
from ..data.models import Conversation


class CLIInterface(BaseInterface):
    """명령줄 인터페이스 - 단일 질문"""

    def __init__(self, memory_manager, provider, **kwargs):
        super().__init__(memory_manager, provider, **kwargs)
        self.max_context_turns = kwargs.get('max_context_turns', 3)

    def run(self, query: str) -> str:
        """단일 질문 처리"""

        # 1. 관련 메모리 검색
        search_result = self.memory_manager.search_memory(query, limit=5)

        # 2. 최근 대화 기록 로드
        recent_conversations = self.memory_manager.load_recent_conversations(
            limit=self.max_context_turns
        )

        # 3. 사용자 프로필 로드
        user_profile = self.memory_manager.load_user_profile()

        # 4. 컨텍스트 구성
        context_prompt = self._build_context_prompt(
            query, search_result, recent_conversations, user_profile
        )

        # 5. AI에게 질문
        messages = [ChatMessage(role="user", content=context_prompt)]
        response = self.provider.chat(messages)

        # 6. 대화 기록 저장
        self._save_conversation(query, response.content)

        return response.content

    def _build_context_prompt(self, query, search_result, recent_conversations, user_profile):
        """컨텍스트가 포함된 프롬프트 생성"""

        context_parts = []

        # 시스템 메시지
        context_parts.append("""당신은 사용자의 개인 개발 비서입니다. 
아래의 이전 기억을 바탕으로 연속성 있는 대화를 제공해주세요.""")

        # 사용자 프로필
        context_parts.append(f"""
# 사용자 프로필
- 이름: {user_profile.name}
- 코딩 스타일: {user_profile.coding_style}
- 선호 언어: {', '.join(user_profile.preferred_languages)}
- IDE: {user_profile.ide}
""")

        # 관련 메모리
        if search_result.items:
            context_parts.append("\n# 관련 기억")
            for i, item in enumerate(search_result.items[:2], 1):
                context_parts.append(f"""
## 기억 {i} (관련도: {item.relevance_score:.2f})
{item.content[:200]}...
""")

        # 최근 대화
        if recent_conversations:
            context_parts.append("\n# 최근 대화 기록")
            for i, conv in enumerate(recent_conversations[:2], 1):
                if conv.turns:
                    last_turn = conv.turns[-1]
                    context_parts.append(f"""
## 대화 {i} ({conv.title or 'No Title'})
사용자: {last_turn.user_message[:100]}...
AI: {last_turn.assistant_message[:100]}...
""")

        # 현재 질문
        context_parts.append(f"\n# 현재 질문\n{query}")

        return "\n".join(context_parts)

    def _save_conversation(self, user_message: str, assistant_message: str):
        """대화 저장"""
        # 오늘 날짜로 세션 ID 생성
        today = datetime.now().strftime("%Y%m%d")
        session_id = f"cli-{today}"

        # 기존 대화 찾기 또는 새로 생성
        recent_conversations = self.memory_manager.load_recent_conversations(limit=1)

        if (recent_conversations and
                recent_conversations[0].session_id == session_id and
                recent_conversations[0].start_time.date() == datetime.now().date()):
            # 기존 대화에 추가
            conversation = recent_conversations[0]
        else:
            # 새 대화 생성
            conversation = Conversation(
                turns=[],
                session_id=session_id,
                start_time=datetime.now(),
                title=f"CLI Session {today}"
            )

        # 새 턴 추가
        conversation.add_turn(user_message, assistant_message)

        # 저장
        self.memory_manager.save_conversation(conversation)