#!/usr/bin/env python3
"""반출 압축 — 검사를 모두 통과한 프로젝트만 zip으로 묶는다.

순서: Ruff 검사 → Ruff 포맷 → Pyrefly → pytest(커버리지 80%) → 키 섞임 검사 → 압축.
하나라도 실패하면 거기서 멈추고 압축하지 않는다.

사용:
    python3 export.py <프로젝트 경로>               # 전체 검사 후 압축
    python3 export.py --check-only <프로젝트 경로>  # 키 섞임 검사와 반출 목록만

맥 기본 python3(3.9)로도 돌도록 표준 라이브러리만 쓴다.
"""
from __future__ import annotations

import argparse
import datetime
import fnmatch
import re
import subprocess
import sys
import zipfile
from pathlib import Path

COVERAGE_MIN = 80

# 반출 제외 목록 — python-project 스킬의 표와 같아야 한다.
EXCLUDE_DIRS = {
    ".git", ".venv", "__pycache__", ".pytest_cache", ".ruff_cache",
    "htmlcov", ".idea", ".vscode", ".mypy_cache", "dist", "build",
}
EXCLUDE_PATHS = {"evals/results", "docs"}
EXCLUDE_FILES = {".coverage", "coverage.xml", ".DS_Store"}
EXCLUDE_GLOBS = ["*.pyc", ".env", ".env.*", ".coverage.*"]
KEEP_FILES = {".env.example"}

REQUIRED = ["main.py", "pyproject.toml", "app"]

