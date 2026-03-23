import asyncio
import random
import re

from aiogram import Bot, Dispatcher
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import CommandStart

from words import english_words, german_words
import database as db

TOKEN = "I'm not gonna publish it:)"

# ---------- ДАНІ ----------
correct_answers = {}
used_words = {}

input_word = {}
input_answer = {}

user_action = {}

# ---------- ПРОГРЕС БАР ----------
def progress_bar(current, total, length=10):
    filled = int(length * current / total)
    empty = length - filled
    return "█" * filled + "░" * empty

# ---------- КЛАВІАТУРИ ----------
language_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en"),
            InlineKeyboardButton(text="🇩🇪 Deutsch", callback_data="lang_de")
        ]
    ]
)

menu_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="📚 Вчити слова", callback_data="learn_words")],
        [InlineKeyboardButton(text="🧠 Тест", callback_data="test")],
        [InlineKeyboardButton(text="✍️ Ввести слово", callback_data="input_test")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="stats")],
        [InlineKeyboardButton(text="🔄 Змінити мову", callback_data="change_lang")]
    ]
)

category_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🍔 Food", callback_data="cat_food")],
        [InlineKeyboardButton(text="✈️ Travel", callback_data="cat_travel")],
        [InlineKeyboardButton(text="🏠 Home", callback_data="cat_home")],
        [InlineKeyboardButton(text="⬅️ Меню", callback_data="back_menu")]
    ]
)

words_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="➡️ Наступне слово", callback_data="next_word")],
        [InlineKeyboardButton(text="⬅️ Меню", callback_data="back_menu")]
    ]
)

# ---------- ТЕСТ ----------
async def send_test_question(bot, user_id):
    lang = db.get_language(user_id)
    action = user_action.get(user_id)

    if not action or not action.startswith("test|"):
        return

    category = action.split("|")[1]
    words_dict = english_words if lang == "en" else german_words
    words_list = words_dict[category]

    if user_id not in used_words:
        used_words[user_id] = []

    available_words = [w for w in words_list if w[0] not in used_words[user_id]]

    if not available_words:
        used_words[user_id] = []
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="⬅️ Меню", callback_data="back_menu")]]
        )
        await bot.send_message(user_id, "🎉 Тест завершено! Далі краще!", reply_markup=keyboard)
        return

    word = random.choice(available_words)
    used_words[user_id].append(word[0])
    correct_answers[user_id] = word[1]

    options = [word[1]]
    while len(options) < 4:
        option = random.choice(words_list)[1]
        if option not in options:
            options.append(option)
    random.shuffle(options)

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=o, callback_data=f"answer|{o}")] for o in options]
    )

    progress = len(used_words[user_id])
    total = len(words_list)
    bar = progress_bar(progress, total)

    await bot.send_message(
        user_id,
        f"📚 Прогрес\n\n{bar} {progress}/{total}\n\nЩо означає слово:\n\n{word[0]}",
        reply_markup=keyboard
    )

# ----------- ВВІД ----------
async def send_input_word(bot, user_id):
    lang = db.get_language(user_id)
    action = user_action.get(user_id)

    if not action or not action.startswith("input_test|"):
        return

    category = action.split("|")[1]
    words_dict = english_words if lang == "en" else german_words
    words_list = words_dict[category]

    if user_id not in used_words:
        used_words[user_id] = []

    available_words = [w for w in words_list if w[0] not in used_words[user_id]]

    if not available_words:
        used_words[user_id] = []
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="⬅️ Меню", callback_data="back_menu")]]
        )
        await bot.send_message(user_id, "🎉 Ти пройшов всі слова! Так тримати!", reply_markup=keyboard)
        return

    word = random.choice(available_words)
    used_words[user_id].append(word[0])

    input_word[user_id] = word[0]
    input_answer[user_id] = word[1]

    progress = len(used_words[user_id])
    total = len(words_list)
    bar = progress_bar(progress, total)

    await bot.send_message(
        user_id,
        f"📚 Прогрес\n\n{bar} {progress}/{total}\n\n✍️ Введи переклад слова:\n\n{word[0]}"
    )

