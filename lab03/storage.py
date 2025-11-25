import json
from pathlib import Path
from typing import Dict, Any


class Storage:
    """
    Класс для хранения данных локального пользователя в JSON файле.
    """

    def __init__(self, path: str):
        """
        Инициализация хранилища.

        :param path: Путь к JSON файлу
        """
        self.path = Path(path)
        self._data: Dict[str, Any] = {}
        self._load()

    def _load(self) -> None:
        """
        Загрузка данных из файла в память.
        """
        if self.path.exists():
            try:
                with self.path.open("r", encoding="utf-8") as f:
                    self._data = json.load(f)
            except Exception:
                self._data = {}
        else:
            self._data = {}

        if "local_user" not in self._data:
            self._data["local_user"] = {"ratings": {}}
            self._save()

    def _save(self) -> None:
        """
        Сохранение данных из памяти в файл.
        """
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as f:
            json.dump(self._data, f, ensure_ascii=False, indent=2)

    def get_local_user(self) -> Dict:
        """
        Получение данных локального пользователя.

        :return: Словарь с данными пользователя
        """
        return self._data.get("local_user", {"ratings": {}})

    def add_rating(self, movie_id: int, rating: float) -> None:
        """
        Добавление или обновление оценки фильма.

        :param movie_id: ID фильма
        :param rating: Оценка фильма
        """
        self._data.setdefault(
            "local_user", {"ratings": {}})
        self._data["local_user"]["ratings"][str(movie_id)] = float(rating)
        self._save()

    def clear_local_user(self) -> None:
        """
        Очистка всех данных локального пользователя.
        """
        self._data["local_user"] = {"ratings": {}}
        self._save()
