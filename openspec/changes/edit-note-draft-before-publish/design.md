## Context

正文发布是**两段式**：生成段把标题 / 正文 / 配图 / 元数据算好，冻存成一条 `publish_log` 记录（状态 `pending_approval`），发一张飞书审核卡后即返回；下发段只在**人点通过**后触发——发布端**重新从那条记录读取草稿**（`loadForDispatch`）、逐字串成 `publish.command` 发给绑定的边缘节点，**绝不重生成**。授权决定是一份**先到先得（O_EXCL）、当前永不删除**的签名文件 `/tmp/aidcp-publish-approve-publish-<id>.json`，Web 审批（`POST /api/publish/:requestId/approve`）与飞书卡片回调**共用同一个字节一致的出口** `writeApprovalSignal`。

三条现状事实决定了本设计的可行性与难点：

1. **下发忠于数据库那条记录、且 Web 授权 payload 只是占位**（`panel-server.ts:269`、`publish-dispatcher.ts:129`）——所以「授权前就地改那条记录」的改动会原样流到真发布，**边缘无需任何改动**（边缘无状态、逐字忠实填入 `params.value`）。
2. **那条待审记录没有任何并发控制**——无版本列、无行锁、无内容哈希；「冻结」纯靠约定（插入后无代码再 UPDATE 内容列）+ 下发幂等（inFlight 集合 + `status==pending_approval` 闸 + 账号串行）+ 签名先到先得。引入编辑就打破了「插入后无人再改」这条约定，必须自带并发闸。
3. **飞书是老版卡片、云端无法主动刷新已发出的卡片**（`messenger` 无 updateCard，就地替换只能作为卡片回调的响应返回）；卡片回调只读构卡时烤入的静态按钮值、读不到用户输入。所以「编辑」不可能落在飞书卡片里，且一旦后台改过、老卡片就成了显示旧文案却仍能点的「陷阱」。

拥有者对象 `PublishLogStore` 已注入面板但**零端点引用**（现成挂载点）；后台已有只读「查看正文」抽屉 + published 历史表 + 一处**手贴 requestId** 的临时审批（有标注的 V1 待办）；写操作有成熟模板（可编辑分组标签：JWT 闸 + 拥有者单写 + 诚实非乐观 + 依赖缺失 503 + `sub` 审计）。

## Goals / Non-Goals

**Goals:**
- 运营能对「待审」正文草稿就地编辑标题 / 正文 / 可见范围 / 话题，改完再授权，**改的内容原样发布**（下发仍重读、绝不重生成）。
- **「审=发」按构造成立**：真正触发下发的那次授权，其人所见的字节 == 真正发出去的字节；所有看的是旧字节的人一律被确定性地拒绝或作废，绝不被静默盖过。
- 一条被合法编辑的好草稿**永不被永久锁死**；一次误点旧卡片**永不误发**。
- 收口后台手贴 requestId → 按行审批。
- 留一条**内容无关**的干净扩展缝，让评论、配图后续复用，本期一行都不多建。

**Non-Goals:**
- 不做评论编辑（评论无草稿库 + 90 秒内存窗口 + 边缘 @/# 保真限制——后续独立期，复用同型 `editDraft` 契约）。
- 不做配图编辑 / 上传（后台无上传组件、面板无传图接口；配图保真闸归 `publish-media-upload`）。
- 不做版本历史表 / diff 日志（`content_version` 即将来扩展键，需要时挂侧表）。
- 不重算 aiEnforced 合规棘轮（本期合规字节保留、不可编辑）。
- 不改边缘、不改协议、不改签名文件跨进程契约 / requestId 格式 / 待审轮询 / 评论-正文判别。
- 不改发布放行阈值 / 降级公式 / forced 必发语义 / 无授权绝不下发。

## Decisions

### D1. 就地 UPDATE 同一条待审记录，而非新起修订行
**选择**：编辑就地改那条 `pending_approval` 记录。**理由**：下发本就在下发时重读该行，就地 UPDATE 零新增重建管线即可流到真发布；修订行会 fork「recordId ↔ requestId ↔ 签名」这条下发 / inFlight / 账号串行都依赖的身份，还会把「待审计数」背压撑大、误饿死新生成。**弃**：修订表（YAGNI，单运营「改完即发」不需要多版本并存）。最小审计以三列就地承载：`content_version INT NOT NULL DEFAULT 0`（真列、非 JSONB，令版本闸是原子 `WHERE` 谓词，既有行回填 0）、`edited_by TEXT`、`edited_at TIMESTAMPTZ`——是「谁 / 何时」，不是 diff。

