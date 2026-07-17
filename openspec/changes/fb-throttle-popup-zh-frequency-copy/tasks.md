## 1. 真机取证（阻塞词条定稿，不阻塞其余实现）

> **偏离说明（2026-07-17，实装时的显式决策）**：本节原设计为「词条 MUST 在真机坐实后才定稿合入」。实装时改为**先合入、真机验收后校正**，理由是**失败方向是安全的**：词条不命中 = 回落到今天的静默行为（现状），**不会误伤**；真正要防的是反向的误报（一次即 `restricted`、钉住恢复窗且不自动回滚）。既然误报风险由「长专属句片段 + 否定用例」控制、而漏报只是维持现状，把词条压在真机之后只会让修复空等一个真机窗口。
>
> 转录风险由**词条构造**对冲而非等待：词条刻意不含标点（全 / 半角未坐实）、不含「社群 / 社区」（地区差异未坐实）、「你 / 您」两版并列。**残留未验的是「发帖」二字**——若 FB 实际用「发布」/「发文」，两条会空转、只剩 `执行其他操作的频率` 兜底。此项已转真机验收簇 91.1，须按真实原文校正。

- [x] 1.1 用 CDP 在真机 FB 环境抓取限流弹窗出现时的整页文本，逐字记录原文（含标点形态与用词），存证到本 change 目录或 backlog 条目 <!-- 转真机 backlog 簇 91.1（本机无法触发真实平台限流；需运营在真机 session 跑） -->
- [x] 1.2 据 1.1 原文定出词条集合：取整句最不可能随版本变动的中段；核对**不含**「限制」/「频率」裸词（spec：判据只用长专属句片段） <!-- edge 26ef2cb 按用户转录文案定稿三条，避开标点/地区差异面；「发帖」用词待簇 91.1 校正 -->
- [x] 1.3 顺带验证 design.md 的假设「遮罩快照候选为空」是否成立；若非空则记录实际命中的分支（回填逻辑降级为无害兜底，本 change 仍成立） <!-- 转真机 backlog 簇 91.3 -->
- [x] 1.4 若真机抓到同框架的其他频率文案变体，一并记录；**未见过的变体不进词库**（design 决策：抓到几条收几条） <!-- 转真机 backlog 簇 91.1；已守「不凭空扩充」：未加任何用户未报告的变体 -->

## 2. aidcp-edge — 证据回填 + 词库

> 先做 2.2（证据回填），它不依赖真机取证，且是本 change 的真正价值点——不修它，词库补了也只到降速档。

- [x] 2.1 遮罩分类模块：限流判据加入 §1.2 定稿的中文频率框架句片段（**依赖 1.2**） <!-- edge 26ef2cb 新增 FB_THROTTLE_ZH_FREQUENCY_PHRASES（overlay.ts）并接入 classify -->
- [x] 2.2 主进程遮罩上报分支：判为阻断态且快照候选为空导致证据文案缺失时，用分类判定时已取得的同一份页面文本回填，截断至有界长度（500–1000 字量级） <!-- edge 26ef2cb 新增 backfillOverlayEvidenceText + FacebookOverlayMonitor.lastScanText；截断上限 OVERLAY_EVIDENCE_MAX_CHARS=1000 -->
- [x] 2.3 确认 2.2 未改变分类判定本身，且快照候选非空时沿用原证据、不覆盖（spec 三个 Scenario） <!-- edge 26ef2cb 三条断言全覆盖；另补「无同源文本时不臆造」与「快照整个失败时仍送达证据」两例 -->
- [x] 2.4 **不碰**遮罩快照的 DOM 可信阈（尺寸阈值 / 关闭控件启发式）——design 决策 2 明确否决，误报代价 3 天 <!-- 已守：overlay-monitor.ts 的 includeForKind/reasonsFor 零改动 -->
- [x] 2.5 单测：词条命中频率框架文案 → 判为阻断态 <!-- edge 26ef2cb 含「你/您」变体与半角标点转录变体 -->
- [x] 2.6 单测（**本 change 的钉**）：判为阻断态 + 快照候选为空 → 上报载荷证据文案非空 <!-- edge 26ef2cb -->
- [x] 2.7 单测：正常页面含「限制」/「频率」裸词但无句片段 → 不命中 <!-- edge 26ef2cb 三条良性文案（群规则/通知设置/广告频率）+ 词条形态断言（不含标点、不含社群/社区、长度≥6） -->
- [x] 2.8 单测：词条集合锁（与云端侧集合语义一致，任一侧漂移即失败） <!-- edge 26ef2cb 与 cloud 8944f75 两侧各锁同一份三条表 -->

