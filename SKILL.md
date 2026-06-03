---
name: 文生图生成
description: >
  DALL·E 图片生成服务技能。
  两种触发方式：
  1. 其他 skill/agent 主动调用
  2. 识别到客户需要生图时自动触发
  支持 DALL·E 2 和 DALL·E 3。
---

# 文生图生成技能

**DALL·E 图片生成服务，支持两种触发方式。**

## 触发方式

### 方式 1：Skill/Agent 主动调用

其他 skill 或 agent 在需要生成图片时，直接调用本技能，无需自行实现图片生成逻辑。

### 方式 2：识别客户需求自动触发

当系统识别到客户有生图需求时，自动调用本技能。

**识别关键词**：
- 明确意图：生成图片、创建图片、制作图片、文生图、AI 绘画、画一张、做一张图
- 场景描述：产品图、海报、宣传图、封面、插图、配图、表情包、头像、Logo
- 需求表达：帮我设计、我需要一张图、能不能出个图、图片素材

**典型场景**：
- 电商：产品展示图、详情页配图、主图
- 营销：海报、Banner、社交媒体配图、朋友圈图片
- 办公：PPT 配图、报告插图、文档配图
- 设计：Logo 概念图、UI 素材、图标
- 个人：头像、表情包、壁纸、贺卡

## 调用方式

- 命令行：直接调用 Python 脚本
- 函数导入：Python 模块直接导入
- 子进程：通过 subprocess 调用

## 核心流程

```
1. 检查 API 密钥
   ↓ 没有 → 要求用户提供
2. 验证 API 连接
   ↓ 失败 → 提示错误
3. 需求不清晰 → 向用户澄清
   ↓ 清晰
4. 生成图片 → 返回结果
```

### 步骤 1：检查 API 密钥

```bash
python3 <SKILL_DIR>/scripts/dalle_generator.py --check
```

- 如果 API 密钥未配置，提示用户："检测到 OpenAI API 密钥未配置，请提供您的 API 密钥"
- 验证密钥格式（以 `sk-` 开头）
- 保存密钥到配置文件（AES-256 加密存储）

### 步骤 2：验证 API 连接

- 调用 OpenAI API 验证连接
- 连接失败时提示：网络问题、密钥无效、配额超限等

### 步骤 3：需求澄清

当用户描述不清晰时，主动提问：

1. **场景**："您希望生成什么类型的图片？产品展示、营销海报还是社交媒体内容？"
2. **风格**："您对风格有什么要求？写实、卡通、扁平化还是其他？"
3. **尺寸**："您需要什么尺寸？正方形(1024x1024)、横版(1792x1024)还是竖版(1024x1792)？"
4. **质量**："您追求速度优先还是质量优先？"

### 步骤 4：生成图片

- 调用 DALL·E API 生成图片
- 自动下载到本地
- 返回图片路径和 URL

## 被其他 Skill 调用

### 方式 1：命令行调用

```bash
# 基础调用
python3 <SKILL_DIR>/scripts/dalle_generator.py "图片描述"

# 完整参数
python3 <SKILL_DIR>/scripts/dalle_generator.py "图片描述" \
  --model dall-e-3 \
  --size 1024x1024 \
  --quality standard \
  --style vivid \
  --output ./output \
  --format png
```

### 方式 2：Python 模块导入

```python
import sys
sys.path.insert(0, "<SKILL_DIR>/scripts")

from dalle_generator import DalleGenerator, DalleConfig

config = DalleConfig()
generator = DalleGenerator(config)

# 检查 API
if not generator.check_api_key():
    generator.prompt_for_api_key()

# 生成图片
urls = generator.generate_image("一只可爱的猫", model="dall-e-3")
for url in urls:
    filepath = generator.download_image(url, "./output")
    print(f"已保存: {filepath}")
```

### 方式 3：子进程调用

```python
import subprocess

def generate_image(prompt, model="dall-e-3", size="1024x1024"):
    cmd = [
        "python3", "<SKILL_DIR>/scripts/dalle_generator.py",
        prompt,
        "--model", model,
        "--size", size,
        "--no-download"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        return result.stdout.strip().split('\n')
    else:
        raise Exception(result.stderr)
```

## 参数说明

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `prompt` | — | 文本描述（中文或英文） |
| `--model` | `dall-e-3` | `dall-e-2` 或 `dall-e-3` |
| `--size` | `1024x1024` | `256x256`, `512x512`, `1024x1024`, `1792x1024`, `1024x1792` |
| `--quality` | `standard` | `standard` 或 `hd`（仅 DALL·E 3） |
| `--style` | `vivid` | `vivid` 或 `natural`（仅 DALL·E 3） |
| `--number` | `1` | 生成数量（DALL·E 2: 1-10，DALL·E 3: 1） |
| `--batch` | — | 批量生成，传入文件路径或多个提示词 |
| `--output` | `./generated_images` | 输出目录 |
| `--format` | `png` | `png`, `jpeg`, `webp` |
| `--check` | — | 仅检查 API 连接，不生成图片 |
| `--auto` | — | 智能选择模型和参数 |
| `--speed` | — | 速度优先模式（DALL·E 2 + 小尺寸） |
| `--no-download` | — | 只输出 URL，不下载 |

## 智能模型选择（--auto）

启用后自动根据需求选择最佳参数：

- **批量生成** → DALL·E 2（支持 1-10 张）
- **速度优先（--speed）** → DALL·E 2 + 512x512
- **大尺寸（1792x1024）** → DALL·E 3
- **高质量（--quality hd）** → DALL·E 3 HD
- **复杂描述**（含"写实"、"产品展示"等）→ DALL·E 3
- **风格检测**（"鲜艳"→vivid，"自然"→natural）

## 模型对比

| 特性 | DALL·E 2 | DALL·E 3 |
|------|----------|----------|
| 批量生成 | ✅ 1-10 张 | ❌ 仅 1 张 |
| 最大尺寸 | 1024x1024 | 1792x1024 |
| 质量选项 | standard | standard / hd |
| 风格选项 | 无 | vivid / natural |
| 生成速度 | 快 | 较慢 |
| 价格 | 低 | 高 |

## 错误处理

| 错误类型 | 处理方式 |
|----------|----------|
| API 密钥未配置 | 引导用户输入 |
| API 密钥无效 | 提示重新输入 |
| 网络超时 | 自动重试 3 次 |
| DALL·E 3 失败 | 降级到 DALL·E 2 |
| 内容审核拒绝 | 提示用户修改描述 |
| 配额超限 | 提示稍后重试 |

## 配置文件

位置：`~/.image-2-skill/config.json`

```json
{
  "openai_api_key_encrypted": "...",
  "default_model": "dall-e-3",
  "default_size": "1024x1024",
  "default_quality": "standard",
  "default_style": "vivid",
  "auto_download": true,
  "download_directory": "./generated_images",
  "max_retries": 3,
  "timeout": 60
}
```

## 环境要求

- Python 3.7+
- 依赖：`requests`, `cryptography`
- OpenAI API 密钥
- 网络连接（国内可能需要代理）

## 注意事项

1. **API 密钥安全**：不要泄露给他人，使用加密存储
2. **内容合规**：遵守 OpenAI 使用政策
3. **费用控制**：DALL·E 3 HD 约 $0.08/张
4. **图片版权**：参考 OpenAI 政策

---

**版本**：v1.0 | **日期**：2026-06-03 | **作者**：WorkBuddy AI Assistant
