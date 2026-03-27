// 引入Wire库，用于I2C通信
#include <Wire.h>
// 引入VL53L1X库，用于控制激光测距模块
#include <VL53L1X.h>
// 创建一个VL53L1X对象，用于与传感器交互
VL53L1X sensor;
// setup函数，Arduino启动时运行一次
void setup()
{
  // 等待串口连接（仅适用于某些Arduino板，如Leonardo）
  while (!Serial) {}
  // 初始化串口通信，波特率为115200
  Serial.begin(115200);
  // 初始化I2C通信
  Wire.begin();
  // 设置I2C时钟频率为400 kHz
  Wire.setClock(400000); // use 400 kHz I2C
  // 设置传感器超时时间为500毫秒
  sensor.setTimeout(500);
  // 初始化传感器，如果初始化失败，输出错误信息并停止程序
  if (!sensor.init())
  {
    Serial.println("Failed to detect and initialize sensor!");
    while (1); // 进入死循环，程序停止
  }
  // 设置传感器为长距离模式
  sensor.setDistanceMode(VL53L1X::Long);
  // 设置测量时间预算为50000微秒（50毫秒）
  sensor.setMeasurementTimingBudget(50000);
  // 开始连续测量，每50毫秒进行一次测量
  sensor.startContinuous(50);
}
// loop函数，Arduino会不断循环执行
void loop()
{
  // 读取传感器的距离测量值，单位为毫米，并通过串口输出
  Serial.print(sensor.read());
  // 检查是否发生超时，如果超时则输出 "TIMEOUT"
  if (sensor.timeoutOccurred()) { Serial.print(" TIMEOUT"); }
  // 换行，准备输出下一个测量值
  Serial.println();
}