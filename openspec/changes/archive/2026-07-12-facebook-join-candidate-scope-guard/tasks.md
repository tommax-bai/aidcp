> **P0 安全修复**：现网今天就可能加错群（推荐栏异群 join 被误点）。edge-only、无协议、无云端。单独即让 pending 场景 fail-safe；是 L2（`facebook-join-actuation-decouple`）clickTarget 匹配的作用域前置。

> **2026-07-12 评审订正**：承重判据从「异群链接排除（黑名单、fail-open）」翻为「目标群头部块正向包含（白名单、fail-closed）」——真机 dump 证实推荐位 join 是兄弟裸 `div` 无异群 `href`、黑名单漏排会误点异群。异群链接（E1）与推荐轮播容器（E2）降为 corroborating 排除。头部块祖先判据须真机校准后方 land。

## 0. 实装前硬前置（真机确认探针）

- [x] 0.1 **头部块祖先判据校准 + 非锚点推荐位形态（承重、决定能否 land）**：**已真机校准完成（2026-07-12，运营机 AdsPower，账号已登录、中文 chrome，群 258908555514638 / 1327258819440839 / 774476963231812）**。只读探针 `scripts/fb-group-scope-probe.ts`（原样注入发货 `SCOPE_HELPERS_JS` + 结构 dump）+ 真实 executor 驱动 `scripts/fb-join-live-drive.ts`。坐实：① 目标群名恒为 `[role=main]` 内**单一 `<h1>`**、其自身 Join「加入小组」正确在域、头部块解析到 `[role=main]`（3 群一致）；② 真实「相关小组/发现更多小组」推荐卡片**不用 `<h1>`**（用链接/纯文本）→ 页面群名 h1 唯一、v4/v5 的「卡片竞争 h1」在真机不出现；③ 每张真实推荐卡片的异群 join 是裸 `div[role=button]`、其异群 `/groups/<id>` 锚点距 join 钮仅 **2–4 跳**（`foreignDescBoundaryHops ∈ {2,3,4}，无一为 -1`）→ 承重的 `__hasForeignGroupRef` 后代扫描恒能检出，「纯 JS 闭包无属性」fail-open 形态**未出现**；④ 不可用群「内容暂时无法显示」→ `scopeResolved=false` → not_ready（fail-closed 正确）；⑤ 嵌套 `[role=main]` 见于 `/groups/discover`（2 个），但群落地页为 1。<!-- 探针 aidcp-edge 571736b -->
- [x] 0.2 E1/E2 定档：真机确认推荐卡片异群 `/groups/<id>` 编码在**卡片内锚点**（`a[href]`，非纯闭包）、距 join 钮 2–4 跳后代；E1 候选祖先链走不到（异群锚点是兄弟子树、非候选祖先）故承重靠 D1 后代扫描而非 E1。E2 推荐轮播容器选择器未定档（`div.x9f619.x1n2onr6` 等混淆类名不稳）、暂不接线，D1 已足。<!-- 真机 571736b -->

## 0b. 真机校准揭示的回归修复（2026-07-12，承重头部判据）

