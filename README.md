# Telegram Song Bot

A Telegram bot that helps users find and download song lyrics, PDFs, and audio files.

## Features

- Search for songs by name
- View song lyrics
- Download lyrics as PDF files optimized for printing
- Download MP3 files with vocals (MP3+)
- Download instrumental MP3 files (MP3-)
- Support for multiple languages and text formats

## Project Structure

```
telegram_song_bot/
├── __init__.py           # Package initialization
├── api_client.py         # API client for fonki.pro
├── bot.py                # Telegram bot implementation
├── pdf_generator.py      # PDF generation utilities
└── text_formatter.py     # Text processing utilities
run.py                    # Entry point
Procfile                  # For deployment to Heroku or similar platforms
requirements.txt          # Python dependencies
```

## Setup

1. Create a Telegram bot via BotFather and get your API token
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Set your Telegram API token as an environment variable:
   ```
   export TOKEN="your_telegram_bot_token"
   ```
4. Run the bot:
   ```
   python run.py
   ```

## Deployment

The application is ready for deployment on platforms like Heroku using the included Procfile.

Make sure to set the TOKEN environment variable on your deployment platform.

## Dependencies

- pyTelegramBotAPI: For Telegram bot functionality
- requests: For API communication
- fpdf: For PDF generation

## Usage

1. Start a chat with your bot in Telegram
2. Type a song name
3. Select the desired song from search results
4. Use buttons to view lyrics or download files