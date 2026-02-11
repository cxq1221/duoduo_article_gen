from typing import List, Optional, Dict, Any, Set
from datetime import datetime
import os


OUTPUT_DIR = "output"
PROCESSED_FILE = "processed_urls.txt"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def load_processed_urls() -> Set[str]:
    """加载已处理的文章 URL 集合"""
    if not os.path.exists(PROCESSED_FILE):
        return set()
    with open(PROCESSED_FILE, "r", encoding="utf-8") as f:
        return {line.strip() for line in f if line.strip()}


def save_processed_url(url: str) -> None:
    """将 URL 追加到已处理记录"""
    with open(PROCESSED_FILE, "a", encoding="utf-8") as f:
        f.write(url + "\n")


def match_tags(
    title: str,
    tags: List[str],
    summary: Optional[str] = None,
) -> bool:
    """
    统一的标签匹配函数，支持匹配标题和摘要。
    
    Args:
        title: 文章标题
        tags: 关键词列表
        summary: 可选的摘要内容，如果提供则同时匹配标题和摘要
    
    Returns:
        如果匹配到任一关键词返回 True，否则返回 False
    """
    if not tags:
        return True
    
    # 构建匹配文本
    text = title.lower()
    if summary:
        text = f"{text}\n{summary.lower()}"
    
    # 检查是否匹配任一关键词
    for tag in tags:
        if tag.lower() in text:
            print(f"  ✅ 判定为目标领域相关（命中关键词: {tag}）")
            return True
    
    print("  ⛔ 非目标标签相关文章，跳过")
    return False


def save_markdown(result: Optional[Dict[str, Any]]) -> None:
    """
    根据抓取结果写入 markdown 文件。
    
    Args:
        result: 包含 title, url, content, image_url 的字典
    """
    if not result:
        print("⚠️ 没有文章结果可保存")
        return

    title = result["title"]
    url = result["url"]
    content = result["content"]
    image_url = result.get("image_url")

    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"{OUTPUT_DIR}/{ts}.md"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"# {title}\n\n")
        f.write(f"> 原文：{url}\n\n")
        if image_url:
            f.write(f"![cover]({image_url})\n\n")
        f.write(content)
    print(f"✅ Saved: {filename}")

