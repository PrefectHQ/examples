"""Tests for example discovery, the example contract and CATALOG.yaml."""

from pathlib import Path

import pytest
import yaml

from .. import catalog
from ..catalog import discover, main, read_frontmatter

FILE_EXAMPLE = """\
# ---
# title: Hello
# description: Say hello.
# owner: "@PrefectHQ/devrel"
# targets:
#   prefect: ">=3.4"
# tags: [basics]
# ---
#
# Some narrative.

print("hello")
"""

FOLDER_MANIFEST = """\
title: Weather server
description: An MCP server that reports the weather.
owner: "@PrefectHQ/devrel"
targets:
  fastmcp: ">=2.12"
requires_secrets: [WEATHER_API_KEY]
test: import-only
"""


def write(root: Path, rel: str, text: str = "") -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def folder_example(root: Path, rel: str, manifest: str = FOLDER_MANIFEST) -> None:
    write(root, f"{rel}/example.yaml", manifest)
    for name in (*catalog.FOLDER_REQUIRED_FILES, catalog.DEFAULT_ENTRYPOINT):
        write(root, f"{rel}/{name}")


# Frontmatter ---------------------------------------------------------------


def test_read_frontmatter():
    assert read_frontmatter(FILE_EXAMPLE)["targets"] == {"prefect": ">=3.4"}


def test_read_frontmatter_after_shebang():
    assert (
        read_frontmatter("#!/usr/bin/env python\n" + FILE_EXAMPLE)["title"] == "Hello"
    )


def test_read_frontmatter_none():
    assert read_frontmatter("import prefect\n") is None


def test_read_frontmatter_unclosed():
    with pytest.raises(catalog.FrontmatterError):
        read_frontmatter("# ---\n# title: x\n")


# Discovery -----------------------------------------------------------------


def test_repo_catalog_is_valid():
    assert discover().errors == []


def test_file_and_folder_examples(tmp_path):
    write(tmp_path, "prefect/getting-started/hello.py", FILE_EXAMPLE)
    folder_example(tmp_path, "fastmcp/servers/weather")
    write(tmp_path, "fastmcp/servers/weather/server.py", "import fastmcp\n")

    found = discover(tmp_path)

    assert found.errors == []
    by_slug = {e.slug: e for e in found.examples}
    assert set(by_slug) == {"hello", "weather"}
    assert by_slug["hello"].meta.product == ["prefect"]
    assert by_slug["hello"].kind == "file"
    weather = by_slug["weather"]
    assert weather.kind == "folder"
    assert weather.path == "fastmcp/servers/weather"
    assert weather.meta.product == ["fastmcp"]
    assert weather.meta.test == "import-only"
    assert weather.meta.requires_secrets == ["WEATHER_API_KEY"]


def test_legacy_folders_are_not_scanned(tmp_path):
    write(tmp_path, "examples/01_getting_started/hello.py", "print('no frontmatter')\n")
    write(tmp_path, "flows/hello_world.py", "print('no frontmatter')\n")
    assert discover(tmp_path).errors == []


def test_file_without_frontmatter_is_an_error(tmp_path):
    write(tmp_path, "prefect/helpers.py", "x = 1\n")
    (error,) = discover(tmp_path).errors
    assert error.startswith("prefect/helpers.py: no '# ---' frontmatter")


def test_unknown_field_is_an_error(tmp_path):
    write(
        tmp_path,
        "prefect/hello.py",
        FILE_EXAMPLE.replace("# tags:", "# requires_secret: [X]\n# tags:"),
    )
    (error,) = discover(tmp_path).errors
    assert "requires_secret" in error


def test_missing_required_fields(tmp_path):
    write(tmp_path, "prefect/hello.py", "# ---\n# title: Hello\n# ---\n")
    (error,) = discover(tmp_path).errors
    for name in ("description", "owner", "targets"):
        assert name in error


def test_product_must_match_folder(tmp_path):
    write(
        tmp_path,
        "dagster/hello.py",
        FILE_EXAMPLE.replace("# tags:", "# product: prefect\n# tags:"),
    )
    (error,) = discover(tmp_path).errors
    assert "product must include 'dagster'" in error


def test_stacks_require_product(tmp_path):
    write(tmp_path, "stacks/combo/hello.py", FILE_EXAMPLE)
    (error,) = discover(tmp_path).errors
    assert "product" in error


def test_stacks_accept_product_list(tmp_path):
    write(
        tmp_path,
        "stacks/combo.py",
        FILE_EXAMPLE.replace("# tags:", "# product: [prefect, fastmcp]\n# tags:"),
    )
    found = discover(tmp_path)
    assert found.errors == []
    assert found.examples[0].meta.product == ["prefect", "fastmcp"]


DEMO_EXAMPLE = FILE_EXAMPLE.replace('">=3.4"', '"==3.4.11"').replace(
    "# tags:", "# product: prefect\n# tags:"
)


def test_demos_default_to_frozen(tmp_path):
    write(tmp_path, "demos/2026-pycon-hello/hello.py", DEMO_EXAMPLE)
    found = discover(tmp_path)
    assert found.errors == []
    assert found.examples[0].meta.status == "frozen"


def test_demos_cannot_be_maintained(tmp_path):
    write(
        tmp_path,
        "demos/2026-pycon-hello.py",
        DEMO_EXAMPLE.replace("# tags:", "# status: maintained\n# tags:"),
    )
    (error,) = discover(tmp_path).errors
    assert "status must be 'frozen'" in error


