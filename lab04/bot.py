import asyncio
import random
from aiogram import Bot, Dispatcher, F
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, Message
from aiogram.filters import Command, CommandStart
from config import get_config
from data_handler import DataProcessor
from svdpp import SVDpp
from storage import Storage

config = get_config()
bot = Bot(token=config["tg_token"])
dp = Dispatcher()

data_processor = DataProcessor()
storage = Storage(config["storage_path"])

user_dialog_state: dict = {}

def _local_user_ratings_dict() -> dict:
    local = storage.get_local_user()
    ratings = {}
    for k, v in local.get("ratings", {}).items():
        try:
            ratings[int(k)] = float(v)
        except Exception:
            continue
    return ratings

@dp.message(CommandStart())
async def cmd_start(message: Message) -> None:
    text = (
        "Привет! Я рекомендательный бот (SVD++).\n\n"
        "Доступные команды:\n"
        "/rate — добавить/изменить локальную оценку (1-5)\n"
        "/whoami — показать локальные оценки\n"
        "/recommend [N] — получить рекомендации (по умолчанию N = из конфига)\n"
        "/info <movie_id> — информация о фильме\n"
        "/clear — очистить все оценки\n"
    )
    await message.answer(text)

@dp.message(Command("rate"))
async def cmd_rate(message: Message) -> None:
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Ввести оценку по id", callback_data="rate_by_id")],
        [InlineKeyboardButton(text="Оценить подборку", callback_data="rate_suggest")]
    ])
    await message.answer("Выберите способ добавления оценки:", reply_markup=kb)

@dp.callback_query(F.data == "rate_by_id")
async def cb_rate_by_id(query: CallbackQuery) -> None:
    chat_id = query.message.chat.id
    user_dialog_state[chat_id] = {"state": "awaiting_manual_rate"}
    await query.message.edit_text("Введите оценку в формате: <movie_id> <rating>\nНапример: 50 4.5")
    await query.answer()

@dp.callback_query(F.data == "rate_suggest")
async def cb_rate_suggest(query: CallbackQuery) -> None:
    chat_id = query.message.chat.id
    random_movies = data_processor.get_random_movies(5)
    movies = [(mid, data_processor.get_movie_title(mid)) for mid in random_movies]
    user_dialog_state[chat_id] = {"state": "awaiting_batch_rate", "initial_movies": movies}
    example = " ".join([f"{mid} {round(random.uniform(3.0,5.0),1)}" for mid, _ in movies])
    text = "Оцените, пожалуйста, эти фильмы в формате: movie_id rating ...\n\nПример:\n" + example + "\n\nСписок:\n"
    for mid, title in movies:
        text += f"{mid} — {title}\n"
    await query.message.edit_text(text)
    await query.answer()

@dp.message(Command("whoami"))
async def cmd_whoami(message: Message) -> None:
    local = storage.get_local_user()
    ratings = local.get("ratings", {})
    lines = ["Локальные рейтинги (movie_id : title -> rating):"]
    if not ratings:
        lines.append("(пусто)")
    else:
        for k, v in ratings.items():
            try:
                mid = int(k)
            except Exception:
                continue
            title = data_processor.get_movie_title(mid)
            lines.append(f"{mid} : {title} -> {v}")
    await message.answer("\n".join(lines))

@dp.message(Command("recommend"))
async def cmd_recommend(message: Message) -> None:
    parts = message.text.strip().split()
    try:
        n = int(parts[1]) if len(parts) > 1 else config["recommend"]["num_recommendations"]
    except Exception:
        n = config["recommend"]["num_recommendations"]

    local_ratings = _local_user_ratings_dict()
    if not local_ratings:
        # cold start: предложить оценить подборку или показать популярные
        popular = data_processor.get_top_popular_movies(5)
        movies = [(mid, data_processor.get_movie_title(mid)) for mid in popular]
        user_dialog_state[message.from_user.id] = {"state": "awaiting_initial_ratings", "initial_movies": movies, "want_n": n}
        text = "У вас ещё нет оценок.\nМогу предложить оценить подборку популярных фильмов (введите movie_id rating...)\nПример:\n50 5 258 4.5 100 4 181 3.8 294 4\n\nИли введите 'skip' чтобы получить популярные фильмы сейчас.\n\nСписок:"
        for mid, title in movies:
            text += f"\n{mid} — {title}"
        await message.answer(text)
        return

    await message.answer("Формирую рекомендации... ⌛")
    # Генерируем рекомендации через SVD++
    recs = svd_engine.recommend_for_virtual_user(local_ratings, n=n)
    if not recs:
        # fallback: популярные
        top_pop = data_processor.get_top_popular_movies(n)
        lines = ["Не удалось предсказать персонализованные рекомендации. Популярные фильмы:"]
        for i, mid in enumerate(top_pop, 1):
            title = data_processor.get_movie_title(mid)
            lines.append(f"{i}. {title} ({mid})")
        await message.answer("\n".join(lines))
        return

    lines = ["Рекомендации:"]
    for i, (mid, score) in enumerate(recs, 1):
        title = data_processor.get_movie_title(mid)
        lines.append(f"{i}. {title} ({mid}) — предсказанный рейтинг: {score:.2f}")
    await message.answer("\n".join(lines))

