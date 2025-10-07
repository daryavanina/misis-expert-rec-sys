import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QPushButton, QLabel
)
from api_handler import analyze_nlp, analyze_tte, format_comparison_results, format_nlp_model_results, format_tte_model_results
from comparer import compare_emotions_results

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Emotion Analyzer")
        self.resize(600, 400)

        layout = QVBoxLayout()

        self.text_input = QTextEdit()
        self.text_input.setPlaceholderText("Введите текст")
        layout.addWidget(QLabel("Текст для анализа:"))
        layout.addWidget(self.text_input)

        button_layout = QHBoxLayout()
        self.btn_nlp_model = QPushButton("Генерация модели NLP")
        self.btn_tte_model = QPushButton("Генерация модели TTE")
        self.btn_compare = QPushButton("Сравнить модели")

        button_layout.addWidget(self.btn_nlp_model)
        button_layout.addWidget(self.btn_tte_model)
        button_layout.addWidget(self.btn_compare)

        layout.addLayout(button_layout)

        layout.addWidget(QLabel("Результат:"))
        self.result_output = QTextEdit()
        self.result_output.setReadOnly(True)
        layout.addWidget(self.result_output)

        self.setLayout(layout)

        self.btn_nlp_model.clicked.connect(self.analyze_nlpcloud)
        self.btn_tte_model.clicked.connect(self.analyze_text_to_emotion)
        self.btn_compare.clicked.connect(self.compare_results)

    def analyze_nlpcloud(self) -> None:
        """
        Функция для анализа текста с помощью NLP Cloud API.
        """
        text = self.text_input.toPlainText().strip()

        if not text:
            self.result_output.setText("Введите текст!")
        
        else:
            try:
                self.nlp_result = analyze_nlp(text)
                if self.nlp_result:
                    self.result_output.clear()
                    self.result_output.append(f"NLP Cloud:\n{format_nlp_model_results(self.nlp_result)}")
                    
            
            except Exception as e:
                self.result_text.append(f"Ошибка: {e}")

    def analyze_text_to_emotion(self) -> None:
        """
        Функция для анализа текста с помощью Text To Emotions API.
        """
        text = self.text_input.toPlainText().strip()

        if not text:
            self.result_output.setText("Введите текст!")
        
        else:
            try:
                self.tte_result = analyze_tte(text)
                if self.tte_result:
                    self.result_output.clear()
                    self.result_output.append(f"TextToEmotion:\n{format_tte_model_results(self.tte_result)}")
        
            except Exception as e:
                self.result_output.append(f"Ошибка: {e}")

    def compare_results(self) -> None:
        """
        Функция для сравнения результатов.
        """
        if self.nlp_result and self.tte_result:
            self.result_output.clear()
            comparison_data = compare_emotions_results(
                self.nlp_result, self.tte_result
            )
            format_results = format_comparison_results(comparison_data)
            self.result_output.append(format_results)
        else:
            self.result_output.setText("Обе модели должны быть выполнены для сравнения.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
