import asyncio
import random
from aiogram import Bot, Dispatcher, F
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, Message
from aiogram.filters import Command, CommandStart
from config import get_config
from data_handler import DataProcessor
from collab_filtering import CollaborativeFiltering
from storage import Storage
from similarity import user_pearson_similarity

config = get_config()
bot = Bot(token=config["tg_token"])
dp = Dispatcher()

data_processor = DataProcessor()
cf_engine: CollaborativeFiltering | None = None
storage = Storage(config["storage_path"])

# Словарь для управления простыми диалоговыми состояниями
# user_dialog_state[chat_id] = {
#    "state": None | "awaiting_initial_ratings",
#    "initial_movies": [ (movie_id, title), ... ]  # временно хранится когда ждем ответы
# }
user_dialog_state: dict = {}


def _local_user_ratings_dict() -> dict:
    """
    Получение словаря оценок локального пользователя.

    :return: Словарь {movie_id: rating}
    """
    local = storage.get_local_user()
    ratings = {}
    for k, v in local.get("ratings", {}).items():
        try:
            ratings[int(k)] = float(v)
        except Exception:
            continue
    return ratings


async def _find_most_similar_real_user(local_ratings: dict) -> tuple[int | None, float]:
    """
    Поиск наиболее похожего реального пользователя.

    :param local_ratings: Оценки локального пользователя
    :return: Кортеж (user_id, similarity) или (None, 0.0)
    """
    if not local_ratings or data_processor.user_item_table is None:
        return None, 0.0
    
    min_common = config["cf"].get("min_common_users")

    def _sync_search():
        best_uid = None
        best_sim = -1.0

        for uid in data_processor.get_all_users():
            other_ratings = data_processor.get_user_ratings(uid)
            sim = user_pearson_similarity(
                local_ratings, other_ratings, min_common=min_common)

            if sim is not None and sim > best_sim:
                best_sim = sim
                best_uid = uid
                
        if best_uid is None:
            return (None, 0.0)
        return (best_uid, float(best_sim))

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _sync_search)


@dp.message(CommandStart())
async def cmd_start(message: Message) -> None:
    text = (
        "Привет! Я рекомендательный бот.\n\n"
        "Вы можете:\n"
        "/rate — добавить/изменить локальную оценку (1-5)\n"
        "/whoami — посмотреть локальные оценки\n"
        "/recommend [N] — получить рекомендации (по умолчанию N = 5)\n"
        "/info <movie_id> — посмотреть информацию о фильме\n"
        "/clear — очистить все оценки текущего пользователя\n\n"
    )
    await message.answer(text)


@dp.message(Command("rate"))
async def cmd_rate(message: Message) -> None:
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Ввести оценку по id",
                              callback_data="rate_by_id")],
        [InlineKeyboardButton(text="Оценить подборку",
                              callback_data="rate_suggest")]
    ])
    await message.answer("Выберите способ добавления оценки:", reply_markup=kb)


@dp.callback_query(F.data == "rate_by_id")
async def cb_rate_by_id(query: CallbackQuery) -> None:
    chat_id = query.message.chat.id
    user_dialog_state[chat_id] = {"state": "awaiting_manual_rate"}
    await query.message.edit_text("Введите оценку в формате: <movie_id> <rating>\n"
                                  "Например: 50 4.5\n\n"
                                  "Для информации о фильме используйте /info <movie_id>.")
    await query.answer()


@dp.callback_query(F.data == "rate_suggest")
async def cb_rate_suggest(query: CallbackQuery) -> None:
    chat_id = query.message.chat.id

    random_movies = data_processor.get_random_movies(5)
    movies = [(mid, data_processor.get_movie_title(mid))
              for mid in random_movies]

    user_dialog_state[chat_id] = {
        "state": "awaiting_batch_rate",
        "initial_movies": movies
    }

    example_ratings = []
    for mid, _ in movies:
        rating = round(random.uniform(3.0, 5.0), 1)
        example_ratings.append(f"{mid}:{rating}")

    example_text = ", ".join(example_ratings)

    text = "Оцените, пожалуйста, эти случайные фильмы в формате:\n" \
           "movie_id:rating, movie_id:rating, ...\n\n" \
           f"Пример:\n{example_text}\n\n" \
           "Список фильмов:\n"

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
        n = int(parts[1]) if len(
            parts) > 1 else config["cf"]["num_recommendations"]
    except Exception:
        n = config["cf"]["num_recommendations"]

    local_ratings = _local_user_ratings_dict()

    if not local_ratings:
        popular = data_processor.get_top_popular_movies(5)
        movies = [(mid, data_processor.get_movie_title(mid))
                  for mid in popular]

        user_dialog_state[message.from_user.id] = {
            "state": "awaiting_initial_ratings",
            "initial_movies": movies,
            "want_n": n
        }

        text = (
            "У вас ещё нет оценок.\n\n"
            "Вы можете оценить подборку популярных фильмов (введите оценки в формате: movie_id:rating, movie_id:rating...)\n\n"
            "Подборка фильмов:\n"
        )
        for mid, title in movies:
            text += f"{mid} — {title}\n"
        text += "\nПример ответа: \n50:4.5, 258:3, 100:5, 181:4, 294:5"

        await message.answer(text)
        return None

    await message.answer("Формирую рекомендации... Пожалуйста, подождите.")
    recommendations = await cf_engine.generate_recommendations(local_ratings, num_recommendations=n)

    best_uid, best_sim = await _find_most_similar_real_user(local_ratings)

    lines = ["Рекомендации:"]
    for i, (movie_id, score) in enumerate(recommendations, 1):
        title = data_processor.get_movie_title(movie_id)
        genres = ", ".join(data_processor.get_movie_genres(movie_id))
        lines.append(
            f"{i}. {title} ({movie_id}) — предсказанный рейтинг: {score:.2f} — жанры: {genres}")

    if best_uid is not None and best_sim > 0:
        lines.append(
            f"\nПохожесть с реальным пользователем id={best_uid}: {best_sim:.3f}")
    else:
        lines.append(
            "\nНет похожих реальных пользователей в датасете (или недостаточно данных).")

    await message.answer("\n".join(lines))


