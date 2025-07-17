# ===== core/control/task_analyzer.py =====
"""
작업 분석기 - Phase 1 단순화 버전
"""

import re
from typing import List, Dict, Any
from ports.control_ports import TaskAnalysisService
from core.shared.models import (
    TaskAnalysis, TaskComplexity, OrchestratorType, SessionContext
)


class SimpleTaskAnalyzer(TaskAnalysisService):
    """단순한 작업 분석기 (Phase 1)"""

    def __init__(self):
        # 복잡도 판별 키워드들
        self.complexity_indicators = {
            TaskComplexity.COMPLEX: [
                # 설계/아키텍처 관련
                "아키텍처", "설계", "구조", "시스템", "architecture", "design", "system",
                "마이크로서비스", "microservice", "패턴", "pattern",

                # 프로젝트 관련
                "프로젝트", "project", "전체적", "종합적", "전반적",
                "계획", "plan", "전략", "strategy",

                # 복잡한 기술 작업
                "최적화", "optimization", "성능", "performance", "스케일링", "scaling",
                "보안", "security", "배포", "deployment", "인프라", "infrastructure",

                # 다단계 작업
                "단계별", "step by step", "순서대로", "절차", "과정", "workflow",
                "통합", "integration", "연동", "연결"
            ],

            TaskComplexity.MODERATE: [
                # 구현 관련
                "구현", "implement", "개발", "develop", "코딩", "coding",
                "함수", "function", "클래스", "class", "모듈", "module",

                # 특정 기능
                "API", "데이터베이스", "database", "웹", "web", "서버", "server",
                "클라이언트", "client", "인터페이스", "interface",

                # 문제 해결
                "해결", "solve", "수정", "fix", "디버깅", "debug", "오류", "error"
            ],

            TaskComplexity.SIMPLE: [
                # 간단한 질문
                "뭐", "what", "어떻게", "how", "왜", "why", "언제", "when",
                "설명", "explain", "알려줘", "tell me", "가르쳐", "teach",

                # 간단한 작업
                "예시", "example", "샘플", "sample", "보여줘", "show me",
                "찾아줘", "find", "검색", "search"
            ]
        }

        # 오케스트레이터 추천 규칙
        self.orchestrator_rules = {
            "memory_keywords": [
                "기억", "remember", "이전", "before", "지난번", "last time",
                "전에", "했던", "말했던", "물어봤던"
            ],
            "control_keywords": [
                "관리", "manage", "조율", "coordinate", "계획", "plan",
                "전략", "strategy", "시스템", "system", "아키텍처", "architecture"
            ]
        }

    def analyze_task(self, user_input: str, context: SessionContext) -> TaskAnalysis:
        """작업 분석 (Phase 1: 기본 구현)"""
        # 1. 복잡도 분류
        complexity = self.classify_complexity(user_input)

        # 2. 오케스트레이터 추천
        recommended_orchestrator = self.recommend_orchestrator(
            TaskAnalysis(
                complexity=complexity,
                estimated_time=0.0,
                recommended_orchestrator=OrchestratorType.SIMPLE,
                required_capabilities=[]
            )
        )

        # 3. 처리 시간 추정
        estimated_time = self._estimate_processing_time(complexity, user_input)

        # 4. 필요 기능 분석
        required_capabilities = self._analyze_required_capabilities(user_input, complexity)

        # 5. 추론 생성
        reasoning = self._generate_reasoning(user_input, complexity, recommended_orchestrator)

        return TaskAnalysis(
            complexity=complexity,
            estimated_time=estimated_time,
            recommended_orchestrator=recommended_orchestrator,
            required_capabilities=required_capabilities,
            confidence=0.8,  # Phase 1에서는 고정값
            reasoning=reasoning
        )

    def classify_complexity(self, user_input: str) -> TaskComplexity:
        """복잡도 분류"""
        user_input_lower = user_input.lower()

        # 점수 계산
        complex_score = sum(1 for keyword in self.complexity_indicators[TaskComplexity.COMPLEX]
                            if keyword in user_input_lower)
        moderate_score = sum(1 for keyword in self.complexity_indicators[TaskComplexity.MODERATE]
                             if keyword in user_input_lower)
        simple_score = sum(1 for keyword in self.complexity_indicators[TaskComplexity.SIMPLE]
                           if keyword in user_input_lower)

        # 추가 휴리스틱
        # 길이 기반 판별
        if len(user_input) > 100:
            complex_score += 1
        elif len(user_input) < 20:
            simple_score += 1

        # 질문 형태 판별
        if user_input.strip().endswith('?'):
            simple_score += 1

        # 명령형 문장 판별
        command_patterns = ['해줘', '만들어', '구현해', '설계해', '만들어줘']
        if any(pattern in user_input for pattern in command_patterns):
            if complex_score > 0:
                complex_score += 1
            else:
                moderate_score += 1

        # 최종 판별
        if complex_score >= max(moderate_score, simple_score):
            return TaskComplexity.COMPLEX
        elif moderate_score >= simple_score:
            return TaskComplexity.MODERATE
        else:
            return TaskComplexity.SIMPLE

    def recommend_orchestrator(self, task_analysis: TaskAnalysis) -> OrchestratorType:
        """오케스트레이터 추천"""
        # 복잡도 기반 기본 추천
        if task_analysis.complexity == TaskComplexity.COMPLEX:
            return OrchestratorType.CONTROL
        elif task_analysis.complexity == TaskComplexity.MODERATE:
            return OrchestratorType.MEMORY  # 기억을 활용한 처리
        else:
            return OrchestratorType.SIMPLE

    def _estimate_processing_time(self, complexity: TaskComplexity, user_input: str) -> float:
        """처리 시간 추정 (초 단위)"""
        base_times = {
            TaskComplexity.SIMPLE: 5.0,
            TaskComplexity.MODERATE: 15.0,
            TaskComplexity.COMPLEX: 45.0
        }

        base_time = base_times[complexity]

        # 입력 길이에 따른 조정
        length_factor = min(len(user_input) / 50, 2.0)  # 최대 2배까지

        return base_time * length_factor

    def _analyze_required_capabilities(self, user_input: str, complexity: TaskComplexity) -> List[str]:
        """필요 기능 분석"""
        capabilities = ["basic_chat"]

        user_input_lower = user_input.lower()

        # 기능별 키워드 매칭
        capability_keywords = {
            "memory_search": ["기억", "이전", "지난번", "전에", "했던"],
            "code_generation": ["코드", "프로그램", "함수", "클래스", "구현"],
            "planning": ["계획", "단계", "절차", "순서", "과정"],
            "reasoning": ["왜", "이유", "원인", "분석", "판단"],
            "research": ["조사", "검색", "찾아", "알아봐", "정보"]
        }

        for capability, keywords in capability_keywords.items():
            if any(keyword in user_input_lower for keyword in keywords):
                capabilities.append(capability)

        # 복잡도에 따른 추가 기능
        if complexity == TaskComplexity.COMPLEX:
            capabilities.extend(["multi_step_processing", "quality_assurance"])
        elif complexity == TaskComplexity.MODERATE:
            capabilities.append("context_awareness")

        return list(set(capabilities))  # 중복 제거

    def _generate_reasoning(self, user_input: str, complexity: TaskComplexity,
                            orchestrator: OrchestratorType) -> str:
        """추론 과정 생성"""
        reasons = []

        # 복잡도 판별 이유
        if complexity == TaskComplexity.COMPLEX:
            reasons.append("아키텍처/설계 관련 키워드가 감지되어 복잡한 작업으로 분류")
        elif complexity == TaskComplexity.MODERATE:
            reasons.append("구현/개발 관련 키워드가 감지되어 중간 복잡도로 분류")
        else:
            reasons.append("질문 형태 또는 간단한 요청으로 분류")

        # 오케스트레이터 선택 이유
        if orchestrator == OrchestratorType.CONTROL:
            reasons.append("복잡한 작업을 위해 관제 오케스트레이터 추천")
        elif orchestrator == OrchestratorType.MEMORY:
            reasons.append("기억 활용이 필요한 작업으로 기억 오케스트레이터 추천")
        else:
            reasons.append("단순한 질답을 위해 기본 오케스트레이터 추천")

        return "; ".join(reasons)