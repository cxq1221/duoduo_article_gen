from typing import List, Optional, Dict, Any
from datetime import datetime
import re

import feedparser
import requests
import trafilatura

from config import MODEL, TIME_WINDOW_HOURS, MIN_CONTENT_LENGTH, client


def fetch_feed(feed_url: str):
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


def extract_article(url: str) -> Optional[str]:
    print(f"  🔍 正在提取文章内容: {url}")
    try:
        html = requests.get(url, timeout=15).text
        content = trafilatura.extract(html)
        if content:
            print(f"  ✅ 提取成功，内容长度: {len(content)} 字符")
        else:
            print("  ⚠️ 提取失败，未获取到内容")
        return content
    except Exception as e:
        print(f"  ❌ 提取出错: {e}")
        return None


def _extract_image_from_entry(entry):
    """从 RSS entry 中尽量提取图片 URL。"""
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

    return image_url


def _fetch_html(url: str) -> str:
    print(f"  🌐 正在获取 HTML: {url}")
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        print(f"  ❌ 获取 HTML 失败: {e}")
        return ""


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
        html = _fetch_html(url)
        image_url = _extract_image_from_html(html)

    if image_url:
        print(f"  🖼️ 图片 URL: {image_url}")
    else:
        print("  ⚠️ 未找到图片 URL")

    return image_url


def summarize(title: str, content: str) -> str:
    print(f"  🤖 正在使用 {MODEL} 生成摘要...")
    prompt = f"""
你是一名科技媒体编辑。

请将下面的 TechCrunch 新闻整理成一篇中文科技文章：
- 不要逐句翻译
- 保留核心事实
- 适当补充背景
- 说明这条新闻为什么重要
- 400~600 字
- 风格：理性、专业、偏技术

标题：{title}

正文：
{content}
"""
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


def _is_related(entry, tags: List[str]) -> bool:
    """根据传入的关键词列表判断文章是否相关。"""
    title = (getattr(entry, "title", "") or "").lower()
    summary = (getattr(entry, "summary", "") or "").lower()
    text = f"{title}\n{summary}"

    for kw in tags:
        if kw.lower() in text:
            print(f"  ✅ 判定为目标领域相关（命中关键词: {kw}）")
            return True

    print("  ⛔ 非目标标签相关文章，跳过")
    return False


def crawl_techcrunch_rss_direct(
    article_tags: List[str],
    feed_url: str,
) -> Optional[Dict[str, Any]]:
    """
    使用 TechCrunch RSS + HTML + LLM 流程，实现最简单的抓取策略：
    - 遍历 RSS 中的文章
    - 用调用方给出的 article_tags 做粗过滤
    - 用 is_recent 做时间过滤
    - 抓正文、抓图片、生成摘要
    - 返回第一篇符合条件的文章摘要结果
    """
    feed = fetch_feed(feed_url)

    for entry in feed.entries:
        title = getattr(entry, "title", "Unknown")
        url = getattr(entry, "link", "")

        print(f"\n检查文章: {title}")

        if not _is_related(entry, article_tags):
            continue

        if not is_recent(entry):
            print("  ⏭️ 跳过（不在时间窗口内）")
            continue

        image_url = get_image_url(entry, url)
        content = extract_article(url)
        if not content or len(content) < MIN_CONTENT_LENGTH:
            print(
                f"  ⚠️ 内容过短（{len(content) if content else 0} 字符 < {MIN_CONTENT_LENGTH}），跳过"
            )
            continue

        summary = summarize(title, content)

        return {
            "title": title,
            "content": summary,
            "image_url": image_url,
            "url": url,
        }

    print("❗ 未找到符合条件的文章")
    return None