# 흔한 키 모양. 오탐은 확인 한 번이면 되지만 미탐은 되돌릴 수 없어서 넓게 잡는다.
SECRET_PATTERNS = [
    ("OpenAI 호환 키", re.compile(r"sk-[A-Za-z0-9_\-]{20,}")),
    ("AWS 액세스 키", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("개인 키", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("Bearer 토큰", re.compile(r"Bearer\s+[A-Za-z0-9._\-]{20,}")),
    (
        "키 값 직접 대입",
        re.compile(
            r"""(?i)(api[_-]?key|secret|password|passwd|token)\s*[:=]\s*["'][^"'\s]{8,}["']"""
        ),
    ),
]
MIN_ENV_VALUE_LENGTH = 8
# 테스트·견본에 일부러 넣은 가짜 값. 진짜 키는 아래 .env 값 대조로 따로 잡는다.
DUMMY_VALUE = re.compile(r"(?i)(test|dummy|fake|example|sample|placeholder|changeme|xxxx)")
# 모델 이름처럼 문서에 써도 되는 값은 빼고, 키·주소 값만 찾는다.
SECRET_ENV_KEY = re.compile(r"(?i)(KEY|SECRET|PASSWORD|TOKEN|URL|DSN)")
TEXT_SUFFIXES = {
    ".py", ".md", ".txt", ".toml", ".cfg", ".ini", ".json", ".jsonl", ".yaml",
    ".yml", ".sh", ".env", ".example", ".html", ".csv",
}


def is_excluded(rel: Path) -> bool:
    parts = rel.parts
    if any(part in EXCLUDE_DIRS for part in parts):
        return True
    rel_posix = rel.as_posix()
    if any(rel_posix == p or rel_posix.startswith(p + "/") for p in EXCLUDE_PATHS):
        return True
    name = rel.name
    if name in KEEP_FILES:
        return False
    if name in EXCLUDE_FILES:
        return True
    return any(fnmatch.fnmatch(name, g) for g in EXCLUDE_GLOBS)


def collect_files(root: Path) -> list[Path]:
    files = []
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root)
        if path.is_file() and not is_excluded(rel):
            files.append(rel)
    return files


def read_env_values(root: Path) -> list[str]:
    """로컬 .env의 실제 값 — 소스에 그대로 들어갔는지 찾는 데 쓴다."""
    env = root / ".env"
    if not env.is_file():
        return []
    values = []
    for line in env.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = (part.strip() for part in line.split("=", 1))
        value = value.strip("\"'")
        if SECRET_ENV_KEY.search(key) and len(value) >= MIN_ENV_VALUE_LENGTH:
            values.append(value)
    return values


def scan_secrets(root: Path, files: list[Path]) -> list[str]:
    env_values = read_env_values(root)
    findings = []
    for rel in files:
        if rel.suffix not in TEXT_SUFFIXES and rel.name not in KEEP_FILES:
            continue
        text = (root / rel).read_text(encoding="utf-8", errors="ignore")
        for lineno, line in enumerate(text.splitlines(), 1):
            for label, pattern in SECRET_PATTERNS:
                match = pattern.search(line)
                if match and not DUMMY_VALUE.search(match.group(0)):
                    findings.append(f"{rel}:{lineno} — {label}")
            if any(value in line for value in env_values):
                findings.append(f"{rel}:{lineno} — .env의 실제 값")
    return findings


def run_step(label: str, cmd: list[str], root: Path) -> bool:
    print(f"\n▶ {label}: {' '.join(cmd)}", flush=True)
    if not Path(cmd[0]).exists():
        print(f"✗ {cmd[0]} 이(가) 없습니다. 가상환경 설치를 먼저 하세요 (python-project).")
        return False
    result = subprocess.run(cmd, cwd=root)
    if result.returncode != 0:
        print(f"✗ {label} 실패 — 압축하지 않습니다.")
        return False
    print(f"✓ {label} 통과")
    return True


def run_checks(root: Path) -> bool:
    bin_dir = root / ".venv" / "bin"
    steps = [
        ("Ruff 검사", [str(bin_dir / "ruff"), "check", "."]),
        ("Ruff 포맷", [str(bin_dir / "ruff"), "format", "--check", "."]),
        ("Pyrefly 타입 검사", [str(bin_dir / "pyrefly"), "check"]),
        (
            "pytest + 커버리지",
            [
                str(bin_dir / "pytest"), "-q", "--cov=app",
                "--cov-report=term-missing", f"--cov-fail-under={COVERAGE_MIN}",
            ],
        ),
    ]
    return all(run_step(label, cmd, root) for label, cmd in steps)


def check_required(root: Path) -> list[str]:
    missing = [name for name in REQUIRED if not (root / name).exists()]
    if not (root / "run-application.sh").exists():
        print("! run-application.sh 가 없습니다. 운영 플랫폼에서 서버를 띄울 수 없을 수 있습니다.")
    return missing


def write_zip(root: Path, files: list[Path], out_dir: Path) -> Path:
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    target = out_dir / f"{root.name}_{stamp}.zip"
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as zf:
        for rel in files:
            zf.write(root / rel, Path(root.name) / rel)
    return target


def main() -> int:
    parser = argparse.ArgumentParser(description="반출용 압축 만들기")
    parser.add_argument("project", nargs="?", default=".")
    parser.add_argument("--check-only", action="store_true", help="키 검사와 목록만")
    parser.add_argument("--out", help="압축 파일을 둘 폴더 (기본: 프로젝트의 상위 폴더)")
    args = parser.parse_args()

    root = Path(args.project).resolve()
    missing = check_required(root)
    if missing:
        print(f"✗ 필수 파일이 없습니다: {', '.join(missing)}")
        return 1

    if not args.check_only and not run_checks(root):
        return 1

    files = collect_files(root)
    print(f"\n▶ 키 섞임 검사 ({len(files)}개 파일)")
    findings = scan_secrets(root, files)
    if findings:
        print("✗ 키로 보이는 값이 있습니다 — 압축하지 않습니다.")
        for item in findings:
            print(f"  - {item}")
        return 1
    print("✓ 키 섞임 없음")

    if args.check_only:
        print("\n반출 대상 파일:")
        for rel in files:
            print(f"  {rel}")
        return 0

    out_dir = Path(args.out).resolve() if args.out else root.parent
    target = write_zip(root, files, out_dir)
    size_kb = target.stat().st_size / 1024
    print(f"\n✓ 압축 완료: {target} ({len(files)}개 파일, {size_kb:.0f}KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
