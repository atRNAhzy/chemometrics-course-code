// Arduino pH计校准程序（基于能斯特方程）  
// 引脚定义  
#define pH_PIN A0      // pH传感器连接至A0  
#define CALIB_BUTTON 2 // 校准按钮连接至D2（接地触发）  
  
// 全局变量  
float voltage, pH_value;  
bool calibrating = false;  

void setup() {  
  Serial.begin(9600);  
  pinMode(CALIB_BUTTON, INPUT_PULLUP);  
  Serial.println("pH Meter Calibration Program");  
}  
  
void loop() {  
  // 读取并计算pH值  
  readpH();  
  printResults();  
  delay(1000);  
}  
  
// 读取电压并计算pH值  
void readpH() {  
  int raw = analogRead(pH_PIN);  
  voltage = raw * (5.0 / 1024.0);  // 转换为电压（假设5V参考电压）  
  // 使用能斯特方程计算pH值   
  pH_value = (voltage-5.0183)/(-0.16665);        
}  

// 打印结果  
void printResults() {  
  Serial.print("Voltage: ");  
  Serial.print(voltage, 3);  
  Serial.print("V | pH: ");  
  Serial.println(pH_value, 2);  
}