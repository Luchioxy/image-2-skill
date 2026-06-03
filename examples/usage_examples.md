# 文生图技能使用示例

## 重要：正确的使用流程

**技能遵循以下流程：**
1. **先检查接口是否可用**（API密钥验证 + 连接测试）
2. **确认能生成后再询问客户需求**
3. **根据需求生成图片**

### 检查API连接

```bash
# 检查API连接是否可用（推荐首次使用前执行）
python3 ~/.workbuddy/skills/dalle-image-generation/scripts/dalle_generator.py --check
```

**输出示例：**
- 成功：`✓ API连接正常，可以开始生成图片`
- 失败：`错误: API密钥无效` 或 `错误: 连接超时`

## 基础用法

### 1. 生成单张图片

```bash
# 生成一只可爱的橘猫
python3 ~/.workbuddy/skills/dalle-image-generation/scripts/dalle_generator.py "一只可爱的橘猫在阳光下打盹"

# 生成产品展示图
python3 ~/.workbuddy/skills/dalle-image-generation/scripts/dalle_generator.py "一款现代设计的智能手表，黑色表带，白色表盘"

# 生成营销海报
python3 ~/.workbuddy/skills/dalle-image-generation/scripts/dalle_generator.py "夏日促销海报，清凉风格，包含冰淇淋和海滩元素"
```

### 2. 指定模型和参数

```bash
# 使用 DALL·E 3 模型
python3 ~/.workbuddy/skills/dalle-image-generation/scripts/dalle_generator.py "未来城市夜景" --model dall-e-3

# 指定图片尺寸
python3 ~/.workbuddy/skills/dalle-image-generation/scripts/dalle_generator.py "产品展示图" --size 1024x1024

# 使用高质量模式
python3 ~/.workbuddy/skills/dalle-image-generation/scripts/dalle_generator.py "艺术画作" --quality hd --style natural
```

### 3. 批量生成

```bash
# 从文件读取提示词批量生成
python3 ~/.workbuddy/skills/dalle-image-generation/scripts/dalle_generator.py --batch prompts.txt

# 命令行多提示词批量生成
python3 ~/.workbuddy/skills/dalle-image-generation/scripts/dalle_generator.py --batch "提示词1" "提示词2" "提示词3"
```

## 高级用法

### 1. 自定义输出

```bash
# 指定输出目录
python3 ~/.workbuddy/skills/dalle-image-generation/scripts/dalle_generator.py "风景照" --output ./my_images

# 指定输出格式
python3 ~/.workbuddy/skills/dalle-image-generation/scripts/dalle_generator.py "产品图" --format jpeg

# 生成多张图片
python3 ~/.workbuddy/skills/dalle-image-generation/scripts/dalle_generator.py "抽象艺术" --model dall-e-2 --number 4
```

### 2. 交互模式

```bash
# 启用交互模式，描述不明确时会提问澄清
python3 ~/.workbuddy/skills/dalle-image-generation/scripts/dalle_generator.py "图片" --interactive
```

### 3. 智能模型选择

```bash
# 自动选择最佳模型（推荐）
python3 ~/.workbuddy/skills/dalle-image-generation/scripts/dalle_generator.py "产品展示图" --auto

# 速度优先模式
python3 ~/.workbuddy/skills/dalle-image-generation/scripts/dalle_generator.py "快速草图" --speed

# 批量生成自动选择DALL·E 2
python3 ~/.workbuddy/skills/dalle-image-generation/scripts/dalle_generator.py --batch prompts.txt --auto
```

**自动选择逻辑：**
- 需要批量生成 → DALL·E 2
- 需要大尺寸(1792x1024) → DALL·E 3
- 需要高质量(HD) → DALL·E 3
- 描述复杂(产品展示、写实) → DALL·E 3
- 速度优先 → DALL·E 2 + 小尺寸

### 3. 只获取 URL 不下载

```bash
# 只显示图片 URL，不下载到本地
python3 ~/.workbuddy/skills/dalle-image-generation/scripts/dalle_generator.py "描述" --no-download
```

