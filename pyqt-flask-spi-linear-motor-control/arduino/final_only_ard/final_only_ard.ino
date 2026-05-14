#include <Arduino.h>

// 데이터 수신 플래그
volatile bool dataReady = false;
volatile bool stopMotorFlag = false;

int DIR = 6;    // Direction pin
int ENA_P = 4;  // Enable Pin
int ENA_M = 5;  // Enable Pin

int directionCode = 0;
float frequency = 0.0;

void setup() {
  Serial.begin(9600); // 시리얼 통신 초기화

  pinMode(DIR, OUTPUT);
  pinMode(ENA_P, OUTPUT);
  pinMode(ENA_M, OUTPUT);
  pinMode(9, OUTPUT); // OC1A 핀 설정 (PWM 출력)

  digitalWrite(ENA_P, LOW);
  digitalWrite(ENA_M, LOW);
  digitalWrite(DIR, LOW);

  // Timer1 초기화
  stopTimer1(); // 🔥 타이머 정지 함수 호출

  Serial.println("Setup complete.");
}

void loop() {
  // 시리얼 입력 처리
  if (Serial.available() > 0) {    
    String input = Serial.readStringUntil('\n');  // 개행 문자('\n')까지 입력 받음
    input.trim();  // 불필요한 공백 제거

    if (input == "start") {
      moveRight1mm();
      return;
    }

    // 입력을 <주파수> <방향> 형식으로 받음
    int spaceIndex = input.indexOf(' ');
    if (spaceIndex != -1) {
      frequency = input.substring(0, spaceIndex).toFloat();
      directionCode = input.substring(spaceIndex + 1).toInt();

      Serial.print("Received Frequency: ");
      Serial.println(frequency);
      Serial.print("Received Direction: ");
      Serial.println(directionCode);

      if (directionCode < 0 || directionCode > 2) {
        Serial.println("Invalid direction code. Use 0 (stop), 1 (left), 2 (right).");
        return;
      }

      stopMotorFlag = (directionCode == 0);
      dataReady = true;
    } else {
      Serial.println("Invalid input format. Use: <frequency> <direction>");
    }
  }

  // 데이터 수신 시 처리
  if (dataReady) {
    dataReady = false; // 🔥 중복 실행 방지

    if (frequency > 0) {
      if (directionCode == 1) mode("left");
      else if (directionCode == 2) mode("right");
      else if (directionCode == 0) mode("stop");

      if (!stopMotorFlag) {
        if (frequency > 0 && frequency <= 1000) {
          setCTCMode(frequency);
        } else if (frequency > 1000) {
          setFastPWMMode(frequency);
        } else {
          Serial.println("Invalid frequency received.");
        }
      }
    }
  }
}

// ✅ **타이머 완전 정지 함수 추가**
void stopTimer1() {
  TCCR1A = 0; // 타이머 설정 초기화
  TCCR1B = 0;  // 타이머 클럭 정지
  TCNT1 = 0;  // 타이머 카운터 초기화

  Serial.println("Timer1 stopped.");
}

// ✅ **CTC 모드 설정 (1000Hz 이하 주파수 처리)**
void setCTCMode(float frequency) {
  stopTimer1(); // 🔥 타이머를 먼저 정지
  TCCR1A = (1 << COM1A0);  // 9번 핀 토글로 사용
  TCCR1B = (1 << WGM12) | (1 << CS12) | (1 << CS10); // CTC 모드, 분주비 1024
  OCR1A = (16000000 / (1024 * frequency)) - 1;

  Serial.print("OCR1A (Corrected): ");
  Serial.println(OCR1A);
}

// ✅ **Fast PWM 모드 설정 (1000Hz 초과 주파수 처리)**
void setFastPWMMode(float frequency) {
  stopTimer1(); // 🔥 타이머를 먼저 정지
  TCCR1A = 0;
  TCCR1B = 0;
  TCCR1A = (1 << COM1A0);
  TCCR1B = (1 << WGM13) | (1 << WGM12) | (1 << CS10); // Fast PWM 모드, 분주비 1
  ICR1 = (16000000 / frequency) - 1;

  Serial.print("ICR1: ");
  Serial.println(ICR1);
}

// ✅ **모터 제어 함수**
void mode(String s) {  
  if (s == "left") {
    digitalWrite(ENA_P, HIGH);
    digitalWrite(ENA_M, HIGH);
    delayMicroseconds(5);
    digitalWrite(DIR, LOW);
    delayMicroseconds(5);
  } else if (s == "right") {
    digitalWrite(ENA_P, HIGH);
    digitalWrite(ENA_M, HIGH);
    delayMicroseconds(5);
    digitalWrite(DIR, HIGH);
    delayMicroseconds(5);
  } else if (s == "stop") {
    stopMotorFlag = true;
    digitalWrite(ENA_P, LOW);
    digitalWrite(ENA_M, LOW);
  }
}

// ✅ **1mm 이동 함수**
void moveRight1mm() {
  Serial.println("Moving 1mm to the right at 10mm/min...");
  mode("right"); // 오른쪽 방향 설정
  setFastPWMMode(6666.667);
  delay(5800);
  mode("stop");
  stopTimer1();
}