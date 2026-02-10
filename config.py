from openai import OpenAI
import os

# 模型与通用抓取配置
MODEL = "deepseek-chat"
TIME_WINDOW_HOURS = 48
MIN_CONTENT_LENGTH = 500

# 图片相关配置
ENABLE_IMAGE_INSERTION = True  # 是否启用图片插入功能
IMAGE_COUNT = 1  # 每篇文章插入的图片数量
USE_AI_IMAGE_GENERATION = False  # 是否优先使用 AI 生成图片（需要配置 API key）
USE_SMART_INSERTION = True  # 是否使用 LLM 智能判断插入位置

# 图片站 API Keys（从环境变量读取，也可以直接在这里配置）
# 获取方式：
# - Pexels: https://www.pexels.com/api/
# - Unsplash: https://unsplash.com/developers
# - Pixabay: https://pixabay.com/api/docs/
# - Hugging Face: https://huggingface.co/settings/tokens
UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY", "")
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "")
PIXABAY_API_KEY = '51527356-5568fca9ae6514e7636767a39'
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY", "")

client = OpenAI(
    api_key="sk-b436939915c14bc1b5bbdedf8d803c7c",
    base_url="https://api.deepseek.com",
)


