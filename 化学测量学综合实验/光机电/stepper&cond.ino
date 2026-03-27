#include <AccelStepper.h>
#include <Arduino.h>
#include <SoftwareSerial.h>

// ---------------- 电机定义 ----------------
#define STEP_PIN_1 2
#define DIR_PIN_1  5
#define EN_PIN_1   8
#define STEP_PIN_2 3
#define DIR_PIN_2  6
#define EN_PIN_2   9

AccelStepper m1(AccelStepper::DRIVER, STEP_PIN_1, DIR_PIN_1);
AccelStepper m2(AccelStepper::DRIVER, STEP_PIN_2, DIR_PIN_2);

// ---------------- 传感器串口 ----------------
SoftwareSerial BA111(10, 11); // RX, TX
static const float TDS_TO_EC_FACTOR = 0.5f;  // TDS→电导换算系数

// 校验函数
static inline uint8_t checksum5(const uint8_t* p) {
  uint16_t s = 0;
  for (int i = 0; i < 5; i++) s += p[i];
  return (uint8_t)(s & 0xFF);
}

// ---------------- 异步读取 EC 模块 ----------------
float lastEC = 0;                 // 上次成功读数
unsigned long lastECPoll = 0;     // 上次发送时间
uint8_t rxBuf[6];                 // 接收缓冲区
int rxIndex = 0;                  // 当前接收位置

void pollEC() {
  unsigned long now = millis();

  // 每隔 200 ms 发送一次命令
  if (now - lastECPoll >= 200) {
    lastECPoll = now;
    uint8_t tx[6] = {0xA0, 0, 0, 0, 0, 0};
    tx[5] = checksum5(tx);
    while (BA111.available()) BA111.read();  // 清空旧数据
    BA111.write(tx, 6);
    rxIndex = 0;
  }

  // 非阻塞读取响应
  while (BA111.available() && rxIndex < 6) {
    rxBuf[rxIndex++] = BA111.read();
  }

  // 如果收到完整帧 → 校验更新
  if (rxIndex >= 6) {
    if (checksum5(rxBuf) == rxBuf[5] && rxBuf[0] == 0xAA) {
      uint16_t tds_ppm = ((uint16_t)rxBuf[1] << 8) | rxBuf[2];
      lastEC = (float)tds_ppm / TDS_TO_EC_FACTOR;
    }
    rxIndex = 0;
  }
}

// ---------------- 日志缓冲 ----------------
String msgBuffer[16];
volatile int msgHead = 0, msgTail = 0;
void logToBuffer(const String &msg) {
  int next = (msgHead + 1) % 16;
  if (next != msgTail) { msgBuffer[msgHead] = msg; msgHead = next; }
}
void flushLogs() {
  while (msgTail != msgHead) {
    Serial.println(msgBuffer[msgTail]);
    msgTail = (msgTail + 1) % 16;
  }
}

// ---------------- 滴定状态机 ----------------
bool titrating = false;
long tgtMax = 0;
unsigned long stepInterval = 0;
int sp1 = 0, sp2 = 0;
unsigned long lastStepMs = 0;

void startTitration(long max_speed, long inc_ms) {
  tgtMax = (max_speed < 0 ? -max_speed : max_speed);
  stepInterval = (inc_ms <= 0 ? 10 : (unsigned long)inc_ms);
  sp1 = 0;
  sp2 = tgtMax;
  m1.setSpeed(sp1);
  m2.setSpeed(sp2);
  titrating = true;
  lastStepMs = millis();
  logToBuffer("Titration start: max=" + String(tgtMax) + ", inc_ms=" + String(stepInterval));
}

void stopTitration() {
  titrating = false;
  m1.setSpeed(0);
  m2.setSpeed(0);
  logToBuffer("Titration stop");
}


// 每个 loop 调一次：按时间推进速度、持续 runSpeed
void updateTitration() {
  if (!titrating) return;

  unsigned long now = millis();
  if (now - lastStepMs >= stepInterval) {
    lastStepMs = now;

    if (sp1 < (int)tgtMax) sp1++;
    if (sp2 > 0)           sp2--;

    m1.setSpeed(sp1);
    m2.setSpeed(sp2);

    if (sp1 >= (int)tgtMax && sp2 <= 0) {
      stopTitration();
    }
  }
}

// ---------------- 串口命令处理 ----------------
void handleCommand(char *cmd) {
  int motor = 0; long sp = 0;
  long max_sp = 0, inc_ms = 0;

  if (cmd[0] == 'f' && sscanf(cmd, "f,%d,%ld", &motor, &sp) == 2) {
    if (motor == 1) m1.setSpeed(sp);
    else if (motor == 2) m2.setSpeed(sp);
    logToBuffer("OK f");
  }
  else if (cmd[0] == 'b' && sscanf(cmd, "b,%d,%ld", &motor, &sp) == 2) {
    sp = -sp;
    if (motor == 1) m1.setSpeed(sp);
    else if (motor == 2) m2.setSpeed(sp);
    logToBuffer("OK b");
  }
  else if (cmd[0] == 't' && sscanf(cmd, "t,%ld,%ld", &max_sp, &inc_ms) == 2) {
    startTitration(max_sp, inc_ms);
    logToBuffer("OK t");
  }
  else if (cmd[0] == 's') {
    stopTitration();
    logToBuffer("OK s");
  }
  else {
    logToBuffer("ERR");
  }
}

// ---------------- 主流程 ----------------
void setup() {
  Serial.begin(115200);
  BA111.begin(9600);   // 初始化电导模块通信

  m1.setEnablePin(EN_PIN_1);
  m2.setEnablePin(EN_PIN_2);
  m1.setPinsInverted(false, false, true);
  m2.setPinsInverted(false, false, true);
  m1.enableOutputs();
  m2.enableOutputs();

  m1.setMinPulseWidth(2);
  m2.setMinPulseWidth(2);
  m1.setMaxSpeed(10000);
  m2.setMaxSpeed(10000);
  m1.setSpeed(0);
  m2.setSpeed(0);
}

void loop() {
  pollEC();  // 异步轮询电导模块（非阻塞）

  static char cmd[64];
  while (Serial.available()) {
    static size_t idx = 0;
    char c = Serial.read();
    if (c == '\n') { cmd[idx] = '\0'; idx = 0; handleCommand(cmd); }
    else if (c != '\r' && idx < sizeof(cmd) - 1) { cmd[idx++] = c; }
  }

  m1.runSpeed();
  m2.runSpeed();
  updateTitration();

  static unsigned long lastPrint = 0;
  if (millis() - lastPrint >= 500) {
    lastPrint = millis();
    logToBuffer("m1=" + String(m1.speed()) + ", m2=" + String(m2.speed()) + ", c=" + String(lastEC));
  }

  flushLogs();
}
