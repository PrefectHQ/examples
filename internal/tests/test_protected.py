"""Tests for the protected-paths check."""

from pathlib import Path

from ..protected import check_protected


def _config(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "protected_paths.yaml"
    path.write_text(text, encoding="utf-8")
    return path


def test_repo_protected_paths_are_intact():
    assert check_protected() == []


def test_missing_file_is_reported(tmp_path):
    config = _config(tmp_path, "entrypoints:\n  - flows/gone.py:hello\n")
    assert check_protected(tmp_path, config) == [
        "flows/gone.py:hello: file flows/gone.py is missing"
    ]


def test_renamed_function_is_reported(tmp_path):
    (tmp_path / "flows").mkdir()
    (tmp_path / "flows" / "hello.py").write_text("def greet():\n    pass\n")
    config = _config(tmp_path, "entrypoints:\n  - flows/hello.py:hello\n")
    problems = check_protected(tmp_path, config)
    assert len(problems) == 1
    assert "no longer defines a top-level 'hello'" in problems[0]


def test_async_function_and_paths_pass(tmp_path):
    (tmp_path / "flows").mkdir()
    (tmp_path / "flows" / "hello.py").write_text("async def hello():\n    pass\n")
    (tmp_path / "apps" / "bg").mkdir(parents=True)
    config = _config(
        tmp_path, "entrypoints:\n  - flows/hello.py:hello\npaths:\n  - apps/bg\n"
    )
    assert check_protected(tmp_path, config) == []


def test_missing_path_is_reported(tmp_path):
    config = _config(tmp_path, "paths:\n  - apps/bg\n")
    assert check_protected(tmp_path, config) == ["apps/bg: path is missing"]
