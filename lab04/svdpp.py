import numpy as np
import pickle
from typing import Dict, List, Optional
from pathlib import Path

class SVDpp:
    """
    Реализация SVD++ для рекомендательной системы.
    """

    def __init__(self, dp, factors: int, lr: float, reg: float, epochs: int, cache_path: Optional[str]):
        """
        Инициализация модели SVD++

        :param dp: объект DataProcessor для доступа к данным
        :param factors: размерность скрытого латентного пространства
        :param lr: скорость обучения (learning rate)
        :param reg: коэффициент регуляризации
        :param epochs: количество эпох обучения
        :param cache_path: путь для сохранения/загрузки обученной модели
        """
        self.dp = dp
        self.factors = factors
        self.lr = lr
        self.reg = reg
        self.epochs = epochs
        self.cache_path = Path(cache_path) if cache_path else None

        self.global_mean = 0.0
        self.bu: Optional[np.ndarray] = None  # смещения пользователей
        self.bi: Optional[np.ndarray] = None  # смещения объектов
        self.pu: Optional[np.ndarray] = None  # latent-векторы пользователей 
        self.qi: Optional[np.ndarray] = None  # latent-векторы объектов
        self.yj: Optional[np.ndarray] = None  # latent-векторы неявной обратной связи

        self.user_index_map: Dict[int, int] = {}
        self.item_index_map: Dict[int, int] = {}
        self.index_user_map: Dict[int, int] = {}
        self.index_item_map: Dict[int, int] = {}

    def _build_mappings(self):
        """
        Строит отображения между user_id/item_id и их индексами в матрицах модели.
        """
        users = sorted(self.dp.get_all_users())
        items = sorted(self.dp.get_all_movies())
        self.user_index_map = {uid: idx for idx, uid in enumerate(users)}
        self.item_index_map = {mid: idx for idx, mid in enumerate(items)}
        self.index_user_map = {idx: uid for uid, idx in self.user_index_map.items()}
        self.index_item_map = {idx: mid for mid, idx in self.item_index_map.items()}

    def _init_params(self):
        """
        Инициализация параметров модели.
        """
        n_users = len(self.user_index_map)
        n_items = len(self.item_index_map)
        self.global_mean = float(self.dp.ratings_df['rating'].mean()) if self.dp.ratings_df is not None else 3.0
        rng = np.random.RandomState(42)
        self.bu = np.zeros(n_users)
        self.bi = np.zeros(n_items)
        self.pu = rng.normal(scale=0.1, size=(n_users, self.factors))
        self.qi = rng.normal(scale=0.1, size=(n_items, self.factors))
        self.yj = rng.normal(scale=0.1, size=(n_items, self.factors))

    def _get_user_rated_items(self, user_id: int) -> List[int]:
        """
        Возвращает список индексов объектов, оцененных пользователем.
        
        :param user_id: ID пользователя
        :return: список индексов объектов
        """
        if self.dp.user_item_table is None or user_id not in self.dp.user_item_table.index:
            return []
        row = self.dp.user_item_table.loc[user_id]
        rated = [self.item_index_map[int(mid)] for mid, val in row.items() if val > 0 and int(mid) in self.item_index_map]
        return rated

    def train(self) -> None:
        """
        Обучение модели SVD++."""
        print("[SVD++] Старт обучения SVD++")
        self._build_mappings()
        self._init_params()

        ratings = []
        for _, row in self.dp.ratings_df.iterrows():
            u = int(row['user_id'])
            i = int(row['movie_id'])
            r = float(row['rating'])
            if u in self.user_index_map and i in self.item_index_map:
                ratings.append((self.user_index_map[u], self.item_index_map[i], r))

        for epoch in range(self.epochs):
            np.random.shuffle(ratings)
            total_loss = 0.0
            for (u_idx, i_idx, r) in ratings:
                user_id = self.index_user_map[u_idx]
                rated_item_indices = self._get_user_rated_items(user_id)
                sqrt_N = np.sqrt(len(rated_item_indices)) if rated_item_indices else 1.0
                y_sum = np.sum(self.yj[rated_item_indices], axis=0) if rated_item_indices else np.zeros(self.factors)

                pu_hat = self.pu[u_idx] + (y_sum / sqrt_N)

                pred = self.global_mean + self.bu[u_idx] + self.bi[i_idx] + np.dot(self.qi[i_idx], pu_hat)
                err = r - pred
                total_loss += err ** 2

                self.bu[u_idx] += self.lr * (err - self.reg * self.bu[u_idx])
                self.bi[i_idx] += self.lr * (err - self.reg * self.bi[i_idx])

                self.qi[i_idx] += self.lr * (err * pu_hat - self.reg * self.qi[i_idx])
                self.pu[u_idx] += self.lr * (err * self.qi[i_idx] - self.reg * self.pu[u_idx])

                if rated_item_indices:
                    coeff = (err / sqrt_N)
                    for j in rated_item_indices:
                        self.yj[j] += self.lr * (coeff * self.qi[i_idx] - self.reg * self.yj[j])

            rmse = np.sqrt(total_loss / len(ratings))
            print(f"[SVD++] Эпоха {epoch+1}/{self.epochs} RMSE={rmse:.4f}")

        if self.cache_path:
            try:
                Path(self.cache_path).parent.mkdir(parents=True, exist_ok=True)
                with open(self.cache_path, "wb") as f:
                    pickle.dump(self.__dict__, f)
                print(f"[SVD++] Модель сохранена в {self.cache_path}")
            except Exception as e:
                print(f"[SVD++] Не удалось сохранить модель: {e}")

    def predict_single(self, user_ratings: Dict[int, float], item_id: int) -> Optional[float]:
        """
        Предсказывает рейтинг для одного пользователя.
        :param user_ratings: словарь {movie_id: rating} для виртуального пользователя
        :param item_id: ID объекта для предсказания рейтингaа
        :return: предсказанный рейтинг или None, если объект неизвестен
        """
        if item_id not in self.item_index_map:
            return None
        i_idx = self.item_index_map[item_id]

        rated_indices = [self.item_index_map[mid] for mid in user_ratings.keys() if mid in self.item_index_map]
        if rated_indices:
            sqrt_N = np.sqrt(len(rated_indices))
            y_sum = np.sum(self.yj[rated_indices], axis=0) if rated_indices else np.zeros(self.factors)
            pu_new = np.zeros(self.factors)
            for mid, r in user_ratings.items():
                if mid not in self.item_index_map:
                    continue
                j_idx = self.item_index_map[mid]
                est = self.global_mean + self.bi[j_idx]
                pu_new += (r - est) * self.qi[j_idx]
            pu_new = pu_new / (len(rated_indices) + 1e-9)
            pu_hat = pu_new + (y_sum / sqrt_N)
        else:
            pu_hat = np.zeros(self.factors)

        pred = self.global_mean + self.bi[i_idx] + np.dot(self.qi[i_idx], pu_hat)
        pred = max(1.0, min(5.0, pred))
        return float(pred)

    def recommend_for_virtual_user(self, user_ratings: Dict[int, float], n: int = 5) -> List[tuple]:
        """
        Рекомендует объекты для виртуального пользователя на основе его оценок.
        :param user_ratings: словарь {movie_id: rating} для виртуального пользователя
        :param n: количество рекомендаций
        :return: список кортежей (movie_id, predicted_rating)"""
        all_items = self.dp.get_all_movies()
        watched = set(user_ratings.keys())
        candidates = [mid for mid in all_items if mid not in watched]
        preds = []
        for mid in candidates:
            p = self.predict_single(user_ratings, mid)
            if p is not None:
                preds.append((mid, p))
        preds.sort(key=lambda x: x[1], reverse=True)
        return preds[:n]
    
    def load_cache(self) -> bool:
        """
        Загружает модель из кэша, если файл существует.
        :return: True, если модель успешно загружена, иначе False
        """
        if self.cache_path and Path(self.cache_path).is_file():
            try:
                with open(self.cache_path, "rb") as f:
                    data = pickle.load(f)
                    self.__dict__.update(data)
                print(f"[SVD++] Модель загружена из {self.cache_path}")
                return True
            except Exception as e:
                print(f"[SVD++] Не удалось загрузить модель: {e}")
        return False
