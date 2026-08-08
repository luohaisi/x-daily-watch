---
name: x-daily-watch
description: 追踪一个或多个 X/Twitter 账号，支持从 @handle、主页 URL 或任意公开帖子链接识别并关注作者，完整获取新帖、回复、长帖、线程、引用、媒体和 X Article，去重后在当前 Agent 或可用通知渠道中交付。使用 RSS 作为主内容源、FxTwitter v2 作为覆盖校验和故障降级。适用于“关注/取消关注 X 账号”“粘贴帖子链接新增关注”“查看关注列表”“抓取最新推文”“每日汇总”“定时追踪”“发送飞书通知”等请求，也适用于 Codex、Claude Code、OpenClaw、WorkBuddy 及其他支持 Agent Skills 或 Markdown 指令的 Agent。
---

# X Daily Watch

完整追踪用户指定的 X 账号。优先使用文字说明和 `curl`，不要安装依赖，不要创建飞书长文文档，不要截断正文。

## 安装

把整个仓库作为一个 Skill 目录安装；根目录已经包含所需的 `SKILL.md`，不需要 Node.js、Python、`jq` 或包管理器。

- Codex：让 `$skill-installer` 从 `https://github.com/VictorAgents/x-daily-watch` 安装，或把目录放入用户的 `.agents/skills/x-daily-watch`。
- Claude Code：把目录放入 `~/.claude/skills/x-daily-watch`，项目内安装则使用 `.claude/skills/x-daily-watch`。
- OpenClaw：运行 `openclaw skills install git:VictorAgents/x-daily-watch@main`；需要全局可用时按宿主规则添加 `--global`。
- WorkBuddy 和其他 Agent：使用其 Skill 导入功能指向仓库根目录；如果没有导入命令，把目录放入该 Agent 的 Skills 根目录，或直接把 `SKILL.md` 作为持久指令加载。

安装后立即调用一次 `x-daily-watch` 完成下面的首次运行询问。安装器不能执行交互钩子时，必须在第一次实际运行前完成询问。

## 核心约束

- 把 RSS 当作主内容源，把 FxTwitter v2 当作覆盖校验、完整正文补全和故障降级源。
- 正常运行时先请求 RSS，再请求 v2 校验覆盖范围；合并两个来源，而不是重复输出。
- 获取所有新增内容，不设置“每个账号最多 N 条”，不按热度丢弃内容。
- 保留普通帖、回复、长帖、完整线程、引用正文、媒体链接和 Article 正文。
- 不把 RSS 中以 `…` 结尾的 141 字标题当成完整正文。
- 不把 `count=100` 当成必定返回 100 条；始终处理 `cursor.bottom` 分页。
- 不把 `since` 当成结果过滤器；它只用于无更新时的 204 快速判断。按时间戳和推文 ID 在本地筛选。
- 不创建飞书文档。启用飞书时发送完整消息；超出单条消息限制时分片，绝不截断。
- 不在仓库、日志或回复中保存或展示访问令牌、机器人密钥和其他凭证。

## 首次运行

把安装阶段和第一次调用视为同一个初始化过程。宿主支持安装钩子时立即询问；不支持时，在第一次执行本 Skill 前询问。

1. 询问要关注的 X 账号；接受 `@handle`、个人主页 URL、不带 `@` 的 handle 或该账号任意一篇公开帖子的 URL。用户不知道 handle 时主动提示：“复制该账号任意一篇公开 X 帖子的链接发给我即可识别作者。”按“通过帖子链接识别账号”完成核验后再加入关注列表。
2. 询问首次抓取范围；用户没有指定时采用最近 24 小时，不默认导入整个历史 feed。
3. 检查当前 Agent 是否具有飞书消息能力。
   - 有能力时询问：“是否发送飞书通知？”
   - 用户同意后再询问接收目标，并在再次确认后发送一条测试消息。
   - 没有能力时说明当前宿主不支持并跳过；不要自行安装飞书 SDK 或读取其他 Agent 的私有配置。
4. 询问：“是否创建定时任务？”
   - 用户同意后再询问频率、时间和时区。
   - 优先使用当前 Agent 的原生自动化或调度功能。
   - 宿主没有调度能力时，只给出该系统可用的 cron、任务计划程序或等价说明；不要擅自创建后台任务。
