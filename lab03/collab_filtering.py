from typing import Dict, List, Tuple, Optional
import asyncio
from data_handler import DataProcessor
from similarity import pearson_item_similarity

import pickle
from pathlib import Path


class CollaborativeFiltering:
    """
    Реализация Item-Based Collaborative Filtering с корреляцией Пирсона.
    """

    def __init__(self, data_processor: DataProcessor, min_common_users: int, top_k: int, cache_path: str) -> None:
        """
        Инициализация Collaborative Filtering.

        :param data_processor: Обработчик данных
        :param min_common_users: Минимальное количество общих пользователей, defaults to 3
        :param top_k: Количество ближайших соседей для предсказания, defaults to 20
        """
        self.dp = data_processor
        self.min_common_users = min_common_users
        self.top_k = top_k
        self.sim: Dict[int, Dict[int, float]] = {}
        self._built = False
        self._build_lock = asyncio.Lock()
        self.cache_file = Path(cache_path)

    async def _ensure_built(self) -> None:
        """
        Гарантирует что матрица сходств построена
        """
        if self._built:
            return None
        async with self._build_lock:
            if not self._built:
                if await self._load_from_cache():
                    self._built = True
                    return None
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(None, self.build_item_similarity)
                await self._save_to_cache()
                self._built = True

    async def _load_from_cache(self) -> bool:
        """
        Загружает матрицу сходств из кэша.
        """
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'rb') as f:
                    cached_data = pickle.load(f)
                    if (cached_data.get('min_common_users') == self.min_common_users and
                            cached_data.get('top_k') == self.top_k):
                        self.sim = cached_data['sim']
                        print("Матрица сходства загружена из кэша")
                        return True
            except Exception as e:
                print(f"Ошибка загрузки кэша: {e}")
        return False

    async def _save_to_cache(self) -> None:
        """
        Сохраняет матрицу сходств в кэш.
        """
        try:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            cache_data = {
                'sim': self.sim,
                'min_common_users': self.min_common_users,
                'top_k': self.top_k
            }
            with open(self.cache_file, 'wb') as f:
                pickle.dump(cache_data, f)
            print("Матрица сходства сохранена в кэш")
        except Exception as e:
            print(f"Ошибка сохранения кэша: {e}")

    def build_item_similarity(self) -> None:
        """
        Построение матрицы сходств между фильмами.
        """
        print("Начинаю построение матрицы сходства...")
        ratings_df = self.dp.ratings_df

        movie_ids = ratings_df['movie_id'].unique().tolist()
        n = len(movie_ids)
        sim: Dict[int, Dict[int, float]] = {}

        for i_idx, item_i in enumerate(movie_ids):
            sim[item_i] = {}
            if (i_idx + 1) % 100 == 0:
                print(f"  обработано {i_idx + 1}/{n} фильмов...")

            for item_j in movie_ids[i_idx + 1:]:
                similarity = pearson_item_similarity(
                    item_i, item_j, ratings_df, min_common=self.min_common_users
                )

                if similarity is not None and abs(similarity) > 0.1:
                    sim[item_i][item_j] = similarity
                    if item_j not in sim:
                        sim[item_j] = {}
                    sim[item_j][item_i] = similarity

        self.sim = sim
        print("Матрица сходства построена.")

    def predict_rating(self, user_ratings: Dict[int, float], item_id: int, k: Optional[int] = None) -> Optional[float]:
        """
        Предсказание рейтинга пользователя для заданного фильма.

        :param user_ratings: Оценки пользователя
        :param item_id: ID целевого фильма
        :param k: Количество соседей для учета, defaults to None
        :return: Предсказанный рейтинг или None если предсказание невозможно
        """
        if k is None:
            k = self.top_k

        if not user_ratings:
            return None

        similarities = []
        for rated_movie_id, user_rating in user_ratings.items():
            similarity = self.sim.get(item_id, {}).get(rated_movie_id)
            if similarity is not None and similarity > 0:
                similarities.append((rated_movie_id, similarity, user_rating))

        if not similarities:
            return None

        similarities.sort(key=lambda x: x[1], reverse=True)
        similarities = similarities[:k]

        user_item_table = self.dp.user_item_table
        if user_item_table is None or item_id not in user_item_table.columns:
            return None

        target_ratings = user_item_table[item_id]
        target_mean = target_ratings[target_ratings > 0].mean() if len(
            target_ratings[target_ratings > 0]) > 0 else 3.0

        numerator = 0.0
        denominator = 0.0

        for rated_movie_id, similarity, user_rating in similarities:
            rated_movie_ratings = user_item_table[rated_movie_id]
            rated_movie_mean = rated_movie_ratings[rated_movie_ratings > 0].mean() if len(
                rated_movie_ratings[rated_movie_ratings > 0]) > 0 else 3.0

            adjusted_rating = user_rating - rated_movie_mean

            numerator += similarity * adjusted_rating
            denominator += abs(similarity)

        if denominator == 0:
            return None

        prediction = target_mean + (numerator / denominator)

        prediction = max(1.0, min(5.0, prediction))

        return prediction

    async def generate_recommendations(self, virtual_user_ratings: Dict[int, float], num_recommendations: int = 5) -> List[Tuple[int, float]]:
        """
        Генерация рекомендаций для пользователя.

        :param virtual_user_ratings: Оценки пользователя
        :param num_recommendations: Количество рекомендаций, defaults to 5
        :return: Список кортежей (movie_id, predicted_rating)
        """
        await self._ensure_built()

        # all_movie_ids = self.dp.ratings_df['movie_id'].unique().tolist()
        popular = self.dp.get_top_popular_movies(1000)
        watched = set(virtual_user_ratings.keys())
        candidate_ids = [m for m in popular if m not in watched]
        # watched = set(virtual_user_ratings.keys())
        # candidate_ids = [m for m in all_movie_ids if m not in watched]

        if len(candidate_ids) > 1000:
            candidate_ids = candidate_ids[:1000]

        predicted = []
        for item_id in candidate_ids:
            pred = self.predict_rating(virtual_user_ratings, item_id)
            if pred is not None and pred > 3.0:
                predicted.append((item_id, pred))

        if not predicted:
            watched = set(virtual_user_ratings.keys())
            popular = self.dp.get_top_popular_movies(num_recommendations * 2)
            result = []
            for mid in popular:
                if mid not in watched:
                    result.append((mid, 0.0))
                if len(result) >= num_recommendations:
                    break
            return result
        predicted.sort(key=lambda x: x[1], reverse=True)
        return predicted[:num_recommendations]
