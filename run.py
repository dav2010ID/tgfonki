"""
Main entry point for the Telegram Song Bot.
"""
import os
from telegram_song_bot.bot import SongBot


if __name__ == "__main__":
    # Get API token from environment variable
    api_token = os.getenv("TOKEN")
    
    if not api_token:
        print("❌ Error: TOKEN environment variable not set")
        print("Please set the TOKEN environment variable with your Telegram bot token")
        exit(1)
    
    # Create and run the bot
    bot = SongBot(api_token)
    bot.run()