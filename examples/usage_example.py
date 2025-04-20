"""
Example of using the telegram_song_bot package.

This file demonstrates how to use the main components of the telegram_song_bot package.
"""
import os
from telegram_song_bot.api_client import APIClient
from telegram_song_bot.text_formatter import format_song
from telegram_song_bot.pdf_generator import create_pdf, LyricsPDFGenerator


def search_example():
    """Example of searching for songs and displaying lyrics."""
    # Create an API client
    client = APIClient()
    
    # Search for songs
    song_name = "Bohemian Rhapsody"
    print(f"Searching for '{song_name}'...")
    songs = client.search_songs(song_name)
    
    if not songs:
        print("No songs found.")
        return
    
    # Display search results
    print(f"Found {len(songs)} songs:")
    for i, song in enumerate(songs[:5]):
        name = song.get('name', 'Untitled')
        artist = song.get('artist', {}).get('name', 'Unknown')
        print(f"{i+1}. {name} - {artist}")
    
    # Display lyrics for the first song
    if songs:
        song = songs[0]
        name = song.get('name', 'Untitled')
        raw_lyrics = song.get('text', 'No lyrics available.')
        
        # Format the lyrics
        lyrics = format_song(raw_lyrics)
        
        print(f"\nLyrics for '{name}':")
        print("="*40)
        print(lyrics[:300] + "..." if len(lyrics) > 300 else lyrics)
        print("="*40)


def pdf_example():
    """Example of creating a PDF from lyrics."""
    lyrics = """Verse 1:
This is a sample song
With some example lyrics
To demonstrate the PDF generator

Chorus:
This is the chorus part
That repeats throughout the song
And is usually more memorable

Verse 2:
This is another verse
With different lyrics this time
But similar structure to the first

Bridge:
This is the bridge
That connects different parts
And adds variety to the song"""

    # Basic usage
    basic_pdf_path = "basic_example.pdf"
    create_pdf(lyrics, basic_pdf_path)
    print(f"Created basic PDF at: {basic_pdf_path}")
    
    # Advanced usage with custom settings
    custom_pdf_path = "custom_example.pdf"
    generator = LyricsPDFGenerator(
        margins=10,  # Larger margins
        min_font_size=12  # Larger minimum font size
    )
    generator.create_pdf(lyrics, custom_pdf_path)
    print(f"Created custom PDF at: {custom_pdf_path}")


if __name__ == "__main__":
    # Create examples directory if it doesn't exist
    os.makedirs("output", exist_ok=True)
    
    print("=== SEARCH EXAMPLE ===")
    search_example()
    
    print("\n=== PDF EXAMPLE ===")
    pdf_example()