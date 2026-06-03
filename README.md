# WorkBuddy 文生图技能

**图片生成服务技能 — 供其他 skill 和 agent 调用**

基于 OpenAI DALL·E 模型，支持 DALL·E 2 和 DALL·E 3。

## 定位

本技能是一个**图片生成服务**，不直接面对终端用户，而是：

```
其他 skill/agent 需要图片 → 调用本技能 → 返回图片
```

其他 skill 无需自己实现图片生成逻辑，直接调用本技能即可。

## 核心流程

```
1. 检查 API 密钥 → 没有 → 要求用户提供
2. 验证 API 连接 → 失败 → 提示错误
3. 需求不清晰 → 向用户澄清
4. 生成图片 → 返回结果给调用方
```

## 目录结构

```
image-2 skill/
├── README.md                   # 本文档
├── SKILL.md                    # WorkBuddy 技能定义（核心）
├── .gitignore
├── 文生图技能设计文档_v2.md     # 详细设计参考
├── GitHub推送指南.md            # 部署指南
├── scripts/
│   ├── dalle_generator.py      # 核心生成脚本（入口）
│   ├── config_manager.py       # 配置管理（密钥加密存储）
│   └── image_downloader.py     # 图片下载模块
└── examples/
    └── usage_examples.md       # 使用示例
```

## 快速开始

### 1. 安装依赖

```bash
pip install requests cryptography
```

### 2. 配置 API 密钥

```bash
# 方式一：命令行设置（加密存储）
python scripts/config_manager.py set-key "sk-your-api-key"

# 方式二：环境变量
export OPENAI_API_KEY="sk-your-api-key"
```

### 3. 验证连接

```bash
python scripts/dalle_generator.py --check
```

### 4. 生成图片

```bash
python scripts/dalle_generator.py "一只可爱的橘猫在阳光下打盹"
```

## 被其他 Skill 调用

### 方式 1：命令行调用

```bash
python3 <SKILL_DIR>/scripts/dalle_generator.py "图片描述" --model dall-e-3 --size 1024x1024
```

### 方式 2：Python 模块导入

```python
import sys
sys.path.insert(0, "<SKILL_DIR>/scripts")

from dalle_generator import DalleGenerator, DalleConfig

config = DalleConfig()
generator = DalleGenerator(config)

if not generator.check_api_key():
    generator.prompt_for_api_key()

urls = generator.generate_image("一只可爱的猫", model="dall-e-3")
for url in urls:
    filepath = generator.download_image(url, "./output")
```

### 方式 3：子进程调用

```python
import subprocess

def generate_image(prompt, model="dall-e-3"):
    cmd = ["python3", "<SKILL_DIR>/scripts/dalle_generator.py", prompt, "--model", model, "--no-download"]
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

- **批量生成** → DALL·E 2
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

## 配置管理

```bash
# 查看当前配置
python scripts/config_manager.py show

# 设置 API 密钥
python scripts/config_manager.py set-key "sk-xxx"

# 验证密钥格式
python scripts/config_manager.py validate "sk-xxx"
```

配置文件位置：`~/.workbuddy/dalle_config.json`

## 注意事项

1. **网络环境**：国内访问 OpenAI API 可能需要代理
2. **费用控制**：DALL·E 3 HD 约 $0.08/张
3. **内容合规**：遵守 OpenAI 使用政策
4. **图片版权**：参考 OpenAI 政策

---

**版本**：v1.0 | **日期**：2026-06-03 | **作者**：WorkBuddy AI Assistant
