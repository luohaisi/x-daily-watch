#!/usr/bin/env python3
"""
Twitter/X 数据获取模块
使用 vxtwitter API 获取用户推文和详情
"""

import requests
import time
from typing import Optional
import xml.etree.ElementTree as ET

API_BASE = "https://api.vxtwitter.com"
REQUEST_DELAY = 1.5  # 请求间隔，避免限流


def get_user_info(username: str) -> Optional[dict]:
    """获取用户信息"""
    url = f"{API_BASE}/{username}"
    try:
        resp = requests.get(url, timeout=15)
        if resp.status_code == 200:
            return resp.json()
        return None
    except Exception as e:
        print(f"获取用户信息失败: {e}")
        return None


def get_user_tweets(username: str) -> Optional[list]:
    """获取用户最近推文列表（RSS feed 解析）"""
    url = f"https://fxtwitter.com/{username}/feed.xml"
    try:
        resp = requests.get(url, timeout=20)
        if resp.status_code != 200:
            return None
        
        root = ET.fromstring(resp.content)
        tweets = []
        
        for item in root.findall(".//item"):
            tweet = {
                "id": item.find("guid").text.split("/")[-1] if item.find("guid") is not None else None,
                "title": item.find("title").text if item.find("title") is not None else "",
                "link": item.find("link").text if item.find("link") is not None else "",
                "pubDate": item.find("pubDate").text if item.find("pubDate") is not None else "",
                "description": item.find("description").text if item.find("description") is not None else ""
            }
            if tweet["id"]:
                tweets.append(tweet)
        
        return tweets
    except Exception as e:
        print(f"获取推文列表失败: {e}")
        return None


def get_tweet_detail(tweet_id: str) -> Optional[dict]:
    """获取推文详情（含转发原文）"""
    url = f"{API_BASE}/status/{tweet_id}"
    try:
        time.sleep(REQUEST_DELAY)  # 避免限流
        resp = requests.get(url, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            
            result = {
                "id": data.get("tweetID"),
                "text": data.get("text", ""),
                "user_name": data.get("user_name"),
                "user_screen_name": data.get("user_screen_name"),
                "date": data.get("date"),
                "likes": data.get("likes", 0),
                "retweets": data.get("retweets", 0),
                "replies": data.get("replies", 0),
                "media_urls": data.get("mediaURLs", []),
                "url": data.get("tweetURL")
            }
            
            if data.get("qrt"):
                qrt = data["qrt"]
                result["quoted_tweet"] = {
                    "id": qrt.get("tweetID"),
                    "text": qrt.get("text", ""),
                    "user_name": qrt.get("user_name"),
                    "user_screen_name": qrt.get("user_screen_name"),
                    "url": qrt.get("tweetURL"),
                    "media_urls": qrt.get("mediaURLs", [])
                }
            else:
                result["quoted_tweet"] = None
            
            return result
        return None
    except Exception as e:
        print(f"获取推文详情失败: {e}")
        return None


def calculate_hotness(tweet: dict) -> int:
    """计算推文热度值"""
    return tweet.get("likes", 0) + tweet.get("retweets", 0) * 2


if __name__ == "__main__":
    print("测试 Twitter 客户端...")
    
    user = get_user_info("LufzzLiz")
    if user:
        print(f"用户: {user.get('name')} (@{user.get('screen_name')})")
        print(f"粉丝: {user.get('followers_count')}")
    
    detail = get_tweet_detail("2039170201208688927")
    if detail:
        print(f"\n推文: {detail['text'][:50]}...")
        print(f"热度: {calculate_hotness(detail)}")