5. 未得到明确同意前，不发送外部消息、不创建定时任务、不执行测试通知。

将非敏感状态保存在当前 Agent 约定的持久化位置，不要写回 Skill 仓库。至少保存：

- 关注账号的当前 handle、显示名称和可选别名
- 可获取时保存账号的稳定数字用户 ID，用于识别 handle 改名或被他人重新注册
- 每个账号最后一次完整成功的 UTC 时间
- 最近已经交付的推文 ID；设置合理的滚动上限
- 飞书通知是否启用及接收目标的非敏感标识
- 定时任务是否启用、频率和时区
- 初始化是否完成

## 对话操作

识别并执行以下自然语言意图：

- “关注 @handle”：校验 handle 后加入关注列表。
- “关注这篇帖子的作者：<帖子 URL>”：从 URL 和帖子详情识别作者，展示“显示名称（@handle）”并在确认后加入。
- “我不知道账号 ID/用户名”：提醒用户复制该账号任意一篇公开帖子的链接。
- “取消关注 @handle”：移除账号，但保留历史去重记录，除非用户明确要求清除。
- “查看关注列表”：显示账号、别名、最后成功时间和上次运行状态。
- “抓取一次”“立即更新”：执行一次完整抓取。
- “开启/关闭飞书通知”：先确认能力和接收目标，再修改设置。
- “设置/取消定时任务”：通过当前 Agent 的调度能力执行，并报告实际创建或删除的任务。

只接受 1 至 15 位英文字母、数字或下划线组成的 handle。把 URL 和 `@` 前缀规范化后再使用；handle 比较和去重不区分大小写，保存接口返回的当前拼写。

### 通过帖子链接识别账号

不要把可重复、可随时修改的显示名称当作账号标识。X 上的 `Elon Musk` 是显示名称，`@elonmusk` 才是用于抓取的 handle；接口中的数字用户 ID 用于校验账号身份连续性。

接受 `x.com`、`twitter.com` 的常见 `www`/`mobile` 子域和 `fxtwitter.com` 的公开帖子链接。忽略查询参数和片段，从路径中的 `/status/<数字 ID>` 提取 2 至 20 位帖子 ID。普通链接形如 `/<handle>/status/<id>`，可把第一段作为候选 handle；`/i/status/<id>` 或其他不含 handle 的链接必须通过帖子详情确定作者，绝不能把 `i` 当作账号。输入 `t.co` 短链接时先跟随重定向，只有最终主机属于上述允许列表且路径包含帖子 ID 时才继续。

使用帖子 ID 请求详情：

```bash
curl --fail-with-body --silent --show-error --location \
  --max-time 30 --retry 2 \
  -H "Accept: application/json" \
  -A "x-daily-watch/2" \
  "https://api.fxtwitter.com/2/status/<status_id>"
```

按以下规则处理：

1. 要求 HTTP 成功、JSON 中 `code` 为 `200`，且 `status.id` 与 URL 的帖子 ID 相同。
2. 优先读取 `status.author.screen_name`、`status.author.name` 和 `status.author.id`；仅在 `status.author` 缺失时回退到顶层 `author`。不要误用 `status.quote.author`、`replying_to` 或 `reposted_by`。
3. URL 中的候选 handle 与详情作者一致时，向用户确认：“识别到 Elon Musk（@elonmusk），是否加入关注？”确认后才保存。
4. 两者不一致时同时展示候选账号和详情作者，不要静默选择。若 `reposted_by.screen_name` 与候选账号相同，询问用户要关注转发者还是原作者；其他冲突也必须确认。
5. 详情请求失败时，普通 `/<handle>/status/<id>` 链接只能给出“未验证的候选 handle”并请求确认；`/i/status/<id>` 等无 handle 链接无法安全识别，要求用户换一条公开帖子或直接提供 `@handle`。
6. 写入关注列表前按 handle 不区分大小写去重。若已保存数字用户 ID，以数字 ID 作为账号身份校验键；同一数字 ID 返回新 handle 时更新 handle，同一 handle 返回不同数字 ID 时暂停抓取并询问用户，防止改名后关注到另一个账号。

