import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QPushButton, QLabel
)
from api_handler import analyze_nlp, analyze_second
from comparer import compare_emotions_results, format_comparison_results, format_model_1_results, format_model_2_results
import random

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Emotion Analyzer")
        self.resize(600, 400)

        layout = QVBoxLayout()

        # Окошко для ввода текста
        self.text_input = QTextEdit()
        self.text_input.setPlaceholderText("Введите текст")
        layout.addWidget(QLabel("Текст для анализа:"))
        layout.addWidget(self.text_input)

        # Кнопки
        button_layout = QHBoxLayout()
        self.btn_model1 = QPushButton("Генерация первой модели")
        self.btn_model2 = QPushButton("Генерация второй модели")
        self.btn_compare = QPushButton("Сравнить модели")

        button_layout.addWidget(self.btn_model1)
        button_layout.addWidget(self.btn_model2)
        button_layout.addWidget(self.btn_compare)

        layout.addLayout(button_layout)

        # Окошко вывода результата
        layout.addWidget(QLabel("Результат:"))
        self.result_output = QTextEdit()
        self.result_output.setReadOnly(True)
        layout.addWidget(self.result_output)

        self.setLayout(layout)

        # Привязка кнопок к функциям
        self.btn_model1.clicked.connect(self.analyze_nlpcloud)
        self.btn_model2.clicked.connect(self.analyze_text_to_emotion)
        self.btn_compare.clicked.connect(self.compare_results)

    def analyze_nlpcloud(self) -> None:
        """
        Функция для анализа текста с помощью NLP Cloud API.
        """
        text = self.text_input.toPlainText().strip()

        if not text:
            self.result_output.setText("Введите текст!")
            return
        
        try:
            self.nlp_result = analyze_nlp(text)
            if self.nlp_result:
                self.result_output.clear()
                self.result_output.append(f"NLP Cloud:\n{format_model_1_results(self.nlp_result)}")
                # if self.second_result:
                #     self.compare_button.setEnabled(True)
        
        except Exception as e:
            self.result_text.append(f"Ошибка: {e}")

        # result = self.mock_sentiment_analysis("Модель 1")
        # self.result_output.setText(f"{result}")

    def analyze_text_to_emotion(self) -> None:
        """
        Функция для анализа текста с помощью Text To Emotions API.
        """
        text = self.text_input.toPlainText().strip()

        if not text:
            self.result_output.setText("Введите текст!")
            return
        
        try:
            self.second_result = analyze_second(text)
            if self.second_result:
                self.result_output.clear()
                self.result_output.append(f"TextToEmotion:\n{format_model_2_results(self.second_result)}")
                # if self.nlp_result:
                #     self.compare_button.setEnabled(True)
        
        except Exception as e:
            self.result_text.append(f"Ошибка: {e}")
        # text = self.text_input.toPlainText().strip()
        # if not text:
        #     self.result_output.setText("Введите текст!")
        #     return

        # result = self.mock_sentiment_analysis("Модель 2")
        # self.result_output.setText(f"{result}")

    def compare_results(self) -> None:
        """
        Функция для сравнения результатов.
        """
        if self.nlp_result and self.second_result:
            self.result_output.clear()
            comparison_data = compare_emotions_results(
                self.nlp_result, self.second_result
            )
            format_results = format_comparison_results(comparison_data)
            self.result_output.append(format_results)
        else:
            self.result_output.setText("Обе модели должны быть выполнены для сравнения.")
        # text = self.text_input.toPlainText()
        # if not text.strip():
        #     self.result_output.setText("Введите текст!")
        #     return

        # result1 = self.mock_sentiment_analysis("Модель 1")
        # result2 = self.mock_sentiment_analysis("Модель 2")

        # compare_text = f"Сравнение моделей:\n\nМодель 1:\n{result1}\n\nМодель 2:\n{result2}"
        # self.result_output.setText(compare_text)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
