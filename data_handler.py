import json
import os

def get_api_results(config_path="close/config.json") -> dict:
    """
    Загружает API ключи и URL из config.json.

    :param config_path: путь к файлу конфигурации
    :return: словарь с API ключами и URL
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Файл конфигурации не найден: {config_path}")

    with open(config_path, "r", encoding="utf-8") as file:
        config = json.load(file)

    return config