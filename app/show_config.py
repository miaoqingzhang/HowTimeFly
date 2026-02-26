#!/usr/bin/env python3
"""
显示当前配置的扫描路径
"""
import sys
import yaml


def show_config(config_file):
    """显示扫描相关配置"""
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        scanner = config.get('scanner', {})
        paths = scanner.get('paths', [])
        recursive = scanner.get('recursive', True)

        print(f"  扫描路径:")
        for p in paths:
            print(f"    - {p}")
        print(f"  递归扫描: {recursive}")

    except Exception as e:
        print(f"  读取配置失败: {e}")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法: show_config.py <配置文件>")
        sys.exit(1)

    show_config(sys.argv[1])
