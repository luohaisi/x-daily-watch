# X Daily Watch

一个可运行在 Codex、Claude Code、OpenClaw、WorkBuddy 等 Agent 中的通用 Skill。它关注指定的 X/Twitter 账号，以 RSS 为主数据源，并用 FxTwitter v2 补全长帖、线程、引用、媒体和 Article。

不需要安装 Node.js、Python、`jq` 或其他依赖。

## 先分清显示名称和账号

X 账号常见的三个标识含义不同：

- 显示名称：例如 `Elon Musk`，可以修改，也可能重名。
- handle：例如 `@elonmusk`，是本 Skill 发起 RSS 和账号状态请求时使用的账号名。
- 数字用户 ID：接口可获取时用于确认是不是同一个账号，尤其适合防止改名后误关注。

因此，不要只告诉 Agent “关注马斯克”后让它猜。最稳妥的方式是提供 `@handle`；不知道 handle 时，复制该账号任意一篇公开帖子的链接发给 Agent 即可。

## 安装

把整个仓库作为一个 Skill 安装，入口文件是根目录的 [`SKILL.md`](SKILL.md)。

- Codex：在对话中让 `$skill-installer` 安装 `https://github.com/VictorAgents/x-daily-watch`。
- Claude Code：把仓库目录放到 `~/.claude/skills/x-daily-watch`，项目级安装可放到 `.claude/skills/x-daily-watch`。
- OpenClaw：运行 `openclaw skills install git:VictorAgents/x-daily-watch@main`。
- WorkBuddy 或其他 Agent：用其 Skill 导入功能指向仓库根目录；没有导入功能时，把 `SKILL.md` 作为持久指令加载。

安装后，在第一次使用时回答 Agent 的初始化问题：关注哪些账号、首次抓取多久、是否发送飞书通知（宿主支持时）以及是否创建定时任务。未明确同意前，Skill 不应发送外部消息或创建定时任务。

## 如何增加关注账号

可以在对话中使用以下任一种输入：

- `@elonmusk`
- `elonmusk`
- `https://x.com/elonmusk`
- `https://x.com/elonmusk/status/2085940169245356114`

前三种方式直接提供 handle。第四种方式适合只知道显示名称、不知道账号 handle 的情况：Agent 提取帖子数字 ID，请求帖子详情，读取作者的当前显示名称、handle 和数字用户 ID，然后先请你确认，再写入关注列表。

普通帖子链接通常形如：

```text
https://x.com/<handle>/status/<帖子数字ID>
```

链接后面的 `?s=...` 等分享参数不会影响识别。`t.co` 短链接需要先展开成可信的 X/Twitter 帖子地址；若链接是 `/i/status/<帖子数字ID>`、转发链接，或链接中的账号与详情作者不一致，Agent 应明确列出候选账号，让你选择，不能擅自关注。

### 示例一：已知 handle，关注伊隆·马斯克

对 Agent 说：

```text
使用 x-daily-watch 关注伊隆·马斯克，账号是 @elonmusk。
立即抓取最近 24 小时的推文，暂不发送飞书通知，也不创建定时任务。
```

Agent 应把 `Elon Musk` 作为显示名称、`@elonmusk` 作为抓取用 handle；确认后加入关注列表并执行一次抓取。

### 示例二：不知道 handle，粘贴马斯克的一篇帖子

对 Agent 说：

```text
我不知道这个账号的 ID，请关注这篇帖子的作者：
https://x.com/elonmusk/status/2085940169245356114
```

Agent 应从链接得到帖子 ID，通过详情接口确认作者为 `Elon Musk（@elonmusk）`，再询问：

```text
识别到 Elon Musk（@elonmusk），是否加入关注？
```

你确认后才会新增关注。以后换成其他人的任意公开帖子链接，操作相同。

## 常用对话命令

```text
查看关注列表
立即抓取一次
取消关注 @elonmusk
把首次抓取范围改成最近 48 小时
开启飞书通知
每天上午 9:00 抓取，时区 Asia/Shanghai
```

飞书通知和定时任务是否可用，取决于当前 Agent 是否具备相应能力。Skill 不会为了启用它们自行安装 SDK，也不会读取其他 Agent 的私有配置。

## 识别失败怎么办

- 帖子已删除、账号私密或接口暂时失败：换一篇该账号的公开帖子，或直接提供 `@handle`。
- 链接作者与转发者不同：让 Agent 同时显示两者，再明确说“关注原作者”或“关注转发者”。
- 账号改过 handle：数字用户 ID 一致时更新为当前 handle；若同一个 handle 对应了不同数字用户 ID，应暂停并由你确认。
- 只知道中文名或昵称：不要猜账号，先到 X 找到本人主页或一篇公开帖子，再把链接粘贴到对话中。

完整的抓取、补全、去重和故障降级规则见 [`SKILL.md`](SKILL.md)。
