from openai import OpenAI

# 模型与通用抓取配置
MODEL = "deepseek-chat"
TIME_WINDOW_HOURS = 48
MIN_CONTENT_LENGTH = 500


client = OpenAI(
    api_key=,
    base_url=,
)


