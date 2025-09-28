import requests
import nlpcloud

from config_handler import get_config

config = get_config()

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
    
def analyze_tte(text: str) -> dict:
    """
    Делает POST-запрос к API text to emotions.

    :param url: URL API
    :param api_key: API ключ
    :param text: текст для анализа
    :return: словарь с результатом анализа эмоций
    """
    url = config["tte_url"]
    headers = {
        "apikey": config["tte_api_key"]
    }

    try:
        response = requests.post(url, headers=headers, data=text.encode("utf-8"))
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        print(f"Ошибка HTTP: {e}")
        return {}
    
def format_comparison_results(comparison_data: dict) -> str:
    """
    Форматирует сравнительные результаты к виду:
    Эмоция          | NLP Cloud   | Text To Emotions     | Разница

    :param comparison_data: словарь с результатами сравнения эмоций
    :return: строка для вывода
    """
    output = "Сравнение эмоций:\n\n"
    header = f"{'Эмоция':<15} | {'NLP Cloud':<10} | {'Text To Emotions':<12} | Разница\n"
    output += header
    output += "-" * len(header) + "\n"

    for emotion, scores in comparison_data.items():
        nlp_model_score = scores["nlp_model"]
        tte_model_score = scores["tte_model"]

        if tte_model_score is None:
            tte_model_display = "Отсутствует"
            diff = "—"
        else:
            tte_model_display = f"{tte_model_score:.3f}"
            diff = f"{nlp_model_score - tte_model_score:+.3f}"

        output += f"{emotion:<15} | {nlp_model_score:<10.3f} | {tte_model_display:<12} | {diff}\n"

    avg_scores = {emotion: (scores["nlp_model"] + (scores["tte_model"] or 0)) / 2
                  for emotion, scores in comparison_data.items()}
    dominant_emotion = max(avg_scores, key=avg_scores.get)

    output += f"\nПреобладающая эмоция: {dominant_emotion} (средний балл: {avg_scores[dominant_emotion]:.3f})\n"

    return output

def format_nlp_model_results(nlp_model_results: dict) -> str:
    lines = []
    for item in nlp_model_results["scored_labels"]:
        lines.append(f"- {item['label']}: {item['score']:.4f}")
    return "\n".join(lines)


def format_tte_model_results(tte_model_results: dict) -> str:
    lines = []
    for label, score in tte_model_results.items():
        lines.append(f"- {label}: {score:.4f}")
    return "\n".join(lines)
    