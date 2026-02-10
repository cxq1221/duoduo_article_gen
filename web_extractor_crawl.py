from typing import Optional, List, Dict
import asyncio
import re

try:
    from crawl4ai import AsyncWebCrawler  # type: ignore
except ImportError:  # pragma: no cover
    AsyncWebCrawler = None  # type: ignore


async def _fetch_with_crawl4ai(url: str):
    """使用 crawl4ai 异步抓取页面，返回完整结果对象。"""
    if AsyncWebCrawler is None:
        raise RuntimeError("crawl4ai 未安装，请先执行 `pip install crawl4ai`")
    async with AsyncWebCrawler() as crawler:  # type: ignore[operator]
        result = await crawler.arun(url=url)
        return result


def fetch_html(url: str) -> str:
    """
    使用 crawl4ai 获取页面的原始 HTML。
    用于需要直接操作 HTML 的场景（如提取图片等）。
    """
    try:
        result = asyncio.run(_fetch_with_crawl4ai(url))
        return getattr(result, "html", "") or ""
    except Exception as e:
        print(f"  ❌ 获取 HTML 失败: {e}")
        return ""


def extract_article_content(url: str) -> Optional[str]:
    """
    使用 crawl4ai 提取文章正文内容（替代 trafilatura）。
    返回清理后的文本内容。
    """
    print(f"  🔍 正在使用 crawl4ai 提取文章内容: {url}")
    try:
        result = asyncio.run(_fetch_with_crawl4ai(url))
        # crawl4ai 通常提供 markdown 或 cleaned_html，优先用 markdown
        content = getattr(result, "markdown", "") or getattr(result, "cleaned_html", "")
        if content:
            # 如果返回的是 HTML，简单提取文本
            if content.startswith("<"):
                # 简单去除 HTML 标签
                content = re.sub(r"<[^>]+>", "", content)
                content = re.sub(r"\s+", " ", content).strip()
            print(f"  ✅ 提取成功，内容长度: {len(content)} 字符")
            return content
        else:
            print("  ⚠️ 提取失败，未获取到内容")
            return None
    except Exception as e:
        print(f"  ❌ 提取出错: {e}")
        return None


def extract_links_from_page(url: str, max_links: int = 10) -> List[Dict[str, str]]:
    """
    使用 crawl4ai 从列表页提取文章链接和标题（替代 BeautifulSoup）。
    返回 [{"url": "...", "title": "..."}, ...]
    """
    print(f"  📋 正在使用 crawl4ai 提取链接: {url}")
    try:
        result = asyncio.run(_fetch_with_crawl4ai(url))
        html = getattr(result, "html", "") or ""
        
        if not html:
            return []
        
        # 使用正则表达式从 HTML 中提取链接和标题
        # 匹配常见的文章链接模式：<a href="..." ...>标题</a>
        candidates: List[Dict[str, str]] = []
        seen_urls = set()
        
        # 匹配 <a> 标签内的链接和文本
        pattern = r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>([^<]+)</a>'
        matches = re.finditer(pattern, html, re.IGNORECASE)
        
        for match in matches:
            href = match.group(1)
            title = match.group(2).strip()
            
            # 过滤掉无效链接
            if not href or not title or len(title) < 5:
                continue
            
            # 处理相对链接
            if href.startswith("/"):
                href = f"{url.split('/')[0]}//{url.split('/')[2]}{href}"
            elif not href.startswith("http"):
                continue
            
            # 去重
            if href in seen_urls:
                continue
            seen_urls.add(href)
            
            candidates.append({"url": href, "title": title})
            if len(candidates) >= max_links:
                break
        
        print(f"  ✅ 提取到 {len(candidates)} 个链接")
        return candidates
    except Exception as e:
        print(f"  ❌ 提取链接出错: {e}")
        return []

