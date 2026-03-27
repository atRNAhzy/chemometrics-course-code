"""
电机命令模块：封装电机控制命令的生成和格式化
"""

class MotorCommands:
    """电机控制命令生成器"""
    
    @staticmethod
    def motor_forward(motor_id: int, speed: int) -> str:
        """电机正转命令"""
        return f"f,{motor_id},{speed}"
    
    @staticmethod
    def motor_backward(motor_id: int, speed: int) -> str:
        """电机反转命令"""
        return f"b,{motor_id},{speed}"
    
    @staticmethod
    def motor_stop(motor_id: int) -> str:
        """电机停止命令"""
        return f"f,{motor_id},0"
    
    @staticmethod
    def start_titration(max_speed: int, increment_ms: int) -> str:
        """开始滴定命令"""
        return f"t,{max_speed},{increment_ms}"
    
    @staticmethod
    def emergency_stop() -> str:
        """紧急停止命令"""
        return "s"
    
    @staticmethod
    def format_command_log(command: str) -> str:
        """格式化命令日志显示"""
        try:
            parts = [p.strip() for p in command.split(',')]
            if not parts:
                return command
            
            cmd = parts[0]
            if cmd in ('f', 'b') and len(parts) >= 3:
                motor = parts[1]
                speed = parts[2]
                direction = "正转" if cmd == 'f' else "反转"
                return f"电机{motor} {direction} 速度:{speed}"
            elif cmd == 't' and len(parts) >= 3:
                return f"开始滴定 最大速度:{parts[1]} 间隔:{parts[2]}ms"
            elif cmd == 's':
                return "紧急停止所有电机"
            
            return command
        except Exception:
            return command