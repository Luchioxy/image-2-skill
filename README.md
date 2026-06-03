# image-2-skill

**图片生成服务技能 / Image Generation Service Skill**

> 中文 | [English](#english)

---

## 中文

### 简介

image-2-skill 是一个基于 OpenAI DALL·E 模型的图片生成服务技能，支持 DALL·E 2 和 DALL·E 3。

**核心定位**：本技能是一个可被其他 Agent/Skill 调用的图片生成服务。

```
其他 Agent/Skill 需要图片 → 调用本技能 → 返回图片
```

### 核心流程

```
1. 检查 API 密钥 → 没有 → 要求用户提供
2. 验证 API 连接 → 失败 → 提示错误
3. 需求不清晰 → 向用户澄清
4. 生成图片 → 返回结果
```

### 目录结构

```
image-2-skill/
├── README.md                   # 本文档
├── SKILL.md                    # 技能定义文件
├── .gitignore
├── scripts/
│   ├── dalle_generator.py      # 核心生成脚本
│   ├── config_manager.py       # 配置管理（密钥加密）
│   └── image_downloader.py     # 图片下载模块
└── examples/
    └── usage_examples.md       # 使用示例
```

### 快速开始

**1. 安装依赖**

```bash
pip install requests cryptography
```

**2. 配置 API 密钥**

```bash
python scripts/config_manager.py set-key "sk-your-api-key"
```

或使用环境变量：

```bash
export OPENAI_API_KEY="sk-your-api-key"
```

**3. 验证连接**

```bash
python scripts/dalle_generator.py --check
```

**4. 生成图片**

```bash
python scripts/dalle_generator.py "一只可爱的橘猫在阳光下打盹"
```

### Agent 兼容性

| Agent | 支持状态 | 调用方式 |
|-------|---------|----------|
| **Claude Code** | ✅ 完全支持 | Bash 命令行调用 |
| **WorkBuddy** | ✅ 完全支持 | Skill 工具调用 |
| **Cursor** | ✅ 完全支持 | 终端命令调用 |
| **Windsurf** | ✅ 完全支持 | 终端命令调用 |
| **ChatGPT (Code Interpreter)** | ✅ 支持 | Python 代码执行 |
| **GitHub Copilot** | ✅ 支持 | 终端命令调用 |
| **Cline** | ✅ 支持 | 命令行调用 |
| **Aider** | ✅ 支持 | 命令行调用 |
| **任意支持命令行的 Agent** | ✅ 支持 | 命令行调用 |

> **原理**：本技能基于标准 Python 脚本和命令行接口，任何能执行 shell 命令的 Agent 均可调用。

### 被其他 Skill 调用

**方式 1：命令行**

```bash
python3 <SKILL_DIR>/scripts/dalle_generator.py "图片描述" --model dall-e-3 --size 1024x1024
```

**方式 2：Python 模块导入**

```python
import sys
sys.path.insert(0, "<SKILL_DIR>/scripts")

from dalle_generator import DalleGenerator, DalleConfig

config = DalleConfig()
generator = DalleGenerator(config)

if not generator.check_api_key():
    generator.prompt_for_api_key()

urls = generator.generate_image("一只可爱的猫", model="dall-e-3")
```

**方式 3：子进程调用**

```python
import subprocess

def generate_image(prompt, model="dall-e-3"):
    cmd = ["python3", "<SKILL_DIR>/scripts/dalle_generator.py", prompt, "--model", model, "--no-download"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout.strip().split('\n')
```

### 参数说明

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `prompt` | — | 文本描述 |
| `--model` | `dall-e-3` | `dall-e-2` 或 `dall-e-3` |
| `--size` | `1024x1024` | `256x256`, `512x512`, `1024x1024`, `1792x1024`, `1024x1792` |
| `--quality` | `standard` | `standard` 或 `hd`（仅 DALL·E 3） |
| `--style` | `vivid` | `vivid` 或 `natural`（仅 DALL·E 3） |
| `--number` | `1` | 生成数量（DALL·E 2: 1-10） |
| `--batch` | — | 批量生成 |
| `--output` | `./generated_images` | 输出目录 |
| `--format` | `png` | `png`, `jpeg`, `webp` |
| `--check` | — | 仅检查 API 连接 |
| `--auto` | — | 智能选择模型 |
| `--speed` | — | 速度优先模式 |
| `--no-download` | — | 只输出 URL |

### 智能模型选择

| 场景 | 自动选择 |
|------|----------|
| 批量生成 | DALL·E 2 |
| 速度优先 | DALL·E 2 + 512x512 |
| 大尺寸（1792x1024） | DALL·E 3 |
| 高质量（HD） | DALL·E 3 HD |
| 复杂描述 | DALL·E 3 |

### 模型对比

| 特性 | DALL·E 2 | DALL·E 3 |
|------|----------|----------|
| 批量生成 | ✅ 1-10 张 | ❌ 仅 1 张 |
| 最大尺寸 | 1024x1024 | 1792x1024 |
| 质量选项 | standard | standard / hd |
| 风格选项 | 无 | vivid / natural |
| 生成速度 | 快 | 较慢 |
| 价格 | 低 | 高 |

### 安全策略

#### API 密钥安全

| 措施 | 说明 |
|------|------|
| **加密算法** | AES-256（Fernet 对称加密） |
| **密钥存储** | 加密后保存到 `~/.workbuddy/dalle_config.json` |
| **加密密钥** | 独立生成，存储在 `~/.workbuddy/.dalle_key` |
| **运行时** | 仅在内存中解密使用，不落盘明文 |
| **访问控制** | 配置文件仅当前用户可读写 |

#### 加密原理

```
用户输入 API Key
    ↓
Fernet 生成随机加密密钥（存储在 .dalle_key）
    ↓
使用 AES-256-CBC 加密 API Key
    ↓
加密后的密文保存到配置文件
    ↓
运行时：读取密文 → 解密 → 调用 API → 立即清除内存中的明文
```

> **说明**：公开加密算法不会降低安全性。安全性依赖于加密密钥的保密，而非算法本身（Kerckhoffs 原则）。

#### 内容安全

- 集成 OpenAI 内容审核 API
- 违规内容自动拦截
- 生成记录可追溯

### 错误处理

| 错误类型 | 处理方式 |
|----------|----------|
| API 密钥未配置 | 引导用户输入 |
| API 密钥无效 | 提示重新输入 |
| 网络超时 | 自动重试 3 次 |
| DALL·E 3 失败 | 降级到 DALL·E 2 |
| 内容审核拒绝 | 提示修改描述 |
| 配额超限 | 提示稍后重试 |

### 注意事项

1. **网络环境**：国内访问 OpenAI API 需要代理
2. **费用控制**：DALL·E 3 HD 约 $0.08/张
3. **内容合规**：遵守 OpenAI 使用政策
4. **图片版权**：参考 OpenAI 政策

---

<a id="english"></a>

## English

### Introduction

image-2-skill is an image generation service skill based on OpenAI DALL·E models, supporting DALL·E 2 and DALL·E 3.

**Core Positioning**: This skill is an image generation service that can be called by other Agents/Skills.

```
Other Agent/Skill needs an image → Calls this skill → Returns the image
```

### Core Flow

```
1. Check API Key → Missing → Ask user to provide
2. Verify API connection → Failed → Show error
3. Request unclear → Clarify with user
4. Generate image → Return result
```

### Project Structure

```
image-2-skill/
├── README.md                   # This file
├── SKILL.md                    # Skill definition file
├── .gitignore
├── scripts/
│   ├── dalle_generator.py      # Core generation script
│   ├── config_manager.py       # Config management (encrypted keys)
│   └── image_downloader.py     # Image download module
└── examples/
    └── usage_examples.md       # Usage examples
```

### Quick Start

**1. Install dependencies**

```bash
pip install requests cryptography
```

**2. Configure API Key**

```bash
python scripts/config_manager.py set-key "sk-your-api-key"
```

Or use environment variable:

```bash
export OPENAI_API_KEY="sk-your-api-key"
```

**3. Verify connection**

```bash
python scripts/dalle_generator.py --check
```

**4. Generate image**

```bash
python scripts/dalle_generator.py "A cute orange cat napping in the sunshine"
```

### Agent Compatibility

| Agent | Support Status | How to Call |
|-------|---------------|-------------|
| **Claude Code** | ✅ Full support | Bash command line |
| **WorkBuddy** | ✅ Full support | Skill tool invocation |
| **Cursor** | ✅ Full support | Terminal command |
| **Windsurf** | ✅ Full support | Terminal command |
| **ChatGPT (Code Interpreter)** | ✅ Supported | Python code execution |
| **GitHub Copilot** | ✅ Supported | Terminal command |
| **Cline** | ✅ Supported | Command line |
| **Aider** | ✅ Supported | Command line |
| **Any Agent with CLI access** | ✅ Supported | Command line |

> **Principle**: This skill is based on standard Python scripts and CLI interface. Any Agent that can execute shell commands can call it.

### Calling from Other Skills

**Method 1: Command Line**

```bash
python3 <SKILL_DIR>/scripts/dalle_generator.py "image description" --model dall-e-3 --size 1024x1024
```

**Method 2: Python Module Import**

```python
import sys
sys.path.insert(0, "<SKILL_DIR>/scripts")

from dalle_generator import DalleGenerator, DalleConfig

config = DalleConfig()
generator = DalleGenerator(config)

if not generator.check_api_key():
    generator.prompt_for_api_key()

urls = generator.generate_image("A cute cat", model="dall-e-3")
```

**Method 3: Subprocess**

```python
import subprocess

def generate_image(prompt, model="dall-e-3"):
    cmd = ["python3", "<SKILL_DIR>/scripts/dalle_generator.py", prompt, "--model", model, "--no-download"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout.strip().split('\n')
```

### Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `prompt` | — | Text description |
| `--model` | `dall-e-3` | `dall-e-2` or `dall-e-3` |
| `--size` | `1024x1024` | `256x256`, `512x512`, `1024x1024`, `1792x1024`, `1024x1792` |
| `--quality` | `standard` | `standard` or `hd` (DALL·E 3 only) |
| `--style` | `vivid` | `vivid` or `natural` (DALL·E 3 only) |
| `--number` | `1` | Number of images (DALL·E 2: 1-10) |
| `--batch` | — | Batch generation |
| `--output` | `./generated_images` | Output directory |
| `--format` | `png` | `png`, `jpeg`, `webp` |
| `--check` | — | Check API connection only |
| `--auto` | — | Smart model selection |
| `--speed` | — | Speed priority mode |
| `--no-download` | — | Output URL only |

### Smart Model Selection

| Scenario | Auto Selection |
|----------|---------------|
| Batch generation | DALL·E 2 |
| Speed priority | DALL·E 2 + 512x512 |
| Large size (1792x1024) | DALL·E 3 |
| High quality (HD) | DALL·E 3 HD |
| Complex description | DALL·E 3 |

### Model Comparison

| Feature | DALL·E 2 | DALL·E 3 |
|---------|----------|----------|
| Batch generation | ✅ 1-10 images | ❌ 1 only |
| Max size | 1024x1024 | 1792x1024 |
| Quality options | standard | standard / hd |
| Style options | None | vivid / natural |
| Speed | Fast | Slower |
| Price | Low | High |

### Security Policy

#### API Key Security

| Measure | Description |
|---------|-------------|
| **Encryption Algorithm** | AES-256 (Fernet symmetric encryption) |
| **Key Storage** | Encrypted in `~/.workbuddy/dalle_config.json` |
| **Encryption Key** | Independently generated, stored in `~/.workbuddy/.dalle_key` |
| **Runtime** | Decrypted only in memory, never written as plaintext |
| **Access Control** | Config files readable/writable only by current user |

#### Encryption Principle

```
User inputs API Key
    ↓
Fernet generates random encryption key (stored in .dalle_key)
    ↓
Encrypt API Key using AES-256-CBC
    ↓
Save encrypted ciphertext to config file
    ↓
Runtime: Read ciphertext → Decrypt → Call API → Clear plaintext from memory
```

> **Note**: Publishing the encryption algorithm does not reduce security. Security depends on keeping the encryption key secret, not the algorithm itself (Kerckhoffs's principle).

#### Content Safety

- Integrated OpenAI Content Moderation API
- Automatic blocking of violating content
- Traceable generation records

### Error Handling

| Error Type | Handling |
|------------|----------|
| API key not configured | Guide user to input |
| Invalid API key | Prompt to re-enter |
| Network timeout | Auto retry 3 times |
| DALL·E 3 failure | Fall back to DALL·E 2 |
| Content moderation rejected | Prompt to modify description |
| Rate limit exceeded | Prompt to try later |

### Notes

1. **Network**: Accessing OpenAI API from China requires a proxy
2. **Cost**: DALL·E 3 HD costs ~$0.08 per image
3. **Compliance**: Follow OpenAI usage policies
4. **Copyright**: Refer to OpenAI policies for image rights

---

**Version**: v1.0 | **Date**: 2026-06-03 | **Author**: WorkBuddy AI Assistant
