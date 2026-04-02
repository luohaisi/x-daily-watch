#!/usr/bin/env python3
"""
X 大V每日追踪 - 主执行脚本
用详情 API 获取完整推文内容，正确判断长文

数据目录: ~/.openclaw/workspace/data/x-daily-watch/
配置文件: ~/.openclaw/workspace/data/x-daily-watch/config.json
飞书配置: 自动从 ~/.openclaw/openclaw.json 读取
"""

import sys
import json
import re
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from config_manager import (
    load_config, update_pushed_tweets, is_tweet_pushed,
    DATA_DIR
)
from twitter_client import get_user_tweets, get_tweet_detail
from feishu_doc import backup_long_articles, send_feishu_message


def clean_html(text: str) -> str:
    return re.sub(r'<[^>]+>', '', text)


def run_daily_push():
    """执行每日推送任务"""
    print(f"\n{'='*50}")
    print(f"X 大V每日追踪 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*50}\n")
    
    config = load_config()
    users = config.get("users", [])
    
    if not users:
        print("关注列表为空，请先添加关注用户")
        return
    
    # 检查飞书配置
    if not config.get("feishu"):
        print("❌ 飞书配置未找到，请在 ~/.openclaw/openclaw.json 配置 channels.feishu")
        return
    
    min_length = config.get("backup_config", {}).get("min_length", 500)
    
    all_tweets = []
    long_tweets = []
    
    for user in users:
        username = user["username"]
        max_tweets = user.get("max_tweets", 5)
        
        print(f"获取 @{username} 的推文...")
        tweets = get_user_tweets(username)
        
        if not tweets:
            print(f"  无法获取")
            continue
        
        print(f"  获取到 {len(tweets)} 条，获取详情...")
        
        count = 0
        for tweet in tweets:
            if is_tweet_pushed(tweet["id"]):
                continue
            
            detail = get_tweet_detail(tweet["id"])
            if not detail:
                continue
            
            detail["alias"] = user.get("alias", username)
            all_tweets.append(detail)
            
            # 计算完整字数
            text_len = len(detail.get("text", ""))
            if detail.get("quoted_tweet"):
                text_len += len(detail["quoted_tweet"].get("text", ""))
            
            if text_len >= min_length:
                long_tweets.append(detail)
                print(f"    发现长文: {text_len} 字")
            
            count += 1
            if count >= max_tweets:
                break
    
    if not all_tweets:
        print("\n没有新的推文需要推送")
        return
    
    print(f"\n准备推送 {len(all_tweets)} 条推文")
    print(f"其中 {len(long_tweets)} 篇长文（>={min_length}字）")
    
    # 生成推送消息
    message_parts = [f"# X 每日追踪 - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"]
    
    current_user = None
    for tweet in all_tweets:
        alias = tweet.get("alias", "unknown")
        if alias != current_user:
            current_user = alias
            message_parts.append(f"\n## {alias}\n")
        
        text = tweet.get("text", "")[:600]
        message_parts.append(f"\n{text}")
        if len(tweet.get("text", "")) > 600:
            message_parts.append("...")
        
        if tweet.get("quoted_tweet"):
            qrt = tweet["quoted_tweet"]
            message_parts.append(f"\n\n**转发 @{qrt.get('user_screen_name')}:**\n> {qrt.get('text', '')[:200]}...")
        
        message_parts.append(f"\n\n❤️ {tweet.get('likes', 0)} | 🔁 {tweet.get('retweets', 0)}")
        message_parts.append(f"\n🔗 {tweet.get('url', '')}\n")
    
    message = "\n".join(message_parts)
    
    # 先创建飞书文档（如果有长文）
    feishu_doc_url = None
    if long_tweets:
        doc_parts = [f"# X每日追踪 - 长文备份 - {datetime.now().strftime('%Y-%m-%d')}\n\n"]
        doc_parts.append(f"共 {len(long_tweets)} 篇长文\n\n---\n")
        
        for tweet in long_tweets:
            alias = tweet.get("alias", "unknown")
            
            doc_parts.append(f"\n## {alias}\n\n")
            doc_parts.append(tweet.get("text", ""))
            
            if tweet.get("quoted_tweet"):
                qrt = tweet["quoted_tweet"]
                doc_parts.append(f"\n\n**转发 @{qrt.get('user_screen_name')}:**\n\n")
                doc_parts.append(qrt.get("text", ""))
            
            doc_parts.append(f"\n\n❤️ {tweet.get('likes', 0)} | 🔁 {tweet.get('retweets', 0)}")
            doc_parts.append(f"\n🔗 {tweet.get('url', '')}")
            doc_parts.append("\n\n---\n")
        
        doc_content = "".join(doc_parts)
        
        # 保存本地备份
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(DATA_DIR / "long_articles.md", "w", encoding="utf-8") as f:
            f.write(doc_content)
        print(f"✅ 长文备份已保存到本地")
        
        # 创建飞书文档
        backup_enabled = config.get("backup_config", {}).get("enabled", True)
        if backup_enabled:
            print("正在创建飞书文档...")
            doc_title = f"X每日追踪-长文备份-{datetime.now().strftime('%Y-%m-%d')}"
            feishu_doc_url = backup_long_articles(doc_content, doc_title)
            if feishu_doc_url:
                print(f"✅ 飞书文档创建成功: {feishu_doc_url}")
                # 在消息末尾添加文档链接
                message += f"\n\n---\n\n📄 **长文备份文档**: {feishu_doc_url}\n共 {len(long_tweets)} 篇长文"
            else:
                print("❌ 飞书文档创建失败")
    
    # 保存推送消息
    with open(DATA_DIR / "push_message.md", "w", encoding="utf-8") as f:
        f.write(message)
    print(f"\n✅ 推送消息已保存")
    
    # 发送飞书消息
    print("正在发送飞书消息...")
    if send_feishu_message(message):
        print("✅ 飞书消息发送成功！")
    else:
        print("❌ 飞书消息发送失败")
    
    # 更新历史
    tweet_ids = [t["id"] for t in all_tweets]
    update_pushed_tweets(tweet_ids)
    
    # 保存统计
    stats = {
        "last_run": datetime.now().isoformat(),
        "total_tweets": len(all_tweets),
        "long_articles": len(long_tweets),
        "feishu_doc_url": feishu_doc_url
    }
    with open(DATA_DIR / "stats.json", "w") as f:
        json.dump(stats, f, indent=2)
    
    print(f"\n完成！共处理 {len(all_tweets)} 条推文")
    
    # 输出预览
    print("\n" + "="*50)
    print("【推送消息预览】")
    print("="*50)
    print(message[:1500])


if __name__ == "__main__":
    run_daily_push()