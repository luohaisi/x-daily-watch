---
name: x-daily-watch
description: "关注 X (Twitter) 大V，每日自动抓取推送，长文备份到飞书文档。支持对话管理关注列表。触发词：关注、取消关注、查看关注列表、手动抓取推文。"
---

# X 大V每日追踪 - OpenClaw 操作指南

## 快速开始

### 用户指令
用户可通过对话触发以下操作：

| 指令 | 功能 |
|------|------|
| `帮我关注 @username` | 添加用户到关注列表 |
| `帮我关注 @username 别名` | 添加用户并设置别名 |
| `取消关注 @username` | 移除用户 |
| `查看关注列表` | 显示所有关注用户 |
| `手动抓取一次推文` | 立即执行抓取和推送 |

---

## 技术架构

### 文件结构
```
~/.openclaw/workspace/
├── skills/x-daily-watch/          # 技能目录
│   ├── SKILL.md                   # 本文档
│   └── scripts/                   # 脚本目录
│       ├── config_manager.py      # 配置管理（自动读取飞书配置）
│       ├── twitter_client.py      # Twitter API 客户端
│       ├── feishu_doc.py          # 飞书推送和文档模块
│       └── fetch_and_push.py      # 主执行脚本
│
└── data/x-daily-watch/            # 数据目录（归档管理）
    ├── config.json                # 关注列表配置
    ├── history.json               # 历史记录（防重复推送）
    ├── push_message.md            # 最新推送消息
    ├── long_articles.md           # 长文备份内容
    └── stats.json                 # 执行统计
```

### 配置来源
| 配置项 | 来源 | 说明 |
|--------|------|------|
| 关注列表 | `data/x-daily-watch/config.json` | 用户通过对话管理 |
| 飞书配置 | `~/.openclaw/openclaw.json` | 系统级配置，自动读取 |
| 用户 ID | `openclaw.json` → `channels.feishu.allowFrom[0]` | 自动提取 |

---

## 脚本使用方法

### 主脚本：fetch_and_push.py

**位置**: `skills/x-daily-watch/scripts/fetch_and_push.py`

**执行方式**:
```bash
cd ~/.openclaw/workspace/skills/x-daily-watch/scripts
python3 fetch_and_push.py
```

**执行流程**:
1. 从 `data/x-daily-watch/config.json` 读取关注列表
2. 从 `~/.openclaw/openclaw.json` 自动读取飞书配置
3. 调用 vxtwitter API 获取每个用户的推文详情
4. 筛选 24 小时内推文，按热度排序
5. 检测长文（默认 ≥500 字）
6. 创建飞书文档保存长文
7. 发送完整消息到飞书
8. 更新历史记录防止重复推送

**依赖模块**:
- `config_manager.py` - 配置管理，自动读取飞书配置
- `twitter_client.py` - Twitter/X API 调用
- `feishu_doc.py` - 飞书消息和文档操作

---

## 定时任务配置

### Cron 配置

**位置**: OpenClaw Gateway cron 系统

**配置命令**:
```bash
# 添加定时任务
openclaw cron add --name "x-daily-watch-push" \
  --schedule "55 5 * * *" \
  --timezone "Asia/Shanghai" \
  --command "cd ~/.openclaw/workspace/skills/x-daily-watch/scripts && python3 fetch_and_push.py"
```

**当前配置**:
```json
{
  "name": "x-daily-watch-push",
  "schedule": {
    "kind": "cron",
    "expr": "55 5 * * *",
    "tz": "Asia/Shanghai"
  },
  "sessionTarget": "isolated",
  "payload": {
    "kind": "agentTurn",
    "message": "执行 x-daily-watch 技能..."
  }
}
```

**手动触发测试**:
```bash
openclaw cron run --id "x-daily-watch-push" --force
```

---

## 飞书配置要求

### 必需权限

在 [飞书开放平台](https://open.feishu.cn/app/) 配置以下权限：

| 权限 | 用途 |
|------|------|
| `docx:document` | 读取文档 |
| `docx:document:create` | 创建文档 |
| `im:message` | 发送消息 |

### 配置文件格式

**~/.openclaw/openclaw.json**:
```json
{
  "channels": {
    "feishu": {
      "enabled": true,
      "appId": "cli_xxx",
      "appSecret": "xxx",
      "dmPolicy": "allowlist",
      "allowFrom": ["ou_用户ID"]
    }
  }
}
```

脚本会自动从此文件读取：
- `appId` → 飞书应用 ID
- `appSecret` → 飞书应用密钥
- `allowFrom[0]` → 接收消息的用户 ID

### 权限测试

**测试文件位置**: `skills/x-daily-watch/scripts/feishu_doc.py`

**测试方法**:
```bash
cd ~/.openclaw/workspace/skills/x-daily-watch/scripts
python3 feishu_doc.py
```

**预期输出**:
```
测试飞书模块...
飞书配置: {'app_id': 'cli_xxx', 'app_secret': 'xxx', 'user_id': 'ou_xxx'}
✅ Token 获取成功: t-g10441dO3GEC...
```

---

## 配置文件说明

### config.json

**位置**: `~/.openclaw/workspace/data/x-daily-watch/config.json`

```json
{
  "users": [
    {
      "username": "LufzzLiz",
      "alias": "岚叔",
      "added_at": "2026-04-01",
      "max_tweets": 5
    }
  ],
  "backup_config": {
    "enabled": true,
    "min_length": 500
  }
}
```

| 字段 | 说明 | 默认值 |
|------|------|--------|
| `users[].username` | X 用户名 | 必填 |
| `users[].alias` | 显示别名 | username |
| `users[].max_tweets` | 每用户最多推送条数 | 5 |
| `backup_config.min_length` | 长文字数阈值 | 500 |

**注意**: 飞书配置不需要在此文件配置，自动从 `~/.openclaw/openclaw.json` 读取。

---

## 故障排查

### 问题 1: 飞书配置未找到

**错误信息**: `飞书配置未找到，请在 ~/.openclaw/openclaw.json 配置 channels.feishu`

**解决方案**:
1. 检查 `~/.openclaw/openclaw.json` 是否存在
2. 确认 `channels.feishu.enabled = true`
3. 确认 `appId` 和 `appSecret` 已配置

### 问题 2: 飞书文档无法访问

**原因**: 文档创建后未授权给用户

**解决方案**:
1. 在飞书开放平台添加 `drive:drive` 权限
2. 或手动分享文档给用户

### 问题 3: 推文获取失败

**可能原因**:
- vxtwitter API 限流（请求间隔已设为 1.5 秒）
- 用户名不存在或账号被封
- 网络问题

**排查**:
```bash
# 测试 API
curl "https://api.vxtwitter.com/elonmusk"
curl "https://fxtwitter.com/elonmusk/feed.xml"
```

---

## 数据文件说明

| 文件 | 说明 |
|------|------|
| `config.json` | 关注列表配置 |
| `history.json` | 已推送推文 ID，防止重复 |
| `push_message.md` | 最新推送消息内容 |
| `long_articles.md` | 长文备份内容 |
| `stats.json` | 执行统计信息 |

---

## 更新日志

### v1.0.0 (2026-04-01)
- 初始版本
- 支持关注管理（对话添加/移除）
- 每日自动推送（5:55 AM）
- 长文备份到飞书文档
- 飞书配置自动从系统读取
- 数据文件归档到统一目录