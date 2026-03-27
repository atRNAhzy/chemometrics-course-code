#include <AccelStepper.h>
#include <MultiStepper.h>
// ===== 防抖配置 =====
#define LIMIT_SWITCH_PIN 9    // 限位开关引脚
#define DEBOUNCE_DELAY 50     // 防抖时间阈值（毫秒）
#define HALL_SENSOR       11
#define STEP_PIN       2
#define DIR_PIN        5
#define ENABLE_PIN      8
#define COOLDOWN_TIME 5000   // 5秒触发冷却时间

// ===== 全局变量 =====
bool lastStableState = HIGH;  // 默认上拉状态
bool lastRawState = HIGH;
unsigned long lastDebounceTime = 0;
int speed = -5000;
unsigned long startTime = 0; 

// 步进电机状态机
enum MotorState { SPEED_MODE, MOVING_STEPS, STOPPED };
MotorState motorState = SPEED_MODE;

AccelStepper stepper(AccelStepper::DRIVER, STEP_PIN, DIR_PIN);

// ===== 状态变量 =====
bool lastHallState = HIGH;   // 默认上拉状态
unsigned long lastTriggerTime = 0;
unsigned long debounceStartTime = 0;
bool inDebounce = false;

// ===== 霍尔电压触发执行逻辑 =====
void onHallTriggered() {
  Serial.println("↓ 霍尔传感器下降沿触发");
  
  // 停止速度模式，切换到位置模式
  stepper.stop();
  stepper.move(4500);            // 左移4500步
  motorState = MOVING_STEPS;     // 更改状态
  Serial.println("开始左移4500步");
}

// ===== 函数声明 =====
void executeOnLimitTriggered();

// ===== 带防抖的限位检测 =====
bool checkLimitSwitch() {
  bool currentState = digitalRead(LIMIT_SWITCH_PIN);
  
  if (currentState != lastRawState) {
    lastDebounceTime = millis();
    lastRawState = currentState;
  }

  if ((millis() - lastDebounceTime) > DEBOUNCE_DELAY) {
    if (currentState != lastStableState) {
      lastStableState = currentState;
      Serial.print("[DEBUG] 稳定状态更新: ");
      Serial.println(lastStableState);
    }
  }
  return lastStableState;
}

// ===== 带状态检测的防抖函数 =====
void checkLimitWithAction() {
  static bool lastTriggerState = HIGH;
  bool currentState = checkLimitSwitch();
  
  if (lastTriggerState == HIGH && currentState == LOW) {
    executeOnLimitTriggered();
    Serial.println("[动作] 限位触发");
  }
  lastTriggerState = currentState;
}

// ===== 霍尔检测函数 =====
void checkHall() {
  bool currentState = digitalRead(HALL_SENSOR);
  unsigned long now = millis();

  // 检测下降沿（1→0）
  if (lastHallState == HIGH && currentState == LOW) {
    debounceStartTime = now;
    inDebounce = true;
  }

  // 防抖处理
  if (inDebounce && (now - debounceStartTime >= 20)) {
    if (digitalRead(HALL_SENSOR) == LOW) {
      if (now - lastTriggerTime >= COOLDOWN_TIME) {
        onHallTriggered();
        lastTriggerTime = now;
      }
    }
    inDebounce = false;
  }
  lastHallState = currentState;
}

// ===== 限位器触发逻辑 =====
void executeOnLimitTriggered() {
  Serial.println("限位器触发，开始反向");
  speed = 0 - speed;
  stepper.setSpeed(speed);
}

void setup() {
  Serial.begin(115200);
  pinMode(LIMIT_SWITCH_PIN, INPUT_PULLUP);
  pinMode(HALL_SENSOR, INPUT);
  pinMode(ENABLE_PIN, OUTPUT);
  digitalWrite(ENABLE_PIN, LOW);
  startTime = millis();

  // 步进电机参数
  stepper.setMaxSpeed(10000);
  stepper.setAcceleration(1000);
  stepper.setSpeed(speed);
}

void loop() {
  checkLimitWithAction();
  checkHall(); // 启用霍尔检测函数

  // 状态机控制
  switch (motorState) {
    case SPEED_MODE:
      stepper.runSpeed();
      break;
      
    case MOVING_STEPS:
      if (stepper.distanceToGo() != 0) {
        stepper.run();
      } else {
        motorState = STOPPED;
        Serial.println("移动完成，电机停止");
      }
      break;
      
    case STOPPED:
      // 保持停止状态
      break;
  }
}