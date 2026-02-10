from extractors import crawl_rss_direct, crawl_list_page
from tools import (
    send_wecom_markdown,
    save_markdown,
    summarize_article,
    fetch_images_for_article,
    insert_images_smart,
    insert_images_to_content,
)
from config import ENABLE_IMAGE_INSERTION, IMAGE_COUNT, USE_AI_IMAGE_GENERATION, USE_SMART_INSERTION


def main():
    # 选择抓取源：techcrunch 或 qbitai
    # source = "techcrunch"
    source = "qbitai"
    if source == "techcrunch":
        feed_url = "https://techcrunch.com/feed/"
        tags = ["ai", "machine learning", "deep learning"]
        result = crawl_rss_direct(tags, feed_url)
    elif source == "qbitai":
        list_url = "https://www.qbitai.com/category/%e8%b5%84%e8%ae%af"
        tags = ["AI", "大模型", "算力", "视频", "OpenAI"]
        result = crawl_list_page(tags, list_url)
        if not result:
            print("❌ 没有找到符合条件的文章")
            return
    else:
        raise ValueError(f"未知的抓取源: {source}")
    
    if not result:
        print("❌ 没有找到符合条件的文章")
        return
    
    # 使用大模型总结文章内容
    result["content"] = summarize_article(result["title"], result["content"])
    
    # 自动获取并插入图片
    if ENABLE_IMAGE_INSERTION:
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
                # 插入图片到正文
                if USE_SMART_INSERTION:
                    result["content"] = insert_images_smart(
                        result["content"], 
                        image_urls, 
                        result["title"]
                    )
                else:
                    result["content"] = insert_images_to_content(
                        result["content"], 
                        image_urls
                    )
                print(f"  ✅ 图片已插入到正文")
            else:
                print(f"  ⚠️ 未能获取到图片，继续保存文章")
        except Exception as e:
            print(f"  ⚠️ 图片获取/插入过程出错: {e}，继续保存文章")
    
    # 保存到本地
    save_markdown(result)
    
    # 发到微信群（可选）
    # send_wecom_markdown(result["content"])


if __name__ == "__main__":
    main()


