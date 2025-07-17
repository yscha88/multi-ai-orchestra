"""
공유 도메인 모델 정의
기존 ai_memory/data/models.py를 확장하여 Orchestra 구조에 맞게 개선
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional, Union
from enum import Enum
import uuid


# ===== 기존 모델들 (ai_memory에서 이동) =====

class MemoryType(Enum):
    """메모리 타입 정의 - 기존 + 확장"""
    CONVERSATION = "conversation"
    PATTERN = "pattern"
    NOTE = "note"
    PROJECT_CONTEXT = "project_context"
    USER_PROFILE = "user_profile"
    # Phase 1 추가
    SIMPLE_TASK = "simple_task"
    COMPLEX_TASK = "complex_task"
    # TODO Phase 2: 고급 메모리 타입
    SEMANTIC = "semantic"
    EPISODIC = "episodic"
    PROCEDURAL = "procedural"
    EMOTIONAL = "emotional"


@dataclass
class ConversationTurn:
    """대화 한 턴 (질문-답변 쌍) - 기존 유지"""
    user_message: str
    assistant_message: str
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Conversation:
    """대화 세션 - 기존 + 확장"""
    turns: List[ConversationTurn]
    session_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    title: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Phase 1 추가: 오케스트레이터 정보
    orchestrator_type: Optional[str] = None
    task_complexity: Optional[str] = None  # "simple" | "complex"

    def add_turn(self, user_msg: str, assistant_msg: str, **metadata):
        """새로운 대화 턴 추가"""
        turn = ConversationTurn(
            user_message=user_msg,
            assistant_message=assistant_msg,
            timestamp=datetime.now(),
            metadata=metadata
        )
        self.turns.append(turn)

    def get_summary(self) -> str:
        """대화 요약 생성"""
        if not self.turns:
            return "빈 대화"
        first_turn = self.turns[0]
        return f"{first_turn.user_message[:50]}..." if len(first_turn.user_message) > 50 else first_turn.user_message


@dataclass
class MemoryItem:
    """메모리 아이템 - 기존 + 확장"""
    content: str
    memory_type: MemoryType
    timestamp: datetime
    relevance_score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Phase 1 추가
    item_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tags: List[str] = field(default_factory=list)
    # TODO Phase 2: 고급 메모리 속성들
    # emotional_valence: float = 0.0
    # connections: List[str] = field(default_factory=list)
    # importance_score: float = 0.0


@dataclass
class UserProfile:
    """사용자 프로필 - 기존 + 확장"""
    name: str = "사용자"
    coding_style: str = "Clean Code 선호"
    preferred_languages: List[str] = field(default_factory=lambda: ["Python"])
    ide: str = "PyCharm"
    common_patterns: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Phase 1 추가: 오케스트레이터 선호도
    preferred_orchestrator: Optional[str] = None
    interaction_style: str = "balanced"  # "brief" | "detailed" | "balanced"

    # TODO Phase 2: 개성 특성들
    # personality_traits: Dict[str, float] = field(default_factory=dict)
    # learning_preferences: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SearchResult:
    """검색 결과 - 기존 + 확장"""
    items: List[MemoryItem]
    query: str
    total_found: int
    search_time: float
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Phase 1 추가
    search_strategy: str = "keyword"  # "keyword" | "semantic" | "hybrid"
    # TODO Phase 2: 고급 검색 결과
    # concept_matches: List[str] = field(default_factory=list)
    # related_queries: List[str] = field(default_factory=list)


# ===== Phase 1 새로운 모델들 =====

class OrchestratorType(Enum):
    """오케스트레이터 타입"""
    SIMPLE = "simple"  # 기존 방식 (단순 래핑)
    MEMORY = "memory"  # 기억 중심
    CONTROL = "control"  # 관제 중심
    # TODO Phase 2
    PERSONALITY = "personality"  # 통합 관제인격
    COLLABORATION = "collaboration"  # 협업 중심


class TaskComplexity(Enum):
    """작업 복잡도"""
    SIMPLE = "simple"  # 단순한 질문/답변
    MODERATE = "moderate"  # 중간 복잡도
    COMPLEX = "complex"  # 복잡한 프로젝트/설계
    # TODO Phase 2
    MULTI_STEP = "multi_step"  # 다단계 작업
    COLLABORATIVE = "collaborative"  # 협업 필요


@dataclass
class TaskAnalysis:
    """작업 분석 결과"""
    complexity: TaskComplexity
    estimated_time: float  # 예상 처리 시간 (초)
    recommended_orchestrator: OrchestratorType
    required_capabilities: List[str]
    confidence: float = 1.0
    reasoning: str = ""

    # TODO Phase 2: 고급 분석
    # subtasks: List[str] = field(default_factory=list)
    # required_resources: Dict[str, Any] = field(default_factory=dict)
    # risk_factors: List[str] = field(default_factory=list)


@dataclass
class OrchestratorResponse:
    """오케스트레이터 응답"""
    content: str
    orchestrator_type: OrchestratorType
    processing_time: float
    token_usage: Dict[str, int] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Phase 1 기본 정보
    task_analysis: Optional[TaskAnalysis] = None
    used_providers: List[str] = field(default_factory=list)

    # TODO Phase 2: 고급 응답 정보
    # quality_score: float = 0.0
    # learning_insights: List[str] = field(default_factory=list)
    # follow_up_suggestions: List[str] = field(default_factory=list)


@dataclass
class SessionContext:
    """세션 컨텍스트"""
    session_id: str
    user_profile: UserProfile
    current_orchestrator: OrchestratorType
    conversation_history: List[ConversationTurn] = field(default_factory=list)
    relevant_memories: List[MemoryItem] = field(default_factory=list)

    # Phase 1 기본 컨텍스트
    start_time: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    total_interactions: int = 0

    # TODO Phase 2: 고급 컨텍스트
    # emotional_state: Dict[str, float] = field(default_factory=dict)
    # learning_progress: Dict[str, float] = field(default_factory=dict)
    # personalization_level: float = 0.0


# ===== Provider 관련 모델들 (기존에서 이동) =====

class ProviderType(Enum):
    """Provider 타입"""
    CLOUD_API = "cloud_api"
    LOCAL_LLM = "local_llm"
    HYBRID = "hybrid"


@dataclass
class ModelInfo:
    """모델 정보"""
    name: str
    provider: str
    type: ProviderType
    max_tokens: int
    cost_per_1k_tokens: float = 0.0
    supports_streaming: bool = False
    supports_function_calling: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ChatMessage:
    """채팅 메시지"""
    role: str  # "user", "assistant", "system"
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ChatResponse:
    """채팅 응답"""
    content: str
    model_info: ModelInfo
    token_usage: Dict[str, int] = field(default_factory=lambda: {"input_tokens": 0, "output_tokens": 0})
    cost_estimate: float = 0.0
    response_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


# ===== 설정 관련 모델들 =====

@dataclass
class OrchestratorConfig:
    """오케스트레이터 설정"""
    orchestrator_type: OrchestratorType
    enabled: bool = True
    priority: int = 0  # 낮을수록 높은 우선순위
    config_params: Dict[str, Any] = field(default_factory=dict)

    # Phase 1 기본 설정
    max_context_length: int = 4000
    default_provider: str = "claude"
    timeout_seconds: int = 120

    # TODO Phase 2: 고급 설정
    # learning_rate: float = 0.1
    # personality_adaptation: bool = False
    # collaboration_enabled: bool = False


@dataclass
class SystemConfig:
    """전체 시스템 설정"""
    base_memory_dir: str = "./orchestra_memory"
    default_orchestrator: OrchestratorType = OrchestratorType.SIMPLE
    orchestrator_configs: Dict[OrchestratorType, OrchestratorConfig] = field(default_factory=dict)

    # Phase 1 기본 설정들
    log_level: str = "INFO"
    cache_enabled: bool = True
    auto_backup: bool = True

    # TODO Phase 2: 고급 설정들
    # vector_db_enabled: bool = False
    # analytics_enabled: bool = False
    # collaboration_mode: bool = False


# ===== 유틸리티 함수들 =====

def create_conversation(session_id: str, title: str = None,
                        orchestrator_type: OrchestratorType = OrchestratorType.SIMPLE) -> Conversation:
    """새로운 대화 세션 생성"""
    return Conversation(
        turns=[],
        session_id=session_id,
        start_time=datetime.now(),
        title=title,
        orchestrator_type=orchestrator_type.value
    )


def create_memory_item(content: str, memory_type: MemoryType,
                       tags: List[str] = None, **kwargs) -> MemoryItem:
    """새로운 메모리 아이템 생성"""
    return MemoryItem(
        content=content,
        memory_type=memory_type,
        timestamp=datetime.now(),
        tags=tags or [],
        **kwargs
    )


def create_session_context(user_profile: UserProfile,
                           orchestrator_type: OrchestratorType = OrchestratorType.SIMPLE) -> SessionContext:
    """새로운 세션 컨텍스트 생성"""
    return SessionContext(
        session_id=str(uuid.uuid4()),
        user_profile=user_profile,
        current_orchestrator=orchestrator_type
    )


# ===== 타입 별칭들 =====

# 편의를 위한 타입 별칭들
MemoryDict = Dict[str, MemoryItem]
ConversationDict = Dict[str, Conversation]
ProviderDict = Dict[str, Any]
ConfigDict = Dict[str, Any]

# TODO Phase 2에서 추가될 타입들
# ConceptGraph = Dict[str, List[str]]
# EmotionalState = Dict[str, float]
# PersonalityTraits = Dict[str, float]
# LearningProgress = Dict[str, float]

