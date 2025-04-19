import telebot
from telebot import types
import requests
import os
import re
from fpdf import FPDF

def create_pdf(lyrics, output_path):
    # Создаем новый PDF-документ с минимальными полями
    margins = 4
    min_font_size = 6  # Минимально допустимый размер шрифта
    
    # Функция для создания PDF с заданным размером шрифта
    def create_pdf_with_font_size(text, size):
        pdf = FPDF()
        pdf.set_margins(left=margins, top=margins, right=margins)
        pdf.set_auto_page_break(auto=True, margin=margins)
        pdf.add_page()
        pdf.add_font('DejaVu', '', "DejaVuSans.ttf", uni=True)
        pdf.set_font('DejaVu', '', size=size)
        line_height = size / 2.5
        pdf.multi_cell(0, line_height, text, align="L")
        return pdf
    
    # Функция для проверки, помещается ли текст на одной странице
    def check_fits_on_page(text, size):
        temp_pdf_path = "temp_check.pdf"
        
        # Создаем временный PDF для проверки
        test_pdf = create_pdf_with_font_size(text, size)
        
        # Сохраняем временный PDF
        test_pdf.output(temp_pdf_path)
        
        # Проверяем количество страниц
        page_count = test_pdf.page_no()
        
        # Удаляем временный файл
        if os.path.exists(temp_pdf_path):
            os.remove(temp_pdf_path)
            
        return page_count == 1
    
    # Определение начального размера шрифта
    font_size = 30
    
    # Подбираем оптимальный размер шрифта
    while font_size > min_font_size:
        if check_fits_on_page(lyrics, font_size):
            break
        font_size -= 0.5  # Уменьшаем размер шрифта с небольшим шагом
    
    # Создаем финальный PDF с найденным размером шрифта
    pdf = create_pdf_with_font_size(lyrics, font_size)
    
    # Проверяем, сколько страниц получилось
    final_page_count = pdf.page_no()
    
    # Если текст все равно занимает больше одной страницы, уменьшаем шрифт еще немного
    if final_page_count > 1:
        print(f"Текст занял {final_page_count} страниц. Уменьшаем шрифт дополнительно.")
        
        # Дополнительное уменьшение шрифта
        additional_reduction = 0.5
        max_attempts = 10  # Максимальное количество попыток
        
        for _ in range(max_attempts):
            # Уменьшаем шрифт еще немного
            font_size -= additional_reduction
            
            if font_size < min_font_size:
                font_size = min_font_size
                print(f"Достигнут минимальный размер шрифта: {min_font_size} пт")
                break
                
            # Пробуем с новым размером шрифта
            pdf = create_pdf_with_font_size(lyrics, font_size)
            
            if pdf.page_no() == 1:
                print(f"После корректировки текст помещается на одной странице")
                break
                
            # Если достигли минимального размера и текст все равно не помещается
            if font_size <= min_font_size:
                print(f"Предупреждение: Текст слишком длинный и не помещается на одной странице даже с минимальным размером шрифта {min_font_size} пт.")
                break
    
    # Вывод финальной информации
    print(f"Выбран финальный размер шрифта: {font_size} пт")
    print(f"Количество страниц в документе: {pdf.page_no()}")
    
    # Сохраняем PDF-файл
    pdf.output(output_path)
    print(f"PDF-файл сохранен как {output_path}")
    return output_path


CHORD_REGEX = re.compile(
    r'^[A-H][b#]?('
    r'2|5|6|7|9|11|13|\+[2-9]|\+1[1-3]|6/9|7[-#]5|7[-#]9|7\+[35]|7\+9|7b[59]|'
    r'7sus[24]|sus4|add[2469]|aug|dim|dim7|m/maj7|m[67]|m7b5|m(9|11|13)|'
    r'maj[79]?|maj1[1-3]|mb5|m|sus[24]?|m7add11|add11|b5|-5|4'
    r')*(/[A-H][b#]*)*$', re.I
)

CHORD_SYMBOLS = {'|', '/', '(', ')', '-', 'x2', 'x3', 'x4', 'x5', 'x6', 'NC'}

