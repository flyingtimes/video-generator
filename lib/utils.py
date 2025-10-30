#!/usr/bin/env python3
"""
工具函数模块
提供跨平台兼容的工具函数
"""

import os
from pathlib import Path

def safe_path(*path_parts):
    """跨平台安全的路径拼接"""
    return Path(*path_parts)

def ensure_dir(path):
    """确保目录存在，如果不存在则创建"""
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path

def get_project_root():
    """获取项目根目录"""
    return Path(__file__).parent.parent

def get_input_path(filename):
    """获取input目录下的文件路径"""
    return get_project_root() / "input" / filename

def get_output_path(filename):
    """获取output目录下的文件路径"""
    return get_project_root() / "output" / filename

def get_slides_path(filename):
    """获取slides目录下的文件路径"""
    return get_project_root() / "slides" / filename

def get_assets_path(filename):
    """获取assets目录下的文件路径"""
    return get_project_root() / "assets" / filename

def normalize_path_separators(path_str):
    """标准化路径分隔符，将反斜杠转换为正斜杠以提高跨平台兼容性"""
    return str(path_str).replace('\\', '/')

def ensure_path_exists(path):
    """确保路径（文件或目录）存在，如果是目录则创建"""
    path = Path(path)
    if not path.exists():
        if path.suffix:  # 如果有扩展名，认为是文件
            path.parent.mkdir(parents=True, exist_ok=True)
        else:  # 否则认为是目录
            path.mkdir(parents=True, exist_ok=True)
    return path