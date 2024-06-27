import sys
import random
import time
import requests
import os
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
                             QMessageBox, QInputDialog, QDialog, QScrollArea, QFrame)
from PyQt5.QtGui import QFont, QIcon, QPixmap
from PyQt5.QtCore import Qt, QSize, QTimer
import qtmodern.styles
import qtmodern.windows


class InvalidToken(Exception):
    pass


class BlumAPI:
    def __init__(self, authorization_token) -> None:
        self.headers = {
            'Authorization': authorization_token
        }

    def request(self, request_method, url, payload=None):
        response = getattr(requests, request_method)(url, headers=self.headers, data=payload)
        if response.status_code == 401:
            raise InvalidToken(response.text)
        return response

    def get_me(self):
        response = self.request('get', "https://gateway.blum.codes/v1/user/me")
        if not response.ok:
            raise Exception(f'Проблема при получении имени пользователя!\nТекст ошибки с сервера: {response.text}')
        return response.json()

    def get_balance(self):
        response = self.request('get', "https://game-domain.blum.codes/api/v1/user/balance")
        if not response.ok:
            raise Exception('Проблема при получении баланса!\nТекст ошибки с сервера: {response.text}')
        return response.json()

    def play_game(self):
        response = self.request('post', "https://game-domain.blum.codes/api/v1/game/play")
        if not response.ok:
            raise Exception(f'При попытке сыграть в игру произошла ошибка!\nТекст ошибки с сервера: {response.text}')
        return response.json()

    def claim_reward(self, game_id: str, points: int):
        payload = {
            'gameId': game_id,
            'points': points
        }
        response = self.request('post', "https://game-domain.blum.codes/api/v1/game/claim", payload=payload)
        if not response.ok:
            raise Exception(f'При попытке собрать награду произошла ошибка!\nТекст ошибки с сервера: {response.text}')


