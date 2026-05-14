import sys
import requests
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QMdiSubWindow, QLabel, QWidget, QVBoxLayout
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt, QTimer, QThread
from flask import Flask, jsonify, request
from ui_mainwindow import Ui_MainWindow  # UI 디자인 파일
from project_pyqt import MotorControlApp  # 모터 컨트롤 UI

FLASK_SERVER_URL = "http://127.0.0.1:5000/current_position"

flask_app = Flask(__name__)

class FlaskThread(QThread):
    """Flask 서버를 별도 스레드에서 실행"""
    def run(self):
        flask_app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)

class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.mdi_area = self.ui.mdiArea

        # Flask 서버 실행 (백그라운드)
        self.flask_thread = FlaskThread()
        self.flask_thread.start()

        # 5개의 서브 윈도우 추가
        for i in range(5):
            if i == 3:
                self.add_motor_control_sub_window()
            elif i in [1, 4]:  # 🚀 2번(인덱스 1), 5번(인덱스 4) 창에 이미지 추가
                self.add_image_sub_window(f"영상 창 {i+1}", "test_image.jpg")  
            else:
                self.add_sub_window(f"서브 창 {i+1}")

    def add_sub_window(self, title):
        """일반 서브 윈도우 추가"""
        sub_window = QMdiSubWindow()
        sub_window.setWindowTitle(title)

        label = QLabel(title)
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.addWidget(label)

        sub_window.setWidget(container)
        self.mdi_area.addSubWindow(sub_window)
        sub_window.show()

    def add_motor_control_sub_window(self):
        """세 번째 서브 윈도우에 MotorControlApp 추가"""
        sub_window = QMdiSubWindow()
        sub_window.setWindowTitle("모터 컨트롤")

        motor_control_widget = MotorControlApp()  

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.addWidget(motor_control_widget)

        sub_window.setWidget(container)
        self.mdi_area.addSubWindow(sub_window)
        sub_window.show()

    def add_image_sub_window(self, title, image_path):
        """이미지 표시 서브 윈도우 추가 (2번, 5번 창)"""
        sub_window = QMdiSubWindow()
        sub_window.setWindowTitle(title)

        label = QLabel()
        pixmap = QPixmap(image_path)

        if pixmap.isNull():
            label.setText("이미지를 찾을 수 없습니다.")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        else:
            label.setPixmap(pixmap)
            label.setScaledContents(True)  # 창 크기에 맞게 조정

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.addWidget(label)

        sub_window.setWidget(container)
        self.mdi_area.addSubWindow(sub_window)
        sub_window.show()
            
if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainApp()
    main_window.show()
    sys.exit(app.exec())
