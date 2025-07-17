# ===== adapters/ai_providers/ollama_provider_adapter.py =====
"""
Ollama Provider 어댑터 (기존 OllamaProvider 리팩터링)
"""

import requests
import json
import time
import subprocess
import os
from typing import List, Dict, Any, Optional

from .base_provider_adapter import BaseProviderAdapter
from core.shared.models import ChatMessage, ChatResponse, ModelInfo, ProviderType


class OllamaProviderAdapter(BaseProviderAdapter):
    """Ollama Provider 어댑터 (기존 OllamaProvider 개선)"""

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

    def chat(self, messages: List[ChatMessage], **kwargs) -> ChatResponse:
        """Ollama와 채팅 (기존 로직 + 성능 추적)"""
        start_time = time.time()
        success = False

        try:
            # 서버 실행 확인
            if not self._ensure_server_running():
                raise RuntimeError("Ollama 서버를 시작할 수 없습니다")

            # 모델 존재 확인
            if not self._model_exists():
                available_models = self.get_model_names()
                raise RuntimeError(f"모델 '{self.model_name}'이 설치되지 않았습니다. 사용 가능한 모델: {available_models}")

            # 모델 패밀리별 프롬프트 최적화
            prompt = self._messages_to_prompt(messages)

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
            success = True

            # 응답 처리
            content = result.get("response", "")

            # 토큰 사용량 추정
            input_tokens = len(prompt.split()) * 1.3
            output_tokens = len(content.split()) * 1.3

            token_usage = {
                "input_tokens": int(input_tokens),
                "output_tokens": int(output_tokens)
            }

            # 성능 메트릭 업데이트
            self._update_performance_metrics(response_time, success, 0.0)

            return ChatResponse(
                content=content,
                model_info=self._model_info,
                token_usage=token_usage,
                cost_estimate=0.0,
                response_time=response_time,
                metadata={
                    "provider": "ollama",
                    "model_family": self._get_model_family(self.model_name),
                    "server_auto_started": self.server_process is not None
                }
            )

        except Exception as e:
            response_time = time.time() - start_time
            self._update_performance_metrics(response_time, success)
            raise RuntimeError(f"Ollama API 오류: {e}")

    def get_model_info(self) -> ModelInfo:
        """모델 정보 반환"""
        return self._model_info

    def is_available(self) -> bool:
        """Ollama 사용 가능 여부 확인"""
        if self._is_server_running():
            return True

        if self.auto_start_server:
            return self._start_ollama_server()

        return self._check_ollama_installed()

    def get_capabilities(self) -> List[str]:
        """지원하는 기능 목록"""
        return [
            "chat", "streaming", "local_execution", "model_listing",
            "model_switching", "zero_cost", "privacy_focused"
        ]

    # ===== Ollama 특화 메서드들 (기존 로직 유지) =====

    def get_model_names(self) -> List[str]:
        """모델 이름만 반환"""
        try:
            if self._is_server_running():
                response = requests.get(f"{self.url}/api/tags", timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    return [model["name"] for model in data.get("models", [])]
        except:
            pass

        # API 실패 시 CLI 사용
        return self._get_models_via_cli()

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
        }
        family = self._get_model_family(model_name)
        return model_contexts.get(family, 2048)

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

    # ===== 서버 관리 메서드들 (기존 로직 유지) =====

    def _is_server_running(self) -> bool:
        """서버가 실행 중인지 확인"""
        try:
            response = requests.get(f"{self.url}/api/tags", timeout=2)
            return response.status_code == 200
        except:
            return False

    def _check_ollama_installed(self) -> bool:
        """Ollama가 설치되어 있는지 확인"""
        try:
            result = subprocess.run(['ollama', '--version'],
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def _start_ollama_server(self) -> bool:
        """Ollama 서버 시작"""
        if not self._check_ollama_installed():
            return False

        try:
            self.server_process = subprocess.Popen(
                ['ollama', 'serve'],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                preexec_fn=os.setsid if os.name != 'nt' else None
            )

            # 서버가 시작될 때까지 대기
            for _ in range(30):
                if self._is_server_running():
                    return True
                time.sleep(1)

            return False
        except Exception:
            return False

    def _ensure_server_running(self) -> bool:
        """서버가 실행 중인지 확인하고 필요시 시작"""
        if self._is_server_running():
            return True

        if self.auto_start_server:
            return self._start_ollama_server()
        else:
            return False

    def _model_exists(self) -> bool:
        """모델이 설치되어 있는지 확인"""
        try:
            available_models = self.get_model_names()
            return self.model_name in available_models
        except:
            return False

    def _get_models_via_cli(self) -> List[str]:
        """CLI를 통해 설치된 모델 목록 가져오기"""
        try:
            result = subprocess.run(['ollama', 'list'],
                                  capture_output=True, text=True, timeout=10)

            if result.returncode != 0:
                return []

            models = []
            lines = result.stdout.strip().split('\n')

            if len(lines) > 1:
                for line in lines[1:]:
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 1:
                            models.append(parts[0])

            return models
        except Exception:
            return []

    def __del__(self):
        """객체 소멸 시 서버 정리"""
        if hasattr(self, 'server_process') and self.server_process:
            try:
                if os.name == 'nt':  # Windows
                    self.server_process.terminate()
                else:  # Unix-like
                    os.killpg(os.getpgid(self.server_process.pid), signal.SIGTERM)
                self.server_process.wait(timeout=5)
            except:
                pass
            finally:
                self.server_process = None