## 抓取工作流

### 1. 确定增量边界

对每个账号读取：

- `last_success`：上次该账号所有发现内容都被完整处理后的 UTC 时间。
- `seen_ids`：已经成功交付的推文 ID。

首次运行使用用户选择的回溯时间。后续运行使用 `last_success`，同时保留少量重叠时间以抵抗缓存和乱序，并依靠 ID 去重。

### 2. 先获取 RSS

使用：

```bash
curl --fail-with-body --silent --show-error --location \
  --max-time 30 --retry 2 \
  -H "Accept: application/rss+xml" \
  -A "x-daily-watch/2" \
  "https://fxtwitter.com/<handle>/feed.xml"
```

把以下情况判定为 RSS 失败：

- HTTP 非 2xx、超时或连接失败
- 响应不是可解析 XML
- 缺少 `channel` 或有效 `item`
- 条目缺少可提取的推文 ID

从每个 `item` 提取 `link` 或 `guid` 中 `/status/<id>` 的数字 ID、`pubDate`、`title`、`description`、`enclosure` 和媒体信息。解码 HTML 实体并规范化空白，但保留正文内部的换行语义。

RSS 标题满足以下任一条件时，不得当成完整正文：

- 长度为 141 且以 Unicode `…` 结尾
- 以 `...` 或其他明显省略标记结尾
- `description`、卡片或链接显示它是 Article、线程、引用或结构化长内容
- RSS 条目无法证明正文完整

### 3. 用 v2 校验覆盖并补全

即使 RSS 成功，也要在完整性模式下请求账号状态接口，以覆盖 RSS 可能缺少的回复、线程、Article 或超出 feed 窗口的内容。RSS 仍先处理；v2 只补充缺失 ID 和更完整的结构化字段。

第一页使用：

```bash
curl --get --fail-with-body --silent --show-error --location \
  --max-time 30 --retry 2 \
  -H "Accept: application/json" \
  -A "x-daily-watch/2" \
  --data-urlencode "count=100" \
  --data-urlencode "since=<last_success_epoch_seconds>" \
  --data-urlencode "with_replies=true" \
  --data-urlencode "groupthreads=true" \
  "https://api.fxtwitter.com/2/profile/<handle>/statuses"
```

没有 `last_success` 时省略 `since` 参数；不要传空字符串或伪造时间戳。

不要依赖 `jq`。让当前 Agent 直接读取 JSON。

处理响应：

- `204`：v2 没有检测到晚于 `since` 的内容；仍保留 RSS 发现的有效新条目。
- `200`：把 `type: status` 直接加入候选；把 `type: thread` 的 `statuses` 按顺序展开。
- 其他状态、无效 JSON 或错误码：记录 v2 失败，继续评估 RSS 是否足以提供完整内容。

存在下一页时，传响应中的 `cursor.bottom`，不要传整个 `cursor` 对象：

```bash
curl --get --fail-with-body --silent --show-error --location \
  --max-time 30 --retry 2 \
  -H "Accept: application/json" \
  -A "x-daily-watch/2" \
  --data-urlencode "count=100" \
  --data-urlencode "with_replies=true" \
  --data-urlencode "groupthreads=true" \
  --data-urlencode "cursor=<cursor.bottom>" \
  "https://api.fxtwitter.com/2/profile/<handle>/statuses"
```

继续分页，直到满足以下任一条件：

- 已覆盖到 `last_success` 之前且本页没有新的未见 ID
- `cursor.bottom` 为空
- 服务明确返回无内容

设置防失控页数保护。触发保护时报告账号抓取未完成，不要静默丢弃内容，也不要推进 `last_success`。

### 4. 单条补全

对 RSS 中被截断、结构不明确或没有在账号 v2 页面中得到完整字段的 ID，请求：

```bash
curl --fail-with-body --silent --show-error --location \
  --max-time 30 --retry 2 \
  -H "Accept: application/json" \
  -A "x-daily-watch/2" \
  "https://api.fxtwitter.com/2/status/<status_id>"
```

按以下优先级构造完整内容：

