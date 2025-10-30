"""Wrapper script that runs the package implementation.

This file keeps backward compatibility for users who run `python SecretSanta.py`.
The actual bot implementation lives in the package module `SecretSanta.SecretSanta`.
"""

import os
import logging
from dotenv import load_dotenv

# Ensure environment variables are loaded
load_dotenv()
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')

try:
    # Import the bot instance from the package implementation
    from SecretSanta.SecretSanta import bot
except Exception:
    logging.exception('Failed to import bot from package. Are package files present?')
    bot = None


if __name__ == '__main__':
    if not DISCORD_BOT_TOKEN:
        logging.error('Environment variable DISCORD_BOT_TOKEN is not set. Set it and restart the bot.')
    elif bot is None:
        logging.error('Bot instance not available, cannot start.')
    else:
        bot.run(DISCORD_BOT_TOKEN)
