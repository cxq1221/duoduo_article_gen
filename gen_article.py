import re
from extractors import crawl_rss_direct, crawl_list_page
from tools import (
    send_wecom_markdown,
    save_markdown,
    summarize_article,
    fetch_images_for_article,
    insert_images_smart,
    insert_images_to_content,
    push_to_feishu,
    save_processed_url,
)
from config import ENABLE_IMAGE_INSERTION, IMAGE_COUNT, USE_AI_IMAGE_GENERATION, USE_SMART_INSERTION


def enrich_images(result):
    """自动获取并插入图片到正文"""
    if not ENABLE_IMAGE_INSERTION:
        return
    print(f"\n🖼️ 开始获取图片（数量: {IMAGE_COUNT}）...")
    try:
        image_urls = fetch_images_for_article(
            result["title"],
            result["content"],
            count=IMAGE_COUNT,
            use_ai_generation=USE_AI_IMAGE_GENERATION
        )
        if image_urls:
            print(f"  ✅ 成功获取 {len(image_urls)} 张图片")
            if USE_SMART_INSERTION:
                result["content"] = insert_images_smart(
                    result["content"], image_urls, result["title"]
                )
            else:
                result["content"] = insert_images_to_content(
                    result["content"], image_urls
                )
            print(f"  ✅ 图片已插入到正文")
        else:
            print(f"  ⚠️ 未能获取到图片，继续保存文章")
    except Exception as e:
        print(f"  ⚠️ 图片获取/插入过程出错: {e}，继续保存文章")


def extract_title_and_cover(result):
    """从正文中提取最终标题、封面图和摘要"""
    title_match = re.search(r'^##\s+(.+)$', result["content"], re.MULTILINE)
    if title_match:
        result["title"] = title_match.group(1).strip()

    if not result.get("image_url"):
        img_match = re.search(r'!\[.*?\]\((.*?)\)', result["content"])
        if img_match:
            result["image_url"] = img_match.group(1)

    # 从 LLM 生成的内容中提取第一段作为摘要
    content = result.get("content", "")
    paragraphs = [p.strip() for p in content.split("\n\n") if p.strip() and not p.strip().startswith(("#", "!", ">"))]
    if paragraphs:
        result["summary"] = paragraphs[0]


def crawl_article(source="qbitai"):
    """抓取文章并用大模型总结"""
    if source == "techcrunch":
        feed_url = "https://techcrunch.com/feed/"
        tags = ["ai", "machine learning", "deep learning","LLM","AI Agent","AI","大模型","Agent","视频","OpenAI"]
        result = crawl_rss_direct(tags, feed_url)
    elif source == "qbitai":
        list_url = "https://www.qbitai.com/category/%e8%b5%84%e8%ae%af"
        tags = ["AI", "大模型", "算力", "视频", "OpenAI","AI Agent","Agent","LLM"]
        result = crawl_list_page(tags, list_url)
    else:
        raise ValueError(f"未知的抓取源: {source}")

    if not result:
        print("❌ 没有找到符合条件的文章")
        return None

    result["content"] = summarize_article(result["title"], result["content"])
    return result


def process_and_publish(source="qbitai", send_wecom=False):
    """抓取文章 → 插入图片 → 提取标题封面 → 保存本地 → 推送飞书 → 发送微信群（可选）"""
    result = crawl_article(source=source)
    if not result:
        return None

    enrich_images(result)
    extract_title_and_cover(result)
    save_markdown(result)
    push_to_feishu(result)
    save_processed_url(result["url"])

    if send_wecom:
        send_wecom_markdown(result["content"])

    return result



