# 📦 multi-ai-orchestra 프로젝트 구조

새로운 프로젝트 구조는 명확한 도메인 분리, 인터페이스 정의, 어댑터 및 인프라 계층 분리를 기반으로 설계되었습니다.

---

## 📁 루트 디렉터리 구조
```
multi-ai-orchestra/                    # 새로운 프로젝트 루트
├── 📁 core/                           # 핵심 도메인 로직
│   ├── 📁 memory/                     # 기억 도메인 (기존 ai_memory 이동)
│   │   ├── __init__.py
│   │   ├── memory_manager.py          # 기존 ai_memory/core/memory_manager.py
│   │   ├── memory_consolidator.py     # TODO: Phase 2
│   │   └── semantic_analyzer.py       # TODO: Phase 2
│   │
│   ├── 📁 control/                    # 관제 도메인 (신규)
│   │   ├── __init__.py
│   │   ├── task_analyzer.py           # Phase 1: 간단한 분류만
│   │   ├── orchestrator_coordinator.py # Phase 1: 기본 조율
│   │   ├── workflow_manager.py        # TODO: Phase 2
│   │   └── quality_controller.py      # TODO: Phase 3
│   │
│   └── 📁 shared/                     # 공유 도메인
│       ├── __init__.py
│       ├── models.py                  # 기존 ai_memory/data/models.py
│       ├── events.py                  # TODO: Phase 2
│       ├── exceptions.py              # 새로 작성
│       └── value_objects.py           # TODO: Phase 2
│
├── 📁 ports/                          # 포트 정의 (인터페이스)
│   ├── __init__.py
│   ├── 📁 memory_ports/
│   │   ├── __init__.py
│   │   ├── memory_repository.py       # 기억 저장소 인터페이스
│   │   └── search_service.py          # 검색 서비스 인터페이스
│   │
│   ├── 📁 control_ports/
│   │   ├── __init__.py
│   │   ├── task_analysis_service.py   # 작업 분석 인터페이스
│   │   └── orchestration_service.py   # 오케스트레이션 인터페이스
│   │
│   └── 📁 ai_ports/
│       ├── __init__.py
│       ├── ai_provider.py             # AI 제공자 인터페이스
│       └── model_selector.py          # 모델 선택 인터페이스
│
├── 📁 adapters/                       # 어댑터 구현
│   ├── __init__.py
│   ├── 📁 ai_providers/               # 기존 ai_memory/providers 이동
│   │   ├── __init__.py
│   │   ├── base_provider.py           # 기존 providers/base.py
│   │   ├── claude_provider.py         # 기존 providers/claude.py
│   │   ├── ollama_provider.py         # 기존 providers/ollama.py
│   │   └── provider_factory.py        # 기존 providers/__init__.py 리팩터링
│   │
│   ├── 📁 storage/                    # 저장소 어댑터
│   │   ├── __init__.py
│   │   ├── file_storage.py            # 기존 유틸리티들 통합
│   │   ├── memory_repository_impl.py  # 메모리 저장소 구현
│   │   └── vector_storage.py          # TODO: Phase 2
│   │
│   └── 📁 interfaces/                 # 사용자 인터페이스
│       ├── __init__.py
│       ├── cli_interface.py           # 기존 interfaces/cli.py
│       ├── interactive_interface.py   # 기존 interfaces/interactive.py
│       └── web_interface.py           # TODO: Phase 3
│
├── 📁 application/                    # 애플리케이션 서비스 레이어
│   ├── __init__.py
│   ├── 📁 orchestrators/              # 오케스트레이터들
│   │   ├── __init__.py
│   │   ├── base_orchestrator.py       # 기본 오케스트레이터 인터페이스
│   │   ├── memory_orchestrator.py     # 기억 중심 (Phase 1)
│   │   ├── control_orchestrator.py    # 관제 중심 (Phase 1)
│   │   ├── simple_orchestrator.py     # 기존 방식 래핑 (Phase 1)
│   │   └── personality_orchestrator.py # TODO: Phase 2
│   │
│   ├── 📁 use_cases/                  # 사용 사례
│   │   ├── __init__.py
│   │   ├── simple_chat.py             # Phase 1: 기본 채팅
│   │   ├── memory_search.py           # Phase 1: 기억 검색
│   │   └── complex_task.py            # TODO: Phase 2
│   │
│   └── 📁 services/                   # 애플리케이션 서비스
│       ├── __init__.py
│       ├── orchestrator_selector.py   # Phase 1: 오케스트레이터 선택
│       └── session_manager.py         # Phase 1: 세션 관리
│
├── 📁 infrastructure/                 # 인프라스트럭처
│   ├── __init__.py
│   ├── 📁 config/                     # 설정 관리
│   │   ├── __init__.py
│   │   ├── settings.py                # 전체 설정
│   │   └── orchestrator_config.py     # 오케스트레이터 설정
│   │
│   ├── 📁 utils/                      # 기존 ai_memory/utils 이동
│   │   ├── __init__.py
│   │   ├── file_utils.py              # 기존 utils/file_utils.py
│   │   ├── search_utils.py            # 기존 utils/search_utils.py
│   │   └── logging_utils.py           # 새로 추가
│   │
│   └── 📁 monitoring/                 # TODO: Phase 2
│       ├── __init__.py
│       ├── performance_monitor.py     # TODO
│       └── metrics_collector.py       # TODO
│
├── 📁 tests/                          # 테스트 (기존 유지)
│   ├── __init__.py
│   ├── 📁 unit/
│   │   ├── test_memory_manager.py     # 기존 테스트 이동
│   │   ├── test_providers.py          # 기존 테스트 이동
│   │   └── test_orchestrators.py      # 새로 추가
│   │
│   ├── 📁 integration/
│   │   ├── test_orchestration_flow.py # 새로 추가
│   │   └── test_memory_integration.py # 새로 추가
│   │
│   └── 📁 e2e/
│       └── test_full_workflow.py      # 새로 추가
│
├── 📁 docs/                          # 문서화
│   ├── README.md                      # 새로 작성
│   ├── ARCHITECTURE.md                # 아키텍처 문서
│   ├── MIGRATION_GUIDE.md             # 마이그레이션 가이드
│   └── PHASE_PLAN.md                  # Phase별 계획
│
├── 📁 scripts/                       # 스크립트
│   ├── migrate_from_ai_memory.py      # 기존 데이터 마이그레이션
│   ├── setup_dev_env.py               # 개발 환경 설정
│   └── run_tests.py                   # 테스트 실행
│
├── 📁 examples/                       # 예제
│   ├── basic_usage.py                 # 기본 사용법
│   ├── orchestrator_examples.py       # 오케스트레이터 예제
│   └── migration_example.py           # 마이그레이션 예제
│
# 메인 실행 파일들
├── main.py                           # 통합 진입점
├── orchestra_cli.py                  # CLI 진입점 (기존 ai_memory_cli.py 개선)
├── requirements.txt                  # 의존성
├── pyproject.toml                    # 프로젝트 설정
├── .env.example                      # 환경변수 예시
└── LICENSE                           # 라이선스
```
---

