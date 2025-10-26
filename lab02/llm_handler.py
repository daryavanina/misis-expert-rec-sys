import aiohttp
from config import get_config
import json
from pathlib import Path

MAX_ANSWER_TIMEOUT_SECONDS = 60
"""
Максимальное время ожидания ответа от LLM API в секундах.
"""

def load_texts():
    static_path = Path(__file__).parent / "static" / "texts.json"
    with open(static_path, "r", encoding="utf-8") as f:
        return json.load(f)

texts = load_texts()

config = get_config()

async def query_llm_api(url: str, host: str, payload: dict) -> dict:
    """
    Асинхронный POST-запрос к LLM API.

    :param url: URL LLM
    :param host: Хост (RapidAPI host)
    :param payload: JSON-данные для запроса
    :return: Словарь с результатом запроса или None при ошибке
    """

    headers = {
        "x-rapidapi-key": config["rapid_key"],
        "x-rapidapi-host": host,
        "Content-Type": "application/json"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=MAX_ANSWER_TIMEOUT_SECONDS)
            ) as response:
                response.raise_for_status()
                return await response.json()
    except aiohttp.ClientError as err:
        print(f"Ошибка API: {err}")
        return None


async def get_gpt4o_response(user_query: str, params: dict) -> str:
    """
    Выполняет анализ эмоций текста с помощью модели GPT-4o (через RapidAPI).

    :param user_query: Текст, отправляемый пользователем для анализа.
    :param context: Необязательный контекст, добавляемый к системному сообщению.
    :return: Текстовое описание эмоционального состояния, сгенерированное моделью.
    """
    base_params = config["model_params"]

    temperature = params.get("temperature", base_params["temperature"])
    max_tokens = params.get("max_tokens", base_params["max_tokens"])
    
    lang_instruction = (
        "Отвечай на русском языке."
        if params.get("language") == "русский"
        else "Answer in English."
    )
    
    system_prompt = (
        f"{texts["SYSTEM_PROMPT"]} {lang_instruction}"
    )

    payload = {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Проанализируй эмоции в тексте: {user_query}"}
        ],
        "temperature": temperature,                             # Контролирует креативность (0 — точнее, 1 — креативнее)
        "max_tokens": max_tokens,                               # Максимальное количество токенов в ответе    
        "top_p": base_params["top_p"],                          # Используется нуклеус-семплинг 
        "presence_penalty": base_params["presence_penalty"],    # Наказывает за повторения
        "frequency_penalty": base_params["frequency_penalty"],  # Наказывает за частое использование одних и тех же фраз
        "web_access": False
    }

    response = await query_llm_api(
        config["gpt4o_url"],
        config["gpt4o_host"],
        payload
    )

    if response:
            if "result" in response:
                return response["result"]
            elif "response" in response:
                return response["response"]
            elif isinstance(response, dict):
                return str(response)
    return texts["ERROR_MESSAGE"].format(error="GPT-4o не смог проанализировать эмоции.")


async def get_llama_response(user_query: str, params: dict) -> str:
    """
    Выполняет анализ эмоций текста с помощью модели LLaMA 2 (через RapidAPI).

    :param user_query: Текст, отправляемый пользователем для анализа.
    :param context: Необязательный контекст, добавляемый к системному сообщению.
    :return: Текстовое описание эмоций, выведенное моделью LLaMA.
    """
    base_params = config["model_params"]

    temperature = params.get("temperature", base_params["temperature"])
    max_tokens = params.get("max_tokens", base_params["max_tokens"])
    
    lang_instruction = (
        "Отвечай на русском языке."
        if params.get("language") == "русский"
        else "Answer in English."
    )
     
    system_prompt = (
        f"{texts["SYSTEM_PROMPT"]} {lang_instruction}"
    )

    payload = {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Проанализируй эмоции в тексте: {user_query}"}
        ],
        "temperature": temperature,                              # Контролирует креативность    (0 — точнее, 1 — креативнее)
        "max_new_tokens": max_tokens,                            # Ограничение длины ответа
        "top_p": base_params["top_p"],                           # Используется нуклеус-семплинг
        "repetition_penalty": base_params["repetition_penalty"], # Штраф за повторения фраз
        "do_sample": 1
        }

    response = await query_llm_api(
        config["llama_url"],
        config["llama_host"],
        payload
    )

    if response:
        if "result" in response:
            return response["result"]
        elif "response" in response:
            return response["response"]
        elif isinstance(response, dict):
            return str(response)
    return texts["ERROR_MESSAGE"].format(error="LLaMA не смогла проанализировать эмоции.")