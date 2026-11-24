# Example contract

Every example under `prefect/`, `dagster/`, `fastmcp/`, `stacks/`, `learn/` and `demos/` follows this contract. CI checks it with `python -m internal.catalog --check`.

## Two shapes

**Single-file example.** One `.py` file that opens with a frontmatter block written as comments:

```python
# ---
# title: Hello, world!
# description: Your first Prefect flow.
# owner: "@PrefectHQ/devrel"
# targets:
#   prefect: ">=3.4"
# tags: [getting_started]
# ---
```

**Folder example.** A folder with an `example.yaml` file. The folder must also contain:

- `pyproject.toml` with the example's own dependencies
- `uv.lock`, so heavy dependencies never collide with other examples
- `README.md` that opens with the versions it targets

Every `.py` file inside a folder example belongs to it and is not checked on its own. Folder examples can't be nested.

Any other `.py` file under the product folders must have a frontmatter block, so no example goes missing from the catalog. Put helper modules inside a folder example.

## Fields

| Field | Required | Values | Default |
| --- | --- | --- | --- |
| `title` | yes | Text | |
| `description` | yes | One sentence | |
| `owner` | yes | GitHub user or team, such as `"@PrefectHQ/devrel"` | |
| `targets` | yes | Map of package to version spec, such as `{prefect: ">=3.4"}`. Demos must pin exact versions, such as `{prefect: "==3.4.11"}` | |
| `product` | under `stacks/`, `learn/`, `demos/` | `prefect`, `dagster`, `fastmcp`, or a list of them | The top-level folder under `prefect/`, `dagster/`, `fastmcp/` |
| `status` | no | `maintained` or `frozen`. Always `frozen` under `demos/` | `maintained` (`frozen` under `demos/`) |
| `test` | no | `run`, `import-only` or `skip` | `run` |
| `requires_secrets` | no | List of environment variable names | `[]` |
| `timeout` | no | Seconds | `600` |
| `tags` | no | List of strings | `[]` |
| `entrypoint` | no, folder examples only | File the runner executes, relative to the folder | `main.py` |

Single-file examples may also set the runner fields `cmd`, `args`, `env`, `dependencies`, `icon` and `draft` used by the existing tooling. Any other field is an error, so typos fail CI instead of being ignored.

## How examples run

`python -m internal.runner` runs examples in CI. Each one gets its own environment:

- **Folder example:** `uv run --project <folder> --locked python <entrypoint>`, from inside the folder, so it uses its own `uv.lock`.
- **Single-file example:** a throwaway environment with its `targets` and `dependencies`, then `python <file>` (or `cmd` and `args` if set).
- **`test: import-only`** imports the entrypoint without running its `if __name__ == "__main__"` block. Use it for servers and anything that doesn't exit on its own.
- **`test: skip`** never runs.
- **`requires_secrets`:** the example is skipped, not failed, unless every listed environment variable is set.
- **`timeout`:** the run fails if it doesn't exit in time.

```bash
python -m internal.runner run hello weather                 # by slug
python -m internal.runner run --changed-since origin/main   # what a PR changes
python -m internal.runner run --all --dry-run               # list every maintained example
```

CI runs it twice:

- **On every PR** ([`pr.yml`](../.github/workflows/pr.yml)): only the examples the PR changes. Changing the runner itself runs every maintained example.
- **After releases** ([`release.yml`](../.github/workflows/release.yml)): every maintained example, against the newest release instead of the lockfile, when Prefect, Dagster or FastMCP sends a `repository_dispatch` event. Also weekly and on demand. Each failure opens an issue for the example's owner. Frozen demos never run here.

## Catalog

[`CATALOG.yaml`](../CATALOG.yaml) is generated from these fields. Don't edit it by hand:

```bash
python -m internal.catalog          # regenerate
python -m internal.catalog --check  # fail if it's out of date or an example is invalid
```

Each entry gets a `slug` (the folder name or file stem, unique across the repo) and a `path`. `last_verified` is written by the post-release CI run and kept when the catalog is regenerated.