## 配置管理

### 1. 设置 API 密钥

```bash
# 设置 API 密钥（加密存储）
python3 ~/.workbuddy/skills/dalle-image-generation/scripts/config_manager.py set-key "sk-your-api-key-here"

# 查看当前配置
python3 ~/.workbuddy/skills/dalle-image-generation/scripts/config_manager.py show

# 验证 API 密钥格式
python3 ~/.workbuddy/skills/dalle-image-generation/scripts/config_manager.py validate "sk-your-api-key-here"
```

### 2. 图片管理

```bash
# 下载单张图片
python3 ~/.workbuddy/skills/dalle-image-generation/scripts/image_downloader.py download "https://example.com/image.png"

# 批量下载图片
python3 ~/.workbuddy/skills/dalle-image-generation/scripts/image_downloader.py batch "https://example.com/img1.png" "https://example.com/img2.png"

# 列出已下载的图片
python3 ~/.workbuddy/skills/dalle-image-generation/scripts/image_downloader.py list

# 清理旧图片（保留30天）
python3 ~/.workbuddy/skills/dalle-image-generation/scripts/image_downloader.py clean --days 30
```

## 实际场景示例

### 场景1：电商产品图

```bash
# 生成产品主图
python3 ~/.workbuddy/skills/dalle-image-generation/scripts/dalle_generator.py \
  "现代简约风格的无线蓝牙耳机，白色，放在纯白背景上，产品摄影风格" \
  --model dall-e-3 \
  --size 1024x1024 \
  --quality hd

# 生成产品使用场景图
python3 ~/.workbuddy/skills/dalle-image-generation/scripts/dalle_generator.py \
  "年轻女性在咖啡厅使用无线蓝牙耳机听音乐，自然光线，真实场景" \
  --model dall-e-3 \
  --size 1792x1024
```

### 场景2：社交媒体内容

```bash
# 生成微信公众号封面
python3 ~/.workbuddy/skills/dalle-image-generation/scripts/dalle_generator.py \
  "科技感十足的AI人工智能主题封面，蓝色调，未来感" \
  --model dall-e-3 \
  --size 1024x1024

# 生成小红书配图
python3 ~/.workbuddy/skills/dalle-image-generation/scripts/dalle_generator.py \
  "温馨的家居场景，原木风格，绿植装饰，适合家居分享" \
  --model dall-e-3 \
  --size 1024x1024
```

### 场景3：营销海报

```bash
# 生成促销海报
python3 ~/.workbuddy/skills/dalle-image-generation/scripts/dalle_generator.py \
  "双11购物节促销海报，红色喜庆风格，包含购物车和礼物元素" \
  --model dall-e-3 \
  --size 1024x1792

# 生成活动邀请函
python3 ~/.workbuddy/skills/dalle-image-generation/scripts/dalle_generator.py \
  "公司年会邀请函，金色奢华风格，包含香槟和彩带元素" \
  --model dall-e-3 \
  --size 1024x1024
```

### 场景4：创意设计

```bash
# 生成Logo概念图
python3 ~/.workbuddy/skills/dalle-image-generation/scripts/dalle_generator.py \
  "现代科技公司Logo设计，简约字母组合，蓝绿色调" \
  --model dall-e-3 \
  --size 1024x1024

# 生成插画
python3 ~/.workbuddy/skills/dalle-image-generation/scripts/dalle_generator.py \
  "可爱卡通风格的小动物插画，适合儿童绘本" \
  --model dall-e-3 \
  --size 1024x1024
```

## 提示词技巧

### 1. 描述要具体

**不好的描述：**
```bash
python3 ~/.workbuddy/skills/dalle-image-generation/scripts/dalle_generator.py "猫"
```

**好的描述：**
```bash
python3 ~/.workbuddy/skills/dalle-image-generation/scripts/dalle_generator.py \
  "一只橘色的虎斑猫，坐在窗台上晒太阳，窗外是绿色的花园，温暖的光线，写实摄影风格"
```

