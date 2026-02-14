#!/usr/bin/env python3
"""
高熵值时间盐密钥图片生成器
使用 secrets 模块生成完全随机的 RGB 像素，保存在 /keys 目录
"""

import os
import sys
import secrets
import hashlib
import math
import json
from datetime import datetime
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("错误: 需要安装 Pillow 库: pip install Pillow")
    sys.exit(1)


def calculate_entropy(data: bytes) -> float:
    """计算字节数据的香农熵，归一化到 0-1 范围"""
    if not data:
        return 0.0
    freq = {}
    for b in data:
        freq[b] = freq.get(b, 0) + 1
    entropy = 0.0
    total = len(data)
    for cnt in freq.values():
        p = cnt / total
        if p > 0:
            entropy -= p * math.log2(p)
    return entropy / 8.0  # 最大熵为 8 比特/字节


def generate_high_entropy_key(width=256, height=256, name=None, save_meta=True):
    """
    生成高熵值密钥图片
    :param width:  图片宽度（像素）
    :param height: 图片高度（像素）
    :param name:   文件名（不指定则自动生成带时间戳的文件名）
    :param save_meta: 是否保存 .meta.json 元数据文件
    :return: (文件路径, 元数据字典)
    """
    # 确保 keys 目录存在
    keys_dir = Path("keys")
    keys_dir.mkdir(exist_ok=True)

    # 自动生成文件名
    if name is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        name = f"key_high_entropy_{timestamp}.png"
    elif not name.endswith(".png"):
        name += ".png"

    filepath = keys_dir / name

    # 生成完全随机的 RGB 像素数据
    total_pixels = width * height
    random_bytes = secrets.token_bytes(total_pixels * 3)

    # 创建图像
    img = Image.new("RGB", (width, height))
    pixels = img.load()

    idx = 0
    for i in range(width):
        for j in range(height):
            r = random_bytes[idx]
            g = random_bytes[idx + 1]
            b = random_bytes[idx + 2]
            idx += 3
            pixels[i, j] = (r, g, b)

    img.save(filepath)

    # 计算文件哈希与熵值
    with open(filepath, "rb") as f:
        file_data = f.read()

    sha256 = hashlib.sha256(file_data).hexdigest()
    # 取前 64KB 计算熵值（足够评估随机性）
    sample = file_data[:65536] if len(file_data) > 65536 else file_data
    entropy = calculate_entropy(sample)

    # 元数据
    meta = {
        "filename": name,
        "path": str(filepath),
        "created": datetime.now().isoformat(),
        "dimensions": (width, height),
        "pixels": total_pixels,
        "file_size": len(file_data),
        "sha256": sha256,
        "entropy": round(entropy, 6),
        "random_source": "secrets.token_bytes",
    }

    if save_meta:
        meta_path = keys_dir / f"{name}.meta.json"
        with open(meta_path, "w") as f:
            json.dump(meta, f, indent=2)
        print(f"✓ 元数据已保存: {meta_path}")

    print(f"✓ 密钥图片已生成: {filepath}")
    print(f"  尺寸: {width}×{height} | 熵值: {entropy:.4f} (理想 1.0)")
    print(f"  SHA-256: {sha256[:16]}…{sha256[-16:]}")

    return str(filepath), meta


def main():
    print("=" * 60)
    print("      高熵值时间盐密钥图片生成器")
    print("=" * 60)

    # 获取用户输入的尺寸（默认 256×256）
    try:
        w_in = input("请输入图片宽度 (默认 256): ").strip()
        width = int(w_in) if w_in else 256
    except ValueError:
        width = 256

    try:
        h_in = input("请输入图片高度 (默认 256): ").strip()
        height = int(h_in) if h_in else 256
    except ValueError:
        height = 256

    # 可选自定义文件名
    name_in = input("请输入文件名 (留空自动生成): ").strip()
    name = name_in if name_in else None

    print("\n正在生成高熵值密钥图片...")
    try:
        filepath, meta = generate_high_entropy_key(width, height, name)
        print("\n✅ 密钥图片生成成功！")
        print(f"   路径: {filepath}")
        print(f"   熵值: {meta['entropy']}")
        print(f"   SHA-256: {meta['sha256']}")
    except Exception as e:
        print(f"❌ 生成失败: {e}")
        return

    print("\n密钥已保存至 keys/ 目录。可直接用于时间盐加密系统。")


if __name__ == "__main__":
    main()