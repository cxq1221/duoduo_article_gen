from typing import List, Optional, Dict, Any

import sys
import os

# 添加项目根目录到路径，以便导入 config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import MIN_CONTENT_LENGTH
from .web_extractor_crawl import extract_article_content, extract_links_from_page
from tools import match_tags


def crawl_list_page(
    article_tags: List[str],
    list_url: str,
    max_links: int = 10,
) -> Optional[Dict[str, Any]]:
    """
    通用的列表页抓取策略（适用于没有 RSS feed 的网站）：
    - 获取列表页 HTML
    - 提取文章链接和标题
    - 按标签过滤标题（可选）
    - 进入文章页，提取正文
    - 返回第一篇符合条件的文章结果
    
    Args:
        article_tags: 关键词列表，用于过滤文章
        list_url: 列表页 URL
        max_links: 最多提取的链接数量
    
    Returns:
        包含 title, url, content, image_url 的字典，如果未找到则返回 None
    """
    # 使用 crawl4ai 提取链接
    candidates = extract_links_from_page(list_url, max_links=max_links)
    if not candidates:
        print("❌ 未提取到任何文章链接")
        return None

    for c in candidates:
        title = c["title"]
        url = c["url"]
        print(f"\n检查文章: {title} ({url})")

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
            "image_url": None,  # 列表页抓取暂不支持图片提取
            "url": url,
        }

    print("❗ 未找到符合条件的文章")
    return None

