#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
image_downloader - 图片下载模块

负责下载生成的图片到本地存储。
"""

import sys
import time
import hashlib
import requests
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
from urllib.parse import urlparse


class ImageDownloader:
    """图片下载器"""
    
    def __init__(self, output_dir: str = "./generated_images"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def _generate_filename(self, url: str, prefix: str = "", suffix: str = "") -> str:
        """生成文件名"""
        # 从 URL 获取扩展名
        parsed = urlparse(url)
        path = parsed.path
        ext = Path(path).suffix.lower()
        
        # 如果没有扩展名或扩展名不常见，默认使用 .png
        if not ext or ext not in ['.png', '.jpg', '.jpeg', '.webp', '.gif']:
            ext = '.png'
        
        # 生成基于时间戳的文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 添加随机部分避免冲突
        hash_obj = hashlib.md5(url.encode())
        hash_hex = hash_obj.hexdigest()[:8]
        
        # 组合文件名
        parts = [prefix, timestamp, hash_hex, suffix]
        filename = "_".join(filter(None, parts)) + ext
        
        return filename
    
    def download_single(
        self,
        url: str,
        filename: Optional[str] = None,
        prefix: str = "",
        suffix: str = "",
        timeout: int = 30,
        max_retries: int = 3
    ) -> str:
        """下载单张图片"""
        if not filename:
            filename = self._generate_filename(url, prefix, suffix)
        
        filepath = self.output_dir / filename
        
        # 确保文件名唯一
        counter = 1
        original_filepath = filepath
        while filepath.exists():
            name = original_filepath.stem
            ext = original_filepath.suffix
            filepath = self.output_dir / f"{name}_{counter}{ext}"
            counter += 1
        
        # 下载图片
        for attempt in range(max_retries):
            try:
                response = requests.get(url, timeout=timeout, stream=True)
                response.raise_for_status()
                
                # 写入文件
                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                
                return str(filepath)
                
            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:
                    raise Exception(f"图片下载失败 (尝试 {max_retries} 次): {str(e)}")
                
                # 等待后重试
                time.sleep(2 ** attempt)
        
        raise Exception("图片下载失败")
    
    def download_batch(
        self,
        urls: List[str],
        prefix: str = "batch",
        timeout: int = 30,
        max_retries: int = 3
    ) -> List[str]:
        """批量下载图片"""
        downloaded_files = []
        
        for i, url in enumerate(urls, 1):
            try:
                # 生成带序号的文件名
                suffix = f"{i:03d}"
                filepath = self.download_single(
                    url=url,
                    prefix=prefix,
                    suffix=suffix,
                    timeout=timeout,
                    max_retries=max_retries
                )
                downloaded_files.append(filepath)
                
            except Exception as e:
                print(f"下载第 {i} 张图片失败: {e}", file=sys.stderr)
                continue
        
        return downloaded_files
    
    def get_image_info(self, filepath: str) -> Dict[str, Any]:
        """获取图片信息"""
        path = Path(filepath)
        
        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {filepath}")
        
        # 获取文件信息
        stat = path.stat()
        
        # 尝试获取图片尺寸
        width, height = None, None
        try:
            from PIL import Image
            with Image.open(path) as img:
                width, height = img.size
        except ImportError:
            # 如果没有 PIL，尝试从文件头读取
            try:
                with open(path, 'rb') as f:
                    header = f.read(32)
                    # PNG
                    if header[:8] == b'\x89PNG\r\n\x1a\n':
                        width = int.from_bytes(header[16:20], 'big')
                        height = int.from_bytes(header[20:24], 'big')
                    # JPEG
                    elif header[:2] == b'\xff\xd8':
                        # 需要更复杂的解析，这里简化处理
                        pass
            except Exception:
                pass
        
        return {
            "filepath": str(path),
            "filename": path.name,
            "size_bytes": stat.st_size,
            "size_mb": round(stat.st_size / (1024 * 1024), 2),
            "width": width,
            "height": height,
            "format": path.suffix.lower().lstrip('.'),
            "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
        }
    
    def list_images(self, pattern: str = "*") -> List[Dict[str, Any]]:
        """列出目录中的图片"""
        images = []
        
        for filepath in self.output_dir.glob(pattern):
            if filepath.is_file():
                # 检查是否是图片文件
                ext = filepath.suffix.lower()
                if ext in ['.png', '.jpg', '.jpeg', '.webp', '.gif', '.bmp']:
                    try:
                        info = self.get_image_info(str(filepath))
                        images.append(info)
                    except Exception:
                        # 跳过无法读取的文件
                        continue
        
        # 按修改时间排序
        images.sort(key=lambda x: x.get("modified", ""), reverse=True)
        
        return images
    
    def clean_old_images(self, days: int = 30) -> int:
        """清理旧图片"""
        if not self.output_dir.exists():
            return 0
        
        cutoff_time = time.time() - (days * 24 * 60 * 60)
        deleted_count = 0
        
        for filepath in self.output_dir.iterdir():
            if filepath.is_file():
                # 检查是否是图片文件
                ext = filepath.suffix.lower()
                if ext in ['.png', '.jpg', '.jpeg', '.webp', '.gif', '.bmp']:
                    # 检查修改时间
                    if filepath.stat().st_mtime < cutoff_time:
                        try:
                            filepath.unlink()
                            deleted_count += 1
                        except Exception:
                            continue
        
        return deleted_count


def main():
    """命令行接口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="图片下载工具")
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # 下载单张图片
    download_parser = subparsers.add_parser("download", help="下载单张图片")
    download_parser.add_argument("url", help="图片 URL")
    download_parser.add_argument("--output", "-o", default="./generated_images", help="输出目录")
    download_parser.add_argument("--filename", "-f", help="文件名")
    download_parser.add_argument("--prefix", "-p", default="", help="文件名前缀")
    
    # 批量下载
    batch_parser = subparsers.add_parser("batch", help="批量下载图片")
    batch_parser.add_argument("urls", nargs="+", help="图片 URL 列表")
    batch_parser.add_argument("--output", "-o", default="./generated_images", help="输出目录")
    batch_parser.add_argument("--prefix", "-p", default="batch", help="文件名前缀")
    
    # 列出图片
    list_parser = subparsers.add_parser("list", help="列出目录中的图片")
    list_parser.add_argument("--output", "-o", default="./generated_images", help="图片目录")
    list_parser.add_argument("--pattern", "-P", default="*", help="文件匹配模式")
    
    # 清理旧图片
    clean_parser = subparsers.add_parser("clean", help="清理旧图片")
    clean_parser.add_argument("--output", "-o", default="./generated_images", help="图片目录")
    clean_parser.add_argument("--days", "-d", type=int, default=30, help="保留天数")
    
    args = parser.parse_args()
    
    if args.command == "download":
        downloader = ImageDownloader(args.output)
        try:
            filepath = downloader.download_single(
                url=args.url,
                filename=args.filename,
                prefix=args.prefix
            )
            print(f"已下载: {filepath}")
            
            # 显示图片信息
            info = downloader.get_image_info(filepath)
            print(f"文件大小: {info['size_mb']} MB")
            if info['width'] and info['height']:
                print(f"图片尺寸: {info['width']} x {info['height']}")
                
        except Exception as e:
            print(f"错误: {e}", file=sys.stderr)
            sys.exit(1)
    
    elif args.command == "batch":
        downloader = ImageDownloader(args.output)
        try:
            filepaths = downloader.download_batch(
                urls=args.urls,
                prefix=args.prefix
            )
            
            print(f"成功下载 {len(filepaths)} 张图片:")
            for filepath in filepaths:
                print(f"  - {filepath}")
                
        except Exception as e:
            print(f"错误: {e}", file=sys.stderr)
            sys.exit(1)
    
    elif args.command == "list":
        downloader = ImageDownloader(args.output)
        images = downloader.list_images(args.pattern)
        
        if not images:
            print("没有找到图片文件")
            return
        
        print(f"找到 {len(images)} 张图片:")
        for img in images:
            size_str = f"{img['size_mb']} MB"
            dim_str = f"{img['width']}x{img['height']}" if img['width'] and img['height'] else "未知尺寸"
            print(f"  {img['filename']} ({size_str}, {dim_str})")
    
    elif args.command == "clean":
        downloader = ImageDownloader(args.output)
        deleted = downloader.clean_old_images(args.days)
        print(f"已清理 {deleted} 张超过 {args.days} 天的图片")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()