## 3. aidcp-cloud — 词库同步 + 告警标注

- [x] 3.1 限流词库同步 §1.2 定稿的同一批中文词条（**依赖 1.2**，与 2.1 词条集合语义一致） <!-- cloud 8944f75 -->
- [x] 3.2 消除两仓现存漂移：云端独有、边缘判据没有的英文条目（今天是死代码：边缘不分类就永不上报）——补齐边缘侧或删除云端侧，二选一并说明理由 <!-- 两条反向处理：'we restrict certain content and actions' 补进边缘判据使其可达（edge 26ef2cb，特异性足够）；'we removed your' 删除（cloud 8944f75）——措辞过宽，"We removed your post…" 会出现在通知中心与历史记录，一条陈年内容删除通知即可把账号打进 restricted -->
- [x] 3.3 阻断协调器：把「已确认限流」这一布尔事实的作用域提升，透传至告警构造（现状是块级局部变量、从未传出） <!-- cloud 8944f75 throttled 提至与 status 同层 + maybeAlert 加参 -->
- [x] 3.4 告警构造：命中限流 → 独立类型 + P0 + 标题明确指认「Facebook 限流阻断」；未命中判据的未知遮罩仍走既有泛化类型与优先级（spec：行为不变） <!-- cloud 8944f75 type='fb_throttle' -->
- [x] 3.5 告警冷却键加类型维度，避免跨类型吞没；确认落库动作在冷却闸之后，故本改动同时修好「卡片不发」与「记录不落」两者 <!-- cloud 8944f75 key=`${edgeId}:${type}`；**连带修 onCleared**：裸 edgeId 在分维键下删不中任何键→冷却残留→清除后新事件被旧冷却压住，改用 clearCooldown 按前缀清该 edge 全部类型（原 tasks 未预见此耦合） -->
- [x] 3.6 确认告警类型取值不需要 DB 迁移（类型字段为裸文本无 CHECK；仅优先级被约束在 P0–P3） <!-- 已核 alert-store.ts：alerts.type 为 TEXT NOT NULL 无 CHECK；零迁移 -->
- [x] 3.7 确认告警路由沿用统一口径（来源会话 → 团队群 → 默认群），**不引入任何路由特例** <!-- 已核 resolveChatId 注入口未改动 -->
- [x] 3.8 单测（**必补，现有是假绿盲区**）：现有告警测试把消息通道打成 undefined、告警函数第一行即返回 → 告警标注改动会零覆盖上线。补一条**带真实消息通道**的用例断言类型与优先级 <!-- cloud 8944f75 新增 makeAlertingCoordinator（真 messenger + alertStore），断言 severity/type/title + 飞书卡真发出 -->
- [x] 3.9 单测：冷却不跨类型吞没（同边缘先验证码后限流 → 限流告警照发且记录落库）；同类型冷却行为不变 <!-- cloud 8944f75 另补「不同 edge 互不影响」与「cleared 清冷却不漏删」两例 -->
- [x] 3.10 单测：词条集合锁（与边缘侧对齐） <!-- cloud 8944f75 另补「词库不含 we removed your」断言，锁住 3.2 的删除决策 -->

## 4. 验证与回归

- [x] 4.1 edge：`npm run test:acceptance` → `npm test` → `npm run typecheck`（既定次序） <!-- acceptance 22/22、全量 1590/1590、typecheck exit 0 -->
- [x] 4.2 cloud：`npm run test:acceptance` → `npm test` → `npm run typecheck` <!-- acceptance 54/54、全量 2353（0 fail）、typecheck exit 0（单独取真实退出码，未用 `|tail` 假绿口径） -->
- [x] 4.3 确认风控红线全过：`AC-RISK-*`（绝不自残、被禁 record 返 false）——本 change 触碰风控输入面 <!-- 含在 acceptance 全绿内 -->
- [x] 4.4 确认 `AC-PROTO-*` 未受扰动：本 change **不改协议**，两份 `protocol.ts` 消息总数不变（该断言值不因本 change 变动） <!-- 两份 protocol.ts 零改动；AC-PROTO 全绿 -->
- [x] 4.5 确认诚实红线两向皆守：未把限流下的评论算成功；也未把已被服务器确认的评论因限流弹窗改判失败（评论执行器现有立场不推翻） <!-- comment-executor.ts 零改动；转真机簇 91.7 复验 -->
- [x] 4.6 确认小红书零回归（词条为 FB 专属措辞，换 XHS 零命中） <!-- 词条为 FB 专属中文措辞；XHS 侧代码零改动；cloud 既有「非限流文案 → 仍 warned」护栏用例仍绿 -->

