# What depends on this repo

Other repositories, docs pages and code load files from this repo by path. Before
moving, renaming or deleting anything listed here, update the dependents first (or
leave a copy at the old path) and change `internal/protected_paths.yaml` in the
same PR.

CI runs `python -m internal.protected` to fail any PR that removes a path that is
still protected.

Last checked: 23 November 2026. See [How this was checked](#how-this-was-checked).

## Files loaded from `main`

| Path in this repo | Used by | How |
| --- | --- | --- |
| `flows/hello_world.py:hello` | `PrefectHQ/prefect` `integration-tests/test_deploy.py` | Clones this repo with `GitRepository` and deploys the flow |
| `flows/hello_world.py:hello`, `flows/whoami.py:whoami` | `PrefectHQ/prefect` `integration-tests/test_load_flows_concurrently.py` | Clones this repo and loads both flows concurrently |
| `flows/hello_world.py:hello` | `PrefectHQ/prefect-operator` `deploy/samples/deployment_end-to-end.yaml` | Sample deployment pulls from `main` |
| `flows/hello-world.py:hello`, `flows/whoami.py:whoami` | `PrefectHQ/nebula` (private) `client-compatibility/flows/load_flows_concurrently.py` | Loads both flows. **`flows/hello-world.py` (hyphen) does not exist in this repo**, so this check may already be failing |
| `flows/hello_world.py:hello` | Prefect docs, `docs/v3/how-to-guides/deployment_infra/run-flows-in-local-processes.mdx` | Code sample using `flow.from_source` |
| `apps/background-tasks/` | Prefect docs, `docs/v3/advanced/background-tasks.mdx` | Links to `tree/main/apps/background-tasks` |

## The `examples-markdown` branch

| Dependent | How |
| --- | --- |
| `examples/02_flows/run_dbt_with_prefect.py` (here) and `examples/run_dbt_with_prefect.py` in `PrefectHQ/prefect` | Downloads `archive/refs/heads/examples-markdown.zip` and looks for `resources/prefect_dbt_project/dbt_project.yml` inside it. Fails if that path changes on the branch |
| `internal/utils.py` `render_example_md` | Hard-codes "View on GitHub" links to `blob/examples-markdown/examples/...` |
| Live docs page [`/v3/examples/run-dbt-with-prefect`](https://docs.prefect.io/v3/examples/run-dbt-with-prefect) | Shows the zip URL in the rendered code |

Do not delete, force-push or restructure this branch until those are repointed.
CI does not check branches.

## Live docs pages that link here

Only three pages on any of our sites link to this repo:

| Page | Link |
| --- | --- |
| [`/v3/advanced/background-tasks`](https://docs.prefect.io/v3/advanced/background-tasks) | `tree/main/apps/background-tasks`, and the repo root ("clone the examples repository") |
| [`/v3/how-to-guides/deployment_infra/run-flows-in-local-processes`](https://docs.prefect.io/v3/how-to-guides/deployment_infra/run-flows-in-local-processes) | `examples.git` with entrypoint `flows/hello_world.py:hello` |
| [`/v3/examples/run-dbt-with-prefect`](https://docs.prefect.io/v3/examples/run-dbt-with-prefect) | The `examples-markdown` zip |

All three come from MDX in `PrefectHQ/prefect` `docs/`.

## Not a dependency

- **The Prefect docs example pages are no longer generated from this repo.** They
  have been generated from `PrefectHQ/prefect` `examples/` by
  `scripts/generate_example_pages.py` since 3.4.x ("Port examples hosting from
  PrefectHQ/examples", PrefectHQ/prefect#18661). Their "View on GitHub" links point
  at the core repo. The docs generator in `internal/` here feeds nothing live.
- **Marketing sites.** No page on prefect.io, dagster.io or gofastmcp.com, and no
  file in `PrefectHQ/marketing`, `PrefectHQ/dagster-website`,
  `PrefectHQ/gofastmcp-website` or `PrefectHQ/content-creation-workflow`, links to
  this repo.
- **Dagster and FastMCP docs.** Nothing in `dagster-io/dagster`,
  `dagster-io/project-dagster-university` or `PrefectHQ/fastmcp` references it.
- **`PrefectHQ/docs`** (archived Prefect 2 docs) has no links to this repo.

## How this was checked

- GitHub code search across `PrefectHQ`, `dagster-io` and `jlowin` (including
  private repos) for `PrefectHQ/examples` and `examples-markdown`.
- A full-text search of shallow clones of `PrefectHQ/prefect`, `PrefectHQ/docs`,
  `PrefectHQ/marketing`, `PrefectHQ/dagster-website`,
  `PrefectHQ/gofastmcp-website`, `PrefectHQ/content-creation-workflow`,
  `PrefectHQ/website-ci`, `PrefectHQ/fastmcp`, `dagster-io/dagster` and
  `dagster-io/project-dagster-university`.
- A crawl of every URL in the sitemaps of www.prefect.io, docs.prefect.io,
  dagster.io, docs.dagster.io and gofastmcp.com (2,943 pages), searching the
  rendered HTML for `github.com/PrefectHQ/examples`.

## Not yet checked

- Links from outside our orgs: personal repos, community posts, Stack Overflow,
  YouTube descriptions, slide decks and QR codes from talks.
- Context7 and DeepWiki entries for this repo.
- Code search only covers default branches.