class App(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Blum Coin Collector")
        self.setWindowIcon(QIcon("logo.png"))
        self.setFixedSize(500, 250)
        self.setStyleSheet("color: #ff66ff;")
        self.blum_api = None

        self.font = QFont("Roboto", 12)
        self.setFont(self.font)

        self.initUI()

    def resource_path(self, relative_path):
        """ Get absolute path to resource, works for dev and for PyInstaller """
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base_path, relative_path)

    def initUI(self):
        self.main_layout = QVBoxLayout()
        self.main_layout.setAlignment(Qt.AlignCenter)

        self.header_layout = QHBoxLayout()
        self.header_layout.setAlignment(Qt.AlignRight)

        self.help_button = QPushButton()
        self.help_button.setIcon(QIcon(self.resource_path('img/help_icon.png')))
        self.help_button.setIconSize(QSize(32, 32))  # Increase icon size
        self.help_button.setStyleSheet("border: none; background: none;")
        self.help_button.clicked.connect(self.show_help)

        self.header_layout.addWidget(self.help_button)
        self.main_layout.addLayout(self.header_layout)

        self.token_label = QLabel("\nВведите токен авторизации Blum:\n\n")
        self.token_label.setAlignment(Qt.AlignCenter)
        self.token_label.setStyleSheet("color: #ff66ff; font-size: 20px; font-family: 'Roboto'; font-weight: bold;")

        self.token_input = QLineEdit()
        self.token_input.setFixedWidth(400)
        self.token_input.setFixedHeight(40)
        self.token_input.setStyleSheet("font-size: 14px; padding: 10px;")

        self.token_button = QPushButton("Подтвердить")
        self.token_button.setFixedHeight(40)
        self.token_button.setStyleSheet("font-size: 14px;")
        self.token_button.clicked.connect(self.verify_token)

        self.main_layout.addWidget(self.token_label)
        self.main_layout.addWidget(self.token_input)
        self.main_layout.addWidget(self.token_button)

        self.setLayout(self.main_layout)

        if os.path.exists("token.txt"):
            with open("token.txt", "r") as file:
                self.token_input.setText(file.read())

    def show_help(self):
        help_dialog = QDialog(self)
        help_dialog.setWindowTitle("Справка по получению токена\n")
        help_dialog.setFixedSize(500, 700)

        scroll_area = QScrollArea(help_dialog)
        scroll_area.setWidgetResizable(True)
        scroll_area.setGeometry(0, 0, 500, 700)

        help_content = QWidget()
        help_layout = QVBoxLayout(help_content)
        help_layout.setAlignment(Qt.AlignTop)

        help_title = QLabel("Справка по получению токена")
        help_title.setFont(QFont("Roboto", 16, QFont.Bold))
        help_layout.addWidget(help_title)

        steps = [
            ('\nШаг 1: Откройте настройки с телеграма на компьютере \nи перейдите в "Продвинутые настройки" ("Advanced").\n', "img/image1.png"),
            ('\nШаг 2: Найдите в конце списка "Экспериментальные \nнастройки" ("Experimental settings") и перейдите по ним.', "img/image2.png"),
            ('\nШаг 3: Пролистывайте чуть ниже и отключайте \n"Enable webview inspecting".\n', "img/image3.png"),
            ('\nШаг 4: Затем заходите в Blum, нажимайте ПКМ по \nпустой области и выбирайте "Проверить".\n', "img/image4.png"),
            ('\nШаг 5: Сверху выбирайте вкладку "Сеть" ("Network").\n', "img/image5.png"),
            ('\nШаг 6: Далее у вас появятся множество запросовк серверу, \nвам нужно выбрать любой XHR запрос.\n', "img/image6.png"),
            ('\nШаг 7: Справа у вас появится колонка с заголовками, \nлистайте ниже и найдите заголовок "Authorization".\n', "img/image7.png"),
            ('\nШаг 8: Справа от заголовка располагается токен. \nСкопируйте его. Он должен быть такого формата, \nкак на изображении ниже.\n', "img/image8.png"),
        ]

        for text, image_path in steps:
            step_label = QLabel(text)
            step_label.setFont(QFont("Roboto", 12))
            help_layout.addWidget(step_label)

            step_image = QLabel()
            pixmap = QPixmap(self.resource_path(image_path))
            if not pixmap.isNull():
                step_image.setPixmap(pixmap.scaledToWidth(480, Qt.SmoothTransformation))
            else:
                step_image.setText("Изображение не найдено")
                step_image.setAlignment(Qt.AlignCenter)
            help_layout.addWidget(step_image)

        help_text = QLabel("\nИтак, мы искренне надеемся, что у вас все получилось.\nПриятного вам дня и удачной охоты :)!")
        help_text.setFont(QFont("Roboto", 14))
        help_layout.addWidget(help_text)

        help_content.setLayout(help_layout)
        scroll_area.setWidget(help_content)

        help_dialog.exec_()

    def verify_token(self):
        token = self.token_input.text()
        try:
            self.blum_api = BlumAPI(token)
            username = self.blum_api.get_me().get('username')
            with open("token.txt", "w") as file:
                file.write(token)
            self.show_main_menu(username)
        except InvalidToken as e:
            QMessageBox.critical(self, "Ошибка", f"Токен недействителен: {e}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка: {e}")

    def show_main_menu(self, username):
        for widget in [self.token_label, self.token_input, self.token_button]:
            widget.hide()

        self.welcome_label = QLabel(f"\nПривет, {username}!\nВыберите, что желаете сделать:\n\n")
        self.welcome_label.setFont(QFont("Roboto", 20, QFont.Bold))
        self.welcome_label.setAlignment(Qt.AlignCenter)
        self.main_layout.addWidget(self.welcome_label)

        self.choice1_button = QPushButton("Получить поинты за игры")
        self.choice1_button.setFixedHeight(40)
        self.choice1_button.setFixedWidth(400)
        self.choice1_button.setStyleSheet("font-size: 14px;")
        self.choice1_button.clicked.connect(self.choice1)

        self.choice2_button = QPushButton("Получить поинты за игру которая началась")
        self.choice2_button.setFixedHeight(40)
        self.choice2_button.setFixedWidth(400)
        self.choice2_button.setStyleSheet("font-size: 14px;")
        self.choice2_button.clicked.connect(self.choice2)

        self.main_layout.addWidget(self.choice1_button)
        self.main_layout.addWidget(self.choice2_button)

    def choice1(self):
        if not self.blum_api:
            QMessageBox.critical(self, "Ошибка", "Пожалуйста, введите токен!")
            return

        try:
            balance_data = self.blum_api.get_balance()
            available_balance = balance_data.get('availableBalance')
            game_passes = balance_data.get('playPasses')

            games_count, ok = QInputDialog.getInt(self, "Кол-во игр",
                                                  f"Выберите кол-во игр которое хотите сыграть (макс {game_passes}):")
            if ok and 0 < games_count <= game_passes:
                for game_number in range(1, games_count + 1):
                    QMessageBox.information(self, "Игра", f"Игра номер {game_number} началась!")
                    response = self.blum_api.play_game()
                    game_id = response.get('gameId')
                    points = random.randrange(260, 280)
                    self.show_countdown(game_id, points, game_number)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка: {e}")

    def show_countdown(self, game_id, points, game_number):
        countdown_dialog = QDialog(self)
        countdown_dialog.setWindowTitle(f"Игра номер {game_number}")
        countdown_dialog.setFixedSize(300, 200)

        layout = QVBoxLayout()
        countdown_label = QLabel("35 секунд до получения награды")
        countdown_label.setAlignment(Qt.AlignCenter)
        countdown_label.setFont(QFont("Roboto", 16))

        layout.addWidget(countdown_label)
        countdown_dialog.setLayout(layout)

        countdown_dialog.show()

        def update_countdown():
            nonlocal remaining_time
            remaining_time -= 1
            countdown_label.setText(f"{remaining_time} секунд\nдо получения награды")
            if remaining_time == 0:
                countdown_dialog.close()
                self.claim_reward(game_id, points, game_number)

        remaining_time = 35
        timer = QTimer(countdown_dialog)
        timer.timeout.connect(update_countdown)
        timer.start(1000)

    def claim_reward(self, game_id, points, game_number):
        try:
            self.blum_api.claim_reward(game_id, points)
            QMessageBox.information(self, "Результат",
                                    f"Игра номер {game_number} завершена!\nВы получили: {points} поинтов.")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка: {e}")

    def choice2(self):
        game_id, ok = QInputDialog.getText(self, "Ввод", "Введите идентификатор вашей игры:")
        if ok and game_id:
            try:
                points = random.randrange(260, 280)
                self.blum_api.claim_reward(game_id, points)
                QMessageBox.information(self, "Результат", f"Успех! Вы получили {points} поинтов!")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Ошибка: {e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    qtmodern.styles.dark(app)
    main_window = qtmodern.windows.ModernWindow(App())
    main_window.show()
    sys.exit(app.exec_())
