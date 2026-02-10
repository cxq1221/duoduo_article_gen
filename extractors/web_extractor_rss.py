from typing import List, Optional, Dict, Any
from datetime import datetime
import re

import feedparser
import requests
import sys
import os

# 添加项目根目录到路径，以便导入 config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import TIME_WINDOW_HOURS, MIN_CONTENT_LENGTH
from .web_extractor_crawl import extract_article_content, fetch_html
from tools import match_tags
import html


def _fetch_feed(feed_url: str):
    print(f"📡 正在获取 RSS feed: {feed_url}")
    try:
        response = requests.get(feed_url, timeout=15, verify=True)
        response.raise_for_status()
        print(f"  ✅ HTTP 请求成功，状态码: {response.status_code}")
        feed = feedparser.parse(response.content)
        print(f"✅ 解析成功，共 {len(feed.entries)} 篇文章")
        if feed.bozo:
            print(f"⚠️ RSS 解析警告: {feed.bozo_exception}")
        if feed.entries:
            print(f"📰 Feed 标题: {feed.feed.get('title', 'Unknown')}")
        return feed
    except requests.exceptions.SSLError:
        print("⚠️ SSL 证书验证失败，尝试禁用验证...")
        response = requests.get(feed_url, timeout=15, verify=False)
        response.raise_for_status()
        feed = feedparser.parse(response.content)
        print(f"✅ 解析成功（已禁用 SSL 验证），共 {len(feed.entries)} 篇文章")
        return feed
    except Exception as e:
        print(f"❌ 获取 feed 失败: {e}")
        raise


def is_recent(entry):
    if not entry.get("published_parsed"):
        print(f"  ⚠️ 文章无发布时间信息: {entry.get('title', 'Unknown')}")
        return False
    published = datetime(*entry.published_parsed[:6])
    delta = datetime.utcnow() - published
    hours_ago = delta.total_seconds() / 3600
    is_recent_flag = delta.total_seconds() < TIME_WINDOW_HOURS * 3600
    print(
        f"  📅 发布时间: {published.strftime('%Y-%m-%d %H:%M:%S')}, "
        f"{hours_ago:.1f} 小时前, "
        f"{'✅ 在时间窗口内' if is_recent_flag else '❌ 超出时间窗口'}"
    )
    return is_recent_flag


def _extract_image_from_entry(entry):
    """从 RSS entry 中尽量提取图片 URL。"""
    print(f"  🖼️ 正在从 RSS entry 中提取图片 URL")
    image_url = None

    if hasattr(entry, "media_content") and entry.media_content:
        image_url = entry.media_content[0].get("url")
    elif hasattr(entry, "media_thumbnail") and entry.media_thumbnail:
        image_url = entry.media_thumbnail[0].get("url")
    else:
        html = getattr(entry, "summary", "") or ""
        m = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', html, re.IGNORECASE)
        if m:
            image_url = m.group(1)
    print(f"  🖼️  image_url: {image_url}")
    return image_url


def _extract_image_from_html(html: str) -> Optional[str]:
    if not html:
        return None

    og_match = re.search(
        r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']',
        html,
        re.IGNORECASE,
    )
    if og_match:
        return og_match.group(1)

    img_match = re.search(
        r'<img[^>]+src=["\']([^"\']+)["\']',
        html,
        re.IGNORECASE,
    )
    if img_match:
        return img_match.group(1)

    return None


def get_image_url(entry, url: str) -> Optional[str]:
    """综合 RSS 与直接爬取两种方式获取图片 URL。"""
    image_url = None

    try:
        image_url = _extract_image_from_entry(entry)
    except Exception as e:
        print(f"  ⚠️ 从 RSS 提取图片失败: {e}")

    if not image_url:
        print(f"  🌐 正在获取 HTML: {url}")
        html = fetch_html(url)
        image_url = _extract_image_from_html(html)

    if image_url:
        print(f"  🖼️ 图片 URL: {image_url}")
    else:
        print("  ⚠️ 未找到图片 URL")

    return image_url


def _extract_content_from_entry(entry) -> Optional[str]:
    """
    从 RSS entry 中提取文章内容。
    优先使用 content 字段，其次使用 summary/description 字段。
    """
    # 尝试获取 content（某些 RSS 包含完整内容）
    content = None
    if hasattr(entry, "content") and entry.content:
        # content 可能是列表，取第一个
        if isinstance(entry.content, list) and entry.content:
            content = entry.content[0].get("value", "")
        elif isinstance(entry.content, str):
            content = entry.content
    
    # 如果没有 content，尝试 summary 或 description
    if not content:
        content = getattr(entry, "summary", "") or getattr(entry, "description", "") or ""
    
    if not content:
        return None
    
    # 清理 HTML 标签（如果内容是 HTML）
    # 简单去除 HTML 标签
    content = re.sub(r"<[^>]+>", "", content)
    # 解码 HTML 实体
    content = html.unescape(content)
    # 清理多余空白
    content = re.sub(r"\s+", " ", content).strip()
    
    return content if content else None


def crawl_rss_direct(
    article_tags: List[str],
    feed_url: str,
) -> Optional[Dict[str, Any]]:
    """
    通用的 RSS feed 抓取策略（适用于所有标准 RSS）：
    - 遍历 RSS feed 中的文章
    - 用调用方给出的 article_tags 做粗过滤
    - 用 is_recent 做时间过滤
    - 抓正文、抓图片、生成摘要
    - 返回第一篇符合条件的文章摘要结果
    """
    feed = _fetch_feed(feed_url)

    for entry in feed.entries:
        title = getattr(entry, "title", "Unknown")
        url = getattr(entry, "link", "")

        print(f"\n检查文章: {title}")

        title_text = getattr(entry, "title", "") or ""
        summary_text = getattr(entry, "summary", "") or ""
        if not match_tags(title_text, article_tags, summary=summary_text):
            continue

        if not is_recent(entry):
            print("  ⏭️ 跳过（不在时间窗口内）")
            continue

        image_url = get_image_url(entry, url)
        
        # 优先从 RSS entry 中提取内容，如果不够再通过 crawl 获取
        content = _extract_content_from_entry(entry)
        if not content or len(content) < MIN_CONTENT_LENGTH:
            print(f"  📄 RSS 内容不足（{len(content) if content else 0} 字符），通过 crawl 获取完整正文...")
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
            "image_url": image_url,
            "url": url,
        }

    print("❗ 未找到符合条件的文章")
    return None

