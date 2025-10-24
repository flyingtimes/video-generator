#!/usr/bin/env python3
"""
统一的日志管理工具类
提供日志记录和执行时长统计功能
"""

import logging
import time
import os
from pathlib import Path
from functools import wraps
from typing import Optional, Any


class Logger:
    """统一的日志管理类"""

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._setup_logger()
            Logger._initialized = True

    def _setup_logger(self):
        """设置日志配置"""
        # 创建日志目录
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        # 配置日志格式
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # 创建根日志器
        self.logger = logging.getLogger('video_generator')
        self.logger.setLevel(logging.DEBUG)

        # 清除已有的处理器
        self.logger.handlers.clear()

        # 文件处理器 - DEBUG级别
        file_handler = logging.FileHandler(
            log_dir / "debug.log",
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

        # 错误日志文件处理器 - ERROR级别
        error_handler = logging.FileHandler(
            log_dir / "error.log",
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        self.logger.addHandler(error_handler)

        # 控制台处理器 - INFO级别，只显示重要信息
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(levelname)s: %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)

        # 设置第三方库日志级别
        logging.getLogger("requests").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("PIL").setLevel(logging.WARNING)

    def debug(self, message: str, **kwargs):
        """记录DEBUG级别日志"""
        self.logger.debug(message, **kwargs)

    def info(self, message: str, **kwargs):
        """记录INFO级别日志"""
        self.logger.info(message, **kwargs)

    def warning(self, message: str, **kwargs):
        """记录WARNING级别日志"""
        self.logger.warning(message, **kwargs)

    def error(self, message: str, **kwargs):
        """记录ERROR级别日志"""
        self.logger.error(message, **kwargs)

    def critical(self, message: str, **kwargs):
        """记录CRITICAL级别日志"""
        self.logger.critical(message, **kwargs)

    def console_only(self, message: str, level: str = "info"):
        """只在控制台输出消息，不写入文件"""
        if level.lower() == "info":
            print(f"INFO: {message}")
        elif level.lower() == "warning":
            print(f"WARNING: {message}")
        elif level.lower() == "error":
            print(f"ERROR: {message}")
        else:
            print(message)

    def log_execution_time(self, func_name: str, duration: float, additional_info: Optional[str] = None):
        """记录执行时长"""
        info = f"函数 {func_name} 执行时长: {duration:.2f}秒"
        if additional_info:
            info += f" - {additional_info}"
        self.debug(info)

    def log_step_start(self, step_name: str):
        """记录步骤开始"""
        self.info(f"🔄 {step_name}")
        self.debug(f"步骤开始: {step_name}")

    def log_step_end(self, step_name: str, success: bool = True, additional_info: Optional[str] = None):
        """记录步骤结束"""
        status = "✅ 完成" if success else "❌ 失败"
        self.info(f"{status} {step_name}")

        info = f"步骤结束: {step_name} - {status}"
        if additional_info:
            info += f" - {additional_info}"
        self.debug(info)

    def log_file_operation(self, operation: str, file_path: str, success: bool = True, details: Optional[str] = None):
        """记录文件操作"""
        status = "成功" if success else "失败"
        message = f"文件{operation}: {file_path} - {status}"

        if details:
            message += f" - {details}"

        if success:
            self.debug(message)
        else:
            self.error(message)

    def log_api_call(self, api_name: str, method: str, params: dict = None, success: bool = True, response_time: float = None):
        """记录API调用"""
        message = f"API调用 - {api_name}.{method}"

        if params:
            # 隐藏敏感参数
            safe_params = {k: '***' if 'key' in k.lower() or 'token' in k.lower() else v
                          for k, v in params.items()}
            message += f" - 参数: {safe_params}"

        if success:
            message += " - 成功"
        else:
            message += " - 失败"

        if response_time:
            message += f" - 响应时间: {response_time:.2f}秒"

        self.debug(message)

    def log_batch_progress(self, current: int, total: int, item_name: str = "项目"):
        """记录批量处理进度"""
        percentage = (current / total) * 100 if total > 0 else 0
        self.debug(f"批量处理进度: {current}/{total} {item_name} ({percentage:.1f}%)")

        # 每25%在控制台显示一次进度
        if current == 0 or current == total or percentage % 25 < 5:
            self.console_only(f"进度: {current}/{total} ({percentage:.0f}%)", "info")


def execution_time_logger(func_name: Optional[str] = None):
    """装饰器：自动记录函数执行时长"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = Logger()
            start_time = time.time()

            # 使用函数名或自定义名称
            name = func_name or f"{func.__module__}.{func.__name__}"
            logger.debug(f"开始执行: {name}")

            try:
                result = func(*args, **kwargs)
                end_time = time.time()
                duration = end_time - start_time

                # 记录执行时长
                additional_info = None
                if isinstance(result, bool):
                    additional_info = f"执行结果: {'成功' if result else '失败'}"
                elif isinstance(result, (int, float)):
                    additional_info = f"处理数量: {result}"
                elif isinstance(result, list) or isinstance(result, tuple):
                    additional_info = f"处理数量: {len(result)}"

                logger.log_execution_time(name, duration, additional_info)
                logger.debug(f"执行完成: {name}")
                return result

            except Exception as e:
                end_time = time.time()
                duration = end_time - start_time
                logger.log_execution_time(name, duration, f"执行异常: {str(e)}")
                logger.error(f"执行异常: {name} - {str(e)}")
                raise

        return wrapper
    return decorator


def step_logger(step_name: str):
    """装饰器：记录步骤开始和结束"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = Logger()
            logger.log_step_start(step_name)

            try:
                result = func(*args, **kwargs)
                logger.log_step_end(step_name, success=True)
                return result
            except Exception as e:
                logger.log_step_end(step_name, success=False, additional_info=str(e))
                raise

        return wrapper
    return decorator


# 全局日志实例
logger = Logger()


def get_logger() -> Logger:
    """获取日志实例"""
    return Logger()