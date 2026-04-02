#!/usr/bin/env python3
"""
飞书文档备份模块
自动从 config_manager 获取飞书配置（来源于 ~/.openclaw/openclaw.json）
"""

import requests
import json
from pathlib import Path
from typing import Optional
import sys

# 添加脚本目录到路径
sys.path.insert(0, str(Path(__file__).parent))
from config_manager import load_config

# 数据目录
DATA_DIR = Path.home() / ".openclaw" / "workspace" / "data" / "x-daily-watch"


def get_feishu_credentials() -> tuple:
    """获取飞书凭证（从系统配置自动读取）"""
    config = load_config()
    feishu = config.get("feishu", {})
    app_id = feishu.get("app_id")
    app_secret = feishu.get("app_secret")
    
    if not app_id or not app_secret:
        raise ValueError("飞书配置未找到。请在 ~/.openclaw/openclaw.json 中配置 channels.feishu")
    
    return app_id, app_secret


def get_feishu_user_id() -> Optional[str]:
    """获取飞书用户 ID（从系统配置读取）"""
    config = load_config()
    return config.get("feishu", {}).get("user_id")


def get_token() -> Optional[str]:
    """获取飞书 tenant_access_token"""
    try:
        app_id, app_secret = get_feishu_credentials()
    except ValueError as e:
        print(f"❌ {e}")
        return None
    
    url = 'https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal'
    resp = requests.post(url, json={
        'app_id': app_id,
        'app_secret': app_secret
    }, timeout=10)
    
    if resp.status_code == 200:
        return resp.json().get('tenant_access_token')
    return None


def create_doc(title: str) -> Optional[str]:
    """创建飞书文档，返回文档 token"""
    token = get_token()
    if not token:
        print("获取 token 失败")
        return None
    
    url = 'https://open.feishu.cn/open-apis/docx/v1/documents'
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    data = {
        'title': title,
        'folder_token': ''
    }
    
    resp = requests.post(url, headers=headers, json=data, timeout=15)
    if resp.status_code == 200:
        result = resp.json()
        if result.get('code') == 0:
            return result['data']['document']['document_id']
        else:
            print(f"创建失败: {result.get('msg')}")
    return None


def write_doc_content(doc_token: str, content: str) -> bool:
    """向飞书文档写入内容"""
    token = get_token()
    if not token:
        return False
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    url = f'https://open.feishu.cn/open-apis/docx/v1/documents/{doc_token}/blocks/{doc_token}/children'
    
    # 分段写入
    chunks = []
    lines = content.split('\n')
    current_chunk = ""
    for line in lines:
        if len(current_chunk) + len(line) > 2500:
            if current_chunk:
                chunks.append(current_chunk)
            current_chunk = line + "\n"
        else:
            current_chunk += line + "\n"
    if current_chunk:
        chunks.append(current_chunk)
    
    success = True
    for i, chunk in enumerate(chunks[:10]):
        data = {
            "index": i,
            "children": [{
                "block_type": 2,
                "text": {"elements": [{"text_run": {"content": chunk[:2500]}}]}
            }]
        }
        resp = requests.post(url, headers=headers, json=data, timeout=15)
        if resp.status_code != 200 or resp.json().get('code') != 0:
            success = False
    
    return success


def backup_long_articles(content: str, title: str) -> Optional[str]:
    """备份长文到飞书文档，返回文档链接"""
    doc_token = create_doc(title)
    if not doc_token:
        print("创建文档失败")
        return None
    
    if write_doc_content(doc_token, content):
        return f"https://open.feishu.cn/docx/{doc_token}"
    return None


def send_feishu_message(content: str) -> bool:
    """发送飞书消息给用户"""
    token = get_token()
    if not token:
        return False
    
    user_id = get_feishu_user_id()
    if not user_id:
        print("未找到飞书用户 ID")
        return False
    
    url = 'https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=open_id'
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    # 截断过长消息
    if len(content) > 30000:
        content = content[:30000] + "\n\n... (内容过长已截断)"
    
    data = {
        'receive_id': user_id,
        'msg_type': 'text',
        'content': json.dumps({'text': content})
    }
    
    resp = requests.post(url, headers=headers, json=data, timeout=15)
    return resp.status_code == 200 and resp.json().get('code') == 0


if __name__ == "__main__":
    print("测试飞书模块...")
    
    # 测试配置读取
    config = load_config()
    print(f"飞书配置: {config.get('feishu', {})}")
    
    # 测试 token 获取
    token = get_token()
    if token:
        print(f"✅ Token 获取成功: {token[:20]}...")
    else:
        print("❌ Token 获取失败")