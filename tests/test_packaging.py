from pathlib import Path


def test_ci_workflow_runs_tests_and_docker_build() -> None:
    workflow = Path(".github/workflows/ci.yml").read_text(encoding="utf-8")

    assert 'UV_VERSION: "0.10.9"' in workflow
    assert 'pip install "uv==${UV_VERSION}"' in workflow
    assert "uv sync --frozen --all-groups" in workflow
    assert "uv run pytest -v" in workflow
    assert "docker build -t snd-revenue-service:ci ." in workflow


def test_dockerfile_uses_locked_dependencies_and_runs_package_entrypoint() -> None:
    dockerfile = Path("Dockerfile").read_text(encoding="utf-8")

    assert "COPY pyproject.toml uv.lock README.md ./" in dockerfile
    assert 'ARG UV_VERSION=0.10.9' in dockerfile
    assert 'pip install --no-cache-dir "uv==${UV_VERSION}"' in dockerfile
    assert "uv sync --frozen --no-dev --no-editable" in dockerfile
    assert 'CMD [".venv/bin/python", "-m", "snd_revenue_service"]' in dockerfile


def test_dockerignore_excludes_generated_python_artifacts() -> None:
    dockerignore = Path(".dockerignore").read_text(encoding="utf-8")

    assert ".venv" in dockerignore
    assert "__pycache__/" in dockerignore