- [x] 0b.1 **头部块「加群后『相关小组』takeover」过度 fail-closed 修复（承重、真机 2/2 复现）**：真机发现——加群成功后 FB 弹「相关小组」takeover，其异群 join 栏与目标 h1 **共享一个 `[role=main]` 之下的中层 `div`**（栏是目标头部的兄弟子树）。早前 v4「walk 没停在 ceiling 就拒该 heading」把**唯一的目标 h1** 也拒掉 → `scopeResolved=false` → 成员信号（收窄到未解析块）为空 → **成功加群误报 `join_failed`、已加入群误读 `not_ready`**（fail-safe，栏 join 仍全出域，但打断 happy path=真实可用性回归）。**修法**（`__resolveHeaderBlock`）：单一群名 h1（真实 FB 群页/成员页/takeover 均如此）→ 用其**最后一个干净祖先**作块（含目标自身 CTA、结构性排除兄弟栏）；多 heading → 保留 v4/v5 甄别（唯一「停在 ceiling」者，≥2 对称→歧义 fail-closed）。**真机验证**：修后 fresh 加群 `ok=true`、post `scopeResolved=true`、`mainCtaText=已加入`、`membershipSignals=[已加入]`、**`outOfScopeJoinCount=10`**（10 个别群 join 仍全出域，安全不变）。residual（真机未见、诚实记录）：目标页自身无 h1 而推荐卡片有 h1 → 单 heading 分支会误接受（真实 FB 目标恒有 h1、卡片从不用 h1，不触发）。<!-- aidcp-edge 571736b __resolveHeaderBlock 最后干净祖先 + 795 测试校正 + 新增 takeover 成员态测试 -->
- [x] 0b.2 测试：更新旧 795（`not_ready`→`pending`，真机校正）+ 新增「加群后 takeover 成员态 → already_member、栏绝不污染」；v4/v5 合成防御全保留（双列卡片/对称歧义/成员方向均绿）。全量 1068 pass、acceptance 16、typecheck 干净。<!-- aidcp-edge 571736b -->
- [x] 0b.3 对抗性评审（Ultracode，承重红线判据变更）：5 镜头攻击精炼规则 + refute-by-default 验证。**10 raised / 0 confirmed**——全被证伪且反驳扎实（逐条对齐真机事实+代码行）。两个 `wouldClickForeign=True` 红线级均伪：①目标无 h1+卡片有 h1（已文档化 residual，真机不触发→走多 heading 分支）；②pre-hydration 栏（premise 与真机事实"异群 join 恒带 2-4 跳锚点"矛盾→hydration 期真实结果 blocks=0→fail-closed 可重试，非 fail-open）。vanity/numeric id 不匹配伪（`__TARGET_GID` 取自 live location、FB 头部自引用与服务 URL 同形→匹配非异群）。一个真实非缺陷 code smell（fallback `__groupHeadings` 在 [role=main] 无 h1 时全文档扫、缺 landmark 约束）——真机不触发、fail-closed 安全，记 residual 不加启发式（守「设停止线」教训）。<!-- workflow w7hth9js8 -->

**land 就绪**：0.1 真机校准 + 0b.1 回归修复 + 0b.3 对抗评审 三闸全清，可 ff master。

## 1. aidcp-edge — 作用域 helper（语言无关）

- [x] 1.1 目标群 id 解析：从 `location.pathname` 的 `/groups/<id>` 段取目标群 id；`numeric-id` / `vanity-slug` 两式规范化，解析失败返回 null（供点击腿 fail-closed）。 <!-- aidcp-edge 70b53e0 __parseGroupId；branch 未land、0.1-gated -->
- [x] 1.2 **候选作用域正向包含（D1 承重、fail-closed）**：定位目标群「头部/动作区」块（含群名主标题的头部/hero 容器，祖先判据见 0.1）；候选 `inTargetScope=true` **当且仅当**它是该块后代——头部块解析不出 → 无候选在域内（点击腿按 D3 fail-closed）。**默认出域**，不是默认在域。 <!-- aidcp-edge 70b53e0 __resolveHeaderBlock/__inTargetScope -->
- [x] 1.3 **corroborating 排除（E1/E2，非承重）**：在 D1 正向包含之上再叠——E1 候选导航引用（`a[href]`/`[role=link]`/属性编码，见 4b.1）解析到 `/groups/<异于目标群 id>` 则 `inTargetScope=false`；E2 候选落在推荐轮播容器内则 `inTargetScope=false`（E2 选择器待真机校准、暂不接线）。最终 `inTargetScope = D1正向包含 AND NOT E1`（E2 校准前不接）。 <!-- aidcp-edge 70b53e0 __candForeignRef（E1，已拓宽非锚点）；E2 defer -->


## 2. aidcp-edge — 点击腿 fail-closed（承重、安全）

