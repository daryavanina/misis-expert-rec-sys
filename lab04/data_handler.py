import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional
from config import get_config
import random

class DataProcessor:
    """
    Загрузка и подготовка MovieLens (u.data, u.item)
    """
    def __init__(self) -> None:
        self.config = get_config()
        self.ratings_df: Optional[pd.DataFrame] = None
        self.user_item_table: Optional[pd.DataFrame] = None
        self.movie_titles: pd.DataFrame = pd.DataFrame(columns=['movie_id', 'title'])
        self.movie_genres: Dict[int, List[str]] = {}

    async def load_data(self) -> None:
        users_path = Path(self.config.get("dataset_users_path"))
        films_path = Path(self.config.get("dataset_films_path"))

        try:
            self.ratings_df = pd.read_csv(
                users_path,
                sep='\t',
                names=['user_id', 'movie_id', 'rating', 'timestamp'],
                dtype={'user_id': int, 'movie_id': int, 'rating': float, 'timestamp': int},
                engine='python'
            )
            print(f"[DATA] Загружено оценок: {len(self.ratings_df)}")
        except Exception as e:
            print(f"[DATA] Ошибка при загрузке {users_path}: {e}")
            self.ratings_df = pd.DataFrame(columns=['user_id', 'movie_id', 'rating', 'timestamp'])
            return

        if films_path.exists():
            try:
                cols = ['movie_id', 'title', 'release_date', 'video_release_date', 'imdb_url']
                df_items = pd.read_csv(
                    films_path,
                    sep='|',
                    encoding='latin-1',
                    header=None,
                    usecols=[0,1,2,3,4],
                    names=cols
                )
                self.movie_titles = df_items[['movie_id', 'title']].copy()
                print(f"[DATA] Загружено названий фильмов: {len(self.movie_titles)}")
            except Exception as e:
                print(f"[DATA] Ошибка загрузки {films_path}: {e}")
                self.movie_titles = pd.DataFrame(columns=['movie_id', 'title'])
        else:
            print(f"[DATA] Файл {films_path} не найден. Названия фильмов не загружены.")

        await self._create_user_item_table()

    async def _create_user_item_table(self) -> None:
        if self.ratings_df is None:
            self.user_item_table = pd.DataFrame()
            return
        self.user_item_table = self.ratings_df.pivot_table(
            index='user_id',
            columns='movie_id',
            values='rating',
            aggfunc='mean'
        ).fillna(0)

    def get_user_ratings(self, user_id: int) -> Dict[int, float]:
        if self.user_item_table is None or user_id not in self.user_item_table.index:
            return {}
        user_ratings = self.user_item_table.loc[user_id]
        return {int(movie_id): float(rating) for movie_id, rating in user_ratings.items() if rating > 0}

    def get_all_users(self) -> List[int]:
        if self.user_item_table is None:
            return []
        return list(self.user_item_table.index.tolist())

    def get_all_movies(self) -> List[int]:
        if self.user_item_table is None:
            return []
        return list(self.user_item_table.columns.tolist())

    def get_movie_title(self, movie_id: int) -> str:
        if not self.movie_titles.empty:
            row = self.movie_titles[self.movie_titles['movie_id'] == movie_id]
            if not row.empty:
                return row['title'].iloc[0]
        return f"Фильм {movie_id}"

    def get_top_popular_movies(self, n: int = 50) -> List[int]:
        if self.ratings_df is None or self.ratings_df.empty:
            return []
        counts = self.ratings_df.groupby('movie_id').size()
        return counts.nlargest(n).index.tolist()

    def get_random_movies(self, n: int = 5) -> List[int]:
        if not self.movie_titles.empty:
            all_movies = self.movie_titles['movie_id'].tolist()
        elif self.ratings_df is not None:
            all_movies = self.ratings_df['movie_id'].unique().tolist()
        else:
            return []
        return random.sample(all_movies, min(n, len(all_movies)))
