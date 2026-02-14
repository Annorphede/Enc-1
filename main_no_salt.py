"""
图片加密系统 - 完整版
支持密钥图片选择、创建和管理
每次操作结果保存在独立的子文件夹中
"""

import os
import time
import hashlib
import hmac
import struct
import re
import shutil
import json
import random
from datetime import datetime
from PIL import Image

# ==================== 常量定义 ====================

# 文件夹路径
KEY_FOLDER = "keys"  # 密钥图片文件夹
ANS_FOLDER = "ans"   # 结果文件夹
TEST_FOLDER = "test_images"  # 测试图片文件夹

# 默认密钥图片名称
DEFAULT_KEY_IMAGE = "default_key.png"

# ==================== 文件管理函数 ====================

def ensure_folders():
    """确保所有必要的文件夹都存在"""
    os.makedirs(KEY_FOLDER, exist_ok=True)
    os.makedirs(ANS_FOLDER, exist_ok=True)
    os.makedirs(os.path.join(ANS_FOLDER, TEST_FOLDER), exist_ok=True)

def create_operation_folder(mode_name):
    """
    为每次操作创建独立的文件夹
    格式: ans/[模式]/操作_时间戳/
    """
    # 创建模式子目录
    mode_dir = os.path.join(ANS_FOLDER, mode_name)
    os.makedirs(mode_dir, exist_ok=True)
    
    # 创建时间戳子目录
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    operation_name = f"{mode_name}_{timestamp}"
    operation_dir = os.path.join(mode_dir, operation_name)
    os.makedirs(operation_dir, exist_ok=True)
    
    return operation_dir, operation_name

def list_operations(mode_name=None):
    """列出所有操作记录"""
    if not os.path.exists(ANS_FOLDER):
        return []
    
    operations = []
    
    if mode_name:
        # 列出特定模式的操作
        mode_dir = os.path.join(ANS_FOLDER, mode_name)
        if os.path.exists(mode_dir):
            for op in os.listdir(mode_dir):
                if os.path.isdir(os.path.join(mode_dir, op)):
                    operations.append((mode_name, op))
    else:
        # 列出所有模式的操作
        for mode in os.listdir(ANS_FOLDER):
            if mode == TEST_FOLDER:
                continue
            mode_dir = os.path.join(ANS_FOLDER, mode)
            if os.path.isdir(mode_dir):
                for op in os.listdir(mode_dir):
                    if os.path.isdir(os.path.join(mode_dir, op)):
                        operations.append((mode, op))
    
    # 按时间戳排序（最新的在前）
    operations.sort(key=lambda x: x[1], reverse=True)
    return operations

def get_operation_info(operation_path):
    """获取操作文件夹信息"""
    if not os.path.exists(operation_path):
        return None
    
    info = {
        'path': operation_path,
        'files': [],
        'created': time.ctime(os.path.getctime(operation_path)),
        'modified': time.ctime(os.path.getmtime(operation_path)),
        'size': 0
    }
    
    # 获取文件列表
    for root, dirs, files in os.walk(operation_path):
        for file in files:
            file_path = os.path.join(root, file)
            file_size = os.path.getsize(file_path)
            info['files'].append({
                'name': file,
                'size': file_size,
                'path': file_path
            })
            info['size'] += file_size
    
    return info

# ==================== 密钥图片管理 ====================

class KeyManager:
    """密钥图片管理器"""
    
    @staticmethod
    def list_key_images():
        """列出所有密钥图片"""
        ensure_folders()
        
        if not os.path.exists(KEY_FOLDER):
            return []
        
        key_images = []
        for file in os.listdir(KEY_FOLDER):
            if file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
                filepath = os.path.join(KEY_FOLDER, file)
                file_size = os.path.getsize(filepath)
                created = time.ctime(os.path.getctime(filepath))
                modified = time.ctime(os.path.getmtime(filepath))
                
                # 获取图片尺寸
                try:
                    with Image.open(filepath) as img:
                        size = img.size
                except:
                    size = (0, 0)
                
                key_images.append({
                    'name': file,
                    'path': filepath,
                    'size': file_size,
                    'dimensions': size,
                    'created': created,
                    'modified': modified
                })
        
        # 按修改时间排序（最新的在前）
        key_images.sort(key=lambda x: os.path.getmtime(x['path']), reverse=True)
        return key_images
    
    @staticmethod
    def select_key_image():
        """选择密钥图片"""
        key_images = KeyManager.list_key_images()
        
        if not key_images:
            print("密钥文件夹中没有找到密钥图片")
            return None
        
        print("\n可用的密钥图片:")
        print("=" * 60)
        for i, key_info in enumerate(key_images, 1):
            print(f"[{i}] {key_info['name']}")
            print(f"    尺寸: {key_info['dimensions'][0]}x{key_info['dimensions'][1]}")
            print(f"    大小: {key_info['size']:,} bytes")
            print(f"    修改时间: {key_info['modified']}")
            print()
        
        try:
            choice = int(input(f"请选择密钥图片 (1-{len(key_images)}): "))
            if 1 <= choice <= len(key_images):
                return key_images[choice-1]
            else:
                print("无效选择")
                return None
        except ValueError:
            print("请输入有效数字")
            return None
    
    @staticmethod
    def create_random_key_image(name=None, width=100, height=100):
        """创建随机密钥图片"""
        ensure_folders()
        
        if name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            name = f"key_{timestamp}.png"
        
        # 确保文件名以.png结尾
        if not name.lower().endswith('.png'):
            name += '.png'
        
        filepath = os.path.join(KEY_FOLDER, name)
        
        # 创建随机图片
        img = Image.new('RGB', (width, height))
        pixels = img.load()
        
        # 填充随机颜色
        for i in range(width):
            for j in range(height):
                r = random.randint(0, 255)
                g = random.randint(0, 255)
                b = random.randint(0, 255)
                pixels[i, j] = (r, g, b)
        
        img.save(filepath)
        
        print(f"✓ 已创建密钥图片: {name} ({width}x{height})")
        print(f"  保存路径: {filepath}")
        
        return filepath
    
    @staticmethod
    def import_key_image(source_path):
        """导入外部图片作为密钥图片"""
        ensure_folders()
        
        if not os.path.exists(source_path):
            print(f"错误: 文件不存在 - {source_path}")
            return None
        
        # 验证是否为图片文件
        try:
            with Image.open(source_path) as img:
                img.verify()
        except:
            print(f"错误: 不是有效的图片文件 - {source_path}")
            return None
        
        # 获取文件名
        filename = os.path.basename(source_path)
        
        # 如果文件已经在密钥文件夹中，添加时间戳
        dest_path = os.path.join(KEY_FOLDER, filename)
        if os.path.exists(dest_path):
            name, ext = os.path.splitext(filename)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{name}_{timestamp}{ext}"
            dest_path = os.path.join(KEY_FOLDER, filename)
        
        # 复制文件
        shutil.copy2(source_path, dest_path)
        
        print(f"✓ 已导入密钥图片: {filename}")
        print(f"  保存路径: {dest_path}")
        
        return dest_path
    
    @staticmethod
    def create_gradient_key_image(name=None, width=100, height=100):
        """创建渐变密钥图片"""
        ensure_folders()
        
        if name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            name = f"gradient_key_{timestamp}.png"
        
        # 确保文件名以.png结尾
        if not name.lower().endswith('.png'):
            name += '.png'
        
        filepath = os.path.join(KEY_FOLDER, name)
        
        # 创建渐变图片
        img = Image.new('RGB', (width, height))
        pixels = img.load()
        
        # 创建渐变效果
        for i in range(width):
            for j in range(height):
                # 水平渐变（红到绿）和垂直渐变（蓝）
                r = int(255 * i / width) if width > 0 else 0
                g = int(255 * (width - i) / width) if width > 0 else 0
                b = int(255 * j / height) if height > 0 else 0
                pixels[i, j] = (r, g, b)
        
        img.save(filepath)
        
        print(f"✓ 已创建渐变密钥图片: {name} ({width}x{height})")
        print(f"  保存路径: {filepath}")
        
        return filepath
    
    @staticmethod
    def delete_key_image():
        """删除密钥图片"""
        key_images = KeyManager.list_key_images()
        
        if not key_images:
            print("没有可删除的密钥图片")
            return
        
        print("\n选择要删除的密钥图片:")
        for i, key_info in enumerate(key_images, 1):
            print(f"[{i}] {key_info['name']} ({key_info['dimensions'][0]}x{key_info['dimensions'][1]})")
        
        try:
            choice = int(input(f"请选择要删除的图片 (1-{len(key_images)}): "))
            if 1 <= choice <= len(key_images):
                key_info = key_images[choice-1]
                confirm = input(f"确定要删除 '{key_info['name']}' 吗? (y/n): ")
                if confirm.lower() == 'y':
                    try:
                        os.remove(key_info['path'])
                        print(f"✓ 已删除密钥图片: {key_info['name']}")
                    except Exception as e:
                        print(f"✗ 删除失败: {e}")
                else:
                    print("删除操作已取消")
            else:
                print("无效选择")
        except ValueError:
            print("请输入有效数字")
    
    @staticmethod
    def view_key_info():
        """查看密钥图片信息"""
        key_images = KeyManager.list_key_images()
        
        if not key_images:
            print("密钥文件夹中没有密钥图片")
            return
        
        print("\n密钥图片信息:")
        print("=" * 70)
        total_size = 0
        
        for key_info in key_images:
            print(f"文件名: {key_info['name']}")
            print(f"  路径: {key_info['path']}")
            print(f"  尺寸: {key_info['dimensions'][0]}x{key_info['dimensions'][1]}")
            print(f"  大小: {key_info['size']:,} bytes")
            print(f"  创建时间: {key_info['created']}")
            print(f"  修改时间: {key_info['modified']}")
            
            # 计算SHA-256哈希值
            try:
                with open(key_info['path'], 'rb') as f:
                    file_data = f.read()
                    sha256_hash = hashlib.sha256(file_data).hexdigest()
                    print(f"  SHA-256: {sha256_hash[:16]}...{sha256_hash[-16:]}")
            except:
                print(f"  SHA-256: 无法计算")
            
            print()
            total_size += key_info['size']
        
        print(f"总计: {len(key_images)} 个密钥图片, {total_size:,} bytes")
    
    @staticmethod
    def create_default_key_image():
        """创建默认密钥图片（如果不存在）"""
        ensure_folders()
        
        default_path = os.path.join(KEY_FOLDER, DEFAULT_KEY_IMAGE)
        
        if not os.path.exists(default_path):
            print("创建默认密钥图片...")
            KeyManager.create_random_key_image(DEFAULT_KEY_IMAGE, 128, 128)
            return default_path
        
        return default_path