@dp.message(Command("info"))
async def cmd_info(message: Message) -> None:
    parts = message.text.strip().split()
    if len(parts) < 2:
        await message.answer("Использование: /info <movie_id>\nПример: \n/info 200")
        return None
    try:
        mid = int(parts[1])
    except ValueError:
        await message.answer("movie_id должен быть целым числом.")
        return None

    title = data_processor.get_movie_title(mid)
    genres = data_processor.get_movie_genres(mid)
    genres_str = ", ".join(genres) if genres else "неизвестно"

    if data_processor.ratings_df is not None and not data_processor.ratings_df.empty:
        dfm = data_processor.ratings_df[data_processor.ratings_df['movie_id'] == mid]
        if not dfm.empty:
            avg = dfm['rating'].mean()
            count = len(dfm)
            stats = f"\nСредний рейтинг: {avg:.2f} (по {count} оценкам)"
        else:
            stats = "\nНет данных по рейтингу для этого фильма."
    else:
        stats = ""

    await message.answer(f"{mid}: {title}\nЖанры: {genres_str}{stats}")


@dp.message(Command("clear"))
async def cmd_clear(message: Message) -> None:
    storage.clear_local_user()
    await message.answer("Все ваши оценки очищены!")


@dp.message()
async def handle_dialog_messages(message: Message) -> None:
    chat_id = message.from_user.id
    state_entry = user_dialog_state.get(chat_id)
    if not state_entry:
        await message.answer("Неверная команда")
    else:
        state = state_entry.get("state")
        text = message.text.strip()

        if state == "awaiting_initial_ratings":
            added = await _parse_and_save_ratings(text)
            if added > 0:
                user_dialog_state.pop(chat_id, None)
                await message.answer(f"Добавлено оценок: {added}. Теперь можете использовать /recommend для получения персонализированных рекомендаций!")
            else:
                await message.answer("Не удалось распознать оценки. Используйте формат: movie_id:rating, movie_id:rating, ...")

        elif state == "awaiting_manual_rate":
            parts = text.replace(":", " ").split()
            if len(parts) < 2:
                await message.answer("Неправильный формат. Введите: <movie_id> <rating>. Например: 50 4.5.")
            else:
                try:
                    mid = int(parts[0])
                    rating = float(parts[1])
                    if 1.0 <= rating <= 5.0:
                        storage.add_rating(mid, rating)
                        title = data_processor.get_movie_title(mid)
                        user_dialog_state.pop(chat_id, None)
                        await message.answer(f"Сохранено: {mid} — {title} -> {rating}")
                    else:
                        await message.answer("Оценка должна быть в диапазоне 1..5.")
                except Exception:
                    await message.answer("Ошибка формата. movie_id должен быть целым, rating — число (например 4.0 или 4.5).")

        elif state == "awaiting_batch_rate":
            added = await _parse_and_save_ratings(text)
            if added > 0:
                user_dialog_state.pop(chat_id, None)
                await message.answer(f"Добавлено оценок: {added}.")
            else:
                await message.answer("Не удалось распознать оценки. Используйте формат: movie_id:rating, movie_id:rating, ...")


async def _parse_and_save_ratings(text: str) -> int:
    """
    Парсинг и сохранение оценок из текстового ввода.

    :param text: Текст с оценками в формате movie_id:rating
    :return: Количество добавленных оценок
    """
    pairs = [p.strip() for p in text.split(',') if p.strip()]
    if not pairs:
        return 0

    added = 0
    for p in pairs:
        if ':' not in p:
            sub = p.split()
            if len(sub) >= 2:
                try:
                    mid = int(sub[0])
                    rating = float(sub[1])
                except Exception:
                    continue
            else:
                continue
        else:
            left, right = p.split(':', 1)
            try:
                mid = int(left.strip())
                rating = float(right.strip())
            except Exception:
                continue
        if 1.0 <= rating <= 5.0:
            storage.add_rating(mid, rating)
            added += 1

    return added


async def main() -> None:
    await data_processor.load_data()
    min_common = config["cf"]["min_common_users"]
    top_k = config["cf"]["top_k"]
    cache_path = config["cache_path"]
    global cf_engine
    cf_engine = CollaborativeFiltering(
        data_processor, min_common_users=min_common, top_k=top_k, cache_path=cache_path)
    print("Данные загружены, бот готов.")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())