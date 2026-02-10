# duoduo_article_gen
# 图片自动获取与插入功能使用说明

## 功能概述

本功能可以在生成文章后，自动从免费图片站获取图片或调用免费文生图 API 生成图片，并智能插入到文章正文中。

## 支持的图片源

### 1. 免费图片站（推荐）

- **Pexels**：https://www.pexels.com/api/
  - 免费，需要注册获取 API key
  - 每日请求限制：200 次/小时
  
- **Unsplash**：https://unsplash.com/developers
  - 免费，需要注册获取 API key
  - 请求限制：50 次/小时
  
- **Pixabay**：https://pixabay.com/api/docs/
  - 免费，需要注册获取 API key
  - 请求限制：5000 次/小时

### 2. AI 文生图（可选）

- **Hugging Face Inference API**：https://huggingface.co/settings/tokens
  - 部分模型免费，需要注册获取 API token
  - 注意：生成的图片需要保存到本地或上传到图床才能使用

## 配置步骤

### 1. 安装依赖

```bash
pip install requests
```

### 2. 获取 API Keys

选择一个或多个图片站，注册并获取 API key：

- **Pexels**：访问 https://www.pexels.com/api/ 注册并创建应用
- **Unsplash**：访问 https://unsplash.com/developers 创建应用
- **Pixabay**：访问 https://pixabay.com/api/docs/ 注册并获取 key

### 3. 配置 API Keys

有两种方式配置：

#### 方式一：环境变量（推荐）

```bash
export PEXELS_API_KEY="your_pexels_api_key"
export UNSPLASH_ACCESS_KEY="your_unsplash_access_key"
export PIXABAY_API_KEY="your_pixabay_api_key"
export HUGGINGFACE_API_KEY="your_huggingface_token"
```

#### 方式二：直接修改 config.py

在 `config.py` 中直接设置：

```python
PEXELS_API_KEY = "your_pexels_api_key"
UNSPLASH_ACCESS_KEY = "your_unsplash_access_key"
PIXABAY_API_KEY = "your_pixabay_api_key"
HUGGINGFACE_API_KEY = "your_huggingface_token"
```

### 4. 配置功能开关

在 `config.py` 中可以调整以下配置：

```python
ENABLE_IMAGE_INSERTION = True  # 是否启用图片插入功能
IMAGE_COUNT = 2  # 每篇文章插入的图片数量（建议 1-3 张）
USE_AI_IMAGE_GENERATION = False  # 是否优先使用 AI 生成图片
USE_SMART_INSERTION = True  # 是否使用 LLM 智能判断插入位置
```

## 工作原理

1. **关键词提取**：使用 LLM 从文章标题和内容中提取适合搜索图片的英文关键词
2. **图片获取**：按优先级依次尝试各个图片源，直到成功获取图片
3. **图片插入**：
   - 如果启用 `USE_SMART_INSERTION`：使用 LLM 分析文章结构，智能判断最佳插入位置
   - 否则：在段落之间均匀分布插入图片

## 使用示例

运行文章生成脚本后，会自动执行图片获取和插入：

```bash
python crawl_article.py
```

输出示例：
```
🖼️ 开始获取图片（数量: 2）...
  🔍 搜索关键词: technology artificial intelligence
  ✅ 从 Pexels 获取图片: https://images.pexels.com/photos/...
  ✅ 成功获取 2 张图片
  ✅ 图片已插入到正文
✅ Saved: output/20260210_022524.md
```

## 注意事项

1. **API 限制**：各图片站都有请求频率限制，建议至少配置一个 API key
2. **图片版权**：使用免费图片站时，注意遵守各站点的使用条款
3. **网络连接**：需要稳定的网络连接才能访问图片站 API
4. **AI 生成图片**：如果使用 Hugging Face 生成图片，需要额外实现图片保存和 URL 获取逻辑（当前版本暂未完全实现）

## 故障排除

### 问题：无法获取图片

- 检查 API key 是否正确配置
- 检查网络连接是否正常
- 查看控制台输出的错误信息

### 问题：图片插入位置不合适

- 尝试调整 `USE_SMART_INSERTION` 设置
- 调整 `IMAGE_COUNT` 控制图片数量

### 问题：API 请求超限

- 减少 `IMAGE_COUNT` 设置
- 配置多个图片源，系统会自动切换

