## Why

飞书手动 `/comment <昵称>` 现在会被两道**软筛选**挡下：小红书侧的「人设强相关」甄选（一篇都不强相关就换词、用尽则本次不评），Facebook 侧的「零重叠相关性」校验（`weak_relevance`），外加两侧的「每笔记/每帖去重」（已评过的一律跳过）。这些软筛选服务于**无人值守**的安全与质量，但当运营**刻意**要对某账号补一条评论、或要在没有强相关目标时也发一条、或要对已评过的目标再评时，当前无法表达这个意图——只能干等「本次不评」的黄卡。需要给操作员一个显式覆盖开关。

## What Changes

- 给飞书 `/comment <昵称>` 增加一个尾部开关 **`--force`**（复用现有 `--contact` / `--join` 的尾部开关解析，可任意顺序组合）。
- `--force` 让**手动命令路径**同时放开两道软筛选：**① 相关性校验**（小红书强相关甄选 + Facebook `weak_relevance`）；**② 每笔记/每帖去重**（允许对已评过的目标再评一条）。一个开关同时触发这两项。
- 小红书：`--force` 下仍先跑甄选角色；有强相关候选就用最优（收藏最高的强相关篇），**一篇都不强相关**时兜底选「全体候选里收藏最高的一篇」继续开帖→撰写→人审→发布，而不是换词/本次不评；同时跳过甄选前的去重过滤与发布前的去重复检。
- Facebook：`--force` 下取容器内搜索结果的第一个候选（不再跳过已评过的），并让相关性校验分支变 no-op（传空目标关键词）。
- **红线不动**：`--force` **绝不**放开——飞书人工审核闸（人是刹车）、Facebook 内容安全校验（链接/联系方式/@提及/刷屏/长度/低信号）、边端诚实闸（搜索关键词一致 / 页型 / 发布前就地核对 noteId / FB 成员态）、账号隔离（PII）。
- **零回归**：`--force` 只由飞书手动命令入口置位；自动排期评论、面板定向评论、热帖引流评论等自动路径绝不带此旗标，行为不变。
- 触发回执文案标注本次为 `--force`（跳过相关性/去重），便于操作员知情。

## Capabilities

### New Capabilities
<!-- 无新增能力：--force 是既有「操作员命令覆盖」能力的延伸，落在 manual-command-override，并修订两条内容侧 spec。 -->

### Modified Capabilities
- `manual-command-override`: 新增一条 requirement——`--force` 是操作员对**相关性 + 每笔记去重**的显式覆盖，与既有「只绕配额、绝不绕人审」覆盖同源、边界一致（仍守人审 / 内容安全校验 / 诚实闸 / 账号隔离）。
- `comment-search-command`: 修订「候选去重后强相关择优；不中则换搜索词重试、用尽诚实结束」与「命令评论……MUST 仍记每笔记去重」两条——为 `--force` 操作员覆盖开显式例外（可兜底选收藏最高的一篇、可再评已评过的），默认路径不变。
- `facebook-scheduled-comment`: 修订「Unattended Facebook composition uses hard validators」——`--force` 下跳过 `weak_relevance` 相关性判定，但 URL/联系方式/@提及/刷屏/长度/低信号等安全校验仍 MUST 保留。

## Impact

- **代码（纯 aidcp-cloud，7 跳接线）**：`src/feishu/commands.ts`（解析 + 选项类型 + 回执透传 + HELP_TEXT）、`src/server.ts`（`actions.comment` 选项 → `triggerManual`，与 `manualOverride` 分开）、`src/comment-agent/comment-scheduler.ts`（`triggerManual` / `runTask`（小红书）/ `runFacebookTargetedTask(Body)` / `runFacebookJoinThenComment`（Facebook）的相关性兜底与去重旁路分支）。
- **不碰**：两份 `protocol.ts`、`command-bridge.ts` 动作映射（无新协议消息）、边端代码。纯 cloud 端。
- **热点文件**：`comment-scheduler.ts` 为单写者热点，须与 `facebook-scheduled-comment` 串行、land 前 rebase 最新 master。
- **验收**：桩测覆盖（`--force` 组合解析、小红书兜底选 top-collect、Facebook 传空关键词跳过 `weak_relevance` 但仍拦 url/contact/spam、人审闸在 `--force` 下依然拦截）；真机验收登记新 backlog 簇。
