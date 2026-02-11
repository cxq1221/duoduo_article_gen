"""
飞书多维表格推送模块
将文章数据推送到飞书 Bitable（多维表格）的最后一行
"""
import requests
import re
from datetime import datetime
from typing import Dict, Any, Optional, List


FEISHU_BASE_URL = "https://open.feishu.cn/open-apis"


def _parse_bitable_url(url: str):
    """从飞书多维表格 URL 中解析 app_token 和 table_id"""
    # wiki URL: /wiki/{node_token}?table={table_id}
    wiki_match = re.search(r'/wiki/([A-Za-z0-9]+)', url)
    # 独立多维表格 URL: /base/{app_token}?table={table_id}
    base_match = re.search(r'/base/([A-Za-z0-9]+)', url)

    app_token = None
    if wiki_match:
        app_token = wiki_match.group(1)
    elif base_match:
        app_token = base_match.group(1)

    table_match = re.search(r'table=([A-Za-z0-9]+)', url)
    table_id = table_match.group(1) if table_match else None

    return app_token, table_id


def _get_tenant_access_token(app_id: str, app_secret: str) -> str:
    """获取飞书 tenant_access_token"""
    url = f"{FEISHU_BASE_URL}/auth/v3/tenant_access_token/internal"
    resp = requests.post(url, json={
        "app_id": app_id,
        "app_secret": app_secret,
    })
    data = resp.json()
    if data.get("code") != 0:
        raise Exception(f"获取 tenant_access_token 失败: {data.get('msg', data)}")
    return data["tenant_access_token"]


def _list_fields(token: str, app_token: str, table_id: str) -> List[Dict]:
    """列出多维表格的字段"""
    url = f"{FEISHU_BASE_URL}/bitable/v1/apps/{app_token}/tables/{table_id}/fields"
    resp = requests.get(url, headers={"Authorization": f"Bearer {token}"})
    data = resp.json()
    if data.get("code") != 0:
        raise Exception(f"获取字段列表失败: {data.get('msg', data)}")
    return data["data"]["items"]


def _add_record(token: str, app_token: str, table_id: str, fields: Dict) -> Dict:
    """向多维表格添加一条记录"""
    url = f"{FEISHU_BASE_URL}/bitable/v1/apps/{app_token}/tables/{table_id}/records"
    resp = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json={"fields": fields},
    )
    data = resp.json()
    if data.get("code") != 0:
        raise Exception(f"添加记录失败: {data.get('msg', data)}")
    return data


def _match_field(field_name: str) -> Optional[str]:
    """根据字段名匹配文章数据的 key"""
    name = field_name.lower()

    if any(k in name for k in ["标题", "title", "名称"]):
        return "title"
    if any(k in name for k in ["链接", "url", "link", "原文", "来源"]):
        return "url"
    if any(k in name for k in ["摘要", "简介", "summary", "description"]):
        return "summary"
    if any(k in name for k in ["内容", "正文", "content"]):
        return "content"
    if any(k in name for k in ["封面", "图片", "image", "cover", "缩略图"]):
        return "image_url"
    if any(k in name for k in ["日期", "时间", "date", "time", "发布", "created"]):
        return "date"

    return None


def _extract_first_image(content: str) -> Optional[str]:
    """从 markdown 正文中提取第一张图片的 URL"""
    match = re.search(r'!\[.*?\]\((.*?)\)', content)
    return match.group(1) if match else None


def _extract_title_from_content(content: str) -> Optional[str]:
    """从 markdown 正文中提取 ## 标题"""
    match = re.search(r'^##\s+(.+)$', content, re.MULTILINE)
    return match.group(1).strip() if match else None


def _format_field_value(field_info: Dict, value: Any) -> Any:
    """根据字段类型格式化值"""
    field_type = field_info.get("type")

    if field_type == 15:  # 超链接
        return {"link": value, "text": value}
    if field_type == 5:  # 日期 - 时间戳(毫秒)
        if isinstance(value, datetime):
            return int(value.timestamp() * 1000)
        return value
    # 文本类型直接返回
    return str(value) if not isinstance(value, str) else value


def push_to_feishu(result: Dict[str, Any]) -> bool:
    """
    推送文章到飞书多维表格

    Args:
        result: 包含 title, url, content, image_url 的文章字典

    Returns:
        是否推送成功
    """
    from config import FEISHU_APP_ID, FEISHU_APP_SECRET, FEISHU_BITABLE_URL

    if not result:
        print("⚠️ 没有文章结果可推送")
        return False

    if not FEISHU_APP_ID or not FEISHU_APP_SECRET or not FEISHU_BITABLE_URL:
        print("⚠️ 飞书配置不完整，跳过推送")
        return False

    # 解析 URL
    app_token, table_id = _parse_bitable_url(FEISHU_BITABLE_URL)
    if not app_token or not table_id:
        print("❌ 无法从 URL 中解析 app_token 或 table_id")
        return False

    print(f"\n📤 推送文章到飞书多维表格...")

    try:
        # 获取 token
        token = _get_tenant_access_token(FEISHU_APP_ID, FEISHU_APP_SECRET)

        # 获取字段列表
        fields = _list_fields(token, app_token, table_id)
        field_map = {f["field_name"]: f for f in fields}
        print(f"  📋 表格字段: {list(field_map.keys())}")

        # 准备文章数据
        article_data = {
            "title": result.get("title", ""),
            "url": result.get("url", ""),
            "summary": result.get("summary", ""),
            "content": result.get("content", ""),
            "image_url": result.get("image_url", ""),
            "date": datetime.now(),
        }

        # 自动匹配字段
        record = {}
        for field_name, field_info in field_map.items():
            data_key = _match_field(field_name)
            if data_key and article_data.get(data_key):
                value = _format_field_value(field_info, article_data[data_key])
                record[field_name] = value

        if not record:
            print("  ⚠️ 无法自动匹配任何字段，请检查表格列名是否包含: 标题/链接/内容/日期 等关键词")
            return False

        print(f"  📝 写入字段: {list(record.keys())}")

        # 添加记录
        _add_record(token, app_token, table_id, record)
        print("  ✅ 文章已推送到飞书多维表格")
        return True

    except Exception as e:
        print(f"  ❌ 推送失败: {e}")
        return False