@pytest.mark.parametrize("spec", [">=3.4", "==3.4.*", "~=3.4.11", "3.4.11"])
def test_demos_must_pin_exact_versions(tmp_path, spec):
    write(
        tmp_path,
        "demos/2026-pycon-hello.py",
        DEMO_EXAMPLE.replace('"==3.4.11"', f'"{spec}"'),
    )
    (error,) = discover(tmp_path).errors
    assert "targets must pin exact versions" in error


def test_folder_missing_files(tmp_path):
    write(tmp_path, "fastmcp/servers/weather/example.yaml", FOLDER_MANIFEST)
    write(tmp_path, "fastmcp/servers/weather/main.py")
    found = discover(tmp_path)
    (error,) = found.errors
    assert "missing pyproject.toml, uv.lock, README.md" in error
    assert found.examples == []


def test_folder_rejects_runner_fields(tmp_path):
    folder_example(
        tmp_path, "fastmcp/servers/weather", FOLDER_MANIFEST + "cmd: [python, x.py]\n"
    )
    (error,) = discover(tmp_path).errors
    assert "cmd only apply to single-file examples" in error


def test_folder_entrypoint_defaults_to_main(tmp_path):
    folder_example(tmp_path, "fastmcp/servers/weather")
    (example,) = discover(tmp_path).examples
    assert example.meta.entrypoint == "main.py"


def test_folder_custom_entrypoint(tmp_path):
    folder_example(
        tmp_path, "fastmcp/servers/weather", FOLDER_MANIFEST + "entrypoint: server.py\n"
    )
    write(tmp_path, "fastmcp/servers/weather/server.py")
    found = discover(tmp_path)
    assert found.errors == []
    assert found.examples[0].meta.entrypoint == "server.py"


@pytest.mark.parametrize(
    "entrypoint", ["server.py", "../../../outside.py", "/etc/hosts"]
)
def test_folder_entrypoint_must_exist_inside(tmp_path, entrypoint):
    folder_example(
        tmp_path,
        "fastmcp/servers/weather",
        FOLDER_MANIFEST + f"entrypoint: {entrypoint}\n",
    )
    write(tmp_path, "outside.py")  # exists, but outside the example folder
    (error,) = discover(tmp_path).errors
    assert "is not a file inside the folder" in error


def test_file_example_rejects_entrypoint(tmp_path):
    write(
        tmp_path,
        "prefect/hello.py",
        FILE_EXAMPLE.replace("# tags:", "# entrypoint: other.py\n# tags:"),
    )
    (error,) = discover(tmp_path).errors
    assert "entrypoint only applies to folder examples" in error


def test_nested_folder_examples(tmp_path):
    folder_example(tmp_path, "fastmcp/servers/weather")
    folder_example(tmp_path, "fastmcp/servers/weather/inner")
    (error,) = discover(tmp_path).errors
    assert "can't be nested" in error


def test_duplicate_slugs(tmp_path):
    write(tmp_path, "prefect/a/hello.py", FILE_EXAMPLE)
    write(tmp_path, "prefect/b/hello.py", FILE_EXAMPLE)
    (error,) = discover(tmp_path).errors
    assert (
        "slug 'hello' is used by both prefect/a/hello.py and prefect/b/hello.py"
        in error
    )


def test_bad_owner(tmp_path):
    write(
        tmp_path,
        "prefect/hello.py",
        FILE_EXAMPLE.replace('"@PrefectHQ/devrel"', "devrel"),
    )
    (error,) = discover(tmp_path).errors
    assert error.startswith("prefect/hello.py: owner")


# Catalog -------------------------------------------------------------------


def test_main_writes_then_check_passes(tmp_path, capsys):
    write(tmp_path, "prefect/hello.py", FILE_EXAMPLE)
    folder_example(tmp_path, "fastmcp/servers/weather")

    assert main(["--check"], root=tmp_path) == 1  # no catalog yet
    assert main([], root=tmp_path) == 0
    assert main(["--check"], root=tmp_path) == 0

    data = yaml.safe_load((tmp_path / "CATALOG.yaml").read_text())
    assert [e["slug"] for e in data["examples"]] == ["weather", "hello"]
    assert data["examples"][1]["path"] == "prefect/hello.py"
    assert "cmd" not in data["examples"][1]


def test_check_fails_when_example_changes(tmp_path):
    path = write(tmp_path, "prefect/hello.py", FILE_EXAMPLE)
    assert main([], root=tmp_path) == 0
    path.write_text(FILE_EXAMPLE.replace("Say hello.", "Say hi."))
    assert main(["--check"], root=tmp_path) == 1


def test_check_fails_on_invalid_example(tmp_path):
    write(tmp_path, "prefect/hello.py", "x = 1\n")
    assert main(["--check"], root=tmp_path) == 1


def test_last_verified_is_kept(tmp_path):
    write(tmp_path, "prefect/hello.py", FILE_EXAMPLE)
    assert main([], root=tmp_path) == 0
    catalog_path = tmp_path / "CATALOG.yaml"
    catalog_path.write_text(
        catalog_path.read_text().replace(
            "  tags:", "  last_verified: 2026-11-20\n  tags:", 1
        )
    )

    assert main(["--check"], root=tmp_path) == 1  # hand edit no longer matches render
    assert main([], root=tmp_path) == 0
    data = yaml.safe_load(catalog_path.read_text())
    assert str(data["examples"][0]["last_verified"]) == "2026-11-20"
    assert main(["--check"], root=tmp_path) == 0
