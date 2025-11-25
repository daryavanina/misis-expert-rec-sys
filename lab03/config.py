from dotenv import load_dotenv
import os

load_dotenv()

def get_config() -> dict:
    """
    Возвращает конфигурацию из переменных окружения.

    :return: Словарь с настройками приложения
    """
    return {
        "tg_token": os.getenv("TELEGRAM_TOKEN"),
        "dataset_users_path": os.getenv("DATASET_USERS_PATH", "data/u.data"),
        "dataset_films_path": os.getenv("DATASET_FILMS_PATH", "data/u.item"),
        "storage_path": os.getenv("STORAGE_PATH", "data/local_user_storage.json"),
        "cache_path": os.getenv("CACHE_PATH", "data/similarity_cache.pkl"),
        "cf": {
            "min_common_users": int(os.getenv("CF_MIN_COMMON", 3)),
            "top_k": int(os.getenv("CF_TOP_K", 20)),
            "num_recommendations": int(os.getenv("CF_NUM_RECOMMENDATIONS", 5))
        }
    }