1. Article：递归检查当前 `status`、`status.quote`、线程中的每个 status 及其 quote。Article 可能位于 `status.article`，也可能位于 `status.quote.article`。找到后读取 `article.title`，再按原顺序处理 `article.content.blocks` 中所有带 `text` 的块；保留标题、段落、列表、引用、媒体实体和块顺序，不要只读取顶层 `status.article`。
2. 长帖或普通帖：读取 `status.raw_text.text`，缺失时回退到 `status.text`。
3. 引用：附上完整引用正文、作者和原始链接，不只保留当前帖中的引文。
4. 媒体：保留图片、视频或 GIF 的 URL、类型和可用替代文本。
5. 线程：优先使用详情响应中的线程；不完整时请求 `https://api.fxtwitter.com/2/thread/<status_id>`。把响应的根 `status` 与 `thread[]` 合并，按 `created_timestamp` 排序，只保留该作者在目标会话中的有序内容；不要假设线程一定嵌套在 `thread.statuses`。

单条补全失败时，把该 ID 留在待重试集合中。不要发送截断正文，不要把它加入 `seen_ids`。

### 5. 合并两个来源

使用推文数字 ID 作为唯一主键：

- 两个来源都有同一 ID：只输出一次。
- RSS 正文明显完整且与 v2 一致：正文来源记为 RSS，v2 只补元数据。
- v2 提供更长正文、Article、线程、引用或媒体结构：采用 v2 的完整版本。
- 只有 RSS：只在正文可确认完整时交付；否则执行单条补全。
- 只有 v2：按完整 v2 内容交付，通常是回复、线程成员或 RSS 窗口外内容。
- 两边内容冲突：选择信息更完整的版本并记录诊断，不要拼接成重复正文。

为每条结果保留 `status_id`、作者、发布时间、原始链接、内容类型、正文来源和补全来源。

### 6. 本地筛选和排序

- 使用 `created_timestamp` 或解析后的 `pubDate` 做 UTC 比较。
- 只交付晚于增量边界且不在 `seen_ids` 的内容。
- 不要因为 `since` 出现在请求里就跳过本地过滤；响应可能仍包含更早内容。
- 按发布时间升序交付，使线程和每日汇总可连续阅读。
- 不按点赞数、转发数或热度删除内容。

## 交付完整正文

默认在当前对话返回完整内容。用户启用通知时，再使用当前 Agent 已有的通知能力。

每条内容至少包含：

- 作者和 `@handle`
- 完整发布时间
- 完整正文
- 完整引用或线程上下文
- 媒体链接和可用替代文本
- 原始 X 链接
- `RSS`、`FxTwitter v2` 或二者合并的来源说明

遇到平台消息长度限制时：

- 优先按推文边界拆成多条消息。
- 单篇 Article 仍过长时按标题和段落拆分，标注“第 n/m 部分”。
- 发送全部分片后才把该 ID 标记为成功。
- 不使用 `[:N]`、`...` 或“阅读全文”链接代替正文。
- 不创建飞书长文文档。

## 成功、降级与检查点

- RSS 成功、v2 失败：交付 RSS 中能够确认完整的内容；保留无法补全的 ID，并报告降级状态。
- RSS 失败、v2 成功：使用 v2 完成该账号本轮内容。
- 两者成功：合并、去重并以完整版本为准。
- 两者失败：报告该账号失败，不更新任何成功检查点。
- 某条消息或分片发送失败：不要把该 ID 标为已交付。
- 只有当该账号本轮发现的所有 ID 都被完整处理或明确仍在待重试集合中时，才更新逐条状态；只有全部成功时才推进账号的 `last_success`。

RSS 与 v2 都由 FxTwitter 提供，只能形成接口级冗余。不要声称它们能抵抗 FxTwitter 整体不可用。用户需要供应商级冗余时，建议另行配置官方 X API，并明确其凭证、费用和速率限制。

## 运行后报告

简洁报告：

- 每个账号由 RSS、v2 或二者合并发现的数量
- 新增、重复、补全、失败和待重试数量
- 是否发生分页、降级或内容冲突
- 通知是否发送完整、定时任务的实际状态
- 每个账号是否推进 `last_success`

不要把“命令退出码为 0”单独当成成功证据；以完整内容、去重结果、交付状态和检查点为准。
