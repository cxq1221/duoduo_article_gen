from typing import Optional
import sys
import os

# 添加项目根目录到路径，以便导入 config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import MODEL, client


def summarize_article(
    title: str,
    content: str,
    prompt_template: Optional[str] = None,
) -> str:
    """
    使用 LLM 将文章内容整理成中文科技文章/视频文案。
    
    Args:
        title: 文章标题
        content: 文章正文内容
        prompt_template: 自定义 prompt 模板，如果为 None 则使用默认模板
                        模板中可以使用 {title} 和 {content} 占位符
    
    Returns:
        整理后的中文文章内容
    """
    if prompt_template is None:
        prompt_template = """
你是一名科技媒体编辑。

请将下面的科技新闻整理成一篇中文科技文章：
- 不要逐句翻译
- 保留核心事实
- 适当补充背景以及新闻的重要程度
- 400~600 字
- 风格：理性、专业、偏技术，符合科技博主的口吻
- 在不改变每句话的原有含义的前提下，仅修改表达方式，使其变成一篇新的文案
- 涉及到英文，专有名词，数据等信息时，不能对其进行修改
- 语言轻快简洁，符合科技博主的口吻

标题：{title}

正文：
{content}
"""
    
    prompt = prompt_template.format(title=title, content=content)
    
    print(f"  🤖 正在使用 {MODEL} 生成摘要...")
    try:
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
        )
        summary = resp.choices[0].message.content.strip()
        print(f"  ✅ 摘要生成成功，长度: {len(summary)} 字符")
        return summary
    except Exception as e:
        print(f"  ❌ 摘要生成失败: {e}")
        raise

