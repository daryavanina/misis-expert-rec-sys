from dotenv import load_dotenv
import os

load_dotenv()

def get_config() -> dict:
    """
    Возвращает конфигурацию тг-бота и RapidAPI
    :return: Словарь с токенами, URL и параметрами.
    """
    return {
        "tg_token": os.getenv("TELEGRAM_TOKEN"),
        "rapid_key": os.getenv("RAPIDAPI_KEY"),
        "gpt4o_host": os.getenv("GPT4O_HOST"),
        "gpt4o_url": os.getenv("GPT4O_URL"),
        "llama_host": os.getenv("LLAMA_HOST"),
        "llama_url": os.getenv("LLAMA_URL"),
        "model_params": {
            "temperature": 0.7,
            "max_tokens": 100,
            "top_p": 0.9,
            "repetition_penalty": 1.1,
            "presence_penalty": 0.6,
            "frequency_penalty": 0.4
        }
    }