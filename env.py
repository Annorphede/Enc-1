#!/usr/bin/env python3
"""
操作文件夹加密打包工具 - 交互增强版
- 命令行模式（使用子命令 pack/unpack）
- 无参数时自动进入交互菜单
- 打包文件默认保存至 enc_wrapped/ 目录
"""

import os
import sys
import json
import argparse
import getpass
import tarfile
import io
import shutil
from pathlib import Path
from datetime import datetime

try:
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.backends import default_backend
    from cryptography.exceptions import InvalidTag
except ImportError:
    print("错误：请安装 cryptography 库：pip install cryptography")
    sys.exit(1)

# 常量
AES_KEY_SIZE = 32
SALT_SIZE = 16
IV_SIZE = 12
TAG_SIZE = 16
PBKDF2_ITERATIONS = 200000
BACKEND = default_backend()
DEFAULT_WRAP_DIR = Path("enc_wrapped")


def derive_key_from_password(password: bytes, salt: bytes) -> bytes:
    """使用 PBKDF2 从口令派生 AES 密钥"""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=AES_KEY_SIZE,
        salt=salt,
        iterations=PBKDF2_ITERATIONS,
        backend=BACKEND,
    )
    return kdf.derive(password)


def derive_key_from_key_image(image_path: Path, salt: bytes) -> bytes:
    """从密钥图片派生 AES 密钥"""
    from PIL import Image  # 需要 Pillow
    import hashlib

    with open(image_path, 'rb') as f:
        img_data = f.read()

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=AES_KEY_SIZE,
        salt=salt,
        iterations=PBKDF2_ITERATIONS,
        backend=BACKEND,
    )
    return kdf.derive(img_data)


def pack_folder(folder_path: Path, output_file: Path, password: bytes = None, key_image: Path = None):
    """打包并加密文件夹"""
    if not folder_path.is_dir():
        raise ValueError(f"不是有效的文件夹: {folder_path}")

    # 如果输出文件为 None，自动生成默认路径
    if output_file is None:
        DEFAULT_WRAP_DIR.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"{folder_path.name}_{timestamp}.enc"
        output_file = DEFAULT_WRAP_DIR / default_name
        print(f"未指定输出文件，将使用默认路径：{output_file}")

    # 生成随机盐和 IV
    salt = os.urandom(SALT_SIZE)
    iv = os.urandom(IV_SIZE)

    # 派生密钥
    if key_image:
        key = derive_key_from_key_image(key_image, salt)
    elif password:
        key = derive_key_from_password(password, salt)
    else:
        raise ValueError("必须提供口令或密钥图片")

    # 内存中创建 tar 归档
    tar_buffer = io.BytesIO()
    with tarfile.open(fileobj=tar_buffer, mode='w:gz') as tar:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                full_path = Path(root) / file
                arcname = str(full_path.relative_to(folder_path))
                tar.add(str(full_path), arcname=arcname)

    tar_data = tar_buffer.getvalue()

    # 加密
    cipher = Cipher(algorithms.AES(key), modes.GCM(iv), backend=BACKEND)
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(tar_data) + encryptor.finalize()
    tag = encryptor.tag

    # 写入文件
    with open(output_file, 'wb') as f:
        f.write(salt)
        f.write(iv)
        f.write(tag)
        f.write(ciphertext)

    print(f"✅ 打包完成：{output_file}")
    print(f"   原始文件夹：{folder_path}")
    print(f"   加密数据大小：{len(ciphertext)} 字节")
    print(f"   使用 {'密钥图片' if key_image else '口令'} 加密")


def unpack_folder(archive_file: Path, output_dir: Path, password: bytes = None, key_image: Path = None):
    """解密并解包"""
    if not archive_file.is_file():
        raise ValueError(f"文件不存在: {archive_file}")

    with open(archive_file, 'rb') as f:
        salt = f.read(SALT_SIZE)
        iv = f.read(IV_SIZE)
        tag = f.read(TAG_SIZE)
        ciphertext = f.read()

    # 派生密钥
    if key_image:
        key = derive_key_from_key_image(key_image, salt)
    elif password:
        key = derive_key_from_password(password, salt)
    else:
        raise ValueError("必须提供口令或密钥图片")

    # 解密
    cipher = Cipher(algorithms.AES(key), modes.GCM(iv, tag), backend=BACKEND)
    decryptor = cipher.decryptor()
    try:
        tar_data = decryptor.update(ciphertext) + decryptor.finalize()
    except InvalidTag:
        raise ValueError("解密失败：口令/密钥图片错误或数据损坏")

    # 解包
    tar_buffer = io.BytesIO(tar_data)
    with tarfile.open(fileobj=tar_buffer, mode='r:gz') as tar:
        output_dir.mkdir(parents=True, exist_ok=True)
        tar.extractall(path=output_dir)

    print(f"✅ 解包完成：{output_dir}")
    print(f"   还原自：{archive_file}")
    print(f"   使用 {'密钥图片' if key_image else '口令'} 解密")


