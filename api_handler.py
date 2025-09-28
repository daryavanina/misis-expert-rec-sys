import requests
import nlpcloud

from data_handler import get_api_results

config = get_api_results()

def analyze_nlp(text: str) -> dict:
    """
    Делает POST-запрос к API NLP Cloud.

    :param url: URL API
    :param api_key: API ключ
    :param text: текст для анализа
    :return: словарь с результатом анализа эмоций
    """
    try:
        client = nlpcloud.Client("distilbert-base-uncased-emotion", config["nlp_api_key"])
        result = client.sentiment(text, target="NLP Cloud")
        return result
    except Exception as e:
        print(f"Ошибка при анализе текста: {e}")
        return {}
    
def analyze_second(text: str) -> dict:
    """
    Делает POST-запрос к API text to emotions.

    :param url: URL API
    :param api_key: API ключ
    :param text: текст для анализа
    :return: словарь с результатом анализа эмоций
    """
    url = config["second_url"]
    headers = {
        "apikey": config["second_api_key"]
    }

    try:
        response = requests.post(url, headers=headers, data=text.encode("utf-8"))
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        print(f"Ошибка HTTP: {e}")
        return {}
    