- [x] 2.1 `GROUP_JOIN_CLICK_JS`：`join` 节点选取**只在 `inTargetScope` 候选内**取文档序首个；**删除**「页面级文档序第一个 join」回落。 <!-- aidcp-edge 70b53e0 -->
- [x] 2.2 fail-closed：目标群 id 解析失败**或头部块解析不出** → `scope_unresolved`；作用域内无 join → `no_target_in_scope`。绝不页面级点。两者在执行端映射为可重试 `not_ready`（见 4b.3），非 no_button。 <!-- aidcp-edge 70b53e0 -->
- [x] 2.3 保持既有 disabled 诚实 bail、`__FB_JOIN_CLICK__` 标记、坐标回报不变。 <!-- aidcp-edge 70b53e0 -->


## 3. aidcp-edge — 观测腿标注作用域（不阻断上报）

- [x] 3.1 `GROUP_JOIN_OBSERVE_JS`：每候选加 `inTargetScope`；`mainCta`/`joinButton` 挑选**只在 `inTargetScope` 候选内**——推荐栏 join 绝不冒充群主 CTA。 <!-- aidcp-edge 70b53e0 -->
- [x] 3.2 **成员信号收窄（红线1 尾巴）**：`membershipSignals` 从页面级 `signals.slice(0,8)` 改为**只在目标群作用域内读取**——推荐位建议群「已加入」信号绝不污染。 <!-- aidcp-edge 70b53e0；另加 D7-2 矛盾守卫双保险 -->
- [x] 3.3 候选清单**仍如实全量上报**（`ctaCandidates` 含 `inTargetScope:false`），不静默丢弃（守 L4）。 <!-- aidcp-edge 70b53e0 -->
- [x] 3.4 D5：作用域内控件 `ctaKind` 判不出 join/member/pending 时据实上报（原文 + `inTargetScope`），不越域找 join。 <!-- aidcp-edge 70b53e0 -->


## 4. 测试（edge）

- [x] 4.1 **红线（兄弟裸 `div` 无异群 href case，订正核心）**：目标 pending「已申请」+ 推荐位异群「加入小组」为兄弟裸 `div[role=button]` → 绝不点、判 pending、`outOfScopeJoinCount=1`（正向包含默认出域挡住，非靠 E1）。 <!-- aidcp-edge 70b53e0 jsdom 真跑 IIFE -->
- [x] 4.2 **红线（带异群链接 case）**：推荐位 join 带 `/groups/<异 id>` 祖先链接 → E1 亦排除、判 pending、不点。 <!-- aidcp-edge 70b53e0 -->
- [x] 4.3 目标群自身可加入（Join 在头部块内）→ 正常点、点后 joined。 <!-- aidcp-edge 70b53e0 -->
- [x] 4.4 目标群 pending（头部块内无 join）→ 诚实不点（含 4.1）。 <!-- aidcp-edge 70b53e0 -->
- [x] 4.5 目标群 id/头部块解析不出 → fail-closed（not_ready），绝不页面级点。 <!-- aidcp-edge 70b53e0 -->
- [x] 4.6 观测腿：`mainCta`/`joinButton` 不取推荐栏候选；`ctaCandidates` 含 `inTargetScope:false`（全量上报）。 <!-- aidcp-edge 70b53e0 -->
- [x] 4.7 目标群自身钮被指向**本群** id 的链接包裹 → 不误排（在域可选）。 <!-- aidcp-edge 70b53e0 -->
- [x] 4.8 **成员信号收窄**：推荐位「已加入」在头部块外 → 不进 `membershipSignals`、不误判 already_member。 <!-- aidcp-edge 70b53e0 -->


## 4b. 二轮实装对抗评审订正（D7；5 确认发现含 1 红线）

