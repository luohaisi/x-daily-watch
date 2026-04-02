#!/usr/bin/env python3
"""
配置管理模块
配置文件位于 ~/.openclaw/workspace/data/x-daily-watch/config.json
自动从 ~/.openclaw/openclaw.json 读取飞书配置
"""

import json
from pathlib import Path
from datetime import datetime

# 路径配置
WORKSPACE_DIR = Path.home() / ".openclaw" / "workspace"
DATA_DIR = WORKSPACE_DIR / "data" / "x-daily-watch"
CONFIG_PATH = DATA_DIR / "config.json"
HISTORY_PATH = DATA_DIR / "history.json"
OPENCLAW_CONFIG_PATH = Path.home() / ".openclaw" / "openclaw.json"


def load_feishu_config() -> dict:
    """从 openclaw.json 读取飞书配置"""
    if OPENCLAW_CONFIG_PATH.exists():
        with open(OPENCLAW_CONFIG_PATH, "r", encoding="utf-8") as f:
            config = json.load(f)
            feishu_channel = config.get("channels", {}).get("feishu", {})
            if feishu_channel and feishu_channel.get("enabled"):
                app_id = feishu_channel.get("appId")
                app_secret = feishu_channel.get("appSecret")
                # 从 allowFrom 获取用户 ID
                allow_from = feishu_channel.get("allowFrom", [])
                user_id = allow_from[0] if allow_from else None
                
                if app_id and app_secret:
                    return {
                        "app_id": app_id,
                        "app_secret": app_secret,
                        "user_id": user_id
                    }
    return {}


def load_config() -> dict:
    """加载配置文件，自动合并飞书配置"""
    default_config = {
        "users": [],
        "push_config": {
            "time": "05:55",
            "timezone": "Asia/Shanghai"
        },
        "backup_config": {
            "enabled": True,
            "min_length": 500
        }
    }
    
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config = json.load(f)
    else:
        config = default_config
    
    # 自动合并飞书配置
    feishu_config = load_feishu_config()
    if feishu_config:
        config["feishu"] = feishu_config
    else:
        config["feishu"] = {}
    
    return config


def save_config(config: dict) -> None:
    """保存配置文件（不保存飞书配置，那是从系统读取的）"""
    # 移除飞书配置后再保存
    config_to_save = {k: v for k, v in config.items() if k != "feishu"}
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config_to_save, f, ensure_ascii=False, indent=2)


def load_history() -> dict:
    """加载历史记录"""
    if not HISTORY_PATH.exists():
        return {
            "last_push": None,
            "pushed_tweets": [],
            "backup_doc_token": None
        }
    with open(HISTORY_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_history(history: dict) -> None:
    """保存历史记录"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(HISTORY_PATH, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def add_user(username: str, alias: str = "") -> dict:
    """添加关注用户"""
    config = load_config()
    
    for user in config["users"]:
        if user["username"].lower() == username.lower():
            return {"success": False, "message": f"@{username} 已在关注列表中"}
    
    user = {
        "username": username,
        "alias": alias or username,
        "added_at": datetime.now().strftime("%Y-%m-%d"),
        "max_tweets": 5
    }
    config["users"].append(user)
    save_config(config)
    
    return {"success": True, "message": f"已添加 @{username} 到关注列表"}


def remove_user(username: str) -> dict:
    """移除关注用户"""
    config = load_config()
    
    for i, user in enumerate(config["users"]):
        if user["username"].lower() == username.lower():
            config["users"].pop(i)
            save_config(config)
            return {"success": True, "message": f"已取消关注 @{username}"}
    
    return {"success": False, "message": f"@{username} 不在关注列表中"}


def list_users() -> list:
    """列出所有关注用户"""
    config = load_config()
    return config.get("users", [])


def update_pushed_tweets(tweet_ids: list) -> None:
    """更新已推送的推文 ID"""
    history = load_history()
    history["pushed_tweets"].extend(tweet_ids)
    history["pushed_tweets"] = history["pushed_tweets"][-1000:]
    history["last_push"] = datetime.now().isoformat()
    save_history(history)


def is_tweet_pushed(tweet_id: str) -> bool:
    """检查推文是否已推送"""
    history = load_history()
    return tweet_id in history["pushed_tweets"]


if __name__ == "__main__":
    print("测试配置管理...")
    config = load_config()
    print(f"关注列表: {config.get('users', [])}")
    print(f"飞书配置: {config.get('feishu', {})}")