SECTION_LABELS = {
    *[f"{i}|" for i in range(10)],
    *[f"{i}:" for i in range(10)],
    *map(str.lower, [
        'Вступление:', 'Интро:', 'Куплет:', 'Припев:', 'Переход:', 'Реп:',
        'Мост:', 'Мостик:', 'Вставка:', 'Речитатив:', 'Бридж:', 'Инструментал:',
        'Проигрыш:', 'Запев:', 'Концовка:', 'Окончание:', 'В конце:', 'Кода:', 'Тэг:',
        'Intro:', 'Verse:', 'Chorus:', 'Pre chorus:', 'Pre-chorus:', 'Bridge:',
        'Instrumental:', 'Ending:', 'Outro:', 'Interlude:', 'Rap:', 'Spontaneous:',
        'Refrain:', 'Tag:', 'Coda:', 'Vamp:', 'Channel:', 'Breakdown:', 'Hook:',
        'Вступ:', 'Приспів:', 'Брідж:', 'Заспів:', 'Міст:', 'Програш:',
        'Перехід:', 'Інтро:', 'Повтор:', 'Кінець:', 'Тег:'
    ])
}

def trim(s): return s.strip() if isinstance(s, str) else ''

def is_non_empty(s): return isinstance(s, str) and s.strip()

def clean_html_entities(s): return re.sub(r'&[\w#]+;', '', s) if is_non_empty(s) else ''

def is_chord_line(line):
    if not is_non_empty(line): return False
    tokens = trim(line).split()
    return all(CHORD_REGEX.match(t) or any(sym in t for sym in CHORD_SYMBOLS) for t in tokens)

def is_section_label(line):
    line = trim(line).lower()
    return any(line.startswith(label.rstrip(':|')) for label in SECTION_LABELS)

def is_numbered_section(line):
    match = re.match(r'^(\d+)\s*(куплет|бридж|verse|bridge)', line.strip(), re.I)
    return {'number': match[1], 'type': match[2].capitalize()} if match else None

def format_lines(text):
    if not is_non_empty(text): return ''
    lines = text.split('\n')
    result, found_header = [], False

    for line in lines:
        line = trim(line)
        if line.startswith('##('):
            if found_header and result and result[-1] != '':
                result.append('')
            found_header = True
        if line != '//':
            result.append(line)
    return trim('\n'.join(result))

def format_song(raw_text):
    if not is_non_empty(raw_text): return ''
    text = clean_html_entities(raw_text)
    output = []

    for line in text.split('\n'):
        line = trim(line)
        if not line or is_chord_line(line):
            continue
        if section := is_numbered_section(line):
            output.append(f"{section['type']} {section['number']}:")
        elif is_section_label(line):
            output.append(re.sub(r'[:|]$', '', line) + ':')
        else:
            output.append(line)

    return format_lines('\n'.join(output))


API_TOKEN = os.getenv('TOKEN')
bot = telebot.TeleBot(API_TOKEN)


bot.user_data = {}

COMMON_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": "https://fonki.pro/"
}


def send_audio_file(chat_id, url, song_name):
    try:
        downloading_message = bot.send_message(chat_id, f"⏳ Скачиваю  ...")

        file_content = download_mp3(url)

        if file_content:
            bot.send_audio(chat_id, file_content, title=song_name, timeout=120)
        else:
            bot.send_message(chat_id, f"❌ Не удалось скачать ...")

        bot.delete_message(chat_id, downloading_message.message_id)
    except Exception as e:
        bot.send_message(chat_id, "⚠️ Ошибка при скачивании файла.")
        print(f"Send minus file error: {e}")




def download_mp3(url):
    print(url)
    try:
        response = requests.get(url, headers=COMMON_HEADERS, timeout=15)
        if response.status_code == 200:
            return response.content
        else:
            print(f"Download error: {response.status_code}")
            return None
    except Exception as e:
        print(f"Exception during MP3 download: {e}")
        return None

