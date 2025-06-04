import os
import pytest


@pytest.fixture(scope="session", autouse=True)
def setup_prefect_env():
    """Set up Prefect environment variables for testing."""
    # Use ephemeral storage for tests
    os.environ.setdefault("PREFECT_HOME", ".prefect")

    # Avoid sending telemetry during tests
    os.environ.setdefault("PREFECT_DISABLE_TELEMETRY", "1")

    yield


# ---------------------------------------------------------------------------
# Fixtures for example testing ---------------------------------------------
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def files() -> list[str]:
    """Return a list of example Python files to test.

    This fixture replicates the logic in *test_examples.py* for discovering
    example files but is shared so the test can request a ``files`` argument
    without redefining discovery each time.
    """

    example_files: list[str] = []
    for root, _, filenames in os.walk("examples"):
        # Skip internal directories
        if "internal" in root.split(os.path.sep):
            continue

        for filename in filenames:
            if filename.endswith(".py") and not filename.startswith("__"):
                example_files.append(os.path.join(root, filename))

    return example_files
