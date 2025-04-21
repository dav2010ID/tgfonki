"""
Main module for the Telegram bot functionality.
"""
import os
import telebot
import logging
from telebot import types
from typing import Dict, Any, Optional

from telegram_song_bot.api_client import APIClient
from telegram_song_bot.text_formatter import format_song
from telegram_song_bot.pdf_generator import create_pdf


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('song_bot')


class SongBot:
    """Telegram bot for searching and downloading songs and lyrics."""
    
    def __init__(self, token: str):
        """
        Initialize the Telegram bot.
        
        Args:
            token: Telegram bot API token
        """
        self.bot = telebot.TeleBot(token)
        self.api_client = APIClient()
        
        # Store user data during interactions
        self.user_data: Dict[int, Dict[str, Any]] = {}
        
        # Register handlers
        self._register_handlers()
        
        logger.info("✅ Bot initialized")
        print("✅ Bot initialized")
    
    def _register_handlers(self) -> None:
        """Register message and callback handlers."""
        self.bot.message_handler(commands=['start'])(self.start_handler)
        self.bot.message_handler(func=lambda message: True)(self.handle_song_request)
        
        self.bot.callback_query_handler(func=lambda call: call.data.startswith("choose::"))(self.handle_song_choice)
        self.bot.callback_query_handler(func=lambda call: call.data == "download_pdf")(self.callback_download_pdf)
        self.bot.callback_query_handler(func=lambda call: call.data == "download_mp3+")(self.callback_download_mp3)
        self.bot.callback_query_handler(func=lambda call: call.data == "download_mp3-")(self.callback_download_mp3_minus)
        self.bot.callback_query_handler(func=lambda call: call.data.startswith("download_specific_minus::"))(self.callback_download_specific_minus)
    
    def _get_user_info(self, message: telebot.types.Message) -> str:
        """
        Get user information for logging purposes.
        
        Args:
            message: Telegram message object
            
        Returns:
            String with user identifiers
        """
        user_id = message.from_user.id
        username = message.from_user.username or "no_username"
        first_name = message.from_user.first_name or "no_first_name"
        last_name = message.from_user.last_name or "no_last_name"
        
        return f"User: {username} ({first_name} {last_name}, ID: {user_id})"
    
    def _get_user_info_from_call(self, call: telebot.types.CallbackQuery) -> str:
        """
        Get user information from callback query for logging purposes.
        
        Args:
            call: Telegram callback query object
            
        Returns:
            String with user identifiers
        """
        user_id = call.from_user.id
        username = call.from_user.username or "no_username"
        first_name = call.from_user.first_name or "no_first_name"
        last_name = call.from_user.last_name or "no_last_name"
        
        return f"User: {username} ({first_name} {last_name}, ID: {user_id})"
    
    def start_handler(self, message: telebot.types.Message) -> None:
        """
        Handle the /start command.
        
        Args:
            message: Telegram message object
        """
        user_info = self._get_user_info(message)
        logger.info(f"{user_info} - Started the bot")
        
        welcome_text = (
            "🎤 Напиши *название песни*, и я помогу тебе:\n"
            "• Найти 🎼 *текст песни*\n"
            "• Скачать 🎵 *плюс* и 🎶 *минус* версии\n"
            "• Получить 📄 *PDF для распечатки*\n\n"
            "💬 Введи название песни, и начнём!"
        )
        self.bot.send_message(message.chat.id, welcome_text, parse_mode="Markdown")
    
    def handle_song_request(self, message: telebot.types.Message) -> None:
        """
        Handle song search requests.
        
        Args:
            message: Telegram message with song name
        """
        user_input = message.text.strip()
        chat_id = message.chat.id
        user_info = self._get_user_info(message)
        
        logger.info(f"{user_info} - Searching for song: '{user_input}'")
        
        try:
            songs = self.api_client.search_songs(user_input)
            
            if not songs:
                logger.info(f"{user_info} - No songs found for query: '{user_input}'")
                self.bot.send_message(chat_id, "❌ Песни не найдены. Попробуй уточнить запрос.")
                return
            
            logger.info(f"{user_info} - Found {len(songs)} results for query: '{user_input}'")
            self.user_data[chat_id] = {"results": songs}
            
            # If only one result, show it immediately
            if len(songs) == 1:
                song_name = songs[0].get('name', 'Без названия')
                logger.info(f"{user_info} - Auto-selected single result: '{song_name}'")
                self._show_selected_song(chat_id, songs[0])
            else:
                # Show selection of songs
                self._display_song_selection(chat_id, songs)
                
        except Exception as e:
            logger.error(f"{user_info} - Error during search: {e}")
            self.bot.send_message(chat_id, "⚠️ Произошла ошибка при поиске. Попробуй снова позже.")
            print(f"Error during search: {e}")
    
    def _show_selected_song(self, chat_id: int, song: Dict[str, Any]) -> None:
        """
        Display selected song lyrics and download options.
        
        Args:
            chat_id: Telegram chat ID
            song: Song data dictionary
        """
        self.user_data[chat_id]["selected"] = song
        
        song_name = song.get('name', 'Без названия')
        lyrics = format_song(song.get('text', 'Нет текста.'))
        
        # Truncate very long lyrics
        if len(lyrics) > 4000:
            lyrics = lyrics[:4000] + "\n...\n(текст обрезан)"
        
        self.bot.send_message(chat_id, f"🎤 *{song_name}*\n\n{lyrics}", parse_mode="Markdown")
        
        # Create keyboard with download options
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📄 Скачать PDF", callback_data="download_pdf"))
        markup.add(
            types.InlineKeyboardButton("🎵 Скачать MP3+ (с голосом)", callback_data="download_mp3+"),
            types.InlineKeyboardButton("🎶 Скачать MP3- (минус)", callback_data="download_mp3-")
        )
        self.bot.send_message(chat_id, "👇 Нажми на кнопку для скачивания:", reply_markup=markup)
    
    def _display_song_selection(self, chat_id: int, songs: list) -> None:
        """
        Display multiple song options for user to choose from.
        
        Args:
            chat_id: Telegram chat ID
            songs: List of song dictionaries
        """
        markup = types.InlineKeyboardMarkup()
        for i, song in enumerate(songs[:5]):  # Limit to first 5 results
            name = song.get('name', 'Без названия')
            artist = song.get('artist', {}).get('name', 'Unknown')
            button_text = f'{name} - {artist}'
            markup.add(types.InlineKeyboardButton(button_text, callback_data=f"choose::{i}"))
        
        self.bot.send_message(
            chat_id,
            "🔍 Вот несколько песен, выбери одну для просмотра текста:",
            reply_markup=markup
        )
    
    def handle_song_choice(self, call: telebot.types.CallbackQuery) -> None:
        """
        Handle song selection from the list.
        
        Args:
            call: Callback query from button press
        """
        try:
            chat_id = call.message.chat.id
            index = int(call.data.split("::")[1])
            user_info = self._get_user_info_from_call(call)
            
            song = self.user_data.get(chat_id, {}).get("results", [])[index]
            if not song:
                logger.warning(f"{user_info} - Failed to select song at index {index}")
                self.bot.send_message(chat_id, "⚠️ Не удалось выбрать песню.")
                return
            
            song_name = song.get('name', 'Без названия')
            artist_name = song.get('artist', {}).get('name', 'Unknown')
            logger.info(f"{user_info} - Selected song: '{song_name}' by '{artist_name}'")
            
            self._show_selected_song(chat_id, song)
            
        except Exception as e:
            user_info = self._get_user_info_from_call(call)
            logger.error(f"{user_info} - Song choice error: {e}")
            self.bot.send_message(call.message.chat.id, "⚠️ Ошибка при выборе песни.")
            print(f"Song choice error: {e}")
    
    def callback_download_pdf(self, call: telebot.types.CallbackQuery) -> None:
        """
        Handle request to download lyrics as PDF.
        
        Args:
            call: Callback query from button press
        """
        chat_id = call.message.chat.id
        user_info = self._get_user_info_from_call(call)
        song = self.user_data.get(chat_id, {}).get("selected")
        
        if not song:
            logger.warning(f"{user_info} - Attempted to download PDF but no song was selected")
            self.bot.send_message(chat_id, "⚠️ Не найден текст песни.")
            return
        
        try:
            song_name = song.get('name', 'Без названия')
            artist_name = song.get('artist', {}).get('name', 'Unknown')
            logger.info(f"{user_info} - Downloading PDF for song: '{song_name}' by '{artist_name}'")
            
            lyrics = format_song(song.get('text', 'Нет текста.'))
            
            # Create and send PDF
            filename = create_pdf(lyrics, f"{song_name}.pdf")
            
            with open(filename, "rb") as pdf_file:
                self.bot.send_document(chat_id, pdf_file, visible_file_name=f"{song_name}.pdf")
            
            logger.info(f"{user_info} - Successfully sent PDF for song: '{song_name}'")
            
            # Clean up temporary file
            os.remove(filename)
            
        except Exception as e:
            logger.error(f"{user_info} - PDF download error: {e}")
            self.bot.send_message(chat_id, "⚠️ Ошибка при создании PDF.")
            print(f"PDF error: {e}")
    
    def callback_download_mp3(self, call: telebot.types.CallbackQuery) -> None:
        """
        Handle request to download MP3 with vocals.
        
        Args:
            call: Callback query from button press
        """
        chat_id = call.message.chat.id
        user_info = self._get_user_info_from_call(call)
        song = self.user_data.get(chat_id, {}).get("selected")
        
        if not song:
            logger.warning(f"{user_info} - Attempted to download MP3+ but no song was selected")
            self.bot.send_message(chat_id, "⚠️ Не найден плюс песни.")
            return
        
        try:
            song_name = song.get('name', 'Без названия')
            artist_name = song.get('artist', {}).get('name', 'Unknown')
            song_plus = str(song.get('file'))
            
            logger.info(f"{user_info} - Downloading MP3+ (with vocals) for song: '{song_name}' by '{artist_name}'")
            
            # Добавляем маркировку в сообщении, что это плюс (с голосом)
            self._send_audio_file(
                chat_id, 
                f"{APIClient.BASE_URL}{song_plus}", 
                f"{song_name} 🎵 (с голосом)"
            )
            
        except Exception as e:
            logger.error(f"{user_info} - MP3+ download error: {e}")
            self.bot.send_message(chat_id, "⚠️ Ошибка при скачивании MP3+ (с голосом).")
            print(f"MP3+ error: {e}")
    
    def callback_download_mp3_minus(self, call: telebot.types.CallbackQuery) -> None:
        """
        Handle request to download MP3 minus (instrumental).
        
        Args:
            call: Callback query from button press
        """
        chat_id = call.message.chat.id
        user_info = self._get_user_info_from_call(call)
        song = self.user_data.get(chat_id, {}).get("selected")
        
        if not song:
            logger.warning(f"{user_info} - Attempted to download MP3- but no song was selected")
            self.bot.send_message(chat_id, "⚠️ Не найден минус песни.")
            return
        
        try:
            song_name = song.get('name', 'Без названия')
            artist_name = song.get('artist', {}).get('name', 'Unknown')
            song_id = str(song.get('id'))
            
            logger.info(f"{user_info} - Searching for minus versions for song: '{song_name}' by '{artist_name}'")
            
            # Get available minus versions
            minus_versions = self.api_client.get_minus_versions(song_id)
            
            if not minus_versions:
                logger.warning(f"{user_info} - No minus versions found for song: '{song_name}'")
                self.bot.send_message(chat_id, "⚠️ Минус не найден.")
                return
            
            logger.info(f"{user_info} - Found {len(minus_versions)} minus versions for song: '{song_name}'")
            
            if len(minus_versions) == 1:
                # Only one version - download immediately
                logger.info(f"{user_info} - Downloading the only minus version for song: '{song_name}'")
                minus_url = self.api_client.get_minus_url(minus_versions[0])
                # Добавляем маркировку в сообщении, что это минус (без голоса)
                self._send_audio_file(chat_id, minus_url, f"{song_name} 🎶 (минус)")
            else:
                # Multiple versions - let user choose
                logger.info(f"{user_info} - Displaying minus version selection for song: '{song_name}'")
                markup = types.InlineKeyboardMarkup()
                for i, version_id in enumerate(minus_versions):
                    btn_text = f"Минус - Версия {i+1} (ID: {version_id})"
                    btn_data = f"download_specific_minus::{version_id}"
                    markup.add(types.InlineKeyboardButton(btn_text, callback_data=btn_data))
                
                msg = self.bot.send_message(
                    chat_id,
                    "🎶 Найдено несколько версий минусовки. Выбери нужную:",
                    reply_markup=markup
                )
                self.user_data[chat_id]["version_pick"] = msg
            
        except Exception as e:
            logger.error(f"{user_info} - MP3- search error: {e}")
            self.bot.send_message(chat_id, "⚠️ Ошибка при поиске минуса.")
            print(f"MP3- search error: {e}")
    
    def callback_download_specific_minus(self, call: telebot.types.CallbackQuery) -> None:
        """
        Handle request to download a specific minus version.
        
        Args:
            call: Callback query from button press with minus version ID
        """
        chat_id = call.message.chat.id
        user_info = self._get_user_info_from_call(call)
        song = self.user_data.get(chat_id, {}).get("selected")
        
        if not song:
            logger.warning(f"{user_info} - Attempted to download specific minus but no song was selected")
            self.bot.send_message(chat_id, "⚠️ Песня не найдена.")
            return
        
        try:
            minus_id = call.data.split("::")[1]
            song_name = song.get('name', 'Без названия')
            artist_name = song.get('artist', {}).get('name', 'Unknown')
            
            logger.info(f"{user_info} - Downloading specific minus version (ID: {minus_id}) for song: '{song_name}' by '{artist_name}'")
            
            minus_url = self.api_client.get_minus_url(minus_id)
            
            # Добавляем маркировку в сообщении, что это минус (без голоса)
            self._send_audio_file(chat_id, minus_url, f"{song_name} 🎶 (минус) #{minus_id}")
            
            # Clean up the version selection message
            version_pick_msg = self.user_data.get(chat_id, {}).get("version_pick")
            if version_pick_msg:
                self.bot.delete_message(chat_id, version_pick_msg.message_id)
                
        except Exception as e:
            logger.error(f"{user_info} - Specific minus download error: {e}")
            self.bot.send_message(chat_id, "⚠️ Ошибка при загрузке выбранной версии минуса.")
            print(f"Specific minus error: {e}")
    
    def _send_audio_file(self, chat_id: int, url: str, song_name: str) -> None:
        """
        Download and send an audio file to the user.
        
        Args:
            chat_id: Telegram chat ID
            url: URL of the audio file
            song_name: Name of the song (with markers for plus/minus)
        """
        # Try to get user info from user_data for logging
        user_info = "User unknown"
        try:
            if chat_id in self.user_data:
                selected_song = self.user_data[chat_id].get("selected", {})
                if "username" in self.user_data[chat_id]:
                    username = self.user_data[chat_id]["username"]
                    user_info = f"User: {username}"
        except:
            pass
            
        try:
            # Determine if this is a plus or minus version from the song name
            is_minus = "минус" in song_name or "(без голоса)" in song_name
            download_type = "минусовку" if is_minus else "плюсовку"
            
            # Log the download attempt
            logger.info(f"{user_info} - Downloading {download_type} for: '{song_name}'")
            
            # Send a loading message with appropriate type
            downloading_message = self.bot.send_message(
                chat_id, 
                f"⏳ Скачиваю {download_type}..."
            )
            
            # Download the file
            file_content = self.api_client.download_mp3(url)
            
            if file_content:
                # Send the audio file
                self.bot.send_audio(chat_id, file_content, title=song_name, timeout=120)
                logger.info(f"{user_info} - Successfully sent {download_type} for: '{song_name}'")
            else:
                # Error message with appropriate type
                error_msg = f"❌ Не удалось скачать {download_type}."
                self.bot.send_message(chat_id, error_msg)
                logger.warning(f"{user_info} - Failed to download {download_type} for: '{song_name}'")
            
            # Delete the loading message
            self.bot.delete_message(chat_id, downloading_message.message_id)
            
        except Exception as e:
            download_type = "минусовки" if "минус" in song_name else "плюсовки"
            error_msg = f"⚠️ Ошибка при скачивании {download_type}."
            self.bot.send_message(chat_id, error_msg)
            logger.error(f"{user_info} - Error downloading {download_type} for '{song_name}': {e}")
            print(f"Send audio file error: {e}")
    
    def run(self) -> None:
        """Start the bot and keep it running."""
        logger.info("✅ Bot started and polling")
        print("✅ Bot started")
        self.bot.infinity_polling()