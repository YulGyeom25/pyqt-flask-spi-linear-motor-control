import sys
import requests
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, 
    QGraphicsView, QGraphicsScene, QGraphicsEllipseItem
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPen, QFont

SERVER_URL = "http://127.0.0.1:5000"

class MotorControlApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Motor Control")
        self.setGeometry(100, 100, 600, 500)

        self.velocity_label = QLabel("Set Velocity:")
        self.velocity_label.setFont(QFont("Arial", 12))
        
        self.velocity_input = QLineEdit()
        self.velocity_input.setPlaceholderText("Enter velocity")
        self.velocity_input.setFont(QFont("Arial", 12))
        self.velocity_input.textChanged.connect(self.debounce_send_data)
        
        self.velocity_unit_label = QLabel("mm/min")
        self.velocity_unit_label.setFont(QFont("Arial", 12))
        
        velocity_layout = QHBoxLayout()
        velocity_layout.addWidget(self.velocity_label)
        velocity_layout.addWidget(self.velocity_input)
        velocity_layout.addWidget(self.velocity_unit_label)
        
        self.start_button = QPushButton("Start")
        self.start_button.setFont(QFont("Arial", 14))
        self.start_button.setFixedSize(100, 40)
        self.start_button.clicked.connect(self.start_motor)
        
        start_layout = QHBoxLayout()
        start_layout.addStretch()
        start_layout.addWidget(self.start_button)
        start_layout.addStretch()
        
        self.left_button = QPushButton("Left")
        self.stop_button = QPushButton("Stop")
        self.right_button = QPushButton("Right")
        
        for btn in [self.left_button, self.stop_button, self.right_button]:
            btn.setFont(QFont("Arial", 14))
            btn.setFixedSize(100, 40)
        
        self.left_button.clicked.connect(lambda: self.send_data("left"))
        self.stop_button.clicked.connect(lambda: self.send_data("stop"))
        self.right_button.clicked.connect(lambda: self.send_data("right"))
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(self.left_button)
        btn_layout.addWidget(self.stop_button)
        btn_layout.addWidget(self.right_button)
        btn_layout.addStretch()
        
        self.status_label = QLabel("Velocity: 0 mm/min | Direction: Stop")
        self.status_label.setFont(QFont("Arial", 16))
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.graphics_view = QGraphicsView()
        self.scene = QGraphicsScene(self)
        self.graphics_view.setScene(self.scene)
        self.graphics_view.setFixedSize(400, 120)
        
        pen = QPen(Qt.GlobalColor.black)
        self.scene.addLine(50, 50, 350, 50, pen)
        self.position_marker = QGraphicsEllipseItem(50, 45, 10, 10)
        self.position_marker.setBrush(Qt.GlobalColor.black)
        self.scene.addItem(self.position_marker)
        
        label_font = QFont("Arial", 12)
        self.scene.addText("0 mm", label_font).setPos(40, 60)
        self.scene.addText("25 mm", label_font).setPos(190, 60)
        self.scene.addText("50 mm", label_font).setPos(340, 60)
        
        layout = QVBoxLayout()
        layout.addLayout(velocity_layout)
        layout.addLayout(start_layout)
        layout.addLayout(btn_layout)
        layout.addWidget(self.status_label)
        layout.addWidget(self.graphics_view, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.setLayout(layout)
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_position)
        self.timer.start(1000)
        
        self.debounce_timer = QTimer(self)
        self.debounce_timer.setSingleShot(True)
        self.debounce_timer.timeout.connect(self.send_debounced_data)
    
    def update_position(self):
        try:
            response = requests.get(f"{SERVER_URL}/current_position")
            if response.status_code == 200:
                current_position = response.json().get("current_position", 0)
                self.position_marker.setRect(self.calculate_ui_position(current_position), 45, 10, 10)
                self.status_label.setText(f"Current Position: {current_position:.1f} mm")
        except requests.exceptions.RequestException as e:
            print(f"Error connecting to server: {e}")
    
    def calculate_ui_position(self, distance):
        canvas_start, canvas_end = 50, 350
        motor_range = canvas_end - canvas_start
        return canvas_start + (motor_range * (distance / 49))
    
    def debounce_send_data(self):
        self.debounce_timer.start(1000)
    
    def send_debounced_data(self):
        velocity = self.velocity_input.text()
        if velocity and self.is_valid_velocity(velocity):
            self.send_data(None)
    
    def send_data(self, direction=None):
        velocity = self.velocity_input.text()
        if not velocity or not self.is_valid_velocity(velocity):
            return  
        if direction is None:
            direction = self.status_label.text().split("|")[-1].strip().split(":")[-1].strip()
        data = {"velocity": float(velocity), "direction": direction}
        try:
            response = requests.post(f"{SERVER_URL}/submit", json=data)
            if response.status_code == 200:
                self.status_label.setText(f"Velocity: {velocity} mm/min | Direction: {direction.capitalize()}")
        except requests.exceptions.RequestException as e:
            print(f"Error connecting to server: {e}")
    
    def start_motor(self):
        try:
            response = requests.get(f"{SERVER_URL}/start")
            if response.status_code == 200:
                print("Start signal sent")
        except requests.exceptions.RequestException as e:
            print(f"Error connecting to server: {e}")
    
    def is_valid_velocity(self, velocity):
        try:
            velocity = float(velocity)
            return 0.1 <= velocity <= 50.0
        except ValueError:
            return False

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MotorControlApp()
    window.show()
    sys.exit(app.exec())