- [x] 4b.1 **D7-1 红线闭合（承重；五轮对抗评审收敛）**：异群检测五轮从「仅 `a[href]`」→「扫全部元素属性(`querySelectorAll('*')`)」→「块保证无异群引用(含块根自身)」→「正向甄别 heading(只接受停在 ceiling 者)」→「歧义即 fail-closed(恰一个合格 heading 才用、≥2 判歧义)」。每轮 jsdom 复现前版本逃逸(现实概率逐轮降至 LOW)。`__hasForeignGroupRef` 含节点自身+后代；`__candForeignRef`(E1) 走到 `__HEADER_BLOCK`。**至此停客户端启发式**，剩余双向角落交 0.1（见 5.3）。 <!-- aidcp-edge 70b53e0+e554fcd+1ae8f66+dec006f+3161203(歧义守卫) -->
- [x] 4b.2 **D7-2 成员矛盾守卫**：`already_member` 仅当作用域内无 join 按钮时成立（`hasMemberSignal && !raw.joinButton?.found`）；正反 mutation-killing 测试已补。 <!-- aidcp-edge 70b53e0(守卫)+e554fcd(测试) -->
- [x] 4b.3 **D7-3 可重试回执**：观测腿 `scopeResolved===false` 与点击腿 scope bail 映射为 `not_ready`（不折叠 `no_button`）；`publicObservation.scopeResolved` 区分 undefined vs false。 <!-- aidcp-edge 70b53e0 -->
- [x] 4b.4 **D7-4 测试补齐**：先序异群 join click-leg 回归护栏 / 畸形 URL fail-closed / 点后推荐位已加入不伪造 / 非锚点推荐位(role=link 与 `div[role=button]` data-*)出域 / D7-2 正反。 <!-- aidcp-edge 70b53e0+e554fcd；full suite 1063 green -->


## 5. 集成与部署（edge-only）

- [x] 5.1 `npm run typecheck` + `npm run test:acceptance`(16) + 全量 `npm test`(1068) 全绿（AC-* 红线过）。 <!-- aidcp-edge 571736b（含真机修复+新测） -->
- [x] 5.2 edge master land（无 ECS/cloud 部署）。**已 land**：三闸全清（0.1 真机 + 0b.1 修复 + 0b.3 评审）→ 干净 ff `7834e94..571736b` 推 origin/master（2026-07-12）。edge 主 checkout 有并发 WIP（他 session 的 `M package.json`/`?? main.cjs`）未扰动，其 pull 后即含。<!-- aidcp-edge master 571736b landed -->
- [x] 5.3 真机验收（原登记 backlog，本次直接真机做完）：pending/member 作用域内正确读、可加入群正常点、成员信号不被推荐位污染、不可用群 fail-closed——**均真机实测通过**。原预警的两个 fail-closed 角落之①（目标头部与关联群栏共处中层容器 → 目标 heading 被甄别掉 → `not_ready`）**已真机命中并修复**（见 0b.1，改最后干净祖先作块）；②（嵌套 `[role=main]`）群落地页为单 main，未触发。真机三群加群/退群全流程验证、账号状态已复原。<!-- 真机 571736b -->

## 5b. 部署（真机验证后）

- [x] 5b.1 edge 桌面安装包重建 + 运营机 pull（用户 gated，§6 打包默认不做）：本 change 纯 edge 定位逻辑已 land master，运营机 pull + 下次安装包重建后运行时生效。真机加群闭环本轮已在开发机 AdsPower 实测通过（见 0.1/0b.1），运营机侧属常规发版节奏、非本 change 单独门槛。用户 2026-07-12 确认“已经 OK，可以归档”；本 session 未重建 edge 安装包，仅据用户放行解除归档 gate。<!-- rollout gate cleared by user confirmation 2026-07-12 -->

## 6. 收尾

- [x] 6.1 `openspec validate facebook-join-candidate-scope-guard --strict` 通过。 <!-- 2026-07-12 valid -->
- [x] 6.2a tasks.md 勾选 + `<!-- <repo> <sha> 备注 -->` 标注（代码 70b53e0；真机校准+修复 571736b；评审 workflow w7hth9js8）。
- [x] 6.2b archive：land + 0.1 真机核 + 0b.3 评审三闸已清；edge 桌面安装包重建 + 运营机 pull gate 已由用户确认 OK 后解除（见 5b.1）。本次归档将 spec delta 并入主 spec。<!-- archive requested 2026-07-12 -->