# ==================== 通用工具函数 ====================

def preprocess_string(text, lowercase=True):
    """预处理字符串：只保留英文字母"""
    text = re.sub(r'[^a-zA-Z]', '', text)
    if lowercase:
        text = text.lower()
    return text

def pad_string_to_multiple(text, multiple=9, pad_char='x'):
    """将字符串补齐到指定倍数长度"""
    length = len(text)
    if length % multiple != 0:
        pad_length = multiple - (length % multiple)
        text += pad_char * pad_length
    return text

def letter_to_number(letter):
    """将字母转换为数字（a=1, b=2, ..., z=26）"""
    if 'a' <= letter <= 'z':
        return ord(letter) - ord('a') + 1
    elif 'A' <= letter <= 'Z':
        return ord(letter) - ord('A') + 1
    return 0

def number_to_letter(number):
    """将数字转换为字母（1=a, 2=b, ..., 26=z）"""
    if 1 <= number <= 26:
        return chr(number + ord('a') - 1)
    return 'x'

def select_carrier_image():
    """选择载体图片"""
    print("\n选择载体图片:")
    print("1. 使用默认黑色背景")
    print("2. 从文件选择")
    print("3. 创建测试图片")
    
    choice = input("请选择 (1-3): ").strip()
    
    if choice == '1':
        return None
    elif choice == '2':
        path = input("请输入图片路径: ").strip()
        if os.path.exists(path):
            return path
        else:
            print("文件不存在，将使用默认黑色背景")
            return None
    elif choice == '3':
        return create_test_image()
    else:
        print("无效选择，将使用默认黑色背景")
        return None

