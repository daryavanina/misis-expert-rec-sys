import aiohttp
from config import get_config
from static import texts

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
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                response.raise_for_status()
                return await response.json()
    except aiohttp.ClientError as err:
        print(f"Ошибка API: {err}")
        return None


async def get_gpt4o_response(user_query: str, context: str = "") -> str:
    """
    Выполняет анализ эмоций текста с помощью модели GPT-4o (через RapidAPI).

    :param user_query: Текст, отправляемый пользователем для анализа.
    :param context: Необязательный контекст, добавляемый к системному сообщению.
    :return: Текстовое описание эмоционального состояния, сгенерированное моделью.
    """
    system_prompt = (
        f"{context} {texts.SYSTEM_PROMPT}"
    )

    payload = {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Проанализируй это сообщение: {user_query}"}
        ],
        "temperature": 0.7,           # Контролирует креативность (0 — точнее, 1 — креативнее)
        "max_tokens": 300,            # Максимальное количество токенов в ответе
        "top_p": 0.9,                 # Нуклеус-семплинг (оставляет верхние p вероятностей)
        "presence_penalty": 0.6,      # Наказывает за повторения
        "frequency_penalty": 0.4,    # Наказывает за частое использование одних и тех же фраз
        "web_access": False
    }

    response = await query_llm_api(
        config["gpt4o_url"],
        config["gpt4o_host"],
        payload
    )

    if response and "result" in response:
        return response["result"]
    elif response and "response" in response:
        return response["response"]
    else:
        return texts.ERROR_MESSAGE.format(error="GPT-4o не смог проанализировать эмоции.")


async def get_llama_response(user_query: str, context: str = "") -> str:
    """
    Выполняет анализ эмоций текста с помощью модели LLaMA 2 (через RapidAPI).

    :param user_query: Текст, отправляемый пользователем для анализа.
    :param context: Необязательный контекст, добавляемый к системному сообщению.
    :return: Текстовое описание эмоций, выведенное моделью LLaMA.
    """
    system_prompt = (
        f"{context} {texts.SYSTEM_PROMPT}"
    )

    payload = {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Проанализируй это сообщение: {user_query}"}
        ],
        "parameters": {
            "temperature": 0.65,          # Умеренно креативный стиль
            "top_p": 0.9,                 # Используется нуклеус-семплинг
            "max_new_tokens": 300,        # Ограничение длины ответа
            "repetition_penalty": 1.1,    # Штраф за повторения фраз
            "do_sample": True             # Включает вероятностную выборку
        }
    }

    response = await query_llm_api(
        config["llama_url"],
        config["llama_host"],
        payload
    )

    if response and "result" in response:
        return response["result"]
    else:
        return texts.ERROR_MESSAGE.format(error="LLaMA не смог проанализировать эмоции.")