### D2. `content_version` 作「审=发」的版本凭证，版本压过来源
**选择**：每次编辑 `content_version+1`；授权必须携带「人当时看到的那一版」版本号；**版本一致性是唯一保真闸，签名里的 source 字段仅供审计**。**理由**：真正决定「谁看到的」是版本号，不是渠道；只要「授权所带版本 == 下发那行版本」，那个人就必然看过那批字节。**弃**：早期「edited 草稿只许 console 授权（source 闸）」——`source` 无法覆盖「console 改了但又在 console 拿旧缓存点批」的情形，版本闸能、且更普适。

### D3. 三层一致性：编辑预闸 + 写时预检 + 下发兜底（唯一权威）
- **编辑预闸**：`editDraft` 若发现该 requestId 的签名文件已存在（授权在途），拒 `already_decided`；叠加 CAS 的 `status='pending_approval'` 谓词——**当且仅当**「待审 且 无签名」时可编辑。此拦截是**暂态**，不是永久：过期签名会被下发兜底删除，草稿下次刷新即回可编辑。
- **写时预检**（console approve 端点 + 飞书回调，仅 `publish-` requestId）：写签名前先读活版本与「人授权的版本」比对，不一致则**拒绝、不写签名**（O_EXCL 槽位留空，记录留待审可编辑）。console 回可区分的 `version_stale{currentVersion}`，飞书回一张就地替换卡「请到控制台重新审批」。同版本并发授权仍在 O_EXCL 上无害相撞（先到胜、后到 `alreadyDecided`，既有行为不变）。
- **下发兜底**（结构性、**唯一权威**）：`runDispatch` 在既有 `status`+`isApproved` 闸之后，若 `signal.contentVersion`（缺→0）≠ 行 `content_version`，则**不发任何东西、删掉过期签名、行留 `pending_approval`**——自愈回可重审（带当前内容），不落 `needs_review`、不锁死。这一层收掉「写时读与 O_EXCL 建之间又落了一次编辑」的 TOCTOU；正确性从不只靠写时预检。删签名要**先于**任何状态翻转（行本就 `pending_approval`、下发在串流前不翻状态），下次轮询见「待审 + 无签名」→ 不再自动重发，直到人写一份新的、版本正确的签名。

### D4. `clampTitle` 单处收口 + 合并动作的二次确认边界
标题长度仍只在云端 `editDraft` 里跑 `clampTitle(≤18 字素，拒空)`，面板不写裸标题。「保存并批准」链式两调用（先 PUT 编辑、再 approve 带 `editDraft` 返回的版本）时：**若返回标题 == 提交标题** → 自动 approve；**若被截断** → **中止自动批准、回显截断后字节、要求就那版再点一次批准**。杜绝「人授权的是截断前、发布的是截断后」。**弃**：客户端 18 字硬镜像（只留纯提示，云端 clamp 是唯一闸，避免两处口径漂移）。

### D5. 合规字节保留、不重算棘轮（与未上线合规改动解耦）
`editDraft` 深合并 `publish_metadata` JSONB，**只拼接 visibility 与 topics**，compliance / permissions / mentions / location / collection / metadataScore **逐字保留**（并断言 compliance 键前后字节一致作廉价护栏），**不重跑 aiEnforced 棘轮**——该值在生成冻结时已归一化，本期不碰，从而与未部署的 `publish-metadata-compliance-roles` 解耦。

### D6. 后台把只读抽屉升级为编辑工作台，授权带抽屉渲染时的不可变版本快照
在既有「查看正文」抽屉上，`status==pending_approval` 时渲染可编辑表单（复用 人设编辑页 的 Modal+Form+TextArea + apiPut + react-query 失效 + 诚实写回 + 拒因码映射）；其余状态仍只读。**授权携带的版本号必须是抽屉渲染时快照的那一版、绝不点击时从活缓存重取**（否则凭证恒等于行、闸形同虚设）；「保存并批准」带的是 `editDraft` 刚返回的版本。requestId 由行 `publish-<id>` 派生，删手贴输入。生命周期标签：待审 v0 / 已编辑待审 v>0（琥珀色，提示飞书卡片已失效）/ 已发布 / 失败 / 已否决（needs_review）；v>0 时抽屉加一条 Alert「此草稿已在控制台修改（第 N 版），原飞书卡片已失效，请在此审批」。

