# Demos

Code from talks, workshops and Sales Engineering demos, frozen at the version it was shown with. Nothing here is updated after the event.

- One folder per demo: `demos/<yyyy>-<event>-<slug>/`.
- `status` must be `frozen`, and `targets` must pin the exact versions used.
- The README opens with the event, the date, the version pin and a link to the maintained example that replaces it.
- This folder is kept out of the docs generator and out of LLM indexers such as Context7, so frozen code never reads as current.
- Demos are reviewed 12 months after the event: promote, keep or delete.

Every demo follows the [example contract](../internal/example-contract.md) and is listed in [`CATALOG.yaml`](../CATALOG.yaml).
