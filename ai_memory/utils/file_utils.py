"""
파일 관련 유틸리티 함수들 - 인코딩 문제 해결 버전
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List

def ensure_directory(path: Path):
    """디렉토리가 없으면 생성"""
    path.mkdir(parents=True, exist_ok=True)

def load_json_file(filepath: Path) -> Dict[str, Any]:
    """JSON 파일 로드 - 인코딩 문제 해결"""
    try:
        # UTF-8으로 시도
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except UnicodeDecodeError:
        try:
            # UTF-8 실패 시 다른 인코딩들 시도
            encodings = ['utf-8-sig', 'cp949', 'euc-kr', 'latin-1']
            for encoding in encodings:
                try:
                    with open(filepath, 'r', encoding=encoding) as f:
                        data = json.load(f)
                        # 성공하면 UTF-8로 다시 저장
                        save_json_file(filepath, data)
                        return data
                except (UnicodeDecodeError, json.JSONDecodeError):
                    continue

            # 모든 인코딩 실패 시 바이너리로 읽어서 처리
            with open(filepath, 'rb') as f:
                content = f.read()
                # 바이너리 내용을 UTF-8로 강제 디코딩 (오류 무시)
                text_content = content.decode('utf-8', errors='ignore')
                return json.loads(text_content)

        except Exception as e:
            print(f"⚠️ 파일 로드 실패 ({filepath}): {e}")
            # 파일 백업 후 빈 객체 반환
            backup_corrupted_file(filepath)
            return {}

    except json.JSONDecodeError as e:
        print(f"⚠️ JSON 형식 오류 ({filepath}): {e}")
        backup_corrupted_file(filepath)
        return {}

    except Exception as e:
        print(f"⚠️ 파일 읽기 오류 ({filepath}): {e}")
        return {}

def save_json_file(filepath: Path, data: Dict[str, Any]):
    """JSON 파일 저장 - 인코딩 명시적 지정"""
    try:
        # 디렉토리 존재 확인
        ensure_directory(filepath.parent)

        # 임시 파일에 먼저 저장 (원자적 쓰기)
        temp_file = filepath.with_suffix('.tmp')

        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        # 성공하면 원본 파일로 이동
        if filepath.exists():
            backup_path = filepath.with_suffix('.bak')
            filepath.rename(backup_path)

        temp_file.rename(filepath)

        # 백업 파일 정리 (성공 시)
        backup_path = filepath.with_suffix('.bak')
        if backup_path.exists():
            backup_path.unlink()

    except Exception as e:
        print(f"⚠️ 파일 저장 실패 ({filepath}): {e}")
        # 임시 파일 정리
        temp_file = filepath.with_suffix('.tmp')
        if temp_file.exists():
            temp_file.unlink()
        raise

def backup_corrupted_file(filepath: Path):
    """손상된 파일 백업"""
    try:
        if filepath.exists():
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = filepath.with_suffix(f'.corrupted_{timestamp}')
            filepath.rename(backup_path)
            print(f"🔄 손상된 파일 백업됨: {backup_path}")
    except Exception as e:
        print(f"⚠️ 백업 실패: {e}")

def get_recent_files(directory: Path, pattern: str = "*.json",
                    limit: int = 10) -> List[Path]:
    """최근 파일들 가져오기"""
    try:
        files = []
        for file_path in directory.glob(pattern):
            try:
                # 파일 상태 확인
                stat = file_path.stat()
                files.append((file_path, stat.st_mtime))
            except Exception:
                # 손상된 파일 건너뛰기
                continue

        # 수정 시간순 정렬
        files.sort(key=lambda x: x[1], reverse=True)
        return [f[0] for f in files[:limit]]

    except Exception as e:
        print(f"⚠️ 파일 목록 조회 실패: {e}")
        return []

def check_file_integrity(filepath: Path) -> bool:
    """파일 무결성 확인"""
    try:
        if not filepath.exists():
            return False

        # 파일 크기 확인
        if filepath.stat().st_size == 0:
            return False

        # JSON 파일인 경우 파싱 테스트
        if filepath.suffix == '.json':
            load_json_file(filepath)

        return True

    except Exception:
        return False

def clean_corrupted_files(directory: Path):
    """손상된 파일들 정리"""
    try:
        cleaned_count = 0
        for file_path in directory.glob("*.corrupted_*"):
            try:
                file_path.unlink()
                cleaned_count += 1
            except Exception:
                continue

        if cleaned_count > 0:
            print(f"🧹 {cleaned_count}개의 손상된 파일 정리됨")

    except Exception as e:
        print(f"⚠️ 파일 정리 실패: {e}")

def repair_json_files(directory: Path):
    """JSON 파일 복구 시도"""
    try:
        repaired_count = 0
        for json_file in directory.glob("*.json"):
            if not check_file_integrity(json_file):
                try:
                    # 빈 JSON 객체로 초기화
                    save_json_file(json_file, {})
                    repaired_count += 1
                    print(f"🔧 복구됨: {json_file}")
                except Exception:
                    continue

        if repaired_count > 0:
            print(f"🔧 {repaired_count}개의 파일 복구됨")

    except Exception as e:
        print(f"⚠️ 파일 복구 실패: {e}")