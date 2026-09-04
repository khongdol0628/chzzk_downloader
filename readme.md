# CHZZK_DOWNLOADER

치지직 통합 녹화·VOD 다운로더

## 개발 환경 준비

프로젝트의 실행 및 개발 의존성은 [uv](https://docs.astral.sh/uv/)로 관리합니다.

```bash
uv sync --dev
```

## 품질 검사

### Ruff

lint 검사를 실행합니다.

```bash
uv run ruff check .
```

자동으로 수정할 수 있는 lint 문제를 고치려면 다음 명령을 실행합니다.

```bash
uv run ruff check . --fix
```

코드 포맷이 적용되어 있는지 검사합니다.

```bash
uv run ruff format --check .
```

코드 포맷을 적용하려면 다음 명령을 실행합니다.

```bash
uv run ruff format .
```

### pyrefly

타입 검사를 실행합니다.

```bash
uv run pyrefly check
```

### pytest

전체 테스트를 실행합니다.

```bash
uv run pytest
```