@bot.message_handler(commands=['start'])
def start_handler(message):
    bot.send_message(
        message.chat.id,
        "🎤 Напиши *название песни*, и я помогу тебе:\n"
        "• Найти 🎼 *текст песни*\n"
        "• Скачать 🎵 *плюс* и 🎶 *минус* версии\n"
        "• Получить 📄 *PDF для распечатки*\n\n"
        "💬 Введи название песни, и начнём!",
        parse_mode="Markdown"
    )

@bot.message_handler(func=lambda message: True)
def handle_song_request(message):
    user_input = message.text.strip()
    search_url = f"https://fonki.pro/search?name={user_input}"

    try:
        response = requests.get(search_url, headers=COMMON_HEADERS, timeout=15)
        response.raise_for_status()

        data = response.json()
        songs = data.get('musics', {}).get('data', [])

        if not songs:
            bot.send_message(message.chat.id, "❌ Песни не найдены. Попробуй уточнить запрос.")
            return

        bot.user_data[message.chat.id] = {"results": songs}

        if len(songs) == 1:
            # Только один результат — сразу отображаем
            song = songs[0]
            bot.user_data[message.chat.id] = {
                "results": songs,
                "selected": song
            }

            song_name = song.get('name', 'Без названия')
            lyrics = format_song(song.get('text', 'Нет текста.'))

            if len(lyrics) > 4000:
                lyrics = lyrics[:4000] + "\n...\n(текст обрезан)"

            bot.send_message(message.chat.id, f"🎤 *{song_name}*\n\n{lyrics}", parse_mode="Markdown")

            markup = types.InlineKeyboardMarkup()
            markup.add(
                types.InlineKeyboardButton("📥 Скачать PDF", callback_data="download_pdf")
            )
            markup.add(
                types.InlineKeyboardButton("🎵 Скачать MP3+", callback_data="download_mp3+"),
                types.InlineKeyboardButton("🎶 Скачать MP3-", callback_data="download_mp3-")
            )
            bot.send_message(message.chat.id, "👇 Нажми на кнопку для скачивания:", reply_markup=markup)

        else:
            # Несколько результатов — показать кнопки выбора
            bot.user_data[message.chat.id] = {"results": songs}
            markup = types.InlineKeyboardMarkup()
            for i, song in enumerate(songs[:5]):
                name = song.get('name', 'Без названия')
                artist = song.get('artist').get('name')
                markup.add(types.InlineKeyboardButton(f'{name} - {artist}', callback_data=f"choose::{i}"))

            bot.send_message(message.chat.id, "🔍 Вот несколько песен, выбери одну для просмотра текста:", reply_markup=markup)


    except Exception as e:
        bot.send_message(message.chat.id, "⚠️ Произошла ошибка при поиске. Попробуй снова позже.")
        print(f"Error during search: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith("choose::"))
def handle_song_choice(call):
    try:
        chat_id = call.message.chat.id
        index = int(call.data.split("::")[1])

        song = bot.user_data.get(chat_id, {}).get("results", [])[index]
        if not song:
            bot.send_message(chat_id, "⚠️ Не удалось выбрать песню.")
            return

        bot.user_data[chat_id]["selected"] = song
        song_name = song.get('name', 'Без названия')
        lyrics = format_song(song.get('text', 'Нет текста.'))

        if len(lyrics) > 4000:
            lyrics = lyrics[:4000] + "\n...\n(текст обрезан)"

        bot.send_message(chat_id, f"🎤 *{song_name}*\n\n{lyrics}", parse_mode="Markdown")

        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📥 Скачать PDF", callback_data="download_pdf"))
        markup.add(
            types.InlineKeyboardButton("🎵 Скачать MP3+", callback_data="download_mp3+"),
            types.InlineKeyboardButton("🎶 Скачать MP3-", callback_data="download_mp3-")
        )
        bot.send_message(chat_id, "👇 Нажми на кнопку для скачивания:", reply_markup=markup)

    except Exception as e:
        bot.send_message(call.message.chat.id, "⚠️ Ошибка при выборе песни.")
        print(f"Song choice error: {e}")

@bot.callback_query_handler(func=lambda call: call.data == "download_pdf")
def callback_download_pdf(call):
    chat_id = call.message.chat.id
    song = bot.user_data.get(chat_id, {}).get("selected")

    if not song:
        bot.send_message(chat_id, "⚠️ Не найден текст песни.")
        return

    try:
        song_name = song.get('name', 'Без названия')
        lyrics = format_song(song.get('text', 'Нет текста.'))

        filename = create_pdf(lyrics, f"{song_name}.pdf")
        with open(filename, "rb") as f:
            bot.send_document(chat_id, f, visible_file_name=f"{song_name}.pdf")
        os.remove(filename)

    except Exception as e:
        bot.send_message(chat_id, "⚠️ Ошибка при создании PDF.")
        print(f"PDF error: {e}")

@bot.callback_query_handler(func=lambda call: call.data == "download_mp3+")
def callback_download_mp3(call):
    chat_id = call.message.chat.id
    song = bot.user_data.get(chat_id, {}).get("selected")

    if not song:
        bot.send_message(chat_id, "⚠️ Не найден плюс песни.")
        return

    try:
        song_name = song.get('name', 'Без названия')
        song_plus = str(song.get('file'))

        send_audio_file(chat_id, "https://fonki.pro" + song_plus, song_name)

    except Exception as e:
        bot.send_message(chat_id, "⚠️ Ошибка при скачивании MP3+.")
        print(f"MP3+ error: {e}")

@bot.callback_query_handler(func=lambda call: call.data == "download_mp3-")
def callback_download_mp3_minus(call):
    chat_id = call.message.chat.id
    song = bot.user_data.get(chat_id, {}).get("selected")

    if not song:
        bot.send_message(chat_id, "⚠️ Не найден минус песни.")
        return

    try:
        song_name = song.get('name', 'Без названия')
        song_id = str(song.get('id'))

        response = requests.get(f"https://fonki.pro/minus/{song_id}", headers=COMMON_HEADERS, timeout=15)
        response.raise_for_status()

        matches = re.findall(r'data-source="/plugin/sounds/uploads/(\d+)\.mp3"', response.text)

        if not matches:
            bot.send_message(chat_id, "⚠️ Минус не найден.")
            return

        if len(matches) == 1:
            # Только один минус — сразу скачиваем
            send_audio_file(chat_id, f"https://fonki.pro/plugin/sounds/uploads/{matches[0]}.mp3", song_name)
        else:
            # Несколько — даём выбрать
            markup = types.InlineKeyboardMarkup()
            for i, match_id in enumerate(matches):
                btn = types.InlineKeyboardButton(f"Версия {i+1} (ID: {match_id})", callback_data=f"download_specific_minus::{match_id}")
                markup.add(btn)
            msg = bot.send_message(chat_id, "🎶 Найдено несколько версий минусовки. Выбери нужную:", reply_markup=markup)
            bot.user_data[chat_id]["version_pick"] = msg


    except Exception as e:
        bot.send_message(chat_id, "⚠️ Ошибка при поиске минуса.")
        print(f"MP3- search error: {e}")


@bot.callback_query_handler(func=lambda call: call.data.startswith("download_specific_minus::"))
def callback_download_specific_minus(call):
    chat_id = call.message.chat.id
    song = bot.user_data.get(chat_id, {}).get("selected")

    if not song:
        bot.send_message(chat_id, "⚠️ Песня не найдена.")
        return

    try:
        song_id = call.data.split("::")[1]
        song_name = song.get('name', 'Без названия')
        send_audio_file(chat_id, f"https://fonki.pro/plugin/sounds/uploads/{song_id}.mp3", song_name)
        msg = bot.user_data.get(chat_id, {}).get("version_pick")
        if msg:
            bot.delete_message(chat_id, msg.message_id)


    except Exception as e:
        bot.send_message(chat_id, "⚠️ Ошибка при загрузке выбранной версии.")
        print(f"Specific minus error: {e}")



print("✅ Бот запущен...")
bot.infinity_polling()
