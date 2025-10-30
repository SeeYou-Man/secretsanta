"""Mocks for Discord objects used in tests."""
from typing import Optional, List
import pytest
import SecretSanta


class MockMember:
    """Mock discord.Member for testing."""
    def __init__(self, id: int, name: str, display_name: Optional[str] = None):
        self.id = id
        self.name = name
        self.display_name = display_name or name
        self.dm_channel = None
        self.bot = False
        self._last_dm = None

    async def send(self, content: str):
        """Mock DM sending."""
        self._last_dm = content

    async def create_dm(self):
        """Mock DM channel creation."""
        self.dm_channel = True


class MockRole:
    """Mock discord.Role for testing."""
    def __init__(self, name: str, members: List[MockMember]):
        self.name = name
        self.members = members


class MockContext:
    """Mock commands.Context for testing."""
    def __init__(self, guild_name: str = "Test Guild"):
        self.guild_name = guild_name
        self.sent_messages = []

    async def send(self, content: str):
        """Record messages sent to channel."""
        self.sent_messages.append(content)

    @property
    def last_message(self) -> Optional[str]:
        """Get the last message sent, if any."""
        return self.sent_messages[-1] if self.sent_messages else None


class MockInteraction:
    """Minimal mock of discord.Interaction for testing app commands.

    Provides a `response` object with `defer()` and `send_message()` and a
    `followup` object with `send()` so tests can assert messages.
    """
    def __init__(self):
        self.guild = None
        self.sent_messages = []
        self.response = self.Response(self)
        self.followup = self.Followup(self)

    class Response:
        def __init__(self, parent):
            self._parent = parent

        async def defer(self):
            # no-op for tests
            return None

        async def send_message(self, content: str):
            self._parent.sent_messages.append(content)

    class Followup:
        def __init__(self, parent):
            self._parent = parent

        async def send(self, content: str):
            self._parent.sent_messages.append(content)

    @property
    def last_message(self) -> Optional[str]:
        return self.sent_messages[-1] if self.sent_messages else None


@pytest.fixture(autouse=True)
def clear_exclusions():
    """Ensure exclusion_store starts empty for each test to avoid cross-test pollution."""
    try:
        SecretSanta.exclusion_store.exclusions.clear()
        SecretSanta.exclusion_store.display_names.clear()
    except Exception:
        pass
    yield
    try:
        SecretSanta.exclusion_store.exclusions.clear()
        SecretSanta.exclusion_store.display_names.clear()
    except Exception:
        pass
