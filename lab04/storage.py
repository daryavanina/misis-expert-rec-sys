import json
from pathlib import Path
from typing import Dict, Any

class Storage:
    """
    Хранилище локального пользователя (JSON).
    """
    def __init__(self, path: str):
        self.path = Path(path)
        self._data: Dict[str, Any] = {}
        self._load()

    def _load(self) -> None:
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
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as f:
            json.dump(self._data, f, ensure_ascii=False, indent=2)

    def get_local_user(self) -> Dict:
        return self._data.get("local_user", {"ratings": {}})

    def add_rating(self, movie_id: int, rating: float) -> None:
        self._data.setdefault("local_user", {"ratings": {}})
        self._data["local_user"]["ratings"][str(movie_id)] = float(rating)
        self._save()

    def clear_local_user(self) -> None:
        self._data["local_user"] = {"ratings": {}}
        self._save()
