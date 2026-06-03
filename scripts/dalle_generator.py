#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dalle_generator - OpenAI DALL·E 图片生成工具

使用 OpenAI DALL·E 模型生成图片，支持 DALL·E 2 和 DALL·E 3。

Usage:
    dalle_generator.py "描述" [选项]
    dalle_generator.py --batch prompts.txt [选项]

Examples:
    dalle_generator.py "一只可爱的橘猫在阳光下打盹"
    dalle_generator.py "未来城市夜景" --model dall-e-3 --size 1024x1024
    dalle_generator.py --batch prompts.txt --model dall-e-3
"""

import argparse
import os
import sys
from pathlib import Path
from typing import List, Optional, Dict, Any
import requests
from datetime import datetime
from config_manager import ConfigManager

# 强制 UTF-8 编码
if sys.stdout.encoding and sys.stdout.encoding.lower().replace('-', '') != 'utf8':
    sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace', buffering=1)
if sys.stderr.encoding and sys.stderr.encoding.lower().replace('-', '') != 'utf8':
    sys.stderr = open(sys.stderr.fileno(), mode='w', encoding='utf-8', errors='replace', buffering=1)


class DalleConfig:
    """配置管理类（使用 ConfigManager 加密存储）"""

    def __init__(self):
        self._manager = ConfigManager()

    def get_api_key(self) -> Optional[str]:
        """获取 API 密钥"""
        return self._manager.get_api_key()

    def set_api_key(self, api_key: str):
        """设置 API 密钥（加密存储）"""
        self._manager.set_api_key(api_key)

    def get_default(self, key: str, default=None):
        """获取默认配置"""
        return self._manager.get_default(key, default)


class DalleGenerator:
    """DALL·E 图片生成器"""
    
    def __init__(self, config: DalleConfig):
        self.config = config
        self.api_key = config.get_api_key()
        self.base_url = "https://api.openai.com/v1"
    
    def check_api_key(self) -> bool:
        """检查 API 密钥是否存在"""
        if not self.api_key:
            return False
        
        # 简单验证密钥格式
        if not self.api_key.startswith("sk-"):
            return False
        
        return True
    
    def verify_api_connection(self) -> Dict[str, Any]:
        """验证 API 连接是否可用
        
        Returns:
            dict: 包含验证结果的字典
                - success: bool, 是否验证成功
                - message: str, 验证结果消息
                - error: str, 错误信息（如果有）
        """
        result = {
            "success": False,
            "message": "",
            "error": None
        }
        
        if not self.check_api_key():
            result["error"] = "API密钥未配置或格式无效"
            result["message"] = "请先配置有效的OpenAI API密钥"
            return result
        
        # 尝试调用一个简单的API来验证连接
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # 使用一个轻量级的API调用来测试连接
            # 这里使用models.list来验证API密钥是否有效
            response = requests.get(
                f"{self.base_url}/models",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                result["success"] = True
                result["message"] = "API连接正常，可以开始生成图片"
            elif response.status_code == 401:
                result["error"] = "API密钥无效"
                result["message"] = "请检查API密钥是否正确"
            elif response.status_code == 429:
                result["error"] = "API调用频率超限"
                result["message"] = "请稍后再试"
            else:
                result["error"] = f"API返回状态码: {response.status_code}"
                result["message"] = "API连接异常，请检查网络或API状态"
                
        except requests.exceptions.Timeout:
            result["error"] = "连接超时"
            result["message"] = "无法连接到OpenAI API，请检查网络连接"
        except requests.exceptions.ConnectionError:
            result["error"] = "连接失败"
            result["message"] = "无法连接到OpenAI API，可能需要配置代理"
        except Exception as e:
            result["error"] = str(e)
            result["message"] = "验证API时发生未知错误"
        
        return result
    
    def prompt_for_api_key(self) -> str:
        """提示用户输入 API 密钥"""
        print("检测到 OpenAI API 密钥未配置", file=sys.stderr)
        print("请提供您的 OpenAI API 密钥：", file=sys.stderr)
        api_key = input().strip()
        
        if not api_key:
            raise ValueError("API 密钥不能为空")
        
        # 验证密钥格式
        if not api_key.startswith("sk-"):
            raise ValueError("API 密钥格式无效，应以 'sk-' 开头")
        
        # 保存密钥
        self.config.set_api_key(api_key)
        self.api_key = api_key
        
        return api_key
    
    def analyze_prompt(self, prompt: str) -> Dict[str, Any]:
        """分析用户描述，判断是否需要澄清"""
        analysis = {
            "is_clear": True,
            "questions": [],
            "suggestions": {}
        }
        
        # 检查描述长度
        if len(prompt.strip()) < 5:
            analysis["is_clear"] = False
            analysis["questions"].append("您的描述太简短，请提供更多细节。")
        
        # 检查是否包含具体元素
        specific_words = ["产品", "海报", "社交媒体", "风景", "人物", "动物", "建筑", "艺术"]
        has_specific = any(word in prompt for word in specific_words)
        
        if not has_specific and len(prompt.strip()) < 20:
            analysis["is_clear"] = False
            analysis["questions"].append("您希望生成什么类型的图片？产品展示、营销海报还是社交媒体内容？")
        
        # 检查风格描述
        style_words = ["写实", "卡通", "扁平", "水彩", "油画", "像素", "3D", "动漫"]
        has_style = any(word in prompt for word in style_words)
        
        if not has_style:
            analysis["suggestions"]["style"] = "您对风格有什么要求？写实、卡通、扁平化还是其他？"
        
        return analysis
    
    def select_best_model(
        self,
        prompt: str,
        num_images: int = 1,
        size: str = None,
        quality: str = None,
        speed_priority: bool = False
    ) -> Dict[str, Any]:
        """智能选择最佳图片生成模型
        
        根据用户需求自动选择最合适的DALL·E模型和参数。
        
        Args:
            prompt: 图片描述
            num_images: 需要生成的图片数量
            size: 期望的图片尺寸
            quality: 期望的图片质量
            speed_priority: 是否优先考虑速度
        
        Returns:
            dict: 包含推荐的模型和参数
                - model: 推荐的模型
                - size: 推荐的尺寸
                - quality: 推荐的质量
                - style: 推荐的风格
                - reason: 选择原因
        """
        recommendation = {
            "model": "dall-e-3",
            "size": "1024x1024",
            "quality": "standard",
            "style": "vivid",
            "reason": ""
        }
        
        reasons = []
        
        # 规则1: 批量生成必须使用 DALL·E 2
        if num_images > 1:
            recommendation["model"] = "dall-e-2"
            recommendation["size"] = "1024x1024"
            recommendation["quality"] = "standard"
            recommendation["style"] = None  # DALL·E 2 不支持 style
            reasons.append(f"需要生成{num_images}张图片，DALL·E 2支持批量生成")
            
            # 根据尺寸调整
            if size and size in ["256x256", "512x512"]:
                recommendation["size"] = size
                reasons.append(f"使用指定尺寸: {size}")
            else:
                recommendation["size"] = "1024x1024"
                reasons.append("使用默认尺寸: 1024x1024")
            
            recommendation["reason"] = "；".join(reasons)
            return recommendation
        
        # 规则2: 速度优先模式
        if speed_priority:
            recommendation["model"] = "dall-e-2"
            recommendation["size"] = "512x512"
            recommendation["quality"] = "standard"
            recommendation["style"] = None
            reasons.append("速度优先模式，使用DALL·E 2快速生成")
            reasons.append("使用较小尺寸(512x512)加快生成速度")
            recommendation["reason"] = "；".join(reasons)
            return recommendation
        
        # 规则3: 大尺寸需求
        if size in ["1792x1024", "1024x1792"]:
            recommendation["model"] = "dall-e-3"
            recommendation["size"] = size
            reasons.append(f"需要大尺寸图片({size})，DALL·E 3支持宽屏/竖屏格式")
        
        # 规则4: 高质量需求
        if quality == "hd":
            recommendation["model"] = "dall-e-3"
            recommendation["quality"] = "hd"
            reasons.append("需要高质量(HD)图片，DALL·E 3支持HD模式")
        
        # 规则5: 分析描述复杂度
        complex_indicators = [
            "细节", "精细", "复杂", "写实", "摄影", "真实", "高清",
            "产品展示", "营销", "专业", "商业", "广告"
        ]
        is_complex = any(indicator in prompt for indicator in complex_indicators)
        
        if is_complex:
            recommendation["model"] = "dall-e-3"
            reasons.append("描述包含复杂/高质量要求的关键词")
        
        # 规则6: 风格需求
        style_keywords = {
            "vivid": ["鲜艳", "生动", "彩色", "活力", "明亮"],
            "natural": ["自然", "柔和", "真实", "朴素", "淡雅"]
        }
        
        detected_style = None
        for style, keywords in style_keywords.items():
            if any(kw in prompt for kw in keywords):
                detected_style = style
                break
        
        if detected_style:
            recommendation["style"] = detected_style
            reasons.append(f"检测到风格偏好: {detected_style}")
        
        # 规则7: 默认选择逻辑
        if not reasons:
            recommendation["model"] = "dall-e-3"
            recommendation["size"] = "1024x1024"
            recommendation["quality"] = "standard"
            recommendation["style"] = "vivid"
            reasons.append("默认使用DALL·E 3，平衡质量和速度")
        
        # 确保DALL·E 2不使用不支持的参数
        if recommendation["model"] == "dall-e-2":
            recommendation["style"] = None
            if recommendation["size"] not in ["256x256", "512x512", "1024x1024"]:
                recommendation["size"] = "1024x1024"
                reasons.append("DALL·E 2最大支持1024x1024尺寸")
        
        recommendation["reason"] = "；".join(reasons)
        return recommendation
    
    def generate_image(
        self,
        prompt: str,
        model: str = "dall-e-3",
        size: str = "1024x1024",
        quality: str = "standard",
        style: str = "vivid",
        n: int = 1
    ) -> List[str]:
        """生成图片"""
        if not self.check_api_key():
            self.prompt_for_api_key()
        
        # 构建请求
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": model,
            "prompt": prompt,
            "size": size,
            "n": n
        }
        
        # DALL·E 3 特有参数
        if model == "dall-e-3":
            data["quality"] = quality
            data["style"] = style
        
        # 发送请求
        try:
            response = requests.post(
                f"{self.base_url}/images/generations",
                headers=headers,
                json=data,
                timeout=60
            )
            response.raise_for_status()
            
            result = response.json()
            
            # 提取图片 URL
            image_urls = [item["url"] for item in result["data"]]
            
            return image_urls
            
        except requests.exceptions.RequestException as e:
            error_msg = f"API 调用失败: {str(e)}"
            
            # 尝试解析错误信息
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    if "error" in error_data:
                        error_msg = f"API 错误: {error_data['error'].get('message', str(e))}"
                except Exception:
                    pass
            
            raise Exception(error_msg)
    
    def download_image(self, url: str, output_dir: str, filename: str = None) -> str:
        """下载图片到本地"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        if not filename:
            # 生成基于时间戳的文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"generated_{timestamp}.png"
        
        filepath = output_path / filename
        
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            return str(filepath)
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"图片下载失败: {str(e)}")


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="使用 OpenAI DALL·E 模型生成图片",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  dalle_generator.py "一只可爱的橘猫在阳光下打盹"
  dalle_generator.py "未来城市夜景" --model dall-e-3 --size 1024x1024
  dalle_generator.py --batch prompts.txt --model dall-e-3
        """
    )
    
    parser.add_argument(
        "prompt",
        nargs="?",
        help="图片描述文本"
    )
    
    parser.add_argument(
        "--model",
        choices=["dall-e-2", "dall-e-3"],
        default="dall-e-3",
        help="模型选择 (默认: dall-e-3)"
    )
    
    parser.add_argument(
        "--size",
        choices=["256x256", "512x512", "1024x1024", "1792x1024", "1024x1792"],
        default="1024x1024",
        help="图片尺寸 (默认: 1024x1024)"
    )
    
    parser.add_argument(
        "--quality",
        choices=["standard", "hd"],
        default="standard",
        help="图片质量，仅 DALL·E 3 (默认: standard)"
    )
    
    parser.add_argument(
        "--style",
        choices=["vivid", "natural"],
        default="vivid",
        help="图片风格，仅 DALL·E 3 (默认: vivid)"
    )
    
    parser.add_argument(
        "--number", "-n",
        type=int,
        default=1,
        help="生成数量 (DALL·E 2: 1-10, DALL·E 3: 1)"
    )
    
    parser.add_argument(
        "--batch",
        nargs="+",
        help="批量生成，从文件或命令行读取提示词"
    )
    
    parser.add_argument(
        "--output", "-o",
        default="./generated_images",
        help="输出目录 (默认: ./generated_images)"
    )
    
    parser.add_argument(
        "--format",
        choices=["png", "jpeg", "webp"],
        default="png",
        help="输出格式 (默认: png)"
    )
    
    parser.add_argument(
        "--no-download",
        action="store_true",
        help="不下载图片，只显示 URL"
    )
    
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="交互模式，描述不明确时提问澄清"
    )
    
    parser.add_argument(
        "--check",
        action="store_true",
        help="仅检查API连接是否可用，不生成图片"
    )
    
    parser.add_argument(
        "--auto",
        action="store_true",
        help="自动选择最佳模型和参数（智能模式）"
    )
    
    parser.add_argument(
        "--speed",
        action="store_true",
        help="速度优先模式，使用较小尺寸加快生成"
    )
    
    return parser.parse_args()


def main():
    """主函数"""
    args = parse_args()
    
    # 初始化配置和生成器
    config = DalleConfig()
    generator = DalleGenerator(config)
    
    # 第一步：检查 API 密钥是否存在
    if not generator.check_api_key():
        try:
            generator.prompt_for_api_key()
        except ValueError as e:
            print(f"错误: {e}", file=sys.stderr)
            sys.exit(1)
    
    # 第二步：验证 API 连接是否可用
    print("正在验证API连接...", file=sys.stderr)
    verification = generator.verify_api_connection()
    
    if not verification["success"]:
        print(f"错误: {verification['error']}", file=sys.stderr)
        print(f"提示: {verification['message']}", file=sys.stderr)
        sys.exit(1)
    
    print(f"✓ {verification['message']}", file=sys.stderr)
    
    # 如果只是检查API，直接返回
    if args.check:
        print("API检查完成，连接正常", file=sys.stderr)
        return
    
    # 第三步：API验证成功，现在询问用户需求或处理已有描述
    if args.interactive and not args.prompt and not args.batch:
        # 交互模式下，如果没有提供描述，询问用户需求
        print("\nAPI已就绪，请告诉我您的图片需求：", file=sys.stderr)
        print("例如：'一只可爱的橘猫在阳光下打盹'", file=sys.stderr)
        prompt = input("> ").strip()
        
        if not prompt:
            print("错误: 未提供图片描述", file=sys.stderr)
            sys.exit(1)
        
        args.prompt = prompt
    
    # 处理批量生成
    if args.batch:
        prompts = []
        for item in args.batch:
            if os.path.isfile(item):
                # 从文件读取
                with open(item, 'r', encoding='utf-8') as f:
                    prompts.extend([line.strip() for line in f if line.strip()])
            else:
                prompts.append(item)
        
        if not prompts:
            print("错误: 没有找到有效的提示词", file=sys.stderr)
            sys.exit(1)
        
        # 批量生成
        total = len(prompts)
        success = 0
        failed = 0
        
        for i, prompt in enumerate(prompts, 1):
            print(f"正在生成第 {i}/{total} 张: {prompt[:50]}...", file=sys.stderr)
            
            try:
                # 交互模式下检查描述
                if args.interactive:
                    analysis = generator.analyze_prompt(prompt)
                    if not analysis["is_clear"]:
                        print(f"警告: 描述可能不够清晰 - {prompt}", file=sys.stderr)
                        for question in analysis["questions"]:
                            print(f"  - {question}", file=sys.stderr)
                
                # 生成图片
                image_urls = generator.generate_image(
                    prompt=prompt,
                    model=args.model,
                    size=args.size,
                    quality=args.quality,
                    style=args.style,
                    n=args.number
                )
                
                # 下载图片
                if not args.no_download:
                    for j, url in enumerate(image_urls):
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"batch_{i}_{j+1}_{timestamp}.{args.format}"
                        filepath = generator.download_image(url, args.output, filename)
                        print(f"已保存: {filepath}")
                
                success += 1
                
            except Exception as e:
                print(f"生成失败: {e}", file=sys.stderr)
                failed += 1
        
        print(f"\n批量生成完成: 成功 {success}, 失败 {failed}", file=sys.stderr)
        return
    
    # 单张图片生成
    if not args.prompt:
        print("错误: 请提供图片描述", file=sys.stderr)
        sys.exit(1)
    
    # 交互模式下检查描述
    if args.interactive:
        analysis = generator.analyze_prompt(args.prompt)
        if not analysis["is_clear"]:
            print("您的描述可能不够清晰，建议补充更多信息：", file=sys.stderr)
            for question in analysis["questions"]:
                print(f"  - {question}", file=sys.stderr)
            
            # 在交互模式下，可以在这里提示用户
            # 但为了简化，我们继续生成
    
    try:
        # 自动模式：智能选择模型和参数
        if args.auto or args.speed:
            print("正在分析需求并选择最佳模型...", file=sys.stderr)
            
            recommendation = generator.select_best_model(
                prompt=args.prompt,
                num_images=args.number,
                size=args.size,
                quality=args.quality,
                speed_priority=args.speed
            )
            
            # 使用推荐的参数
            model = recommendation["model"]
            size = recommendation["size"]
            quality = recommendation["quality"]
            style = recommendation["style"]
            
            print(f"已选择模型: {model}", file=sys.stderr)
            print(f"尺寸: {size}", file=sys.stderr)
            if quality:
                print(f"质量: {quality}", file=sys.stderr)
            if style:
                print(f"风格: {style}", file=sys.stderr)
            print(f"选择原因: {recommendation['reason']}", file=sys.stderr)
            print("", file=sys.stderr)
        else:
            # 使用用户指定的参数
            model = args.model
            size = args.size
            quality = args.quality
            style = args.style
        
        # 生成图片
        print(f"正在生成图片: {args.prompt[:50]}...", file=sys.stderr)
        
        image_urls = generator.generate_image(
            prompt=args.prompt,
            model=model,
            size=size,
            quality=quality,
            style=style,
            n=args.number
        )
        
        # 输出结果
        if args.no_download:
            # 只显示 URL
            for url in image_urls:
                print(url)
        else:
            # 下载图片
            for i, url in enumerate(image_urls):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                if args.number > 1:
                    filename = f"generated_{i+1}_{timestamp}.{args.format}"
                else:
                    filename = f"generated_{timestamp}.{args.format}"
                
                filepath = generator.download_image(url, args.output, filename)
                print(f"已保存: {filepath}")
        
        print("图片生成完成!", file=sys.stderr)
        
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()