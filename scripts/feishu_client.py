#!/usr/bin/env python3
"""
飞书推送模块
负责发送消息和创建文档
"""

import json
import requests
from pathlib import Path
from typing import Optional

SKILL_DIR = Path(__file__).parent.parent
CONFIG_PATH = SKILL_DIR / "config.json"


def load_feishu_config() -> dict:
    """加载飞书配置 - 从 openclaw.json 读取"""
    # 从 openclaw.json 读取飞书配置
    openclaw_config_path = Path.home() / ".openclaw" / "openclaw.json"
    if openclaw_config_path.exists():
        with open(openclaw_config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
            feishu_channel = config.get("channels", {}).get("feishu", {})
            if feishu_channel:
                return {
                    "app_id": feishu_channel.get("appId"),
                    "app_secret": feishu_channel.get("appSecret")
                }
    return {}


def get_feishu_token() -> Optional[str]:
    """获取飞书 access token"""
    config = load_feishu_config()
    app_id = config.get("app_id")
    app_secret = config.get("app_secret")
    
    if not app_id or not app_secret:
        print("未找到飞书配置，请先配置飞书 skill")
        return None
    
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    resp = requests.post(url, json={
        "app_id": app_id,
        "app_secret": app_secret
    })
    
    if resp.status_code == 200:
        return resp.json().get("tenant_access_token")
    return None


def send_message(user_id: str, content: str, msg_type: str = "text") -> bool:
    """发送飞书消息给用户"""
    token = get_feishu_token()
    if not token:
        return False
    
    url = "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=user_id"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    if msg_type == "text":
        body = {"text": content}
    else:
        body = {"content": content}
    
    data = {
        "receive_id": user_id,
        "msg_type": msg_type,
        "content": json.dumps(body)
    }
    
    resp = requests.post(url, headers=headers, json=data)
    
    if resp.status_code == 200:
        result = resp.json()
        return result.get("code") == 0
    return False


def create_document(title: str, content: str, folder_token: str = "") -> Optional[str]:
    """创建飞书文档，返回文档 token"""
    token = get_feishu_token()
    if not token:
        return None
    
    url = "https://open.feishu.cn/open-apis/docx/v1/documents"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    data = {
        "title": title,
        "folder_token": folder_token
    }
    
    resp = requests.post(url, headers=headers, json=data)
    
    if resp.status_code == 200:
        result = resp.json()
        if result.get("code") == 0:
            doc_token = result["data"]["document"]["document_id"]
            return doc_token
    
    return None


def format_tweet_message(tweets: list, username: str) -> str:
    """格式化推文为消息文本"""
    lines = [f"## @{username} 的最新推文\n"]
    
    for i, tweet in enumerate(tweets, 1):
        lines.append(f"### {i}. {tweet.get('title', '推文')[:30]}...")
        lines.append(f"📅 {tweet.get('date', '未知时间')}")
        lines.append(f"❤️ {tweet.get('likes', 0)} | 🔁 {tweet.get('retweets', 0)}")
        lines.append(f"\n{tweet.get('text', '')[:500]}...")
        
        if tweet.get("quoted_tweet"):
            qrt = tweet["quoted_tweet"]
            lines.append(f"\n> **转发 @{qrt.get('user_screen_name')}:**")
            lines.append(f"> {qrt.get('text', '')[:200]}...")
        
        lines.append(f"\n🔗 {tweet.get('url', '')}\n")
        lines.append("---\n")
    
    return "\n".join(lines)


if __name__ == "__main__":
    print("测试飞书客户端...")
    
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = json.load(f)
    
    user_id = config.get("push_config", {}).get("feishu_user_id")
    if user_id:
        print(f"将发送测试消息到: {user_id}")
    else:
        print("未配置飞书接收用户 ID")