## 🔁 파일 마이그레이션 매핑

| 기존 경로 | → | 새로운 경로 |
|-----------|---|--------------|
| `ai_memory/core/memory_manager.py` | → | `core/memory/memory_manager.py` |
| `ai_memory/data/models.py` | → | `core/shared/models.py` |
| `ai_memory/providers/` | → | `adapters/ai_providers/` |
| `ai_memory/interfaces/` | → | `adapters/interfaces/` |
| `ai_memory/utils/` | → | `infrastructure/utils/` |
| `ai_memory/tests/` | → | `tests/` (구조 개선 포함) |
| `ai_memory_cli.py` | → | `orchestra_cli.py` (개선됨) |

---

## 🧭 Phase 계획 대응 현황

| Phase | 주요 구현 내용 |
|-------|----------------|
| Phase 1 | `task_analyzer.py`, `orchestrator_coordinator.py`, `simple_chat.py`, `orchestrator_selector.py`, `session_manager.py`, CLI 개선 등 |
| Phase 2 | `memory_consolidator.py`, `semantic_analyzer.py`, `workflow_manager.py`, `vector_storage.py`, `events.py`, `value_objects.py`, `complex_task.py` 등 |
| Phase 3 | `quality_controller.py`, `web_interface.py`, `performance_monitor.py`, `metrics_collector.py` 등 |

---

## 📌 참고

- 이 구조는 **Hexagonal Architecture (Ports & Adapters)** 및 **DDD (Domain-Driven Design)**의 영향을 받아 설계됨
- 각 계층은 명확한 **관심사 분리(SOC)**를 유지하며, 테스트 용이성 및 유지보수성을 높임

---