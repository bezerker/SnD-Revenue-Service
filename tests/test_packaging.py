import subprocess
import tarfile
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


def test_sdist_does_not_include_worktree_git_metadata(tmp_path: Path) -> None:
    subprocess.run(
        ["uv", "build", "--sdist", "--out-dir", str(tmp_path)],
        check=True,
        capture_output=True,
        text=True,
    )

    sdist_path = next(tmp_path.glob("snd_revenue_service-*.tar.gz"))
    with tarfile.open(sdist_path, "r:gz") as sdist:
        names = {member.name for member in sdist.getmembers()}

    assert "snd_revenue_service-0.1.0/.git" not in names
    assert "snd_revenue_service-0.1.0/src/snd_revenue_service/__main__.py" in names
