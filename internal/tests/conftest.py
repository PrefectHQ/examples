import os
import sys
import pytest


@pytest.fixture(scope="session", autouse=True)
def setup_prefect_env():
    """Set up Prefect environment variables for testing."""
    # Use ephemeral storage for tests
    os.environ.setdefault("PREFECT_HOME", ".prefect")
    
    # Avoid sending telemetry during tests
    os.environ.setdefault("PREFECT_DISABLE_TELEMETRY", "1")
    
    yield 