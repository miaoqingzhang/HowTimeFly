#!/usr/bin/env python3
"""
配置文件更新脚本
支持通过命令行更新 YAML 配置
"""
import sys
import yaml


def update_config(config_file, key_path, value):
    """
    更新 YAML 配置文件

    Args:
        config_file: 配置文件路径
        key_path: 配置键路径，如 "scanner.paths"
        value: 新值（字符串或多值）
    """
    try:
        # 读取现有配置
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}

        # 解析键路径
        keys = key_path.split('.')
        current = config

        # 导航到目标位置
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        # 设置值
        final_key = keys[-1]

        # 处理布尔值
        if isinstance(value, str) and value.lower() in ('true', 'false'):
            current[final_key] = value.lower() == 'true'
        # 处理列表（多个值）
        elif len(value) > 1:
            current[final_key] = list(value)
        # 处理单个值
        else:
            current[final_key] = value[0]

        # 写回配置文件
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.safe_dump(config, f, allow_unicode=True, default_flow_style=False)

        print(f"  ✓ {key_path} = {current[final_key]}")

    except Exception as e:
        print(f"  ✗ 更新配置失败: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    if len(sys.argv) < 4:
        print("用法: update_config.py <配置文件> <键路径> <值1> [值2 ...]")
        print("示例: update_config.py config.yaml scanner.paths /media/photos /media/videos")
        sys.exit(1)

    config_file = sys.argv[1]
    key_path = sys.argv[2]
    values = sys.argv[3:]

    update_config(config_file, key_path, values)
