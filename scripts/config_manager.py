#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
config_manager - 配置管理模块

管理 OpenAI API 密钥和用户偏好设置。
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import base64
import hashlib
from cryptography.fernet import Fernet


class ConfigManager:
    """配置管理器"""
    
    def __init__(self):
        self.config_dir = Path.home() / ".workbuddy"
        self.config_file = self.config_dir / "dalle_config.json"
        self.key_file = self.config_dir / ".dalle_key"
        self.config = self._load_config()
        self.cipher = self._init_cipher()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}
    
    def _save_config(self):
        """保存配置文件"""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    def _init_cipher(self) -> Optional[Fernet]:
        """初始化加密器"""
        if not self.key_file.exists():
            return None
        
        try:
            with open(self.key_file, 'rb') as f:
                key = f.read()
            return Fernet(key)
        except Exception:
            return None
    
    def _generate_key(self) -> bytes:
        """生成加密密钥"""
        key = Fernet.generate_key()
        self.config_dir.mkdir(parents=True, exist_ok=True)
        with open(self.key_file, 'wb') as f:
            f.write(key)
        return key
    
    def _encrypt(self, data: str) -> str:
        """加密数据"""
        if not self.cipher:
            key = self._generate_key()
            self.cipher = Fernet(key)
        
        encrypted = self.cipher.encrypt(data.encode())
        return base64.b64encode(encrypted).decode()
    
    def _decrypt(self, encrypted_data: str) -> str:
        """解密数据"""
        if not self.cipher:
            raise ValueError("加密器未初始化")
        
        try:
            encrypted = base64.b64decode(encrypted_data)
            decrypted = self.cipher.decrypt(encrypted)
            return decrypted.decode()
        except Exception as e:
            raise ValueError(f"解密失败: {e}")
    
    def get_api_key(self) -> Optional[str]:
        """获取 API 密钥"""
        # 优先从环境变量获取
        api_key = os.environ.get("OPENAI_API_KEY")
        if api_key:
            return api_key
        
        # 从配置文件获取（加密存储）
        encrypted_key = self.config.get("openai_api_key_encrypted")
        if encrypted_key:
            try:
                return self._decrypt(encrypted_key)
            except ValueError:
                return None
        
        # 兼容旧版本（明文存储）
        return self.config.get("openai_api_key")
    
    def set_api_key(self, api_key: str):
        """设置 API 密钥（加密存储）"""
        encrypted_key = self._encrypt(api_key)
        self.config["openai_api_key_encrypted"] = encrypted_key
        
        # 移除旧版本明文存储
        if "openai_api_key" in self.config:
            del self.config["openai_api_key"]
        
        self._save_config()
    
    def get_default(self, key: str, default=None):
        """获取默认配置"""
        return self.config.get(key, default)
    
    def set_default(self, key: str, value):
        """设置默认配置"""
        self.config[key] = value
        self._save_config()
    
    def validate_api_key(self, api_key: str) -> bool:
        """验证 API 密钥格式"""
        if not api_key:
            return False
        
        # 检查格式
        if not api_key.startswith("sk-"):
            return False
        
        # 检查长度
        if len(api_key) < 20:
            return False
        
        return True
    
    def prompt_for_api_key(self) -> str:
        """提示用户输入 API 密钥"""
        print("检测到 OpenAI API 密钥未配置", file=sys.stderr)
        print("请提供您的 OpenAI API 密钥：", file=sys.stderr)
        
        api_key = input().strip()
        
        if not api_key:
            raise ValueError("API 密钥不能为空")
        
        if not self.validate_api_key(api_key):
            raise ValueError("API 密钥格式无效，应以 'sk-' 开头且长度足够")
        
        # 保存密钥
        self.set_api_key(api_key)
        
        return api_key
    
    def get_all_defaults(self) -> Dict[str, Any]:
        """获取所有默认配置"""
        return {
            "default_model": self.get_default("default_model", "dall-e-3"),
            "default_size": self.get_default("default_size", "1024x1024"),
            "default_quality": self.get_default("default_quality", "standard"),
            "default_style": self.get_default("default_style", "vivid"),
            "auto_download": self.get_default("auto_download", True),
            "download_directory": self.get_default("download_directory", "./generated_images"),
            "max_retries": self.get_default("max_retries", 3),
            "timeout": self.get_default("timeout", 60)
        }


# 全局配置实例
_config_instance = None


def get_config() -> ConfigManager:
    """获取全局配置实例"""
    global _config_instance
    if _config_instance is None:
        _config_instance = ConfigManager()
    return _config_instance


def main():
    """命令行接口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="配置管理工具")
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # 设置 API 密钥
    set_key_parser = subparsers.add_parser("set-key", help="设置 API 密钥")
    set_key_parser.add_argument("api_key", help="OpenAI API 密钥")
    
    # 查看配置
    subparsers.add_parser("show", help="查看当前配置")
    
    # 验证密钥
    validate_parser = subparsers.add_parser("validate", help="验证 API 密钥")
    validate_parser.add_argument("api_key", help="要验证的 API 密钥")
    
    args = parser.parse_args()
    
    config = get_config()
    
    if args.command == "set-key":
        try:
            config.set_api_key(args.api_key)
            print("API 密钥已保存（加密存储）")
        except Exception as e:
            print(f"错误: {e}", file=sys.stderr)
            sys.exit(1)
    
    elif args.command == "show":
        api_key = config.get_api_key()
        if api_key:
            # 显示部分密钥
            masked_key = api_key[:8] + "..." + api_key[-4:]
            print(f"API 密钥: {masked_key}")
        else:
            print("API 密钥: 未配置")
        
        defaults = config.get_all_defaults()
        print("\n默认配置:")
        for key, value in defaults.items():
            print(f"  {key}: {value}")
    
    elif args.command == "validate":
        if config.validate_api_key(args.api_key):
            print("API 密钥格式有效")
        else:
            print("API 密钥格式无效")
            sys.exit(1)
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()