@dp.message(Command("info"))
async def cmd_info(message: Message) -> None:
    parts = message.text.strip().split()
    if len(parts) < 2:
        await message.answer("Использование: /info <movie_id>")
        return
    try:
        mid = int(parts[1])
    except ValueError:
        await message.answer("movie_id должен быть целым.")
        return
    title = data_processor.get_movie_title(mid)
    await message.answer(f"{mid}: {title}")

@dp.message(Command("clear"))
async def cmd_clear(message: Message) -> None:
    storage.clear_local_user()
    await message.answer("Все ваши оценки очищены!")

@dp.message()
async def handle_dialog_messages(message: Message) -> None:
    chat_id = message.from_user.id
    state_entry = user_dialog_state.get(chat_id)
    if not state_entry:
        await message.answer("Команда не распознана. Используйте /start или /recommend.")
        return

    state = state_entry.get("state")
    text = message.text.strip().lower()

    if state == "awaiting_initial_ratings":
        if text == "skip":
            want_n = state_entry.get("want_n", config["recommend"]["num_recommendations"])
            top_pop = data_processor.get_top_popular_movies(want_n * 2)[want_n:want_n * 2]
            lines = ["Популярные фильмы:"]
            for i, mid in enumerate(top_pop, 1):
                title = data_processor.get_movie_title(mid)
                lines.append(f"{i}. {title} ({mid})")
            user_dialog_state.pop(chat_id, None)
            await message.answer("\n".join(lines))
            return

        added = _parse_and_save_ratings_sync(text)
        if added > 0:
            user_dialog_state.pop(chat_id, None)
            await message.answer(f"Добавлено оценок: {added}. Теперь используйте /recommend.")
        else:
            await message.answer("Не удалось распознать пары. Формат: movie_id rating ...")

    elif state == "awaiting_manual_rate":
        parts = text.replace(":", " ").split()
        if len(parts) < 2:
            await message.answer("Неправильный формат. Введите: <movie_id> <rating>.")
            return
        try:
            mid = int(parts[0]); rating = float(parts[1])
        except Exception:
            await message.answer("Ошибка формата.")
            return
        if not (1.0 <= rating <= 5.0):
            await message.answer("Оценка должна быть 1..5.")
            return
        storage.add_rating(mid, rating)
        user_dialog_state.pop(chat_id, None)
        await message.answer(f"Сохранено: {mid} → {rating}")

    elif state == "awaiting_batch_rate":
        added = _parse_and_save_ratings_sync(text)
        if added > 0:
            user_dialog_state.pop(chat_id, None)
            await message.answer(f"Добавлено оценок: {added}.")
        else:
            await message.answer("Не удалось распознать оценки. Используйте формат: movie_id rating...")

def _parse_and_save_ratings_sync(text: str) -> int:
    """
    Парсит текст с оценками и сохраняет их в локальное хранилище.    
    
    :param text: Description
    :return: Description
    """
    if not text or not text.strip():
        return 0

    tokens = text.strip().split()

    if len(tokens) < 2:
        return 0

    added = 0

    for i in range(0, len(tokens) - 1, 2):
        try:
            movie_id = int(tokens[i])
            rating = float(tokens[i + 1])

            if 1.0 <= rating <= 5.0:
                storage.add_rating(movie_id, rating)
                added += 1

        except Exception:
            continue

    return added
    
async def main() -> None:
    await data_processor.load_data()
    
    global svd_engine
    svd_conf = config["svdpp"]
    svd_engine = SVDpp(
        data_processor,
        factors=svd_conf["factors"],
        lr=svd_conf["lr"],
        reg=svd_conf["reg"],
        epochs=svd_conf["epochs"],
        cache_path=config.get("model_cache_path")
    )
    
    loaded = svd_engine.load_cache()
    if not loaded:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, svd_engine.train)
        print("[BOT] SVD++ обучен, бот запущен.")
    else:
        print("[BOT] SVD++ модель загружена из кэша, бот запущен.")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
