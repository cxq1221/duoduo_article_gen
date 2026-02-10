"""
图片获取模块
支持从免费图片站获取图片或调用免费文生图 API 生成图片
"""
import requests
from typing import Optional, List
from config import (
    client, MODEL,
    UNSPLASH_ACCESS_KEY, PEXELS_API_KEY, PIXABAY_API_KEY, HUGGINGFACE_API_KEY,
    USE_AI_IMAGE_GENERATION
)


class ImageFetcher:
    """图片获取器，支持多种图片源"""
    
    def __init__(self):
        # 图片站 API Keys（从配置文件读取）
        self.unsplash_access_key = UNSPLASH_ACCESS_KEY
        self.pexels_api_key = PEXELS_API_KEY
        self.pixabay_api_key = PIXABAY_API_KEY
        self.huggingface_api_key = HUGGINGFACE_API_KEY
        
        # 优先使用的图片源顺序（根据是否有 API key 动态调整）
        self.source_priority = []
        if self.pexels_api_key:
            self.source_priority.append("pexels")
        if self.unsplash_access_key:
            self.source_priority.append("unsplash")
        if self.pixabay_api_key:
            self.source_priority.append("pixabay")
        if self.huggingface_api_key:
            self.source_priority.append("huggingface")
        
        # 如果没有配置任何 API key，使用默认顺序
        if not self.source_priority:
            self.source_priority = ["pexels", "unsplash", "pixabay"]
    
    def extract_keywords(self, title: str, content: str) -> List[str]:
        """
        从文章标题和内容中提取关键词，用于图片搜索
        
        Args:
            title: 文章标题
            content: 文章内容（前500字用于提取关键词）
        
        Returns:
            关键词列表
        """
        # 使用 LLM 提取关键词
        prompt = f"""请从以下文章标题和内容中总结出合适的插图类型，并且输出适合从Pixabay/PEXELS等站点搜索的该类型图片的英文关键词，用逗号分隔：
标题：{title}
内容：{content[:500]}

只返回关键词，不要其他说明。关键词应该是具体的、可视觉化的概念。
例如：technology, artificial intelligence, computer, data center, innovation

关键词："""
        
        try:
            resp = client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
            )
            keywords_text = resp.choices[0].message.content.strip()
            # 清理并分割关键词
            keywords = [k.strip() for k in keywords_text.split(",") if k.strip()]
            return keywords[:5] if keywords else ["technology", "innovation"]
        except Exception as e:
            print(f"  ⚠️ 关键词提取失败: {e}，使用默认关键词")
            return ["technology", "innovation"]
    
    def fetch_from_pexels(self, query: str) -> Optional[str]:
        """从 Pexels 获取图片（免费，需要注册获取 API key）"""
        if not self.pexels_api_key:
            return None
        
        try:
            url = "https://api.pexels.com/v1/search"
            headers = {"Authorization": self.pexels_api_key}
            params = {"query": query, "per_page": 1, "orientation": "landscape"}
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("photos") and len(data["photos"]) > 0:
                    image_url = data["photos"][0]["src"]["large"]
                    print(f"  ✅ 从 Pexels 获取图片: {image_url}")
                    return image_url
        except Exception as e:
            print(f"  ⚠️ Pexels API 调用失败: {e}")
        
        return None
    
    def fetch_from_unsplash(self, query: str) -> Optional[str]:
        """从 Unsplash 获取图片（免费，需要注册获取 API key）"""
        if not self.unsplash_access_key:
            return None
        
        try:
            url = "https://api.unsplash.com/search/photos"
            headers = {"Authorization": f"Client-ID {self.unsplash_access_key}"}
            params = {"query": query, "per_page": 1, "orientation": "landscape"}
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("results") and len(data["results"]) > 0:
                    image_url = data["results"][0]["urls"]["regular"]
                    print(f"  ✅ 从 Unsplash 获取图片: {image_url}")
                    return image_url
        except Exception as e:
            print(f"  ⚠️ Unsplash API 调用失败: {e}")
        
        return None
    
    def fetch_from_pixabay(self, query: str) -> Optional[str]:
        """从 Pixabay 获取图片（免费，需要注册获取 API key）"""
        if not self.pixabay_api_key:
            return None
        
        try:
            url = "https://pixabay.com/api/"
            params = {
                "key": self.pixabay_api_key,
                "q": query,
                "image_type": "photo",
                "orientation": "horizontal",
                "per_page": 3,
                "safesearch": "true"
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("hits") and len(data["hits"]) > 0:
                    image_url = data["hits"][0]["webformatURL"]
                    print(f"  ✅ 从 Pixabay 获取图片: {image_url}")
                    return image_url
        except Exception as e:
            print(f"  ⚠️ Pixabay API 调用失败: {e}")
        
        return None
    
    def generate_with_huggingface(self, prompt: str) -> Optional[str]:
        """
        使用 Hugging Face Inference API 生成图片
        免费模型：stabilityai/stable-diffusion-2-1（需要 API key）
        """
        if not self.huggingface_api_key:
            return None
        
        try:
            # 使用 Stability AI 的免费模型
            api_url = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-2-1"
            headers = {"Authorization": f"Bearer {self.huggingface_api_key}"}
            
            # 简化 prompt，添加质量提示
            enhanced_prompt = f"{prompt}, high quality, professional photography, 4k"
            
            response = requests.post(
                api_url,
                headers=headers,
                json={"inputs": enhanced_prompt},
                timeout=30
            )
            
            if response.status_code == 200:
                # Hugging Face 返回的是图片字节，需要保存到本地或上传到图床
                # 这里简化处理，返回 base64 或上传到临时图床
                # 实际使用时建议保存到本地或云存储
                print(f"  ✅ 从 Hugging Face 生成图片成功")
                # 注意：这里需要处理图片保存和 URL 获取
                # 暂时返回 None，需要实现图片上传逻辑
                return None
            else:
                print(f"  ⚠️ Hugging Face API 调用失败: {response.status_code}")
        except Exception as e:
            print(f"  ⚠️ Hugging Face API 调用异常: {e}")
        
        return None
    
    def fetch_image(self, title: str, content: str, use_ai_generation: bool = False) -> Optional[str]:
        """
        获取图片的主入口
        
        Args:
            title: 文章标题
            content: 文章内容
            use_ai_generation: 是否优先使用 AI 生成图片
        
        Returns:
            图片 URL，如果获取失败返回 None
        """
        print(f"  🖼️ 开始获取图片...")
        
        # 提取关键词
        keywords = self.extract_keywords(title, content)
        query = " ".join(keywords[:3])  # 使用前3个关键词
        print(f"  🔍 搜索关键词: {query}")
        
        # 如果启用 AI 生成，优先尝试
        if use_ai_generation and self.huggingface_api_key:
            ai_prompt = f"{title}, {query}"
            image_url = self.generate_with_huggingface(ai_prompt)
            if image_url:
                return image_url
        
        # 按优先级尝试各个图片站
        for source in self.source_priority:
            if source == "pexels":
                image_url = self.fetch_from_pexels(query)
            elif source == "unsplash":
                image_url = self.fetch_from_unsplash(query)
            elif source == "pixabay":
                image_url = self.fetch_from_pixabay(query)
            elif source == "huggingface":
                ai_prompt = f"{title}, {query}"
                image_url = self.generate_with_huggingface(ai_prompt)
            else:
                continue
            
            if image_url:
                return image_url
        
        print(f"  ⚠️ 所有图片源都获取失败")
        return None


def fetch_images_for_article(title: str, content: str, count: int = 2, use_ai_generation: bool = False) -> List[str]:
    """
    为文章获取多张图片
    
    Args:
        title: 文章标题
        content: 文章内容
        count: 需要获取的图片数量
        use_ai_generation: 是否优先使用 AI 生成图片
    
    Returns:
        图片 URL 列表
    """
    fetcher = ImageFetcher()
    images = []
    
    # 将内容分段，为每段提取不同的关键词
    content_parts = content.split("\n\n")
    part_size = max(1, len(content_parts) // count)
    
    for i in range(count):
        # 取不同部分的内容来提取关键词
        start_idx = i * part_size
        end_idx = min((i + 1) * part_size, len(content_parts))
        part_content = "\n\n".join(content_parts[start_idx:end_idx])
        
        # 只在第一张图片时尝试 AI 生成（如果启用）
        use_ai = use_ai_generation and i == 0
        image_url = fetcher.fetch_image(title, part_content, use_ai_generation=use_ai)
        if image_url:
            images.append(image_url)
    
    return images

