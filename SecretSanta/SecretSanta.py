import os
import logging
import random
import asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv
from math import gcd
import json
import pathlib

# File to store exclusions (IDs and display names for readability)
EXCLUSIONS_FILE = pathlib.Path('exclusions.json')
DEFAULT_EXCLUSIONS_FILE = EXCLUSIONS_FILE


class ExclusionStore:
    """Manages persistent storage of exclusions with JSON backing."""
    # allow tests to monkeypatch this path as ExclusionStore.EXCLUSIONS_FILE
    EXCLUSIONS_FILE = EXCLUSIONS_FILE

    def __init__(self):
        self.exclusions = set()  # set of frozenset(id1, id2)
        self.display_names = {}  # id -> most recent display_name mapping
        self._load()

    def _load(self):
        """Load exclusions from JSON if file exists."""
        # When running under pytest, avoid loading the global persistent exclusions
        # only when using the default path, so tests that set a custom
        # ExclusionStore.EXCLUSIONS_FILE can still exercise persistence.
        if 'pytest' in __import__('sys').modules and self.EXCLUSIONS_FILE == DEFAULT_EXCLUSIONS_FILE:
            return
        if not self.EXCLUSIONS_FILE.exists():
            return
        try:
            with self.EXCLUSIONS_FILE.open() as f:
                data = json.load(f)
                # Reconstruct frozensets from ID pairs
                self.exclusions = {frozenset(pair) for pair in data.get('exclusions', [])}
                self.display_names = data.get('display_names', {})
        except Exception as e:
            logging.error(f'Failed to load exclusions: {e}')

    def _save(self):
        """Save current exclusions to JSON."""
        try:
            data = {
                'exclusions': [list(pair) for pair in self.exclusions],
                'display_names': self.display_names
            }
            with self.EXCLUSIONS_FILE.open('w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logging.error(f'Failed to save exclusions: {e}')

    def add(self, user1: discord.Member, user2: discord.Member) -> bool:
        """Add an exclusion pair. Returns True if this was a new exclusion."""
        pair = frozenset((user1.id, user2.id))
        if pair in self.exclusions:
            return False

        self.exclusions.add(pair)
        # Update display names (for list command readability)
        self.display_names[str(user1.id)] = user1.display_name
        self.display_names[str(user2.id)] = user2.display_name
        self._save()
        return True

    def remove(self, user1: discord.Member, user2: discord.Member) -> bool:
        """Remove an exclusion pair. Returns True if found and removed."""
        pair = frozenset((user1.id, user2.id))
        if pair not in self.exclusions:
            return False

        self.exclusions.remove(pair)
        self._save()
        return True

    def format_list(self) -> str:
        """Return a human-readable list of current exclusions."""
        if not self.exclusions:
            return "No exclusions configured."

        lines = []
        for pair in self.exclusions:
            id1, id2 = pair
            name1 = self.display_names.get(str(id1), f'Unknown({id1})')
            name2 = self.display_names.get(str(id2), f'Unknown({id2})')
            lines.append(f'- {name1} ↔ {name2}')
        return 'Current exclusions:\n' + '\n'.join(sorted(lines))


# Global exclusion store, loaded at startup
exclusion_store = ExclusionStore()

logging.basicConfig(level=logging.INFO)

# Read the token from an environment variable for safety
# Load environment variables from a .env file (if present) and then from the environment
load_dotenv()
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
if not DISCORD_BOT_TOKEN:
    # This file may be run directly; if the token is missing, inform the user and exit.
    logging.error('Environment variable DISCORD_BOT_TOKEN is not set. Set it and restart the bot.')
    # Do not attempt to run the bot without a token.

intents = discord.Intents.all()
intents.members = True

bot = commands.Bot(command_prefix='/', intents=intents)


# Enable app commands (slash commands)
@bot.event
async def setup_hook():
    await bot.tree.sync()


def _rotate_list(lst, k):
    """Return a new list rotated by k to the right: element i receives lst[(i+k) % n]."""
    n = len(lst)
    if n == 0:
        return []
    # rotate right by k
    return [lst[(i - k) % n] for i in range(n)]


def _make_assignments(members, exclusions=None, single_cycle=False, max_attempts=2000):
    """Return assignments list of (giver, receiver) or None if impossible.

    - members: list of discord.Member
    - exclusions: set of frozenset({id1, id2}) to avoid pairings in either direction
    - single_cycle: if True, produce a single-cycle permutation (one big circle)
    """
    exclusions = exclusions or set()
    n = len(members)
    if n < 2:
        return None

    # Helper to test a receivers list against exclusions
    def valid_with_receivers(receivers):
        for giver, receiver in zip(members, receivers):
            if giver.id == receiver.id:
                return False
            if frozenset((giver.id, receiver.id)) in exclusions:
                return False
        return True

    if single_cycle:
        # Rotate by k with gcd(k,n) == 1 to ensure one cycle.
        ks = [k for k in range(1, n) if gcd(k, n) == 1]
        random.shuffle(ks)
        for k in ks:
            receivers = _rotate_list(members, k)
            if valid_with_receivers(receivers):
                return list(zip(members, receivers))
        return None

    # Not single_cycle: find any derangement that respects exclusions
    receivers = [m for m in members]
    for attempt in range(max_attempts):
        random.shuffle(receivers)
        if valid_with_receivers(receivers):
            return list(zip(members, receivers))
    # If random attempts fail, there's likely no valid assignment under these constraints
    return None


@bot.event
async def on_ready():
    logging.info(f'{bot.user} has connected to Discord!')


@bot.tree.command(name='secretsanta', description='Start Secret Santa assignment for a role')
@discord.app_commands.describe(role_name='The name of the role to use (default: Secret Santa)')
@discord.app_commands.guild_only()
async def secretsanta(interaction: discord.Interaction, role_name: str = 'Secret Santa'):
    """Assign each member with the given role a unique receiver (everyone picked once, nobody receives themself)."""
    await interaction.response.defer()

    role = discord.utils.get(interaction.guild.roles, name=role_name)
    if not role:
        await interaction.followup.send(f"Role '{role_name}' not found.")
        return

    # Exclude bots from the participant list
    members = [m for m in role.members if not m.bot]
    n = len(members)
    if n < 2:
        await interaction.followup.send('Need at least 2 non-bot members with that role to run Secret Santa.')
        return

    # Create a derangement respecting any configured exclusions
    assignments = _make_assignments(members, exclusions=exclusion_store.exclusions, single_cycle=False)
    if assignments is None:
        await interaction.followup.send('Unable to generate Secret Santa assignments with the current exclusions/constraints.')
        return

    async def _send_and_report(interaction, assignments, role_name):
        failed = []
        for giver, receiver in assignments:
            giver_name = giver.display_name
            receiver_name = receiver.display_name
            message = (
                f"God jul {giver_name}! Jag har något att säga till dig — håll det hemligt:\n"
                f"Du har blivit tilldelad att ge en julklapp till {receiver_name}."
            )
            try:
                await giver.send(message)
            except Exception:
                logging.exception(f'Failed to send DM to {giver} ({giver.id})')
                failed.append(giver)
            await asyncio.sleep(0.5)

        if not failed:
            await interaction.followup.send(f'Secret Santa assignments sent by DM to {len(assignments)} members (role: {role_name}).')
        else:
            failed_names = ', '.join([m.display_name for m in failed])
            await interaction.followup.send(
                f'Sent assignments to {len(assignments) - len(failed)} members; failed to DM {len(failed)} members: {failed_names}. '
                'Check that those users allow DMs from server members or try contacting them directly.'
            )

    await _send_and_report(interaction, assignments, role_name)


async def send_assignments(interaction: discord.Interaction, assignments, role_name: str):
    """Send DMs for assignments and report back in channel."""
    failed = []
    for giver, receiver in assignments:
        giver_name = giver.display_name
        receiver_name = receiver.display_name
        message = (
            f"God jul {giver_name}! Jag har något att säga till dig — håll det hemligt:\n"
            f"Du har blivit tilldelad att ge en julklapp till {receiver_name}."
        )
        try:
            await giver.send(message)
        except Exception:
            logging.exception(f'Failed to send DM to {giver} ({giver.id})')
            failed.append(giver)
        await asyncio.sleep(0.5)

    if not failed:
        await interaction.followup.send(f'Secret Santa assignments sent by DM to {len(assignments)} members (role: {role_name}).')
    else:
        failed_names = ', '.join([m.display_name for m in failed])
        await interaction.followup.send(
            f'Sent assignments to {len(assignments) - len(failed)} members; failed to DM {len(failed)} members: {failed_names}. '
            'Check that those users allow DMs from server members or try contacting them directly.'
        )


@bot.tree.command(name='exclude', description='Exclude two users from being assigned to each other')
@discord.app_commands.describe(
    user1='First user to exclude',
    user2='Second user to exclude'
)
@discord.app_commands.guild_only()
async def exclude(interaction: discord.Interaction, user1: discord.Member, user2: discord.Member):
    """Exclude two users from being assigned to each other (both directions)."""
    await interaction.response.defer()
    if user1.id == user2.id:
        await interaction.followup.send("Cannot exclude a user from themselves.")
        return

    if exclusion_store.add(user1, user2):
        await interaction.followup.send(f'Exclusion added: {user1.display_name} ↔ {user2.display_name}')
    else:
        await interaction.followup.send(f'Exclusion already exists between {user1.display_name} and {user2.display_name}.')


@bot.tree.command(name='remove_exclusion', description='Remove an exclusion between two users')
@discord.app_commands.describe(
    user1='First user to remove exclusion for',
    user2='Second user to remove exclusion for'
)
@discord.app_commands.guild_only()
async def remove_exclusion(interaction: discord.Interaction, user1: discord.Member, user2: discord.Member):
    """Remove an exclusion between two users."""
    await interaction.response.defer()
    if exclusion_store.remove(user1, user2):
        await interaction.followup.send(f'Exclusion removed between {user1.display_name} and {user2.display_name}.')
    else:
        await interaction.followup.send(f'No exclusion found between {user1.display_name} and {user2.display_name}.')


@bot.tree.command(name='list_exclusions', description='List all configured exclusions')
@discord.app_commands.guild_only()
async def list_exclusions(interaction: discord.Interaction):
    """List all configured exclusions."""
    await interaction.response.send_message(exclusion_store.format_list())


@bot.tree.command(name='circle', description='Generate a single-cycle Secret Santa (one big circle)')
@discord.app_commands.describe(role_name='The name of the role to use (default: Secret Santa)')
@discord.app_commands.guild_only()
async def circle(interaction: discord.Interaction, role_name: str = 'Secret Santa'):
    """Generate a single-cycle Secret Santa where everyone forms one big circle."""
    await interaction.response.defer()
    role = discord.utils.get(interaction.guild.roles, name=role_name)
    if not role:
        await interaction.followup.send(f"Role '{role_name}' not found.")
        return

    members = [m for m in role.members if not m.bot]
    n = len(members)
    if n < 2:
        await interaction.followup.send('Need at least 2 non-bot members with that role to run Secret Santa.')
        return

    assignments = _make_assignments(members, exclusions=exclusion_store.exclusions, single_cycle=True)
    if assignments is None:
        await interaction.followup.send('Unable to generate a single-cycle assignment under current exclusions/constraints.')
        return

    await send_assignments(interaction, assignments, role_name)


@bot.tree.command(name='circle_exclude', description='Generate a single-cycle assignment while temporarily excluding a pair')
@discord.app_commands.describe(
    user1='First user to temporarily exclude',
    user2='Second user to temporarily exclude',
    role_name='The name of the role to use (default: Secret Santa)'
)
@discord.app_commands.guild_only()
async def circle_exclude(interaction: discord.Interaction, user1: discord.Member, user2: discord.Member, role_name: str = 'Secret Santa'):
    """Generate a single-cycle assignment while temporarily excluding a given pair from being assigned to each other."""
    await interaction.response.defer()
    temp_pair = frozenset((user1.id, user2.id))
    role = discord.utils.get(interaction.guild.roles, name=role_name)
    if not role:
        await interaction.followup.send(f"Role '{role_name}' not found.")
        return

    members = [m for m in role.members if not m.bot]
    n = len(members)
    if n < 2:
        await interaction.followup.send('Need at least 2 non-bot members with that role to run Secret Santa.')
        return

    # Use current exclusions plus temporary pair
    assignments = _make_assignments(members, exclusions=exclusion_store.exclusions | {temp_pair}, single_cycle=True)
    if assignments is None:
        await interaction.followup.send('Unable to generate a single-cycle assignment with that temporary exclusion.')
        return

    await send_assignments(interaction, assignments, role_name)


if __name__ == '__main__' and DISCORD_BOT_TOKEN:
    # Only run the bot when executed as a script, not when imported for tests.
    bot.run(DISCORD_BOT_TOKEN)