## 5. 集成与部署

- [x] 5.1 两仓分别提交推送（edge / cloud 默认分支 `master`）；提交显式列文件，不 `git add -A` <!-- edge 26ef2cb / cloud 8944f75，均经 scripts/land-change ff 推送；已用 merge-base --is-ancestor 确认两 sha 在 origin/master 上 -->
- [x] 5.2 cloud 按标准安全序列部署 dev：`scripts/deploy-target dev --check` → ECS 先备份 → `rsync`（排除 `.env` / `node_modules` / `.git`）→ `systemctl restart aidcp-cloud.service` → healthcheck → 失败即回滚。**绝不碰同机 isales** <!-- 2026-07-17 deployed；备份 /opt/aidcp/cloud.bak.20260717-094346.tar.gz；部署前探得 ECS 两文件 md5 == 前一 master 9ccf545（无并发漂移）、近 1h 无他人部署；因主 checkout 有他人未跟踪文件 `1`（脏工作区），按 §6 改用 `git archive 8944f75` 干净快照 rsync；部署后线上 md5 == 目标提交；healthcheck 全绿（active / 8787+8090 listening / 飞书长连接已建立 / isales 8000+80 未受影响）；依赖未变故未跑 npm ci -->
- [x] 5.3 edge 改动随默认收尾提交推送即可，**不出安装包**（打包属用户显式触发） <!-- 已守：未跑 electron:build -->
- [x] 5.4 tasks.md 回写：按 `<!-- <repo> <commit-sha> 备注 -->` 标注，部署后追加 `<!-- <date> deployed -->`；sha MUST 取自已推送提交（判据：`git merge-base --is-ancestor`） <!-- 本文件 -->

## 6. 真机验收登记与收口

- [x] 6.1 真机验收项登记 `docs/real-machine-acceptance-backlog.md`，归入现有 FB 簇（82 / 88）：① 词条对真弹窗逐字命中；② 快照候选为空这一假设确认；③ 告警确为 P0 + 独立类型；④ 账号确实迁到 `restricted` 而非仅降速 <!-- 新起簇 91（7 项，共享 FB 环境同簇 82/88/90）；较原计划多两项：91.2 正常页面不误报（否定验收，与命中同等重要）、91.6 冷却不跨类型吞没、91.7 回执诚实性 -->
- [x] 6.2 **另行登记**（不在本 change 范围）：孤儿 spec 清账——change `account-nurture-discipline-spine` 的 spec delta 只存在于分支 `feature/fb-full-integration`，代码已进 edge/cloud master 而文档从未合回 `main`，致主干 spec 缺失「FB 限流信号 → 激进退避到 `restricted`」这条需求 <!-- 见本节末「孤儿 spec 清账」小节 + memory fb-throttle-popup-zh-frequency-copy -->
- [x] 6.3 `openspec validate fb-throttle-popup-zh-frequency-copy --strict` 通过 <!-- 2026-07-17 valid -->
- [x] 6.4 归档（archive 时 `specs/` delta 并入 `openspec/specs/captcha-incident-handling/`） <!-- 2026-07-17 archived -->

### 孤儿 spec 清账（本 change 之外，待单独处理）

实装期核实：主干 spec **缺失**「Facebook 限流信号 → 激进退避到 `restricted`」这条需求。

- 它属 change `account-nurture-discipline-spine`，spec delta 在 `feature/fb-full-integration:openspec/changes/account-nurture-discipline-spine/specs/captcha-incident-handling/spec.md`
- 该 change 的**代码已进** edge/cloud master（`facebook-throttle-signals.ts` 即其产物），**文档从未合回 `main`**（`git merge-base --is-ancestor 5a76229 origin/main` = 否）
- 同 memory `fb-full-integration-design` 记的「隔离分支未合回 main → 清账必漏」
- 本 change 的新增需求**刻意与其不重叠**（只覆盖「文案覆盖面 + 证据非空 + 告警可辨」），避免两 change 抢同一 capability

**建议**：单开一个清账 change 把该孤儿 delta 合回主干（或确认其已被取代后显式废弃）。**勿在本 change 内顺手搬运**。