# ---------- MAIN ----------
async def main():
    bot = Bot(token=TOKEN)
    dp = Dispatcher()

    db.init_db()

    @dp.message(CommandStart())
    async def start_handler(message: Message):
        await message.answer("Привіт! Я бот для вивчення мов EasyLingua. Мій творець написав мене щоб допомогти тобі вивчити нові слова! 🌍\n\nОбери мову:", reply_markup=language_keyboard)

    @dp.callback_query()
    async def callbacks(callback: CallbackQuery):
        user_id = callback.from_user.id

        if callback.data == "lang_en":
            db.set_language(user_id, "en")
            await callback.message.answer("🇬🇧 English обрано!", reply_markup=menu_keyboard)

        elif callback.data == "lang_de":
            db.set_language(user_id, "de")
            await callback.message.answer("🇩🇪 Deutsch обрано!", reply_markup=menu_keyboard)

        elif callback.data in ["learn_words", "test", "input_test"]:
            used_words[user_id] = []
            user_action[user_id] = callback.data
            await callback.message.answer("Обери категорію:", reply_markup=category_keyboard)

        elif callback.data.startswith("cat_"):
            category = callback.data.split("_")[1]
            action = user_action.get(user_id)

            if action == "learn_words":
                user_action[user_id] = f"learn_words|{category}"
                await callback.message.answer("Натисни 'Наступне слово'", reply_markup=words_keyboard)

            elif action == "test":
                user_action[user_id] = f"test|{category}"
                await send_test_question(bot, user_id)

            elif action == "input_test":
                user_action[user_id] = f"input_test|{category}"
                await send_input_word(bot, user_id)

        elif callback.data == "next_word":
            lang = db.get_language(user_id)
            action = user_action.get(user_id)

            if not action or not action.startswith("learn_words|"):
                return

            category = action.split("|")[1]
            words_dict = english_words if lang == "en" else german_words
            word = random.choice(words_dict[category])

            await callback.message.answer(f"{word[0]} — {word[1]}", reply_markup=words_keyboard)

        elif callback.data.startswith("answer|"):
            answer = callback.data.split("|")[1]
            correct = correct_answers.get(user_id)

            if answer == correct:
                await callback.message.answer("✅ Правильно!")
                db.add_result(user_id, correct_increment=1)
            else:
                await callback.message.answer(f"❌ Неправильно\n\nПравильна: {correct}")
                db.add_result(user_id, wrong_increment=1)

            await send_test_question(bot, user_id)

        elif callback.data == "stats":
            stats = db.get_stats(user_id)
            total = stats["correct"] + stats["wrong"]
            accuracy = int(stats["correct"] / total * 100) if total > 0 else 0

            await callback.message.answer(
                f"📊 Статистика\n\n"
                f"✅ Правильні: {stats['correct']}\n"
                f"❌ Неправильні: {stats['wrong']}\n"
                f"🎯 Точність: {accuracy}%"
            )

        elif callback.data == "back_menu":
            user_action.pop(user_id, None)
            await callback.message.answer("Головне меню:", reply_markup=menu_keyboard)

        elif callback.data == "change_lang":
            await callback.message.answer("Обери мову:", reply_markup=language_keyboard)

        await callback.answer()

    @dp.message()
    async def handle_input(message: Message):
        user_id = message.from_user.id
        action = user_action.get(user_id)

        if not action or not action.startswith("input_test|"):
            return

        user_text = re.sub(r'[^а-яa-zіїєґ]', '', message.text.lower())
        correct = input_answer.get(user_id)

        if not correct:
            return

        correct_text = re.sub(r'[^а-яa-zіїєґ]', '', correct.lower())

        if user_text == correct_text:
            await message.answer("✅ Правильно!")
            db.add_result(user_id, correct_increment=1)
        else:
            await message.answer(f"❌ Неправильно\n\nПравильна відповідь: {correct}")
            db.add_result(user_id, wrong_increment=1)

        await send_input_word(message.bot, user_id)

    print("Бот запущений ✅")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
