import os
import logging
import random
import asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv

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


def _rotate_list(lst, k):
    """Return a new list rotated by k to the right: element i receives lst[(i+k) % n]."""
    n = len(lst)
    return [lst[(i + k) % n] for i in range(n)]


@bot.event
async def on_ready():
    logging.info(f'{bot.user} has connected to Discord!')


@bot.command(name='secretsanta')
@commands.guild_only()
async def secretsanta(ctx, *, role_name: str = 'Secret Santa'):
    """Assign each member with the given role a unique receiver (everyone picked once, nobody receives themself).

    Usage: /secretsanta or /secretsanta Role Name
    """
    role = discord.utils.get(ctx.guild.roles, name=role_name)
    if not role:
        await ctx.send(f"Role '{role_name}' not found.")
        return

    # Exclude bots from the participant list
    members = [m for m in role.members if not m.bot]
    n = len(members)
    if n < 2:
        await ctx.send('Need at least 2 non-bot members with that role to run Secret Santa.')
        return

    # Create a derangement by rotating the list by a random offset k (1..n-1).
    k = random.randint(1, n - 1)
    receivers = _rotate_list(members, k)

    assignments = list(zip(members, receivers))

    failed = []
    # Send DMs to each giver with their assigned receiver
    for giver, receiver in assignments:
        # Prefer display_name (nick if set, otherwise username)
        giver_name = giver.display_name
        receiver_name = receiver.display_name
        message = (
            f"God jul {giver_name}! Jag har något att säga till dig — håll det hemligt:\n"
            f"Du har blivit tilldelad att ge en julklapp till {receiver_name}."
        )
        try:
            # `send` will create a DM channel if needed
            await giver.send(message)
        except Exception as e:
            logging.exception(f'Failed to send DM to {giver} ({giver.id})')
            failed.append((giver, str(e)))
        # small delay to avoid hitting rate limits
        await asyncio.sleep(0.5)

    # Report summary in the channel where the command was invoked (avoid exposing assignments)
    if not failed:
        await ctx.send(f'Secret Santa assignments sent by DM to {n} members (role: {role_name}).')
    else:
        failed_names = ', '.join([f.display_name for f, _ in failed])
        await ctx.send(
            f'Sent assignments to {n - len(failed)} members; failed to DM {len(failed)} members: {failed_names}. '
            'Check that those users allow DMs from server members or try contacting them directly.'
        )


if DISCORD_BOT_TOKEN:
    bot.run(DISCORD_BOT_TOKEN)

