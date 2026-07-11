// =====================================================
// NEMA 17 스텝모터 생존 테스트 (ESP32 + A4988)
// 배선: STEP=GPIO26, DIR=GPIO27
// =====================================================

#define STEP_PIN 26
#define DIR_PIN  27

// 테스트 파라미터
#define STEPS_PER_REV 200    // NEMA 17 기본 (1.8도/스텝)
#define STEP_DELAY_US 2000   // 스텝 간격 (us) — 2000=느리고 안정적

void setup() {
  Serial.begin(115200);
  pinMode(STEP_PIN, OUTPUT);
  pinMode(DIR_PIN, OUTPUT);

  delay(500);
  Serial.println();
  Serial.println("=== NEMA 17 스텝모터 테스트 (ESP32) ===");
  Serial.println("1: 시계방향 1회전");
  Serial.println("2: 반시계방향 1회전");
  Serial.println("3: 왕복 테스트 (2회전씩 x3)");
  Serial.println("4: 저속 10스텝 (코일쌍 확인용)");
  Serial.println("5: 고속 5회전 (성능 테스트)");
  Serial.println("번호 입력 후 Enter");
}

void loop() {
  if (Serial.available()) {
    char cmd = Serial.read();
    if (cmd == '\n' || cmd == '\r') return;

    switch (cmd) {
      case '1':
        Serial.println(">> 시계방향 1회전 (200스텝)");
        runMotor(HIGH, STEPS_PER_REV, STEP_DELAY_US);
        Serial.println(">> 완료!");
        break;

      case '2':
        Serial.println(">> 반시계방향 1회전 (200스텝)");
        runMotor(LOW, STEPS_PER_REV, STEP_DELAY_US);
        Serial.println(">> 완료!");
        break;

      case '3':
        Serial.println(">> 왕복 테스트 시작");
        for (int i = 0; i < 3; i++) {
          Serial.print("  왕복 "); Serial.println(i + 1);
          runMotor(HIGH, STEPS_PER_REV * 2, STEP_DELAY_US);
          delay(500);
          runMotor(LOW, STEPS_PER_REV * 2, STEP_DELAY_US);
          delay(500);
        }
        Serial.println(">> 왕복 완료!");
        break;

      case '4':
        Serial.println(">> 저속 10스텝 (1스텝마다 0.5초 대기)");
        Serial.println("   모터가 한 칸씩 움직이는지 확인하세요");
        digitalWrite(DIR_PIN, HIGH);
        for (int i = 0; i < 10; i++) {
          digitalWrite(STEP_PIN, HIGH);
          delayMicroseconds(10);
          digitalWrite(STEP_PIN, LOW);
          Serial.print("  스텝 "); Serial.println(i + 1);
          delay(500);
        }
        Serial.println(">> 완료!");
        break;

      case '5':
        Serial.println(">> 고속 5회전 (500us 간격)");
        runMotor(HIGH, STEPS_PER_REV * 5, 500);
        Serial.println(">> 완료!");
        break;
    }
  }
}

void runMotor(int dir, int steps, int delayUs) {
  digitalWrite(DIR_PIN, dir);
  for (int i = 0; i < steps; i++) {
    digitalWrite(STEP_PIN, HIGH);
    delayMicroseconds(delayUs);
    digitalWrite(STEP_PIN, LOW);
    delayMicroseconds(delayUs);
  }
}
