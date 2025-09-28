def compare_emotions_results(result1: dict, result2: dict) -> dict:
    """
    Сравнивает результаты двух моделей анализа эмоций, объединяя схожие эмоции.
    Отмечает, если эмоция отсутствует во второй модели.

    :param result1: результат первой модели (список scored_labels)
    :param result2: результат второй модели (словарь эмоций)
    :return: словарь с сопоставлением эмоций и выводом о преобладающей эмоции
    """
    emotions1 = {item["label"].lower(): item["score"] for item in result1.get("scored_labels", [])}
    emotions2 = {emotion.lower(): score for emotion, score in result2.items()}

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
        score1 = sum(emotions1.get(label, 0.0) for label in labels)
        score2_values = [emotions2.get(label, None) for label in labels if label in emotions2]
        score2 = sum(value for value in score2_values if value is not None) if score2_values else None

        comparison[group_name] = {
            "model1": score1,
            "model2": score2
        }

    return comparison

def format_comparison_results(comparison_data: dict) -> str:
    """
    Форматирует сравнительные результаты в читабельный вид.

    :param comparison_data: словарь с результатами сравнения эмоций
    :return: строка для вывода
    """
    output = "Сравнение эмоций:\n\n"
    header = f"{'Эмоция':<15} | {'Модель 1':<10} | {'Модель 2':<12} | Разница\n"
    output += header
    output += "-" * len(header) + "\n"

    for emotion, scores in comparison_data.items():
        model1_score = scores["model1"]
        model2_score = scores["model2"]

        if model2_score is None:
            model2_display = "Отсутствует"
            diff = "—"
        else:
            model2_display = f"{model2_score:.3f}"
            diff = f"{model1_score - model2_score:+.3f}"

        output += f"{emotion:<15} | {model1_score:<10.3f} | {model2_display:<12} | {diff}\n"

    avg_scores = {emotion: (scores["model1"] + (scores["model2"] or 0)) / 2
                  for emotion, scores in comparison_data.items()}
    dominant_emotion = max(avg_scores, key=avg_scores.get)

    output += f"\nПреобладающая эмоция: {dominant_emotion} (средний балл: {avg_scores[dominant_emotion]:.3f})\n"

    return output

def format_model_1_results(model1_results: dict) -> str:
    lines = []
    for item in model1_results["scored_labels"]:
        lines.append(f"- {item['label']}: {item['score']:.4f}")
    return "\n".join(lines)


def format_model_2_results(model2_results: dict) -> str:
    lines = []
    for label, score in model2_results.items():
        lines.append(f"- {label}: {score:.4f}")
    return "\n".join(lines)
