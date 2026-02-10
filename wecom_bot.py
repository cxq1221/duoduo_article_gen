from typing import Optional

import requests


DEFAULT_WEBHOOK_URL = (
    "https://qyapi.weixin.qq.com/cgi-bin/webhook/send"
    "?key=755e6374-9b60-4c50-a347-e8e54c72e444"
)


def send_wecom_markdown(
    content: str,
    webhook_url: str = DEFAULT_WEBHOOK_URL,
) -> bool:
    """
    将 markdown 文本推送到企业微信群机器人。
    返回 True 表示企业微信返回 errcode == 0，False 表示失败（包含 HTTP 或业务错误）。
    """
    payload = {
        "msgtype": "markdown",
        "markdown": {"content": content},
    }

    try:
        resp = requests.post(webhook_url, json=payload, timeout=5)
        resp.raise_for_status()
        data: dict = resp.json()
        if data.get("errcode") != 0:
            print(f"❌ 企业微信机器人发送失败: {data}")
            return False
        print("✅ 企业微信机器人发送成功")
        return True
    except Exception as e:
        print(f"❌ 企业微信机器人请求异常: {e}")
        return False



