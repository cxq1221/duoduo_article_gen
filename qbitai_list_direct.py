from typing import List, Optional, Dict, Any

from config import MIN_CONTENT_LENGTH
from web_extractor_crawl import extract_article_content, extract_links_from_page
from utils import match_tags


def crawl_qbitai_list_direct(
    article_tags: List[str],
    list_url: str,
) -> Optional[Dict[str, Any]]:
    """
    使用 QbitAI 列表页 + HTML + LLM 流程：
    - 获取资讯列表页
    - 抽取前若干篇文章链接 + 标题
    - 按标签过滤标题（可选）
    - 进入文章页，提取正文并生成摘要
    - 返回第一篇符合条件的文章摘要结果
    """
    # 直接使用 crawl4ai 提取链接
    candidates = extract_links_from_page(list_url, max_links=10)
    if not candidates:
        print("❌ 未提取到任何文章链接")
        return None

    for c in candidates:
        title = c["title"]
        url = c["url"]
        print(f"\n检查 QbitAI 文章: {title} ({url})")

        if not match_tags(title, article_tags):
            continue

        content = extract_article_content(url)
        if not content or len(content) < MIN_CONTENT_LENGTH:
            print(
                f"  ⚠️ 内容过短（{len(content) if content else 0} 字符 < {MIN_CONTENT_LENGTH}），跳过"
            )
            continue

        # 返回原始内容，不进行总结（总结由调用方负责）
        return {
            "title": title,
            "content": content,
            "image_url": None,
            "url": url,
        }

    print("❗ QbitAI 未找到符合条件的文章")
    return None



