"""
创建测试数据 - 生成简单的测试图片
"""
import os
import time
from datetime import datetime, timedelta
from pathlib import Path

# 尝试导入 PIL，如果没有则提示安装
try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("请先安装 Pillow: pip install pillow")
    exit(1)


def create_test_image(path: str, size: tuple, color: tuple, text: str, date_offset_days: int = 0):
    """创建测试图片

    Args:
        path: 保存路径
        size: 图片尺寸 (width, height)
        color: 背景颜色 (R, G, B)
        text: 图片上的文字
        date_offset_days: 创建时间偏移天数
    """
    # 转换为 Path 对象
    path = Path(path)

    # 创建图片
    img = Image.new('RGB', size, color)
    draw = ImageDraw.Draw(img)

    # 绘制文字
    try:
        # 尝试使用系统字体
        font = ImageFont.truetype("arial.ttf", 40)
    except:
        # 如果没有找到字体，使用默认字体
        font = ImageFont.load_default()

    # 计算文字位置（居中）
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    position = ((size[0] - text_width) // 2, (size[1] - text_height) // 2)

    draw.text(position, text, fill=(255, 255, 255), font=font)

    # 保存图片
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(path))

    # 修改文件时间
    create_time = time.time() - (date_offset_days * 24 * 60 * 60)
    os.utime(str(path), (create_time, create_time))

    print(f"[OK] {path}")


def create_test_video_placeholder(path: str, date_offset_days: int = 0):
    """Create test video placeholder"""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(str(path), 'w') as f:
        f.write("# Test video placeholder\n")
        f.write("# Replace with real .mp4 file\n")

    create_time = time.time() - (date_offset_days * 24 * 60 * 60)
    os.utime(str(path), (create_time, create_time))
    print(f"[OK] {path}")


def main():
    # 测试目录
    test_dir = Path("./test_media")
    test_dir.mkdir(exist_ok=True)

    print(f"在 {test_dir} 目录创建测试数据...\n")

    # 颜色方案
    colors = [
        (239, 71, 111),   # 红色
        (255, 209, 102),  # 黄色
        (6, 214, 160),    # 绿色
        (17, 138, 178),   # 蓝色
        (112, 58, 140),   # 紫色
    ]

    # 创建不同日期的图片（模拟时间线）
    num_days = 30
    photos_per_day = 3

    for day in range(num_days):
        date = datetime.now() - timedelta(days=day)
        date_str = date.strftime("%Y-%m-%d")

        for i in range(photos_per_day):
            filename = f"photo_{date_str}_{i+1:02d}.jpg"
            path = test_dir / "photos" / filename
            color = colors[day % len(colors)]

            create_test_image(
                str(path),
                size=(800, 600),
                color=color,
                text=f"{date_str}\n照片 {i+1}",
                date_offset_days=day
            )

    # 创建一些视频占位符
    for day in [0, 5, 10, 15, 20]:
        date = datetime.now() - timedelta(days=day)
        date_str = date.strftime("%Y-%m-%d")
        filename = f"video_{date_str}.mp4"
        path = test_dir / "videos" / filename

        create_test_video_placeholder(str(path), date_offset_days=day)

    # 创建一些子目录测试递归扫描
    for subdir in ["vacation", "family", "work"]:
        subdir_path = test_dir / subdir
        subdir_path.mkdir(exist_ok=True)

        # 每个子目录放几张照片
        for i in range(2):
            filename = f"{subdir}_{i+1}.jpg"
            path = subdir_path / filename
            create_test_image(
                str(path),
                size=(600, 800),
                color=colors[i % len(colors)],
                text=f"{subdir}\n{i+1}",
                date_offset_days=i * 2
            )

    print(f"\n[OK] Test data created!")
    print(f"  Directory: {test_dir.absolute()}")
    print(f"  Next: python scripts/scan.py")
    print(f"  Then: python run.py")


if __name__ == "__main__":
    main()
