from pathlib import Path


def test_ci_workflow_runs_tests_and_docker_build() -> None:
    workflow = Path(".github/workflows/ci.yml").read_text(encoding="utf-8")

    assert "pip install uv" in workflow
    assert "uv run pytest -v" in workflow
    assert "docker build -t snd-revenue-service:ci ." in workflow


def test_dockerfile_runs_package_entrypoint() -> None:
    dockerfile = Path("Dockerfile").read_text(encoding="utf-8")

    assert "uv pip install --system ." in dockerfile
    assert 'CMD ["python", "-m", "snd_revenue_service"]' in dockerfile