### D7. 部署缺版本→0 兜底
飞书按钮烤入版本缺失→0、下发闸 `signal.contentVersion` 缺失→0。部署前在飞的老审批（未编辑：烤入 0 == 活 0）写 `contentVersion=0`、下发闸 `0===0` 通过 → 照常发布，不被 deploy 卡死。

## Risks / Trade-offs

- **[写时预检与 O_EXCL 建非原子，残留 TOCTOU]** → 下发兜底（D3 第三层）是结构性权威，任何漏网的旧版本授权在下发处被作废、草稿留待审，正确性不靠写时预检。
- **[飞书活版本读取时 PG 抖动]** → fail-safe 取「拒到 console」（回「暂时无法确认版本，请到控制台审批」），绝不放行未确认版本；下发兜底再兜一层。宁可让运营多点一步，也不误发。
- **[废弃 / 卡住的编辑草稿如何退场]** → 「废弃」= 拥有者 `updateStatus(needs_review)`（运营主动、不碰已锁签名），`runDispatch` 的 `status!='pending_approval'` 闸自然把它丢弃；满足「无超时自动发 / 无自毁」。needs_review 只做**人的终态否决**，版本作废绝不落此态（保证好草稿不被永久锁死）。
- **[共享 PG、无迁移器、有并发部署方]** → 加列走启动期 `ADD COLUMN IF NOT EXISTS DEFAULT`；部署前先探 ECS 现状、核实 `publish_metadata` JSONB 形状与在飞的合规 / 重建改动一致，深合并绝不丢下发依赖的键。
- **[与在途发布改动同段代码相撞]** → 下发版本闸严格排在 `publish-trigger-and-apply`（拥有 `runDispatch`）部署之后或并入之；面板 / 抽屉扩展待 `publish-history-account-and-detail` 归档后增量扩展、不 fork、不 co-edit 未完成的 change。
- **[「保存并批准」拆两调用而非单原子端点]** → 取两调用（YAGNI）；D4 的截断二次确认 + D3 下发兜底令「两调用间又滑进一次并发编辑」的结局是「被拒 / 可重审」而非误发。若实测频繁再加合并端点。

## Migration Plan

1. **先探 ECS 现状**（有并发部署方也在改同机、schema 启动自建无迁移器）+ 核实 `publish_metadata` JSONB 形状。
2. 云端加三列（`ADD COLUMN IF NOT EXISTS`，`content_version DEFAULT 0` 回填既有行）。
3. 云端实现 `editDraft` + `PUT /api/publish/:recordId/draft` + 写时版本预检（approve 端点 & 飞书回调）+ 签名 payload 带 `contentVersion` + 缺版本→0 兜底；保 O_EXCL 出口字节不变、同版本先到先得不变。
4. 云端下发版本闸 + 作废过期签名并留待审分支（**land 在 `publish-trigger-and-apply` 部署之后**）。
5. published 投影增量带 `content_version`（协调已归档的 publish-history item 形状）。
6. **云端整套先上 ECS**（缺版本→0 护住在飞审批），验证后再放**控制台编辑 UI**。
7. 部署走安全序列：ECS 备份 → rsync（排除 .env/node_modules/.git）→ restart → healthcheck → 失败回滚；**绝不碰同机 isales**。
8. **回滚**：编辑 UI 可先撤（云端向后兼容、老审批照常）；列为加性、回滚保留无害（默认 0）。

## Open Questions

- 「驳回」是否也版本门控？当前选择：照人意否决→needs_review（不发布无误发风险），写时预检仅给「内容已变」提示。仅当运营反馈误否决非预期内容时再收紧。
- 本期可编辑元数据是否只到 visibility/topics？mentions/location/collection/permissions 同为文本类但本期未要求——扩展是 patch 类型 + 深合并的平凡增量，留缝不建。
- 「保存并批准」若观测到并发被拒率偏高，是否升级为单原子端点——先不做，留作后续。
