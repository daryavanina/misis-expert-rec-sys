import json
import os

def get_config(config_path="C:/progs/recsys/first/lab01/config.json") -> dict:
    """
    Загружает API ключи и URL из config.json.

    :param config_path: путь к файлу конфигурации
    :return: словарь с API ключами и URL
    """
    print(config_path)
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Файл конфигурации не найден: {config_path}")

    with open(config_path, "r", encoding="utf-8") as file:
        config = json.load(file)

    return config

#print(get_config("C:/progs/recsys/first/lab01/config.json"))