"""Mocks for Discord objects used in tests."""
from typing import Optional, List
import discord


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


import pytest
import SecretSanta


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