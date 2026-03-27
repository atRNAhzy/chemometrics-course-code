// 超声波传感器引脚定义
const int trigPin = 7;  // 触发引脚
const int echoPin = 6;  // 回波引脚

// 温度传感器引脚定义
const int tempPin = A0; // 温度传感器模拟输入引脚

// 常量定义
const float R0 = 10000.0; // NTC在25°C时的电阻值（10kΩ）
const float T0 = 298.15;  // 参考温度（25°C，单位为开尔文）
const float B = 3950.0;   // NTC的材料常数
const float VCC = 5.0;    // 电源电压

void setup() {
  Serial.begin(9600);     // 初始化串口通信
  pinMode(trigPin, OUTPUT); // 设置触发引脚为输出模式
  pinMode(echoPin, INPUT);  // 设置回波引脚为输入模式
}

void loop() {
  // 1. 读取温度
  float temperature = readTemperature(); // 获取当前温度
  Serial.print("Temperature: ");
  Serial.print(temperature);
  Serial.println(" °C");

  // 2. 计算当前声速
  float speedOfSound = 331.45 + 0.61 * temperature; // 声速公式
  Serial.print("Speed of Sound: ");
  Serial.print(speedOfSound);
  Serial.println(" m/s");

  // 3. 超声波测距
  float distance = measureDistance(speedOfSound); // 测量距离
  Serial.print("Distance: ");
  Serial.print(distance);
  Serial.println(" cm");

  delay(1000); // 延迟1秒
}

// 读取温度函数
float readTemperature() {
  int sensorValue = analogRead(tempPin); // 读取模拟值
  float Vout = (sensorValue / 1023.0) * VCC; // 计算分压点电压
  float Rt = R0 * Vout/ (VCC - Vout); // 计算NTC电阻值

  // 将电阻值转换为温度（开尔文）
  float T = 1 / (1/T0 + (1/B) * log(Rt/R0));
  float temperature = T - 273.15; // 转换为摄氏度
  return temperature;
}

// 超声波测距函数
float measureDistance(float speedOfSound) {
  // 发送超声波脉冲
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  // 读取回波时间
  long duration = pulseIn(echoPin, HIGH);

  // 计算距离（单位：厘米）
  float distance = (duration * speedOfSound) / 20000.0;
  return distance;
}