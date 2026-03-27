"""
命令解析模块：解析Arduino串口数据
"""

import re
from typing import Optional, Dict, Any

class CommandParser:
    """串口数据解析器"""
    
    def __init__(self):
        # 主要格式的正则表达式
        self.main_pattern = re.compile(r'm1=([+-]?\d+).*?m2=([+-]?\d+).*?c=([+-]?\d*\.?\d+)')
        
    def parse_arduino_data(self, line: str) -> Optional[Dict[str, Any]]:
        """
        解析Arduino数据行，返回解析结果
        
        Returns:
            Dict包含: {'type': 'data'|'stop'|'unknown', 'motor1': int, 'motor2': int, 'conductivity': float}
            或 None 如果解析失败
        """
        line = line.strip()
        if not line:
            return None
            
        # 检查滴定结束信号
        if 'titration stop' in line.lower():
            return {'type': 'stop'}
            
        # 主要格式: m1=<speed>, m2=<speed>, c=<ec_value>
        if ('m1=' in line) and ('m2=' in line) and ('c=' in line):
            match = self.main_pattern.search(line)
            if match:
                try:
                    motor1 = int(match.group(1))
                    motor2 = int(match.group(2))
                    conductivity = float(match.group(3))
                    return {
                        'type': 'data',
                        'motor1': motor1,
                        'motor2': motor2,
                        'conductivity': conductivity
                    }
                except (ValueError, IndexError):
                    pass
        
        # 兼容旧格式处理
        result = self._parse_legacy_formats(line)
        if result:
            return result
            
        return {'type': 'unknown', 'raw': line}
    
    def _parse_legacy_formats(self, line: str) -> Optional[Dict[str, Any]]:
        """解析兼容的旧格式数据"""
        if ',' not in line:
            return None
            
        parts = [p.strip() for p in line.split(',')]
        
        # 格式1: c,<conductivity>
        if len(parts) >= 2 and parts[0].lower() == 'c':
            try:
                conductivity = float(parts[1])
                return {
                    'type': 'conductivity_only',
                    'conductivity': conductivity
                }
            except ValueError:
                pass
        
        # 格式2: motor1,motor2[,conductivity]
        elif len(parts) >= 2:
            try:
                motor1 = int(parts[0])
                motor2 = int(parts[1])
                result = {
                    'type': 'motors_only',
                    'motor1': motor1,
                    'motor2': motor2
                }
                
                if len(parts) >= 3:
                    try:
                        conductivity = float(parts[2])
                        result['conductivity'] = conductivity
                        result['type'] = 'legacy_data'
                    except ValueError:
                        pass
                        
                return result
            except ValueError:
                pass
                
        return None