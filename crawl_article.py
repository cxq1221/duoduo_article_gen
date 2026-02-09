from typing import Optional, Dict, Any
from datetime import datetime
import os

from techcrunch_rss_direct import crawl_techcrunch_rss_direct


OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def saveMarkdown(result: Optional[Dict[str, Any]]) -> None:
    """根据抓取结果写入 markdown 文件。"""
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


def main():
    feed_url = "https://techcrunch.com/feed/"
    tags = ["ai", "machine learning", "deep learning"]

    result = crawl_techcrunch_rss_direct(tags, feed_url)
    saveMarkdown(result)
    print(result)

if __name__ == "__main__":
    main()


