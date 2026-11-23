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
| `targets` | yes | Map of package to version spec, such as `{prefect: ">=3.4"}`. Demos pin exact versions | |
| `product` | under `stacks/`, `learn/`, `demos/` | `prefect`, `dagster`, `fastmcp`, or a list of them | The top-level folder under `prefect/`, `dagster/`, `fastmcp/` |
| `status` | no | `maintained` or `frozen`. Always `frozen` under `demos/` | `maintained` (`frozen` under `demos/`) |
| `test` | no | `run`, `import-only` or `skip` | `run` |
| `requires_secrets` | no | List of environment variable names | `[]` |
| `timeout` | no | Seconds | `600` |
| `tags` | no | List of strings | `[]` |

Single-file examples may also set the runner fields `cmd`, `args`, `env`, `dependencies`, `icon` and `draft` used by the existing tooling. Any other field is an error, so typos fail CI instead of being ignored.

## Catalog

[`CATALOG.yaml`](../CATALOG.yaml) is generated from these fields. Don't edit it by hand:

```bash
python -m internal.catalog          # regenerate
python -m internal.catalog --check  # fail if it's out of date or an example is invalid
```

Each entry gets a `slug` (the folder name or file stem, unique across the repo) and a `path`. `last_verified` is written by the post-release CI run and kept when the catalog is regenerated.
