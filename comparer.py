def compare_emotions_results(nlp_result: dict, tte_result: dict) -> dict:
    """
    Сравнивает результаты двух моделей анализа эмоций, объединяя схожие эмоции.
    Отмечает, если эмоция отсутствует во второй модели.

    :param result1: результат первой модели (список scored_labels)
    :param result2: результат второй модели (словарь эмоций)
    :return: словарь с сопоставлением эмоций и выводом о преобладающей эмоции
    """
    emotions1 = {item["label"].lower(): item["score"] for item in nlp_result.get("scored_labels", [])}
    emotions2 = {emotion.lower(): score for emotion, score in tte_result.items()}

    comparison = {}

    groups = {
        "joy/happy": ["joy", "happy"],
        "anger/angry": ["anger", "angry"],
        "sadness/sad": ["sadness", "sad"],
        "fear": ["fear"],
        "surprise": ["surprise"],
        "love": ["love"]
    }

    for group_name, labels in groups.items():
        nlp_score = sum(emotions1.get(label, 0.0) for label in labels)
        tte_score_values = [emotions2.get(label, None) for label in labels if label in emotions2]
        tte_score = sum(value for value in tte_score_values if value is not None) if tte_score_values else None

        comparison[group_name] = {
            "nlp_model": nlp_score,
            "tte_model": tte_score
        }

    return comparison
