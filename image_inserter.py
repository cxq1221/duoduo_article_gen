"""
图片插入模块
智能分析文章结构并在合适位置插入图片
"""
import re
from typing import List, Optional
from config import client, MODEL


def insert_images_to_content(content: str, image_urls: List[str]) -> str:
    """
    将图片插入到文章内容的合适位置
    
    Args:
        content: 文章正文内容
        image_urls: 图片 URL 列表
    
    Returns:
        插入图片后的文章内容
    """
    if not image_urls:
        return content
    
    # 按段落分割内容
    paragraphs = re.split(r'\n\n+', content)
    
    # 过滤空段落
    paragraphs = [p.strip() for p in paragraphs if p.strip()]
    
    if len(paragraphs) <= 1:
        # 如果段落太少，直接在末尾插入所有图片
        image_markdown = "\n\n".join([f"![image]({url})" for url in image_urls])
        return f"{content}\n\n{image_markdown}"
    
    # 计算插入位置：在段落之间均匀分布
    num_images = len(image_urls)
    num_paragraphs = len(paragraphs)
    
    # 每 N 个段落插入一张图片
    interval = max(2, num_paragraphs // (num_images + 1))
    
    result_paragraphs = []
    image_index = 0
    
    for i, paragraph in enumerate(paragraphs):
        result_paragraphs.append(paragraph)
        
        # 在合适的位置插入图片（避免在开头和结尾）
        if (i + 1) % interval == 0 and i > 0 and i < num_paragraphs - 1:
            if image_index < num_images:
                image_markdown = f"![image]({image_urls[image_index]})"
                result_paragraphs.append(image_markdown)
                image_index += 1
    
    # 如果还有未插入的图片，在末尾插入
    if image_index < num_images:
        remaining_images = image_urls[image_index:]
        for img_url in remaining_images:
            result_paragraphs.append(f"![image]({img_url})")
    
    return "\n\n".join(result_paragraphs)


def insert_images_smart(content: str, image_urls: List[str], title: str) -> str:
    """
    使用 LLM 智能判断图片插入位置
    
    Args:
        content: 文章正文内容
        image_urls: 图片 URL 列表
        title: 文章标题（用于上下文）
    
    Returns:
        插入图片后的文章内容
    """
    if not image_urls:
        return content
    
    # 如果图片数量少，使用简单插入
    if len(image_urls) == 1:
        return insert_images_to_content(content, image_urls)
    
    # 使用 LLM 判断最佳插入位置
    prompt = f"""你是一名内容编辑。请分析以下文章，并在合适的位置插入图片标记。

文章标题：{title}

文章内容：
{content}

需要在文章中插入 {len(image_urls)} 张图片。请返回修改后的文章内容，在合适的位置插入以下标记：
- 使用 [IMAGE_1]、[IMAGE_2] 等标记来表示图片插入位置
- 图片应该插入在段落之间，与上下文相关
- 不要改变文章的其他内容
- 只返回修改后的文章内容，不要其他说明

修改后的文章："""
    
    try:
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        result = resp.choices[0].message.content.strip()
        
        # 替换标记为实际的图片 Markdown
        for i, img_url in enumerate(image_urls, 1):
            marker = f"[IMAGE_{i}]"
            image_markdown = f"![image]({img_url})"
            result = result.replace(marker, image_markdown)
        
        # 如果 LLM 没有插入标记，回退到简单插入
        if "[IMAGE_" not in result and "[image_" not in result:
            print("  ⚠️ LLM 未返回图片标记，使用简单插入方式")
            return insert_images_to_content(content, image_urls)
        
        return result
    except Exception as e:
        print(f"  ⚠️ 智能插入失败: {e}，使用简单插入方式")
        return insert_images_to_content(content, image_urls)

