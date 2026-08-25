from pathlib import Path

from atproto import Client
from prefect.blocks.core import Block
from pydantic import Field, SecretStr

from atproto_dashboard.settings import settings


class ATProtoClient(Block):
    """
    Block for managing ATProto (Bluesky) authentication with session caching.

    Attributes:
        login: Bluesky handle (e.g., user.bsky.social)
        password: App password for authentication
        session_cache_path: Path to cache session string (reduces API calls)
    """

    _block_type_name = "atproto-client"
    _block_type_slug = "atproto-client"
    _logo_url = "https://bsky.social/favicon.ico"
    _documentation_url = "https://atproto.com/docs"

    login: str = Field(description="Bluesky handle (e.g., user.bsky.social)")
    password: SecretStr = Field(description="App password for authentication")
    session_cache_path: Path = Field(
        default=Path("atproto-session.txt"), description="Path to cache session string"
    )

    def get_client(self) -> Client:
        """
        Get an authenticated ATProto client, using cached session if available.

        Returns:
            Client: Authenticated ATProto client
        """
        client = Client()

        # Try to use cached session first
        if self.session_cache_path.exists():
            with open(self.session_cache_path) as f:
                session_string = f.read().strip()
            try:
                client.login(session_string=session_string)
                return client
            except Exception:
                # If cached session fails, proceed with normal login
                pass

        # Login with credentials
        client.login(login=self.login, password=self.password.get_secret_value())

        # Cache the session for future use
        session_string = client.export_session_string()
        with open(self.session_cache_path, "w") as f:
            f.write(session_string)

        return client


def get_atproto_client() -> ATProtoClient:
    """
    Factory function to get ATProto client from settings.
    """

    return ATProtoClient(
        login=settings.bsky_login,
        password=SecretStr(settings.bsky_app_password),
    )