def interactive_mode():
    """交互式菜单"""
    print("\n" + "=" * 50)
    print("    操作文件夹加密打包工具 - 交互模式")
    print("=" * 50)

    while True:
        print("\n请选择操作：")
        print("  1. 打包文件夹")
        print("  2. 解包文件")
        print("  0. 退出")
        choice = input("请输入数字 (0-2): ").strip()

        if choice == '0':
            print("再见！")
            break

        elif choice == '1':
            # 打包
            folder = input("请输入要打包的文件夹路径: ").strip()
            folder_path = Path(folder).expanduser().resolve()
            if not folder_path.is_dir():
                print("错误：文件夹不存在或不是目录")
                continue

            # 选择认证方式
            auth_type = input("选择认证方式 (1-口令, 2-密钥图片): ").strip()
            password = None
            key_image = None
            if auth_type == '1':
                p1 = getpass.getpass("请输入口令: ").encode('utf-8')
                p2 = getpass.getpass("请确认口令: ").encode('utf-8')
                if p1 != p2:
                    print("错误：两次口令不一致")
                    continue
                password = p1
            elif auth_type == '2':
                img = input("请输入密钥图片路径: ").strip()
                img_path = Path(img).expanduser().resolve()
                if not img_path.is_file():
                    print("错误：密钥图片不存在")
                    continue
                key_image = img_path
            else:
                print("无效选择")
                continue

            # 输出文件（可选）
            out = input("请输入输出加密文件路径 (留空使用默认 enc_wrapped/ 下自动命名): ").strip()
            output_file = Path(out).expanduser().resolve() if out else None

            try:
                pack_folder(folder_path, output_file, password, key_image)
            except Exception as e:
                print(f"打包失败：{e}")

        elif choice == '2':
            # 解包
            archive = input("请输入加密文件路径: ").strip()
            archive_path = Path(archive).expanduser().resolve()
            if not archive_path.is_file():
                print("错误：文件不存在")
                continue

            out_dir = input("请输入解包输出目录: ").strip()
            if not out_dir:
                print("错误：输出目录不能为空")
                continue
            out_path = Path(out_dir).expanduser().resolve()

            # 认证方式
            auth_type = input("选择认证方式 (1-口令, 2-密钥图片): ").strip()
            password = None
            key_image = None
            if auth_type == '1':
                p1 = getpass.getpass("请输入口令: ").encode('utf-8')
                # 注意：解包不需要确认口令
                password = p1
            elif auth_type == '2':
                img = input("请输入密钥图片路径: ").strip()
                img_path = Path(img).expanduser().resolve()
                if not img_path.is_file():
                    print("错误：密钥图片不存在")
                    continue
                key_image = img_path
            else:
                print("无效选择")
                continue

            try:
                unpack_folder(archive_path, out_path, password, key_image)
            except Exception as e:
                print(f"解包失败：{e}")

        else:
            print("无效选择，请重试")


def main():
    # 如果没有命令行参数，则进入交互模式
    if len(sys.argv) == 1:
        interactive_mode()
        return

    # 否则使用命令行参数解析
    parser = argparse.ArgumentParser(description="操作文件夹加密打包工具")
    subparsers = parser.add_subparsers(dest='command', required=True)

    # pack 子命令
    pack_parser = subparsers.add_parser('pack', help='打包文件夹')
    pack_parser.add_argument('folder', type=Path, help='要打包的文件夹路径')
    pack_parser.add_argument('-o', '--output', type=Path, help='输出加密文件路径（默认保存在 enc_wrapped/ 下）')
    pack_parser.add_argument('--password', action='store_true', help='使用口令加密（交互式输入）')
    pack_parser.add_argument('--key-image', type=Path, help='使用密钥图片加密')

    # unpack 子命令
    unpack_parser = subparsers.add_parser('unpack', help='解包文件夹')
    unpack_parser.add_argument('archive', type=Path, help='加密文件路径')
    unpack_parser.add_argument('-o', '--output', type=Path, required=True, help='解包输出目录')
    unpack_parser.add_argument('--password', action='store_true', help='使用口令解密（交互式输入）')
    unpack_parser.add_argument('--key-image', type=Path, help='使用密钥图片解密')

    args = parser.parse_args()

    # 处理口令
    password_bytes = None
    if hasattr(args, 'password') and args.password:
        p1 = getpass.getpass("请输入口令: ").encode('utf-8')
        if args.command == 'pack':
            p2 = getpass.getpass("请确认口令: ").encode('utf-8')
            if p1 != p2:
                print("错误：两次口令不一致")
                sys.exit(1)
        password_bytes = p1

    key_image_path = None
    if hasattr(args, 'key_image') and args.key_image:
        key_image_path = args.key_image
        if not key_image_path.is_file():
            print(f"错误：密钥图片不存在 {key_image_path}")
            sys.exit(1)

    if not password_bytes and not key_image_path:
        print("错误：必须提供 --password 或 --key-image 之一")
        sys.exit(1)

    try:
        if args.command == 'pack':
            pack_folder(args.folder, args.output, password_bytes, key_image_path)
        elif args.command == 'unpack':
            unpack_folder(args.archive, args.output, password_bytes, key_image_path)
    except Exception as e:
        print(f"错误：{e}")
        sys.exit(1)


if __name__ == '__main__':
    main()