### 2. 包含风格信息

```bash
# 写实风格
python3 ~/.workbuddy/skills/dalle-image-generation/scripts/dalle_generator.py \
  "城市街景，写实摄影风格，高清细节"

# 卡通风格
python3 ~/.workbuddy/skills/dalle-image-generation/scripts/dalle_generator.py \
  "可爱的卡通动物，扁平化设计风格，明亮色彩"

# 水彩风格
python3 ~/.workbuddy/skills/dalle-image-generation/scripts/dalle_generator.py \
  "山水风景，水彩画风格，柔和色调"
```

### 3. 指定构图和视角

```bash
# 俯视视角
python3 ~/.workbuddy/skills/dalle-image-generation/scripts/dalle_generator.py \
  "办公桌面，俯视视角，包含笔记本电脑和咖啡杯"

# 特写镜头
python3 ~/.workbuddy/skills/dalle-image-generation/scripts/dalle_generator.py \
  "手表细节特写，展示表盘和表带纹理"

# 广角风景
python3 ~/.workbuddy/skills/dalle-image-generation/scripts/dalle_generator.py \
  "壮丽的山脉全景，广角镜头，日出时分"
```

## 错误处理

### 常见错误及解决方法

1. **API 密钥错误**
   ```
   错误: API 密钥无效
   解决: 检查 API 密钥是否正确，或重新设置
   ```

2. **网络连接问题**
   ```
   错误: 连接超时
   解决: 检查网络连接，或配置代理
   ```

3. **内容审核拒绝**
   ```
   错误: 内容不符合政策
   解决: 修改提示词，避免违规内容
   ```

4. **参数错误**
   ```
   错误: 无效的尺寸参数
   解决: 使用正确的尺寸选项
   ```

## 性能优化建议

1. **批量生成时使用并发**
   - 可以同时生成多张图片
   - 注意 API 调用限制

2. **合理选择模型**
   - DALL·E 2：速度快，价格低，适合批量生成
   - DALL·E 3：质量高，细节丰富，适合重要图片

3. **优化提示词**
   - 清晰具体的描述减少重新生成次数
   - 包含风格信息减少后期调整

4. **使用缓存**
   - 相同提示词使用缓存结果
   - 避免重复生成相同图片

## 故障排除

### 问题1：无法连接到 OpenAI API

```bash
# 检查网络连接
ping api.openai.com

# 如果在中国大陆，可能需要配置代理
export HTTPS_PROXY="http://your-proxy:port"
```

### 问题2：API 密钥无效

```bash
# 验证密钥格式
python3 ~/.workbuddy/skills/dalle-image-generation/scripts/config_manager.py validate "your-api-key"

# 重新设置密钥
python3 ~/.workbuddy/skills/dalle-image-generation/scripts/config_manager.py set-key "new-api-key"
```

### 问题3：图片下载失败

```bash
# 检查输出目录权限
ls -la ./generated_images

# 手动下载测试
curl -o test.png "image-url"
```

## 集成到其他技能

### 作为工具调用

```python
import subprocess
import json

def generate_image(prompt, model="dall-e-3", size="1024x1024"):
    """调用文生图技能"""
    cmd = [
        "python3",
        "~/.workbuddy/skills/dalle-image-generation/scripts/dalle_generator.py",
        prompt,
        "--model", model,
        "--size", size,
        "--no-download"  # 只获取 URL
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        return result.stdout.strip().split('\n')
    else:
        raise Exception(f"生成失败: {result.stderr}")
```

### 函数导入

```python
import sys
sys.path.insert(0, "~/.workbuddy/skills/dalle-image-generation/scripts")

from dalle_generator import DalleGenerator, DalleConfig

# 使用
config = DalleConfig()
generator = DalleGenerator(config)
image_urls = generator.generate_image("一只可爱的猫")
```

---

**文档版本**：v1.0  
**创建日期**：2026-06-03  
**最后更新**：2026-06-03