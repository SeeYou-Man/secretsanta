"""Unit tests for Secret Santa bot core functionality."""
import pytest
import json

from SecretSanta import (
    _rotate_list,
    _make_assignments,
    ExclusionStore,
    circle,
    exclude,
    remove_exclusion,
    list_exclusions
)
from conftest import MockMember, MockRole, MockContext


def test_rotate_list():
    """Test list rotation logic."""
    assert _rotate_list([1, 2, 3], 1) == [3, 1, 2]
    assert _rotate_list([1, 2, 3], 2) == [2, 3, 1]
    assert _rotate_list([1, 2, 3], 3) == [1, 2, 3]
    assert _rotate_list([1], 1) == [1]
    assert _rotate_list([], 1) == []


@pytest.mark.parametrize("n", [2, 3, 4, 5, 6])
def test_make_assignments_basic(n):
    """Test basic assignment generation for different group sizes."""
    members = [MockMember(i, f"Person{i}") for i in range(n)]
    result = _make_assignments(members)
    assert result is not None
    assert len(result) == n
    # No self-assignments
    assert all(g != r for g, r in result)
    # Everyone assigned once as giver and receiver
    givers = {g.id for g, _ in result}
    receivers = {r.id for _, r in result}
    assert givers == receivers == {m.id for m in members}


def test_make_assignments_respects_exclusions():
    """Test that assignments respect exclusion pairs."""
    members = [MockMember(i, f"Person{i}") for i in range(4)]
    exclusions = {frozenset((0, 1)), frozenset((2, 3))}
    result = _make_assignments(members, exclusions=exclusions)
    assert result is not None
    # Check no excluded pairs are assigned
    for g, r in result:
        assert frozenset((g.id, r.id)) not in exclusions


@pytest.mark.parametrize("n", [3, 4, 5, 7])
def test_make_assignments_single_cycle(n):
    """Test single-cycle assignment generation."""
    members = [MockMember(i, f"Person{i}") for i in range(n)]
    result = _make_assignments(members, single_cycle=True)
    assert result is not None
    # Verify it's one cycle by following assignments
    seen = {result[0][0].id}
    current = result[0][1].id
    while current not in seen:
        seen.add(current)
        for g, r in result:
            if g.id == current:
                current = r.id
                break
    assert len(seen) == n


class TestExclusionStore:
    """Test ExclusionStore functionality."""

    @pytest.fixture
    def store(self, tmp_path):
        """Create a temporary ExclusionStore for testing."""
        old_path = ExclusionStore.EXCLUSIONS_FILE
        test_file = tmp_path / "test_exclusions.json"
        ExclusionStore.EXCLUSIONS_FILE = test_file
        store = ExclusionStore()
        yield store
        ExclusionStore.EXCLUSIONS_FILE = old_path

    def test_add_and_remove(self, store):
        """Test adding and removing exclusions."""
        user1 = MockMember(1, "Alice")
        user2 = MockMember(2, "Bob")
 
        # Test adding
        assert store.add(user1, user2)
        assert not store.add(user2, user1)  # reverse should fail
        assert len(store.exclusions) == 1

        # Test removing
        assert store.remove(user1, user2)
        assert len(store.exclusions) == 0
        assert not store.remove(user1, user2)  # already removed

    def test_persistence(self, store, tmp_path):
        """Test that exclusions persist to file."""
        user1 = MockMember(1, "Alice")
        user2 = MockMember(2, "Bob")
        store.add(user1, user2)

        # Check file contents
        data = json.loads(store.EXCLUSIONS_FILE.read_text())
        assert len(data["exclusions"]) == 1
        assert data["display_names"][str(user1.id)] == "Alice"

        # New store should load existing exclusions
        store2 = ExclusionStore()
        assert len(store2.exclusions) == 1


@pytest.mark.asyncio
async def test_exclude_command():
    """Test the exclude command."""
    ctx = MockContext()
    user1 = MockMember(1, "Alice")
    user2 = MockMember(2, "Bob")

    await exclude(ctx, user1, user2)
    assert "Exclusion added" in ctx.last_message

    # Try adding again
    await exclude(ctx, user2, user1)
    assert "already exists" in ctx.last_message


@pytest.mark.asyncio
async def test_circle_command():
    """Test the circle command."""
    ctx = MockContext()
    members = [MockMember(i, f"Person{i}") for i in range(5)]
    role = MockRole("Secret Santa", members)
    ctx.guild = type("Guild", (), {"roles": [role]})

    await circle(ctx, role_name="Secret Santa")
    assert "sent by DM" in ctx.last_message


@pytest.mark.asyncio
async def test_list_exclusions_command():
    """Test listing exclusions."""
    ctx = MockContext()
    user1 = MockMember(1, "Alice")
    user2 = MockMember(2, "Bob")

    # Start empty
    await list_exclusions(ctx)
    assert "No exclusions" in ctx.last_message

    # Add one and list
    await exclude(ctx, user1, user2)
    await list_exclusions(ctx)
    assert "Alice" in ctx.last_message
    assert "Bob" in ctx.last_message