def create_test_image(width=200, height=200, save=True):
    """创建测试图片"""
    img = Image.new('RGB', (width, height))
    pixels = img.load()
    
    # 创建测试图案
    for i in range(width):
        for j in range(height):
            # 创建棋盘格效果
            if (i // 20 + j // 20) % 2 == 0:
                r = (i * 255) // width
                g = (j * 255) // height
                b = 128
            else:
                r = 128
                g = (i * 255) // width
                b = (j * 255) // height
            pixels[i, j] = (r, g, b)
    
    if save:
        test_dir = os.path.join(ANS_FOLDER, TEST_FOLDER)
        os.makedirs(test_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"test_carrier_{timestamp}.png"
        filepath = os.path.join(test_dir, filename)
        img.save(filepath)
        print(f"✓ 已创建测试图片: {filename}")
        return filepath
    
    return img

# ==================== 模式1：原始编码模式 ====================

class OriginalEncoder:
    """原始编码模式（无密钥）"""
    
    @staticmethod
    def encode_group(group):
        """对一组9个字符进行原始编码"""
        if len(group) != 9:
            raise ValueError(f"Group length must be 9, got {len(group)}")
        
        numbers = [letter_to_number(c) for c in group]
        encoded_values = []
        
        for i in range(8, -1, -1):
            temp_numbers = numbers[:i] + numbers[i+1:]
            sum_value = sum(temp_numbers)
            encoded_values.append(sum_value)
        
        return encoded_values
    
    @staticmethod
    def decode_group(encoded_values):
        """对一组9个编码值进行原始解码"""
        if len(encoded_values) != 9:
            raise ValueError(f"Expected 9 encoded values, got {len(encoded_values)}")
        
        total_sum = sum(encoded_values)
        sum_of_all_letters = total_sum / 8
        
        letters = []
        for i in range(9):
            letter_number = round(sum_of_all_letters - encoded_values[8-i])
            letter = number_to_letter(letter_number)
            letters.append(letter)
        
        return ''.join(letters)
    
    @staticmethod
    def encode(text, carrier_image_path=None, operation_dir=None):
        """原始编码"""
        # 创建操作文件夹
        if operation_dir is None:
            operation_dir, operation_name = create_operation_folder("original_encode")
        
        # 预处理
        processed = preprocess_string(text)
        padded = pad_string_to_multiple(processed, 9, 'x')
        
        # 分组
        groups = [padded[i:i+9] for i in range(0, len(padded), 9)]
        
        # 编码每组
        encoded_groups = []
        for group in groups:
            encoded_values = OriginalEncoder.encode_group(group)
            encoded_groups.append(encoded_values)
        
        # 创建图片
        rows = (len(groups) + 2) // 3
        img_width = 9
        
        if carrier_image_path and os.path.exists(carrier_image_path):
            img = Image.open(carrier_image_path)
            if img.size[0] < img_width or img.size[1] < rows:
                img = img.resize((max(img_width, img.size[0]), max(rows, img.size[1])))
        else:
            img = Image.new('RGB', (img_width, rows), color='black')
        
        pixels = img.load()
        
        for group_idx in range(len(groups)):
            row = group_idx // 3
            channel = group_idx % 3
            
            encoded_values = encoded_groups[group_idx]
            
            for col in range(9):
                if col < img_width:
                    value = encoded_values[col]
                    value = min(255, max(0, value))
                    
                    current_rgb = pixels[col, row] if row < img.size[1] else (0, 0, 0)
                    
                    if channel == 0:
                        new_rgb = (value, current_rgb[1], current_rgb[2])
                    elif channel == 1:
                        new_rgb = (current_rgb[0], value, current_rgb[2])
                    else:
                        new_rgb = (current_rgb[0], current_rgb[1], value)
                    
                    if col < img.size[0] and row < img.size[1]:
                        pixels[col, row] = new_rgb
        
        # 保存文件
        output_path = os.path.join(operation_dir, "encoded.png")
        img.save(output_path)
        
        # 保存输入文本
        input_text_path = os.path.join(operation_dir, "input.txt")
        with open(input_text_path, 'w', encoding='utf-8') as f:
            f.write(text)
        
        # 保存处理后的文本
        processed_path = os.path.join(operation_dir, "processed.txt")
        with open(processed_path, 'w', encoding='utf-8') as f:
            f.write(padded)
        
        # 保存元数据
        metadata = {
            'mode': 'original_encode',
            'original_text': text,
            'original_length': len(processed),
            'padded_text': padded,
            'padded_length': len(padded),
            'num_groups': len(groups),
            'carrier_image': carrier_image_path,
            'output_image': output_path,
            'image_size': img.size,
            'timestamp': datetime.now().isoformat()
        }
        
        metadata_path = os.path.join(operation_dir, "metadata.json")
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        # 创建操作报告
        report_path = os.path.join(operation_dir, "report.txt")
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(f"原始编码操作报告\n")
            f.write(f"==================\n\n")
            f.write(f"操作时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"原始文本: {text}\n")
            f.write(f"原始长度: {len(text)} 字符\n")
            f.write(f"处理后文本: {padded}\n")
            f.write(f"处理后长度: {len(padded)} 字符\n")
            f.write(f"分组数: {len(groups)}\n")
            if carrier_image_path:
                f.write(f"载体图片: {carrier_image_path}\n")
            f.write(f"输出文件: {output_path}\n")
            f.write(f"图片尺寸: {img.size[0]}x{img.size[1]} 像素\n")
        
        return operation_dir, metadata
    
    @staticmethod
    def decode(image_path, original_length=None, operation_dir=None):
        """原始解码"""
        # 创建操作文件夹
        if operation_dir is None:
            operation_dir, operation_name = create_operation_folder("original_decode")
        
        # 复制源图片到操作文件夹
        img_filename = os.path.basename(image_path)
        img_copy_path = os.path.join(operation_dir, img_filename)
        shutil.copy2(image_path, img_copy_path)
        
        img = Image.open(img_copy_path)
        width, height = img.size
        pixels = img.load()
        
        # 计算最大组数
        max_groups = height * 3
        
        # 提取所有组
        groups = []
        for group_idx in range(max_groups):
            row = group_idx // 3
            channel = group_idx % 3
            
            if row >= height:
                break
                
            encoded_values = []
            for col in range(9):
                if col < width:
                    rgb = pixels[col, row]
                    if channel == 0:
                        value = rgb[0]
                    elif channel == 1:
                        value = rgb[1]
                    else:
                        value = rgb[2]
                else:
                    value = 0
                encoded_values.append(value)
            
            # 检查这组是否有数据
            if any(value > 0 for value in encoded_values):
                groups.append(encoded_values)
            else:
                break
        
        # 解码每组
        decoded_groups = []
        for i, encoded_values in enumerate(groups):
            try:
                decoded_group = OriginalEncoder.decode_group(encoded_values)
                decoded_groups.append(decoded_group)
            except Exception as e:
                print(f"第{i+1}组解码失败: {e}")
                break
        
        # 组合结果
        decoded_text = ''.join(decoded_groups)
        
        # 移除填充
        if original_length is not None and original_length <= len(decoded_text):
            final_text = decoded_text[:original_length]
            removed_padding = decoded_text[original_length:]
        else:
            # 自动移除末尾的x
            original_length = len(decoded_text.rstrip('x'))
            final_text = decoded_text[:original_length]
            removed_padding = decoded_text[original_length:]
        
        # 保存结果
        output_path = os.path.join(operation_dir, "decoded.txt")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(final_text)
        
        # 保存完整解码结果
        full_output_path = os.path.join(operation_dir, "decoded_full.txt")
        with open(full_output_path, 'w', encoding='utf-8') as f:
            f.write(decoded_text)
        
        # 保存元数据
        metadata = {
            'mode': 'original_decode',
            'source_image': img_copy_path,
            'original_length_input': original_length,
            'decoded_full': decoded_text,
            'decoded_final': final_text,
            'removed_padding': removed_padding,
            'num_groups': len(groups),
            'output_text': output_path,
            'timestamp': datetime.now().isoformat()
        }
        
        metadata_path = os.path.join(operation_dir, "metadata.json")
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        # 创建操作报告
        report_path = os.path.join(operation_dir, "report.txt")
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(f"原始解码操作报告\n")
            f.write(f"==================\n\n")
            f.write(f"操作时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"源图片: {image_path}\n")
            f.write(f"图片尺寸: {img.size[0]}x{img.size[1]} 像素\n")
            f.write(f"检测到组数: {len(groups)}\n")
            f.write(f"完整解码文本: {decoded_text}\n")
            f.write(f"最终文本 (移除填充): {final_text}\n")
            f.write(f"移除的填充: {removed_padding}\n")
            f.write(f"输出文件: {output_path}\n")
        
        return operation_dir, final_text

# ==================== 模式2：增强加密模式 ====================

class EnhancedEncoder:
    """增强加密模式（图片密钥）"""
    
    @staticmethod
    def extract_image_data(image_path):
        """从图片中提取字节数据"""
        img = Image.open(image_path)
        img_bytes = bytearray()
        
        pixels = list(img.getdata())
        for pixel in pixels:
            if len(pixel) >= 3:
                img_bytes.extend(pixel[:3])
        
        return bytes(img_bytes)
    
    @staticmethod
    def generate_key_stream(seed, length):
        """生成密钥流"""
        key_stream = []
        counter = 0
        
        while len(key_stream) < length:
            h = hmac.new(seed, struct.pack('>I', counter), hashlib.sha256)
            key_stream.extend(bytearray(h.digest()))
            counter += 1
        
        return key_stream[:length]
    
    @staticmethod
    def encode(text, key_image_path, carrier_image_path=None, operation_dir=None):
        """增强加密"""
        # 创建操作文件夹
        if operation_dir is None:
            operation_dir, operation_name = create_operation_folder("enhanced_encode")
        
        # 检查密钥图片
        if not os.path.exists(key_image_path):
            raise FileNotFoundError(f"密钥图片不存在: {key_image_path}")
        
        # 复制密钥图片到操作文件夹
        key_img_filename = os.path.basename(key_image_path)
        key_img_copy_path = os.path.join(operation_dir, key_img_filename)
        shutil.copy2(key_image_path, key_img_copy_path)
        
        # 如果有载体图片，也复制
        carrier_copy_path = None
        if carrier_image_path and os.path.exists(carrier_image_path):
            carrier_filename = os.path.basename(carrier_image_path)
            carrier_copy_path = os.path.join(operation_dir, carrier_filename)
            shutil.copy2(carrier_image_path, carrier_copy_path)
        
        # 预处理
        processed = preprocess_string(text)
        padded = pad_string_to_multiple(processed, 9, 'x')
        
        # 转换为数字 (a=0, b=1, ..., z=25)
        numbers = [ord(c) - ord('a') for c in padded]
        
        # 从密钥图片生成密钥流
        key_data = EnhancedEncoder.extract_image_data(key_img_copy_path)
        seed = hashlib.sha256(key_data).digest()
        key_stream = EnhancedEncoder.generate_key_stream(seed, len(numbers))
        
        # 加密 (异或运算)
        cipher_numbers = []
        for i in range(len(numbers)):
            encrypted = numbers[i] ^ (key_stream[i] % 26)
            cipher_numbers.append(encrypted)
        
        # 分组
        num_groups = len(padded) // 9
        groups = [cipher_numbers[i*9:(i+1)*9] for i in range(num_groups)]
        
        # 创建图片
        rows = (num_groups + 2) // 3
        
        if carrier_copy_path and os.path.exists(carrier_copy_path):
            img = Image.open(carrier_copy_path)
            if img.size[0] < 9 or img.size[1] < rows:
                img = img.resize((max(9, img.size[0]), max(rows, img.size[1])))
        else:
            img = Image.new('RGB', (9, rows), color='black')
        
        pixels = img.load()
        
        # 存入图片
        for group_idx in range(num_groups):
            row = group_idx // 3
            channel = group_idx % 3
            group_values = groups[group_idx]
            
            for col in range(9):
                value = min(255, max(0, group_values[col]))
                current = pixels[col, row]
                
                if channel == 0:
                    pixels[col, row] = (value, current[1], current[2])
                elif channel == 1:
                    pixels[col, row] = (current[0], value, current[2])
                else:
                    pixels[col, row] = (current[0], current[1], value)
        
        # 保存加密图片
        output_path = os.path.join(operation_dir, "encoded.png")
        img.save(output_path)
        
        # 保存输入文本
        input_text_path = os.path.join(operation_dir, "input.txt")
        with open(input_text_path, 'w', encoding='utf-8') as f:
            f.write(text)
        
        # 保存处理后的文本
        processed_path = os.path.join(operation_dir, "processed.txt")
        with open(processed_path, 'w', encoding='utf-8') as f:
            f.write(padded)
        
        # 保存密钥流信息
        key_stream_path = os.path.join(operation_dir, "key_stream.txt")
        with open(key_stream_path, 'w', encoding='utf-8') as f:
            f.write(f"密钥流长度: {len(key_stream)}\n")
            f.write(f"前10个值: {key_stream[:10]}\n")
            f.write(f"SHA-256种子: {seed.hex()}\n")
        
        # 保存元数据
        metadata = {
            'mode': 'enhanced_encode',
            'original_text': text,
            'original_length': len(processed),
            'padded_text': padded,
            'padded_length': len(padded),
            'num_groups': num_groups,
            'key_image': key_img_copy_path,
            'key_image_name': key_img_filename,
            'key_image_sha256': hashlib.sha256(key_data).hexdigest(),
            'carrier_image': carrier_copy_path,
            'output_image': output_path,
            'image_size': img.size,
            'key_stream_seed': seed.hex(),
            'timestamp': datetime.now().isoformat()
        }
        
        metadata_path = os.path.join(operation_dir, "metadata.json")
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        # 创建操作报告
        report_path = os.path.join(operation_dir, "report.txt")
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(f"增强加密操作报告\n")
            f.write(f"==================\n\n")
            f.write(f"操作时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"原始文本: {text}\n")
            f.write(f"原始长度: {len(text)} 字符\n")
            f.write(f"处理后文本: {padded}\n")
            f.write(f"处理后长度: {len(padded)} 字符\n")
            f.write(f"分组数: {num_groups}\n")
            f.write(f"密钥图片: {key_img_filename}\n")
            f.write(f"密钥SHA-256: {hashlib.sha256(key_data).hexdigest()}\n")
            if carrier_copy_path:
                f.write(f"载体图片: {carrier_filename}\n")
            f.write(f"输出文件: {output_path}\n")
            f.write(f"图片尺寸: {img.size[0]}x{img.size[1]} 像素\n")
            f.write(f"SHA-256种子: {seed.hex()}\n")
        
        return operation_dir, metadata
    
    @staticmethod
    def decode(image_path, key_image_path, original_length=None, num_groups=None, operation_dir=None):
        """增强解密"""
        # 创建操作文件夹
        if operation_dir is None:
            operation_dir, operation_name = create_operation_folder("enhanced_decode")
        
        if not os.path.exists(key_image_path):
            raise FileNotFoundError(f"密钥图片不存在: {key_image_path}")
        
        # 复制源图片到操作文件夹
        img_filename = os.path.basename(image_path)
        img_copy_path = os.path.join(operation_dir, img_filename)
        shutil.copy2(image_path, img_copy_path)
        
        # 复制密钥图片到操作文件夹
        key_img_filename = os.path.basename(key_image_path)
        key_img_copy_path = os.path.join(operation_dir, key_img_filename)
        shutil.copy2(key_image_path, key_img_copy_path)
        
        img = Image.open(img_copy_path)
        width, height = img.size
        pixels = img.load()
        
        # 计算最大组数
        max_groups = height * 3
        
        # 确定要提取的组数
        if num_groups is None:
            # 尝试自动检测
            num_groups = 0
            for i in range(max_groups):
                row = i // 3
                if row >= height:
                    break
                # 检查该组是否有数据
                has_data = False
                for col in range(min(9, width)):
                    rgb = pixels[col, row]
                    if rgb[0] > 0 or rgb[1] > 0 or rgb[2] > 0:
                        has_data = True
                        break
                if has_data:
                    num_groups += 1
                else:
                    break
        
        # 提取加密数据
        cipher_numbers = []
        for group_idx in range(num_groups):
            row = group_idx // 3
            channel = group_idx % 3
            
            for col in range(9):
                if col < width and row < height:
                    rgb = pixels[col, row]
                    if channel == 0:
                        value = rgb[0]
                    elif channel == 1:
                        value = rgb[1]
                    else:
                        value = rgb[2]
                else:
                    value = 0
                cipher_numbers.append(value)
        
        # 从密钥图片生成密钥流
        key_data = EnhancedEncoder.extract_image_data(key_img_copy_path)
        seed = hashlib.sha256(key_data).digest()
        key_stream = EnhancedEncoder.generate_key_stream(seed, len(cipher_numbers))
        
        # 解密
        plain_numbers = []
        for i in range(len(cipher_numbers)):
            decrypted = cipher_numbers[i] ^ (key_stream[i] % 26)
            plain_numbers.append(decrypted)
        
        # 转换为文本
        decoded_text = ''.join(chr(n + ord('a')) for n in plain_numbers)
        
        # 移除填充
        if original_length is not None and original_length <= len(decoded_text):
            final_text = decoded_text[:original_length]
            removed_padding = decoded_text[original_length:]
        else:
            # 自动移除末尾的x
            original_length = len(decoded_text.rstrip('x'))
            final_text = decoded_text[:original_length]
            removed_padding = decoded_text[original_length:]
        
        # 保存结果
        output_path = os.path.join(operation_dir, "decoded.txt")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(final_text)
        
        # 保存完整解码结果
        full_output_path = os.path.join(operation_dir, "decoded_full.txt")
        with open(full_output_path, 'w', encoding='utf-8') as f:
            f.write(decoded_text)
        
        # 保存密钥流信息
        key_stream_path = os.path.join(operation_dir, "key_stream.txt")
        with open(key_stream_path, 'w', encoding='utf-8') as f:
            f.write(f"密钥流长度: {len(key_stream)}\n")
            f.write(f"前10个值: {key_stream[:10]}\n")
            f.write(f"SHA-256种子: {seed.hex()}\n")
        
        # 保存元数据
        metadata = {
            'mode': 'enhanced_decode',
            'source_image': img_copy_path,
            'key_image': key_img_copy_path,
            'key_image_name': key_img_filename,
            'original_length_input': original_length,
            'num_groups_used': num_groups,
            'decoded_full': decoded_text,
            'decoded_final': final_text,
            'removed_padding': removed_padding,
            'output_text': output_path,
            'key_stream_seed': seed.hex(),
            'timestamp': datetime.now().isoformat()
        }
        
        metadata_path = os.path.join(operation_dir, "metadata.json")
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        # 创建操作报告
        report_path = os.path.join(operation_dir, "report.txt")
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(f"增强解密操作报告\n")
            f.write(f"==================\n\n")
            f.write(f"操作时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"源图片: {image_path}\n")
            f.write(f"密钥图片: {key_image_path}\n")
            f.write(f"密钥图片名: {key_img_filename}\n")
            f.write(f"图片尺寸: {img.size[0]}x{img.size[1]} 像素\n")
            f.write(f"使用的组数: {num_groups}\n")
            f.write(f"完整解码文本: {decoded_text}\n")
            f.write(f"最终文本 (移除填充): {final_text}\n")
            f.write(f"移除的填充: {removed_padding}\n")
            f.write(f"输出文件: {output_path}\n")
            f.write(f"SHA-256种子: {seed.hex()}\n")
        
        return operation_dir, final_text

# ==================== 模式3：简化加密模式 ====================

class SimpleEncoder:
    """简化加密模式"""
    
    def __init__(self, key_image_path):
        self.key_image_path = key_image_path
    
    def _image_to_seed(self, image_path):
        """将图片转换为密钥种子"""
        img = Image.open(image_path)
        data = bytearray()
        for pixel in list(img.getdata()):
            if len(pixel) >= 3:
                data.extend(pixel[:3])
        return hashlib.sha256(bytes(data)).digest()
    
    def _generate_key_stream(self, seed, length):
        """生成密钥流"""
        stream = []
        counter = 0
        while len(stream) < length:
            h = hmac.new(seed, struct.pack('>I', counter), hashlib.sha256)
            stream.extend(bytearray(h.digest()))
            counter += 1
        return stream[:length]
    
    def encode(self, text, carrier_image_path=None, operation_dir=None):
        """简化加密"""
        # 创建操作文件夹
        if operation_dir is None:
            operation_dir, operation_name = create_operation_folder("simple_encode")
        
        if not os.path.exists(self.key_image_path):
            raise FileNotFoundError(f"密钥图片不存在: {self.key_image_path}")
        
        # 复制密钥图片到操作文件夹
        key_img_filename = os.path.basename(self.key_image_path)
        key_img_copy_path = os.path.join(operation_dir, key_img_filename)
        shutil.copy2(self.key_image_path, key_img_copy_path)
        
        # 如果有载体图片，也复制
        carrier_copy_path = None
        if carrier_image_path and os.path.exists(carrier_image_path):
            carrier_filename = os.path.basename(carrier_image_path)
            carrier_copy_path = os.path.join(operation_dir, carrier_filename)
            shutil.copy2(carrier_image_path, carrier_copy_path)
        
        # 预处理
        processed = preprocess_string(text)
        padded = pad_string_to_multiple(processed, 9, 'x')
        
        # 转换为数字
        numbers = [ord(c) - ord('a') for c in padded]
        
        # 生成密钥流
        seed = self._image_to_seed(key_img_copy_path)
        key_stream = self._generate_key_stream(seed, len(numbers))
        
        # 加密
        cipher_numbers = [n ^ (k % 26) for n, k in zip(numbers, key_stream)]
        
        # 创建图片
        groups = len(padded) // 9
        rows = (groups + 2) // 3
        
        if carrier_copy_path and os.path.exists(carrier_copy_path):
            img = Image.open(carrier_copy_path)
            if img.size[0] < 9 or img.size[1] < rows:
                img = img.resize((max(9, img.size[0]), max(rows, img.size[1])))
        else:
            img = Image.new('RGB', (9, rows), color='black')
        
        pixels = img.load()
        
        # 存入图片
        for i in range(groups):
            row = i // 3
            channel = i % 3
            group_values = cipher_numbers[i*9:(i+1)*9]
            
            for col in range(9):
                value = min(255, max(0, group_values[col]))
                current = pixels[col, row]
                
                if channel == 0:
                    pixels[col, row] = (value, current[1], current[2])
                elif channel == 1:
                    pixels[col, row] = (current[0], value, current[2])
                else:
                    pixels[col, row] = (current[0], current[1], value)
        
        # 保存加密图片
        output_path = os.path.join(operation_dir, "encoded.png")
        img.save(output_path)
        
        # 保存输入文本
        input_text_path = os.path.join(operation_dir, "input.txt")
        with open(input_text_path, 'w', encoding='utf-8') as f:
            f.write(text)
        
        # 保存处理后的文本
        processed_path = os.path.join(operation_dir, "processed.txt")
        with open(processed_path, 'w', encoding='utf-8') as f:
            f.write(padded)
        
        # 保存元数据
        metadata = {
            'mode': 'simple_encode',
            'original_text': text,
            'original_length': len(processed),
            'padded_text': padded,
            'padded_length': len(padded),
            'num_groups': groups,
            'key_image': key_img_copy_path,
            'key_image_name': key_img_filename,
            'carrier_image': carrier_copy_path,
            'output_image': output_path,
            'image_size': img.size,
            'key_stream_seed': seed.hex(),
            'timestamp': datetime.now().isoformat()
        }
        
        metadata_path = os.path.join(operation_dir, "metadata.json")
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        # 创建操作报告
        report_path = os.path.join(operation_dir, "report.txt")
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(f"简化加密操作报告\n")
            f.write(f"==================\n\n")
            f.write(f"操作时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"原始文本: {text}\n")
            f.write(f"原始长度: {len(text)} 字符\n")
            f.write(f"处理后文本: {padded}\n")
            f.write(f"处理后长度: {len(padded)} 字符\n")
            f.write(f"分组数: {groups}\n")
            f.write(f"密钥图片: {key_img_filename}\n")
            if carrier_copy_path:
                f.write(f"载体图片: {carrier_filename}\n")
            f.write(f"输出文件: {output_path}\n")
            f.write(f"图片尺寸: {img.size[0]}x{img.size[1]} 像素\n")
        
        return operation_dir, metadata
    
    def decode(self, image_path, original_length=None, num_groups=None, operation_dir=None):
        """简化解密"""
        # 创建操作文件夹
        if operation_dir is None:
            operation_dir, operation_name = create_operation_folder("simple_decode")
        
        if not os.path.exists(self.key_image_path):
            raise FileNotFoundError(f"密钥图片不存在: {self.key_image_path}")
        
        # 复制源图片到操作文件夹
        img_filename = os.path.basename(image_path)
        img_copy_path = os.path.join(operation_dir, img_filename)
        shutil.copy2(image_path, img_copy_path)
        
        # 复制密钥图片到操作文件夹
        key_img_filename = os.path.basename(self.key_image_path)
        key_img_copy_path = os.path.join(operation_dir, key_img_filename)
        shutil.copy2(self.key_image_path, key_img_copy_path)
        
        # 提取数据
        img = Image.open(img_copy_path)
        pixels = img.load()
        width, height = img.size
        
        # 确定组数
        if num_groups is None:
            num_groups = height * 3
        
        cipher_numbers = []
        for i in range(num_groups):
            row = i // 3
            channel = i % 3
            
            for col in range(9):
                if col < width and row < height:
                    rgb = pixels[col, row]
                    value = rgb[channel]
                else:
                    value = 0
                cipher_numbers.append(value)
        
        # 生成密钥流
        seed = self._image_to_seed(key_img_copy_path)
        key_stream = self._generate_key_stream(seed, len(cipher_numbers))
        
        # 解密
        plain_numbers = [c ^ (k % 26) for c, k in zip(cipher_numbers, key_stream)]
        
        # 转换为文本
        text = ''.join(chr(n + ord('a')) for n in plain_numbers)
        
        # 截取原始长度
        if original_length is not None and original_length <= len(text):
            final_text = text[:original_length]
            removed_padding = text[original_length:]
        else:
            # 自动移除末尾的x
            original_length = len(text.rstrip('x'))
            final_text = text[:original_length]
            removed_padding = text[original_length:]
        
        # 保存结果
        output_path = os.path.join(operation_dir, "decoded.txt")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(final_text)
        
        # 保存完整解码结果
        full_output_path = os.path.join(operation_dir, "decoded_full.txt")
        with open(full_output_path, 'w', encoding='utf-8') as f:
            f.write(text)
        
        # 保存元数据
        metadata = {
            'mode': 'simple_decode',
            'source_image': img_copy_path,
            'key_image': key_img_copy_path,
            'key_image_name': key_img_filename,
            'original_length_input': original_length,
            'num_groups_used': num_groups,
            'decoded_full': text,
            'decoded_final': final_text,
            'removed_padding': removed_padding,
            'output_text': output_path,
            'key_stream_seed': seed.hex(),
            'timestamp': datetime.now().isoformat()
        }
        
        metadata_path = os.path.join(operation_dir, "metadata.json")
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        # 创建操作报告
        report_path = os.path.join(operation_dir, "report.txt")
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(f"简化解密操作报告\n")
            f.write(f"==================\n\n")
            f.write(f"操作时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"源图片: {image_path}\n")
            f.write(f"密钥图片: {self.key_image_path}\n")
            f.write(f"密钥图片名: {key_img_filename}\n")
            f.write(f"图片尺寸: {img.size[0]}x{img.size[1]} 像素\n")
            f.write(f"使用的组数: {num_groups}\n")
            f.write(f"完整解码文本: {text}\n")
            f.write(f"最终文本 (移除填充): {final_text}\n")
            f.write(f"移除的填充: {removed_padding}\n")
            f.write(f"输出文件: {output_path}\n")
        
        return operation_dir, final_text

# ==================== 用户界面函数 ====================

def print_banner():
    """打印横幅"""
    banner = """
╔══════════════════════════════════════════════════════════════════╗
║                  图片加密系统 - 完整版                           ║
║              Image Crypto System (Complete Edition)             ║
╚══════════════════════════════════════════════════════════════════╝
    """
    print(banner)

def print_file_structure():
    """打印文件结构说明"""
    structure = f"""
文件组织结构:
{ANS_FOLDER}/                         # 主输出文件夹
├── keys/                            # 密钥图片文件夹
│   ├── default_key.png              # 默认密钥图片
│   ├── key_20250129_143022.png      # 随机密钥图片
│   ├── gradient_key_20250129_143123.png  # 渐变密钥图片
│   └── ...                          # 其他密钥图片
│
├── original_encode/                 # 原始编码模式
│   ├── original_encode_20250129_143022/  # 每次操作一个文件夹
│   │   ├── input.txt                     # 输入文本
│   │   ├── processed.txt                 # 处理后的文本
│   │   ├── encoded.png                   # 编码后的图片
│   │   ├── metadata.json                 # 元数据
│   │   └── report.txt                    # 操作报告
│   └── ...
│
├── original_decode/                 # 原始解码模式
│   └── ... (类似结构)
│
├── enhanced_encode/                 # 增强加密模式
│   └── ... (类似结构，包含密钥图片副本)
│
├── enhanced_decode/                 # 增强解密模式
│   └── ... (类似结构)
│
├── simple_encode/                   # 简化加密模式
│   └── ... (类似结构)
│
├── simple_decode/                   # 简化解密模式
│   └── ... (类似结构)
│
└── test_images/                     # 测试图片文件夹
    └── test_carrier_20250129_143022.png  # 测试载体图片
    """
    print(structure)

# ==================== 密钥管理界面 ====================

def manage_keys():
    """密钥管理主菜单"""
    while True:
        print("\n" + "="*50)
        print("密钥图片管理")
        print("="*50)
        print("请选择操作:")
        print("  [1] 查看所有密钥图片")
        print("  [2] 创建随机密钥图片")
        print("  [3] 创建渐变密钥图片")
        print("  [4] 导入外部图片作为密钥")
        print("  [5] 选择密钥图片用于加密")
        print("  [6] 删除密钥图片")
        print("  [7] 创建默认密钥图片")
        print("  [0] 返回主菜单")
        
        choice = input("\n请选择 (0-7): ").strip()
        
        if choice == '0':
            break
        elif choice == '1':
            KeyManager.view_key_info()
        elif choice == '2':
            name = input("请输入密钥图片名称 (留空使用默认): ").strip()
            width = input("请输入宽度 (默认100): ").strip()
            height = input("请输入高度 (默认100): ").strip()
            
            try:
                width = int(width) if width else 100
                height = int(height) if height else 100
                KeyManager.create_random_key_image(name if name else None, width, height)
            except ValueError:
                print("尺寸必须为数字，使用默认值")
                KeyManager.create_random_key_image(name if name else None)
        elif choice == '3':
            name = input("请输入密钥图片名称 (留空使用默认): ").strip()
            width = input("请输入宽度 (默认100): ").strip()
            height = input("请输入高度 (默认100): ").strip()
            
            try:
                width = int(width) if width else 100
                height = int(height) if height else 100
                KeyManager.create_gradient_key_image(name if name else None, width, height)
            except ValueError:
                print("尺寸必须为数字，使用默认值")
                KeyManager.create_gradient_key_image(name if name else None)
        elif choice == '4':
            path = input("请输入要导入的图片路径: ").strip()
            KeyManager.import_key_image(path)
        elif choice == '5':
            return KeyManager.select_key_image()
        elif choice == '6':
            KeyManager.delete_key_image()
        elif choice == '7':
            KeyManager.create_default_key_image()
        else:
            print("无效选择")
        
        input("\n按回车键继续...")
    
    return None

# ==================== 操作模式界面 ====================

def mode_original_encode():
    """原始编码模式"""
    print("\n" + "="*50)
    print("模式1: 原始编码 (无密钥)")
    print("="*50)
    
    print("请输入要编码的字符串:")
    text = input()
    
    # 选择载体图片
    carrier_image = select_carrier_image()
    
    try:
        operation_dir, metadata = OriginalEncoder.encode(text, carrier_image)
        operation_name = os.path.basename(operation_dir)
        
        print(f"\n✓ 编码完成!")
        print(f"  操作文件夹: {operation_dir}")
        print(f"  操作名称: {operation_name}")
        print(f"  原始文本: {text[:50]}..." if len(text) > 50 else f"  原始文本: {text}")
        if carrier_image:
            print(f"  载体图片: {carrier_image}")
        print(f"  输出图片: {os.path.basename(metadata['output_image'])}")
        print(f"  图片尺寸: {metadata['image_size'][0]}x{metadata['image_size'][1]}")
        print(f"  分组数: {metadata['num_groups']}")
        
        # 显示文件夹内容
        print(f"\n  文件夹内容:")
        for item in os.listdir(operation_dir):
            item_path = os.path.join(operation_dir, item)
            if os.path.isfile(item_path):
                size = os.path.getsize(item_path)
                print(f"    • {item} ({size:,} bytes)")
        
    except Exception as e:
        print(f"\n✗ 编码失败: {e}")

def select_encoded_operation(mode="original_encode"):
    """选择已编码的操作"""
    operations = list_operations(mode)
    
    if not operations:
        print(f"没有找到{mode}操作记录")
        return None, None
    
    print(f"\n找到 {len(operations)} 个{mode}操作:")
    for i, (mode_name, op_name) in enumerate(operations[:10], 1):  # 只显示前10个
        op_path = os.path.join(ANS_FOLDER, mode_name, op_name)
        info = get_operation_info(op_path)
        
        if info:
            # 查找编码图片
            encoded_image = None
            for file_info in info['files']:
                if file_info['name'] == 'encoded.png':
                    encoded_image = file_info['path']
                    break
            
            print(f"  [{i}] {op_name}")
            print(f"      时间: {info['created']}")
            print(f"      文件数: {len(info['files'])}")
            if encoded_image:
                print(f"      编码图片: encoded.png")
            print()
    
    try:
        choice = int(input(f"请选择操作 (1-{min(10, len(operations))}): "))
        if 1 <= choice <= min(10, len(operations)):
            selected_mode, selected_op = operations[choice-1]
            operation_path = os.path.join(ANS_FOLDER, selected_mode, selected_op)
            return operation_path, selected_op
        else:
            print("无效选择")
            return None, None
    except ValueError:
        print("请输入有效数字")
        return None, None

def mode_original_decode():
    """原始解码模式"""
    print("\n" + "="*50)
    print("模式1: 原始解码 (无密钥)")
    print("="*50)
    
    print("请选择解码方式:")
    print("  1. 从已编码的操作中选择")
    print("  2. 手动输入图片路径")
    
    choice = input("请选择 (1-2): ").strip()
    
    if choice == '1':
        # 从已编码的操作中选择
        operation_path, operation_name = select_encoded_operation("original_encode")
        if not operation_path:
            return
        
        # 查找编码图片
        encoded_image = None
        for item in os.listdir(operation_path):
            if item == 'encoded.png':
                encoded_image = os.path.join(operation_path, item)
                break
        
        if not encoded_image:
            print("在操作文件夹中未找到编码图片")
            return
        
        # 从元数据获取原始长度
        metadata_path = os.path.join(operation_path, "metadata.json")
        original_length = None
        
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
                original_length = metadata.get('original_length')
        
        try:
            operation_dir, decoded_text = OriginalEncoder.decode(encoded_image, original_length)
            operation_name = os.path.basename(operation_dir)
            
            print(f"\n✓ 解码完成!")
            print(f"  操作文件夹: {operation_dir}")
            print(f"  操作名称: {operation_name}")
            print(f"  解码结果: {decoded_text[:50]}..." if len(decoded_text) > 50 else f"  解码结果: {decoded_text}")
            print(f"  长度: {len(decoded_text)} 字符")
            
            # 显示关联
            print(f"\n  关联的编码操作: {os.path.basename(operation_path)}")
            
        except Exception as e:
            print(f"\n✗ 解码失败: {e}")
    
    elif choice == '2':
        # 手动输入
        image_path = input("请输入编码图片路径: ").strip()
        
        if not os.path.exists(image_path):
            print("文件不存在")
            return
        
        original_length = None
        try:
            length_input = input("请输入原始文本长度 (留空自动检测): ").strip()
            if length_input:
                original_length = int(length_input)
        except:
            pass
        
        try:
            operation_dir, decoded_text = OriginalEncoder.decode(image_path, original_length)
            operation_name = os.path.basename(operation_dir)
            
            print(f"\n✓ 解码完成!")
            print(f"  操作文件夹: {operation_dir}")
            print(f"  操作名称: {operation_name}")
            print(f"  解码结果: {decoded_text[:50]}..." if len(decoded_text) > 50 else f"  解码结果: {decoded_text}")
            print(f"  长度: {len(decoded_text)} 字符")
        except Exception as e:
            print(f"\n✗ 解码失败: {e}")
    else:
        print("无效选择")

def mode_enhanced_encode():
    """增强加密模式"""
    print("\n" + "="*50)
    print("模式2: 增强加密 (图片密钥)")
    print("="*50)
    
    # 选择密钥图片
    print("请选择密钥图片:")
    print("  1. 从密钥库选择")
    print("  2. 创建新的密钥图片")
    
    key_choice = input("请选择 (1-2): ").strip()
    key_image = None
    
    if key_choice == '1':
        key_info = KeyManager.select_key_image()
        if key_info:
            key_image = key_info['path']
    elif key_choice == '2':
        key_image = KeyManager.create_random_key_image()
    else:
        print("无效选择，使用默认密钥图片")
        key_image = KeyManager.create_default_key_image()
    
    if not key_image:
        print("未选择密钥图片，操作取消")
        return
    
    print(f"\n使用密钥图片: {os.path.basename(key_image)}")
    
    # 输入文本
    print("\n请输入要加密的字符串:")
    text = input()
    
    # 选择载体图片
    carrier_image = select_carrier_image()
    
    try:
        operation_dir, metadata = EnhancedEncoder.encode(text, key_image, carrier_image)
        operation_name = os.path.basename(operation_dir)
        
        print(f"\n✓ 加密完成!")
        print(f"  操作文件夹: {operation_dir}")
        print(f"  操作名称: {operation_name}")
        print(f"  原始文本: {text[:50]}..." if len(text) > 50 else f"  原始文本: {text}")
        print(f"  密钥图片: {os.path.basename(key_image)}")
        if carrier_image:
            print(f"  载体图片: {os.path.basename(carrier_image)}")
        print(f"  输出图片: {os.path.basename(metadata['output_image'])}")
        print(f"  图片尺寸: {metadata['image_size'][0]}x{metadata['image_size'][1]}")
        print(f"  分组数: {metadata['num_groups']}")
        print(f"  密钥SHA-256: {metadata['key_image_sha256'][:16]}...")
        
        # 显示文件夹内容
        print(f"\n  文件夹内容:")
        for item in os.listdir(operation_dir):
            item_path = os.path.join(operation_dir, item)
            if os.path.isfile(item_path):
                size = os.path.getsize(item_path)
                print(f"    • {item} ({size:,} bytes)")
        
    except Exception as e:
        print(f"\n✗ 加密失败: {e}")

def mode_enhanced_decode():
    """增强解密模式"""
    print("\n" + "="*50)
    print("模式2: 增强解密 (图片密钥)")
    print("="*50)
    
    print("请选择解密方式:")
    print("  1. 从已加密的操作中选择")
    print("  2. 手动输入图片路径")
    
    choice = input("请选择 (1-2): ").strip()
    
    if choice == '1':
        # 从已加密的操作中选择
        operation_path, operation_name = select_encoded_operation("enhanced_encode")
        if not operation_path:
            return
        
        # 查找加密图片和密钥图片
        encoded_image = None
        key_image = None
        
        for item in os.listdir(operation_path):
            if item == 'encoded.png':
                encoded_image = os.path.join(operation_path, item)
            elif item.endswith('.png') and item != 'encoded.png':
                # 假设第一个非encoded.png的图片是密钥图片
                if not key_image and ('key' in item.lower() or 'cipher' in item.lower()):
                    key_image = os.path.join(operation_path, item)
        
        if not encoded_image:
            print("在操作文件夹中未找到加密图片")
            return
        
        if not key_image:
            # 尝试从元数据获取密钥图片名
            metadata_path = os.path.join(operation_path, "metadata.json")
            if os.path.exists(metadata_path):
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                    key_image_name = metadata.get('key_image_name')
                    if key_image_name:
                        key_image = os.path.join(operation_path, key_image_name)
            
            if not key_image:
                print("在操作文件夹中未找到密钥图片")
                print("请手动选择密钥图片")
                key_info = KeyManager.select_key_image()
                if key_info:
                    key_image = key_info['path']
                else:
                    return
        
        # 从元数据获取信息
        metadata_path = os.path.join(operation_path, "metadata.json")
        original_length = None
        num_groups = None
        
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
                original_length = metadata.get('original_length')
                num_groups = metadata.get('num_groups')
        
        try:
            operation_dir, decoded_text = EnhancedEncoder.decode(
                encoded_image, key_image, original_length, num_groups
            )
            operation_name = os.path.basename(operation_dir)
            
            print(f"\n✓ 解密完成!")
            print(f"  操作文件夹: {operation_dir}")
            print(f"  操作名称: {operation_name}")
            print(f"  解密结果: {decoded_text[:50]}..." if len(decoded_text) > 50 else f"  解密结果: {decoded_text}")
            print(f"  长度: {len(decoded_text)} 字符")
            
            # 显示关联
            print(f"\n  关联的加密操作: {os.path.basename(operation_path)}")
            
        except Exception as e:
            print(f"\n✗ 解密失败: {e}")
    
    elif choice == '2':
        # 手动输入
        image_path = input("请输入加密图片路径: ").strip()
        
        if not os.path.exists(image_path):
            print("文件不存在")
            return
        
        # 选择密钥图片
        print("\n请选择密钥图片:")
        key_info = KeyManager.select_key_image()
        if not key_info:
            return
        
        key_image = key_info['path']
        
        original_length = None
        num_groups = None
        
        try:
            length_input = input("请输入原始文本长度 (留空自动检测): ").strip()
            if length_input:
                original_length = int(length_input)
        except:
            pass
        
        try:
            groups_input = input("请输入分组数 (留空自动检测): ").strip()
            if groups_input:
                num_groups = int(groups_input)
        except:
            pass
        
        try:
            operation_dir, decoded_text = EnhancedEncoder.decode(
                image_path, key_image, original_length, num_groups
            )
            operation_name = os.path.basename(operation_dir)
            
            print(f"\n✓ 解密完成!")
            print(f"  操作文件夹: {operation_dir}")
            print(f"  操作名称: {operation_name}")
            print(f"  解密结果: {decoded_text[:50]}..." if len(decoded_text) > 50 else f"  解密结果: {decoded_text}")
            print(f"  长度: {len(decoded_text)} 字符")
        except Exception as e:
            print(f"\n✗ 解密失败: {e}")
    else:
        print("无效选择")

def mode_simple_encode():
    """简化加密模式"""
    print("\n" + "="*50)
    print("模式3: 简化加密")
    print("="*50)
    
    # 选择密钥图片
    print("请选择密钥图片:")
    print("  1. 从密钥库选择")
    print("  2. 创建新的密钥图片")
    
    key_choice = input("请选择 (1-2): ").strip()
    key_image = None
    
    if key_choice == '1':
        key_info = KeyManager.select_key_image()
        if key_info:
            key_image = key_info['path']
    elif key_choice == '2':
        key_image = KeyManager.create_random_key_image()
    else:
        print("无效选择，使用默认密钥图片")
        key_image = KeyManager.create_default_key_image()
    
    if not key_image:
        print("未选择密钥图片，操作取消")
        return
    
    print(f"\n使用密钥图片: {os.path.basename(key_image)}")
    
    encoder = SimpleEncoder(key_image)
    
    # 输入文本
    print("\n请输入要加密的字符串:")
    text = input()
    
    # 选择载体图片
    carrier_image = select_carrier_image()
    
    try:
        operation_dir, metadata = encoder.encode(text, carrier_image)
        operation_name = os.path.basename(operation_dir)
        
        print(f"\n✓ 加密完成!")
        print(f"  操作文件夹: {operation_dir}")
        print(f"  操作名称: {operation_name}")
        print(f"  原始文本: {text[:50]}..." if len(text) > 50 else f"  原始文本: {text}")
        print(f"  密钥图片: {os.path.basename(key_image)}")
        if carrier_image:
            print(f"  载体图片: {os.path.basename(carrier_image)}")
        print(f"  输出图片: {os.path.basename(metadata['output_image'])}")
        print(f"  图片尺寸: {metadata['image_size'][0]}x{metadata['image_size'][1]}")
        print(f"  分组数: {metadata['num_groups']}")
        
        # 显示文件夹内容
        print(f"\n  文件夹内容:")
        for item in os.listdir(operation_dir):
            item_path = os.path.join(operation_dir, item)
            if os.path.isfile(item_path):
                size = os.path.getsize(item_path)
                print(f"    • {item} ({size:,} bytes)")
        
    except Exception as e:
        print(f"\n✗ 加密失败: {e}")

def mode_simple_decode():
    """简化解密模式"""
    print("\n" + "="*50)
    print("模式3: 简化解密")
    print("="*50)
    
    print("请选择解密方式:")
    print("  1. 从已加密的操作中选择")
    print("  2. 手动输入图片路径")
    
    choice = input("请选择 (1-2): ").strip()
    
    if choice == '1':
        # 从已加密的操作中选择
        operation_path, operation_name = select_encoded_operation("simple_encode")
        if not operation_path:
            return
        
        # 查找加密图片和密钥图片
        encoded_image = None
        key_image = None
        
        for item in os.listdir(operation_path):
            if item == 'encoded.png':
                encoded_image = os.path.join(operation_path, item)
            elif item.endswith('.png') and item != 'encoded.png':
                # 假设第一个非encoded.png的图片是密钥图片
                if not key_image:
                    key_image = os.path.join(operation_path, item)
        
        if not encoded_image:
            print("在操作文件夹中未找到加密图片")
            return
        
        if not key_image:
            # 尝试从元数据获取密钥图片名
            metadata_path = os.path.join(operation_path, "metadata.json")
            if os.path.exists(metadata_path):
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                    key_image_name = metadata.get('key_image_name')
                    if key_image_name:
                        key_image = os.path.join(operation_path, key_image_name)
            
            if not key_image:
                print("在操作文件夹中未找到密钥图片")
                print("请手动选择密钥图片")
                key_info = KeyManager.select_key_image()
                if key_info:
                    key_image = key_info['path']
                else:
                    return
        
        encoder = SimpleEncoder(key_image)
        
        # 从元数据获取信息
        metadata_path = os.path.join(operation_path, "metadata.json")
        original_length = None
        num_groups = None
        
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
                original_length = metadata.get('original_length')
                num_groups = metadata.get('num_groups')
        
        try:
            operation_dir, decoded_text = encoder.decode(
                encoded_image, original_length, num_groups
            )
            operation_name = os.path.basename(operation_dir)
            
            print(f"\n✓ 解密完成!")
            print(f"  操作文件夹: {operation_dir}")
            print(f"  操作名称: {operation_name}")
            print(f"  解密结果: {decoded_text[:50]}..." if len(decoded_text) > 50 else f"  解密结果: {decoded_text}")
            print(f"  长度: {len(decoded_text)} 字符")
            
            # 显示关联
            print(f"\n  关联的加密操作: {os.path.basename(operation_path)}")
            
        except Exception as e:
            print(f"\n✗ 解密失败: {e}")
    
    elif choice == '2':
        # 手动输入
        image_path = input("请输入加密图片路径: ").strip()
        
        if not os.path.exists(image_path):
            print("文件不存在")
            return
        
        # 选择密钥图片
        print("\n请选择密钥图片:")
        key_info = KeyManager.select_key_image()
        if not key_info:
            return
        
        key_image = key_info['path']
        
        encoder = SimpleEncoder(key_image)
        
        original_length = None
        num_groups = None
        
        try:
            length_input = input("请输入原始文本长度 (留空自动检测): ").strip()
            if length_input:
                original_length = int(length_input)
        except:
            pass
        
        try:
            groups_input = input("请输入分组数 (留空自动检测): ").strip()
            if groups_input:
                num_groups = int(groups_input)
        except:
            pass
        
        try:
            operation_dir, decoded_text = encoder.decode(image_path, original_length, num_groups)
            operation_name = os.path.basename(operation_dir)
            
            print(f"\n✓ 解密完成!")
            print(f"  操作文件夹: {operation_dir}")
            print(f"  操作名称: {operation_name}")
            print(f"  解密结果: {decoded_text[:50]}..." if len(decoded_text) > 50 else f"  解密结果: {decoded_text}")
            print(f"  长度: {len(decoded_text)} 字符")
        except Exception as e:
            print(f"\n✗ 解密失败: {e}")
    else:
        print("无效选择")

# ==================== 文件管理界面 ====================

def view_operations():
    """查看所有操作"""
    print("\n" + "="*50)
    print("查看所有操作")
    print("="*50)
    
    operations = list_operations()
    
    if not operations:
        print("没有找到任何操作记录")
        return
    
    # 按模式分组
    operations_by_mode = {}
    for mode, op_name in operations:
        if mode not in operations_by_mode:
            operations_by_mode[mode] = []
        operations_by_mode[mode].append((mode, op_name))
    
    total_ops = 0
    total_size = 0
    
    for mode, ops in operations_by_mode.items():
        print(f"\n{mode} ({len(ops)}个操作):")
        print("-" * 50)
        
        for i, (m, op_name) in enumerate(ops[:5], 1):  # 每个模式只显示前5个
            op_path = os.path.join(ANS_FOLDER, m, op_name)
            info = get_operation_info(op_path)
            
            if info:
                # 查找主要文件
                main_files = []
                for file_info in info['files']:
                    if file_info['name'] in ['encoded.png', 'decoded.txt', 'input.txt']:
                        main_files.append(file_info['name'])
                
                print(f"  [{i}] {op_name}")
                print(f"      创建时间: {info['created']}")
                print(f"      文件数: {len(info['files'])}")
                if main_files:
                    print(f"      主要文件: {', '.join(main_files[:3])}")
                print(f"      总大小: {info['size']:,} bytes")
                print()
                
                total_ops += 1
                total_size += info['size']
    
    print(f"\n总计: {total_ops} 个操作, {total_size:,} bytes")
    
    if total_ops > 20:
        print("注: 只显示了部分操作，使用'查看操作详情'查看更多")

def view_operation_detail():
    """查看操作详情"""
    print("\n" + "="*50)
    print("查看操作详情")
    print("="*50)
    
    operations = list_operations()
    
    if not operations:
        print("没有找到任何操作记录")
        return
    
    print("选择要查看详细信息的操作:")
    for i, (mode, op_name) in enumerate(operations[:20], 1):
        print(f"  [{i}] {mode}/{op_name}")
    
    try:
        choice = int(input(f"\n请选择操作 (1-{min(20, len(operations))}): "))
        if 1 <= choice <= min(20, len(operations)):
            selected_mode, selected_op = operations[choice-1]
            operation_path = os.path.join(ANS_FOLDER, selected_mode, selected_op)
            info = get_operation_info(operation_path)
            
            if info:
                print(f"\n操作详情: {selected_mode}/{selected_op}")
                print(f"=" * 60)
                print(f"路径: {info['path']}")
                print(f"创建时间: {info['created']}")
                print(f"修改时间: {info['modified']}")
                print(f"总大小: {info['size']:,} bytes")
                print(f"文件数: {len(info['files'])}")
                
                print(f"\n文件列表:")
                for file_info in info['files']:
                    print(f"  • {file_info['name']} ({file_info['size']:,} bytes)")
                
                # 尝试显示文本文件内容
                print(f"\n文本文件内容预览:")
                for file_info in info['files']:
                    if file_info['name'].endswith('.txt'):
                        print(f"\n{file_info['name']}:")
                        try:
                            with open(file_info['path'], 'r', encoding='utf-8') as f:
                                content = f.read()
                                if len(content) > 200:
                                    print(f"  {content[:200]}...")
                                else:
                                    print(f"  {content}")
                        except:
                            print(f"  (无法读取)")
                
                # 显示元数据
                metadata_path = os.path.join(operation_path, "metadata.json")
                if os.path.exists(metadata_path):
                    print(f"\n元数据:")
                    with open(metadata_path, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                        for key, value in metadata.items():
                            if key not in ['original_text', 'padded_text', 'decoded_full', 'decoded_final']:
                                if isinstance(value, str) and len(value) > 100:
                                    print(f"  {key}: {value[:100]}...")
                                else:
                                    print(f"  {key}: {value}")
            else:
                print("无法获取操作信息")
        else:
            print("无效选择")
    except ValueError:
        print("请输入有效数字")

def cleanup_operations():
    """清理操作"""
    print("\n" + "="*50)
    print("清理操作")
    print("="*50)
    
    print("选择清理方式:")
    print("  [1] 清理特定操作")
    print("  [2] 清理特定模式的所有操作")
    print("  [3] 清理所有操作")
    print("  [4] 清理测试图片")
    
    choice = input("\n请选择 (1-4): ").strip()
    
    if choice == '1':
        # 清理特定操作
        operations = list_operations()
        
        if not operations:
            print("没有找到任何操作记录")
            return
        
        print("\n选择要删除的操作:")
        for i, (mode, op_name) in enumerate(operations[:20], 1):
            print(f"  [{i}] {mode}/{op_name}")
        
        try:
            selection = input(f"\n请输入要删除的操作编号 (多个用逗号分隔，或输入'all'删除所有): ").strip()
            
            if selection.lower() == 'all':
                confirm = input("确定要删除所有操作吗? (y/n): ")
                if confirm.lower() == 'y':
                    deleted_count = 0
                    for mode, op_name in operations:
                        op_path = os.path.join(ANS_FOLDER, mode, op_name)
                        try:
                            shutil.rmtree(op_path)
                            print(f"  已删除: {mode}/{op_name}")
                            deleted_count += 1
                        except Exception as e:
                            print(f"  删除失败 {mode}/{op_name}: {e}")
                    
                    # 检查并删除空模式文件夹
                    for mode in os.listdir(ANS_FOLDER):
                        if mode == TEST_FOLDER:
                            continue
                        mode_path = os.path.join(ANS_FOLDER, mode)
                        if os.path.isdir(mode_path) and not os.listdir(mode_path):
                            try:
                                os.rmdir(mode_path)
                                print(f"  已删除空模式文件夹: {mode}")
                            except:
                                pass
                    
                    print(f"\n✓ 已删除 {deleted_count} 个操作")
            else:
                indices = [int(i.strip()) for i in selection.split(',') if i.strip().isdigit()]
                indices = [i for i in indices if 1 <= i <= len(operations)]
                
                if not indices:
                    print("无效选择")
                    return
                
                confirm = input(f"确定要删除这 {len(indices)} 个操作吗? (y/n): ")
                if confirm.lower() == 'y':
                    deleted_count = 0
                    for idx in indices:
                        mode, op_name = operations[idx-1]
                        op_path = os.path.join(ANS_FOLDER, mode, op_name)
                        try:
                            shutil.rmtree(op_path)
                            print(f"  已删除: {mode}/{op_name}")
                            deleted_count += 1
                        except Exception as e:
                            print(f"  删除失败 {mode}/{op_name}: {e}")
                    
                    print(f"\n✓ 已删除 {deleted_count} 个操作")
        
        except ValueError:
            print("输入格式错误")
    
    elif choice == '2':
        # 清理特定模式
        modes = []
        if os.path.exists(ANS_FOLDER):
            for item in os.listdir(ANS_FOLDER):
                if item == TEST_FOLDER:
                    continue
                if os.path.isdir(os.path.join(ANS_FOLDER, item)):
                    modes.append(item)
        
        if not modes:
            print("没有找到任何模式")
            return
        
        print("\n选择要清理的模式:")
        for i, mode in enumerate(modes, 1):
            mode_path = os.path.join(ANS_FOLDER, mode)
            op_count = len([d for d in os.listdir(mode_path) if os.path.isdir(os.path.join(mode_path, d))])
            print(f"  [{i}] {mode} ({op_count}个操作)")
        
        try:
            mode_idx = int(input(f"\n请选择模式 (1-{len(modes)}): "))
            if 1 <= mode_idx <= len(modes):
                selected_mode = modes[mode_idx-1]
                mode_path = os.path.join(ANS_FOLDER, selected_mode)
                
                confirm = input(f"确定要删除'{selected_mode}'模式的所有操作吗? (y/n): ")
                if confirm.lower() == 'y':
                    deleted_count = 0
                    for op_name in os.listdir(mode_path):
                        op_path = os.path.join(mode_path, op_name)
                        if os.path.isdir(op_path):
                            try:
                                shutil.rmtree(op_path)
                                print(f"  已删除: {selected_mode}/{op_name}")
                                deleted_count += 1
                            except Exception as e:
                                print(f"  删除失败 {selected_mode}/{op_name}: {e}")
                    
                    # 尝试删除空模式文件夹
                    try:
                        os.rmdir(mode_path)
                        print(f"  已删除空模式文件夹: {selected_mode}")
                    except:
                        print(f"  模式文件夹不为空，保留: {selected_mode}")
                    
                    print(f"\n✓ 已删除 {deleted_count} 个操作")
            else:
                print("无效选择")
        except ValueError:
            print("请输入有效数字")
    
    elif choice == '3':
        # 清理所有
        confirm = input("确定要删除所有操作吗? (y/n): ")
        if confirm.lower() == 'y':
            if os.path.exists(ANS_FOLDER):
                try:
                    # 保留密钥文件夹
                    if os.path.exists(KEY_FOLDER):
                        temp_key = KEY_FOLDER + "_temp"
                        shutil.move(KEY_FOLDER, temp_key)
                    
                    shutil.rmtree(ANS_FOLDER)
                    
                    # 恢复密钥文件夹
                    if os.path.exists(temp_key):
                        shutil.move(temp_key, KEY_FOLDER)
                    
                    print("✓ 已删除所有操作和ans文件夹")
                except Exception as e:
                    print(f"删除失败: {e}")
            else:
                print("ans文件夹不存在")
    
    elif choice == '4':
        # 清理测试图片
        test_dir = os.path.join(ANS_FOLDER, TEST_FOLDER)
        if os.path.exists(test_dir):
            files = os.listdir(test_dir)
            if files:
                print(f"找到 {len(files)} 个测试图片:")
                for file in files:
                    print(f"  • {file}")
                
                confirm = input("确定要删除所有测试图片吗? (y/n): ")
                if confirm.lower() == 'y':
                    deleted_count = 0
                    for file in files:
                        file_path = os.path.join(test_dir, file)
                        try:
                            os.remove(file_path)
                            print(f"  已删除: {file}")
                            deleted_count += 1
                        except Exception as e:
                            print(f"  删除失败 {file}: {e}")
                    
                    print(f"\n✓ 已删除 {deleted_count} 个测试图片")
            else:
                print("没有测试图片可删除")
        else:
            print("测试图片文件夹不存在")
    
    else:
        print("无效选择")

def show_help():
    """显示帮助信息"""
    print("\n" + "="*50)
    print("帮助信息")
    print("="*50)
    
    help_text = """
图片加密系统 - 完整版

系统特点:
• 支持三种加密模式：原始编码、增强加密、简化加密
• 密钥图片管理：创建、导入、选择、删除密钥图片
• 每次操作结果保存在独立的文件夹中
• 完整的元数据和操作报告
• 支持载体图片选择

文件组织结构:
1. keys/ - 密钥图片文件夹，所有密钥图片存储在这里
2. ans/ - 操作结果文件夹，按模式和操作时间组织
3. ans/test_images/ - 测试图片文件夹

三种加密模式:

1. 原始编码模式 (无密钥)
   • 简单的编码方案，无加密密钥
   • 将文本转换为数字和并存入图片
   • 安全性低，仅用于演示基本编码原理

2. 增强加密模式 (图片密钥)
   • 使用图片作为加密密钥
   • 基于SHA-256和HMAC生成密钥流
   • 流密码加密 (异或运算)
   • 支持载体图片隐藏加密数据
   • 需要相同的密钥图片才能解密

3. 简化加密模式
   • 增强模式的简化版本
   • 相同的加密原理，更简洁的接口
   • 同样需要密钥图片

使用步骤:
1. 创建或导入密钥图片（密钥管理菜单）
2. 选择加密模式进行加密
3. 保存加密图片和操作记录
4. 使用相同密钥图片进行解密

注意事项:
• 密钥图片必须保密，安全性依赖于密钥图片
• 不要用同一密钥图片加密多条重要信息
• 原始编码模式不提供真正的加密安全性
• 每次操作都会创建独立的文件夹，便于管理
    """
    print(help_text)

# ==================== 主程序 ====================

def main():
    """主函数"""
    ensure_folders()
    
    # 确保有默认密钥图片
    KeyManager.create_default_key_image()
    
    while True:
        print_banner()
        
        print("请选择操作:")
        print()
        print("=== 密钥管理 ===")
        print("  [K] 密钥图片管理")
        print()
        print("=== 加密/编码操作 ===")
        print("  [1] 原始编码 - 将文本编码为图片")
        print("  [2] 原始解码 - 从图片解码文本")
        print("  [3] 增强加密 - 使用图片密钥加密")
        print("  [4] 增强解密 - 使用图片密钥解密")
        print("  [5] 简化加密 - 简化接口加密")
        print("  [6] 简化解密 - 简化接口解密")
        print()
        print("=== 文件管理 ===")
        print("  [7] 查看所有操作")
        print("  [8] 查看操作详情")
        print("  [9] 清理操作")
        print()
        print("=== 工具 ===")
        print("  [T] 创建测试图片")
        print("  [S] 显示文件结构")
        print("  [H] 帮助信息")
        print("  [0] 退出程序")
        print()
        
        choice = input("请输入选项: ").strip().upper()
        
        if choice == '0':
            print("\n感谢使用，再见!")
            break
        elif choice == 'K':
            manage_keys()
        elif choice == '1':
            mode_original_encode()
        elif choice == '2':
            mode_original_decode()
        elif choice == '3':
            mode_enhanced_encode()
        elif choice == '4':
            mode_enhanced_decode()
        elif choice == '5':
            mode_simple_encode()
        elif choice == '6':
            mode_simple_decode()
        elif choice == '7':
            view_operations()
        elif choice == '8':
            view_operation_detail()
        elif choice == '9':
            cleanup_operations()
        elif choice == 'T':
            create_test_image(save=True)
        elif choice == 'S':
            print_file_structure()
            input("\n按回车键继续...")
        elif choice == 'H':
            show_help()
            input("\n按回车键继续...")
        else:
            print("\n无效选项，请重新输入")
        
        input("\n按回车键继续...")

# ==================== 程序入口 ====================

if __name__ == "__main__":
    # 检查依赖
    try:
        from PIL import Image
    except ImportError:
        print("错误: 缺少必要的库 Pillow")
        print("请先安装依赖: pip install Pillow")
        exit(1)
    
    # 运行主程序
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n程序被用户中断")
    except Exception as e:
        print(f"\n程序运行出错: {e}")
        import traceback
        traceback.print_exc()
        print("\n请检查输入和文件路径")