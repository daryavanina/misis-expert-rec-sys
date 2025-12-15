from dotenv import load_dotenv
import os

load_dotenv()

def get_config() -> dict:
    """
    Конфигурация приложения из .env
    """
    return {
        "tg_token": os.getenv("TELEGRAM_TOKEN"),
        "dataset_users_path": os.getenv("DATASET_USERS_PATH", "data/u.data"),
        "dataset_films_path": os.getenv("DATASET_FILMS_PATH", "data/u.item"),
        "storage_path": os.getenv("STORAGE_PATH", "data/local_user_storage.json"),
        "model_cache_path": os.getenv("MODEL_CACHE_PATH", "data/svdpp_model.pkl"),
        "svdpp": {
            "factors": int(os.getenv("SVDPP_FACTORS")),
            "lr": float(os.getenv("SVDPP_LR")),
            "reg": float(os.getenv("SVDPP_REG")),
            "epochs": int(os.getenv("SVDPP_EPOCHS"))
        },
        "recommend": {
            "num_recommendations": int(os.getenv("CF_NUM_RECOMMENDATIONS", 5))
        }
    }
