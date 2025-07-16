"""
Ollama Local LLM Provider 구현 - 서버 자동 관리 및 CLI 통합
"""

import requests
import json
import time
import subprocess
import os
import signal
import threading
from typing import List, Dict, Any, Optional
from pathlib import Path

from .base import BaseProvider, ChatMessage, ChatResponse, ModelInfo, ProviderType
from .base import ProviderError, ProviderUnavailableError, ProviderConfigError

class OllamaProvider(BaseProvider):
    """Ollama Local LLM Provider - 서버 자동 관리"""

    def __init__(self, url: str = "http://localhost:11434",
                 model_name: str = "llama3.1:8b",
                 auto_start_server: bool = True, **kwargs):
        super().__init__(model_name, **kwargs)

        self.url = url.rstrip('/')
        self.api_url = f"{self.url}/api"
        self.auto_start_server = auto_start_server
        self.server_process = None

        # 모델 정보 설정
        self._model_info = ModelInfo(
            name=model_name,
            provider="ollama",
            type=ProviderType.LOCAL_LLM,
            max_tokens=self._get_model_context_length(model_name),
            cost_per_1k_tokens=0.0,
            supports_streaming=True,
            supports_function_calling=False,
            metadata={
                "url": self.url,
                "local": True,
                "model_family": self._get_model_family(model_name),
                "auto_start_server": auto_start_server
            }
        )

    def _get_model_family(self, model_name: str) -> str:
        """모델 패밀리 추출"""
        if "llama" in model_name.lower():
            return "llama"
        elif "codellama" in model_name.lower():
            return "codellama"
        elif "phi" in model_name.lower():
            return "phi"
        elif "tinyllama" in model_name.lower():
            return "tinyllama"
        elif "mistral" in model_name.lower():
            return "mistral"
        elif "gemma" in model_name.lower():
            return "gemma"
        else:
            return "unknown"

    def _get_model_context_length(self, model_name: str) -> int:
        """모델별 컨텍스트 길이 추정"""
        model_contexts = {
            "llama": 4096,
            "codellama": 4096,
            "phi": 2048,
            "tinyllama": 2048,
            "mistral": 8192,
            "gemma": 8192
        }

        family = self._get_model_family(model_name)
        return model_contexts.get(family, 2048)

    def _check_ollama_installed(self) -> bool:
        """Ollama가 설치되어 있는지 확인"""
        try:
            result = subprocess.run(['ollama', '--version'],
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def _get_models_via_cli(self) -> List[Dict[str, Any]]:
        """CLI를 통해 설치된 모델 목록 가져오기"""
        try:
            result = subprocess.run(['ollama', 'list'],
                                  capture_output=True, text=True, timeout=10)

            if result.returncode != 0:
                return []

            models = []
            lines = result.stdout.strip().split('\n')

            # 헤더 라인 건너뛰기
            if len(lines) > 1:
                for line in lines[1:]:
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 3:
                            name = parts[0]
                            model_id = parts[1] if len(parts) > 1 else ""
                            size = parts[2] if len(parts) > 2 else "0"
                            modified = " ".join(parts[3:]) if len(parts) > 3 else ""

                            # 크기를 바이트로 변환
                            size_bytes = self._parse_size(size)

                            models.append({
                                "name": name,
                                "id": model_id,
                                "size": size_bytes,
                                "modified": modified,
                                "family": self._get_model_family(name),
                                "context_length": self._get_model_context_length(name)
                            })

            return models

        except Exception as e:
            print(f"⚠️ CLI를 통한 모델 목록 조회 실패: {e}")
            return []

    def _parse_size(self, size_str: str) -> int:
        """크기 문자열을 바이트로 변환"""
        if not size_str or size_str == "0":
            return 0

        try:
            size_str = size_str.upper()
            if 'GB' in size_str:
                return int(float(size_str.replace('GB', '')) * 1024**3)
            elif 'MB' in size_str:
                return int(float(size_str.replace('MB', '')) * 1024**2)
            elif 'KB' in size_str:
                return int(float(size_str.replace('KB', '')) * 1024)
            else:
                return int(float(size_str))
        except:
            return 0

    def _start_ollama_server(self) -> bool:
        """Ollama 서버 시작"""
        if not self._check_ollama_installed():
            print("❌ Ollama가 설치되지 않았습니다.")
            print("   설치 방법: https://ollama.ai/download")
            return False

        try:
            print("🚀 Ollama 서버 시작 중...")

            # 백그라운드에서 서버 시작
            self.server_process = subprocess.Popen(
                ['ollama', 'serve'],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                preexec_fn=os.setsid if os.name != 'nt' else None
            )

            # 서버가 시작될 때까지 대기 (최대 30초)
            for i in range(30):
                if self._is_server_running():
                    print("✅ Ollama 서버 시작 완료")
                    return True
                time.sleep(1)
                if i % 5 == 0:
                    print(f"⏳ 서버 시작 대기 중... ({i+1}/30)")

            print("❌ Ollama 서버 시작 시간 초과")
            return False

        except Exception as e:
            print(f"❌ Ollama 서버 시작 실패: {e}")
            return False

    def _is_server_running(self) -> bool:
        """서버가 실행 중인지 확인"""
        try:
            response = requests.get(f"{self.url}/api/tags", timeout=2)
            return response.status_code == 200
        except:
            return False

    def _stop_ollama_server(self):
        """Ollama 서버 중지"""
        if self.server_process:
            try:
                if os.name == 'nt':  # Windows
                    self.server_process.terminate()
                else:  # Unix-like
                    os.killpg(os.getpgid(self.server_process.pid), signal.SIGTERM)

                self.server_process.wait(timeout=5)
                print("🛑 Ollama 서버 중지됨")
            except:
                pass
            finally:
                self.server_process = None

    def is_available(self) -> bool:
        """Ollama 사용 가능 여부 확인"""
        # 1. 서버가 이미 실행 중인지 확인
        if self._is_server_running():
            return True

        # 2. 자동 시작이 활성화되어 있으면 시작 시도
        if self.auto_start_server:
            return self._start_ollama_server()

        # 3. 자동 시작이 비활성화되어 있으면 설치 여부만 확인
        return self._check_ollama_installed()

    def get_available_models(self) -> List[Dict[str, Any]]:
        """사용 가능한 모델 목록 반환"""
        # 1. 서버가 실행 중이면 API 사용
        if self._is_server_running():
            try:
                response = requests.get(f"{self.url}/api/tags", timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    models = []
                    for model in data.get("models", []):
                        models.append({
                            "name": model["name"],
                            "size": model.get("size", 0),
                            "modified": model.get("modified", ""),
                            "family": self._get_model_family(model["name"]),
                            "context_length": self._get_model_context_length(model["name"])
                        })
                    return models
            except:
                pass

        # 2. API 실패 시 CLI 사용
        print("🔄 CLI를 통해 모델 목록 조회 중...")
        return self._get_models_via_cli()

    def get_model_names(self) -> List[str]:
        """모델 이름만 반환"""
        models = self.get_available_models()
        return [model["name"] for model in models]

    def _ensure_server_running(self) -> bool:
        """서버가 실행 중인지 확인하고 필요시 시작"""
        if self._is_server_running():
            return True

        if self.auto_start_server:
            print("🔄 Ollama 서버가 중지되어 있습니다. 재시작 중...")
            return self._start_ollama_server()
        else:
            print("❌ Ollama 서버가 실행되지 않았습니다.")
            print("   다음 명령으로 서버를 시작하세요: ollama serve")
            return False

    def chat(self, messages: List[ChatMessage], **kwargs) -> ChatResponse:
        """Ollama와 채팅"""

        # 서버 실행 확인
        if not self._ensure_server_running():
            raise ProviderUnavailableError("Ollama 서버를 시작할 수 없습니다")

        # 모델 존재 확인
        if not self._model_exists():
            available_models = self.get_model_names()
            if available_models:
                print(f"❌ 모델 '{self.model_name}'이 설치되지 않았습니다.")
                print(f"   사용 가능한 모델: {', '.join(available_models[:3])}")
                print(f"   설치 명령: ollama pull {self.model_name}")
            else:
                print("❌ 설치된 모델이 없습니다.")
                print("   모델 설치 예시: ollama pull llama3.1:8b")
            raise ProviderError(f"모델 '{self.model_name}'을 사용할 수 없습니다")

        # 모델 패밀리별 프롬프트 최적화
        prompt = self._messages_to_prompt(messages)

        start_time = time.time()

        try:
            response = requests.post(
                f"{self.api_url}/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": kwargs.get("temperature", 0.7),
                        "num_predict": kwargs.get("max_tokens", 2000),
                        "top_p": kwargs.get("top_p", 0.9),
                        "stop": kwargs.get("stop", [])
                    }
                },
                timeout=120
            )

            response.raise_for_status()
            result = response.json()

            response_time = time.time() - start_time

            # 응답 처리
            content = result.get("response", "")

            # 토큰 사용량 추정
            input_tokens = len(prompt.split()) * 1.3
            output_tokens = len(content.split()) * 1.3

            token_usage = {
                "input_tokens": int(input_tokens),
                "output_tokens": int(output_tokens)
            }

            return ChatResponse(
                content=content,
                model_info=self._model_info,
                token_usage=token_usage,
                cost_estimate=0.0,
                response_time=response_time,
                metadata={
                    "raw_response": result,
                    "model_family": self._get_model_family(self.model_name),
                    "server_auto_started": self.server_process is not None
                }
            )

        except requests.RequestException as e:
            raise ProviderError(f"Ollama API 오류: {e}")
        except Exception as e:
            raise ProviderError(f"예상치 못한 오류: {e}")

    def _model_exists(self) -> bool:
        """모델이 설치되어 있는지 확인"""
        try:
            available_models = self.get_model_names()
            return self.model_name in available_models
        except:
            return False

    def switch_model(self, new_model_name: str) -> bool:
        """모델 변경"""
        try:
            available_models = self.get_model_names()
            if new_model_name not in available_models:
                print(f"❌ 모델 '{new_model_name}'이 설치되지 않았습니다.")
                print(f"   설치 명령: ollama pull {new_model_name}")
                return False

            # 모델 정보 업데이트
            self.model_name = new_model_name
            self._model_info = ModelInfo(
                name=new_model_name,
                provider="ollama",
                type=ProviderType.LOCAL_LLM,
                max_tokens=self._get_model_context_length(new_model_name),
                cost_per_1k_tokens=0.0,
                supports_streaming=True,
                supports_function_calling=False,
                metadata={
                    "url": self.url,
                    "local": True,
                    "model_family": self._get_model_family(new_model_name),
                    "auto_start_server": self.auto_start_server
                }
            )

            return True

        except Exception as e:
            print(f"❌ 모델 변경 실패: {e}")
            return False

    def get_model_recommendations(self) -> Dict[str, str]:
        """모델별 추천 용도"""
        return {
            "llama3.1:8b": "일반적인 대화 및 텍스트 생성",
            "codellama:latest": "코딩, 프로그래밍 도움 (🔥 코딩 추천)",
            "phi4:latest": "빠른 추론, 간단한 질문",
            "tinyllama:latest": "매우 빠른 응답, 리소스 절약",
            "mistral": "높은 품질의 텍스트 생성",
            "gemma": "구글의 고성능 모델"
        }

    def _messages_to_prompt(self, messages: List[ChatMessage]) -> str:
        """메시지들을 모델별 최적화된 프롬프트로 변환"""
        family = self._get_model_family(self.model_name)

        if family == "codellama":
            return self._codellama_prompt(messages)
        elif family == "phi":
            return self._phi_prompt(messages)
        elif family == "tinyllama":
            return self._tinyllama_prompt(messages)
        else:
            return self._llama_prompt(messages)

    def _codellama_prompt(self, messages: List[ChatMessage]) -> str:
        """CodeLlama 최적화 프롬프트"""
        prompt_parts = []

        for msg in messages:
            if msg.role == "system":
                prompt_parts.append(f"<s>\n{msg.content}\n</s>")
            elif msg.role == "user":
                prompt_parts.append(f"<user>\n{msg.content}\n</user>")
            elif msg.role == "assistant":
                prompt_parts.append(f"<assistant>\n{msg.content}\n</assistant>")

        prompt_parts.append("<assistant>")
        return "\n\n".join(prompt_parts)

    def _phi_prompt(self, messages: List[ChatMessage]) -> str:
        """Phi 최적화 프롬프트"""
        prompt_parts = []

        for msg in messages:
            if msg.role == "system":
                prompt_parts.append(f"System: {msg.content}")
            elif msg.role == "user":
                prompt_parts.append(f"User: {msg.content}")
            elif msg.role == "assistant":
                prompt_parts.append(f"Assistant: {msg.content}")

        return "\n".join(prompt_parts)

    def _tinyllama_prompt(self, messages: List[ChatMessage]) -> str:
        """TinyLlama 최적화 프롬프트"""
        if messages:
            last_msg = messages[-1]
            if last_msg.role == "user":
                return last_msg.content

        return self._llama_prompt(messages)

    def _llama_prompt(self, messages: List[ChatMessage]) -> str:
        """기본 Llama 프롬프트"""
        prompt_parts = []

        for msg in messages:
            if msg.role == "system":
                prompt_parts.append(f"System: {msg.content}")
            elif msg.role == "user":
                prompt_parts.append(f"User: {msg.content}")
            elif msg.role == "assistant":
                prompt_parts.append(f"Assistant: {msg.content}")

        return "\n\n".join(prompt_parts)

    def validate_config(self) -> bool:
        """설정 유효성 검증"""
        return self._check_ollama_installed()

    def get_supported_features(self) -> List[str]:
        """지원하는 기능 목록"""
        return [
            "chat",
            "streaming",
            "local_execution",
            "model_listing",
            "model_switching",
            "model_optimization",
            "server_auto_start",
            "cli_integration"
        ]

    def __del__(self):
        """객체 소멸 시 서버 정리"""
        if hasattr(self, 'server_process') and self.server_process:
            self._stop_ollama_server()