import math
from typing import Optional, Dict
import pandas as pd


def pearson_item_similarity(item_i: int, item_j: int, ratings_df: pd.DataFrame, min_common: int) -> Optional[float]:
    """
    Вычисление коэффициента корреляции Пирсона между двумя фильмами.

    :param item_i: ID первого фильма
    :param item_j: ID второго фильма
    :param ratings_df: DataFrame с оценками пользователей
    :param min_common: Минимальное количество общих пользователей
    :return: Значение корреляции Пирсона или None если недостаточно данных
    """
    df_i = ratings_df[ratings_df['movie_id'] == item_i][['user_id', 'rating']]
    df_j = ratings_df[ratings_df['movie_id'] == item_j][['user_id', 'rating']]

    if df_i.empty or df_j.empty:
        return None

    merged = pd.merge(df_i, df_j, on='user_id', how='inner', suffixes=('_i', '_j'))

    if len(merged) < min_common:
        return None

    r_i = merged['rating_i'].astype(float)
    r_j = merged['rating_j'].astype(float)
    mean_i = r_i.mean()
    mean_j = r_j.mean()

    num = ((r_i - mean_i) * (r_j - mean_j)).sum()
    den_i = ((r_i - mean_i) ** 2).sum()
    den_j = ((r_j - mean_j) ** 2).sum()

    if den_i <= 0 or den_j <= 0:
        return None

    denom = math.sqrt(den_i) * math.sqrt(den_j)
    if denom == 0:
        return None

    return float(num / denom)

def user_pearson_similarity(user_ratings: Dict[int, float], other_ratings: Dict[int, float], min_common: int) -> Optional[float]:
    """
    Вычисление коэффициента корреляции Пирсона между двумя пользователями.

    :param user_ratings: Оценки первого пользователя
    :param other_ratings: Оценки второго пользователя
    :param min_common: Минимальное количество общих фильмов
    :return: Значение корреляции Пирсона или None если недостаточно данных
    """
    common = set(user_ratings.keys()) & set(other_ratings.keys())
    if len(common) < min_common:
        return None

    u_vals = [float(user_ratings[m]) for m in common]
    v_vals = [float(other_ratings[m]) for m in common]

    n = len(u_vals)
    mean_u = sum(u_vals) / n
    mean_v = sum(v_vals) / n

    num = 0.0
    den_u = 0.0
    den_v = 0.0
    for a, b in zip(u_vals, v_vals):
        ua = a - mean_u
        vb = b - mean_v
        num += ua * vb
        den_u += ua * ua
        den_v += vb * vb

    if den_u <= 0.0 or den_v <= 0.0:
        return None

    denom = math.sqrt(den_u) * math.sqrt(den_v)
    if denom == 0.0:
        return None

    return num / denom
