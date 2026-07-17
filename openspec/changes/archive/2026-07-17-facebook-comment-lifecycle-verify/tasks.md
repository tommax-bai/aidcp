# Tasks

> 按仓分节。红线：任何一步都 MUST NOT 让「被拒 / 在飞 / 押审」判成成功。
> 真机证据来源见 `design.md` Context；改动集中在 edge 单文件确认段。

## 1. aidcp-edge — 状态判据基座（先做，后面都依赖它）

- [x] 1.1 加「已拒绝」文案正则 `FB_COMMENT_REJECTED_RE`（中英覆盖：`已拒绝` / `查看反馈` / `rejected` / `declined` / `see feedback`；留越南语扩展缝），并导出同源纯函数断言（对齐既有 `isFacebookPendingApprovalText` 形态，供脱离 DOM 单测） <!-- aidcp-edge cbe2db9 越南语已直接写入(đã từ chối/xem phản hồi)，非仅留缝 -->
- [x] 1.2 加「发布中」文案正则 `FB_COMMENT_IN_FLIGHT_RE`（`发布中` / `發佈中` / `Posting` / `Sending`；留越南语缝）+ 同源纯函数断言 <!-- aidcp-edge cbe2db9 -->
- [x] 1.3 加「具名赞/回复控件」判别助手：在评论行内按 `aria-label`/文本识别**赞**控件与**回复**控件（中英覆盖），替代裸 `role=button` 计数；与页内 JS 同源 <!-- aidcp-edge cbe2db9 页内 fbHasLikeAndReply + TS 侧 isFacebookLikeControlLabel/isFacebookReplyControlLabel 同源 -->
- [x] 1.4 回归断言：`FB_COMMENT_REJECTED_RE` MUST NOT 命中正常行文案（`1 分钟 赞 回复`），`FB_PENDING_APPROVAL_RE` MUST NOT 命中 `已拒绝 查看反馈`（两词表互不串味） <!-- aidcp-edge cbe2db9 测试「三个词表互不串味」，另加正常行「查看翻译」不得当「查看反馈」 -->
- [x] 1.5 **（计划外，实装期发现的真洞）** 加 `stripSubmittedText`：状态判别前先从行文本剥掉**完整**正文+联系方式。评论行 innerText 含我们自己的正文，不剥则「正文含『已拒绝』的正常评论」被误判被拒 → 成功报失败 → 不打去重 → **下轮真重复评论**（正是本 change 要堵的洞，差点自造一个） <!-- aidcp-edge cbe2db9 页内 fbStripSubmitted 与 TS 侧同源；剥完整正文而非 60 字片段，长正文同样安全 -->

## 2. aidcp-edge — 确认段改造（`src/facebook/comment-executor.ts`）

- [x] 2.1 `buildAckVerifyJs`：成功判据由 `hasServer || reactions>=2` 改为 `hasServer || (具名赞控件 && 具名回复控件)`；**删除按钮计数判据**（红线：被拒行有 2 个按钮） <!-- aidcp-edge cbe2db9 -->
- [x] 2.2 `buildAckVerifyJs`：加 `rejected` 与 `inFlight` 两个回传位（与既有 `pendingApproval` 同层级，均在「本人+文本」收窄之后判） <!-- aidcp-edge cbe2db9 AckVerifyResult.reactions 同时删除，改 likeAndReply -->
- [x] 2.3 `inPlaceAckConfirm`：返回 `{confirmed, pendingApproval, rejected, inFlight}`；命中 `rejected` 立即停止轮询（终态，不再等）；`inFlight` 不停、继续等 <!-- aidcp-edge cbe2db9 -->
- [x] 2.4 `submitComment` 确认段：`rejected` → 新 reason（终态失败，`submitted:true`、`serverConfirmed:false`）；顺序上 `rejected` 与 `pendingApproval` 的判定优先于「窗口耗尽 → ambiguous」 <!-- aidcp-edge cbe2db9 新 reason = comment_rejected -->
- [x] 2.5 **删除刷新腿**：移除 `Page.reload` 调用、`reloadScopedConfirm`、`buildScopedVerifyJs` 及其 `waitAfterReloadMs` / `reloadVerifyRounds` / `reloadVerifyIntervalMs` 配置项（红线依据：真机假阴性 + 只认本人+文本必假绿 + 刷新毁押审证据） <!-- aidcp-edge cbe2db9 ScopedVerifyResult 接口一并删除 -->
- [x] 2.6 就地窗预算吸收刷新腿的额度（`inPlaceVerifyRounds` 约 32 → 约 63，间隔 300ms 不变，≈19s），**总提交后预算保持不变**；轮询仍按迭代次数限界 + 注入 sleep（不用 wall-clock） <!-- aidcp-edge cbe2db9 -->
- [x] 2.7 窗口耗尽仍 `inFlight` → 回 `verification_ambiguous`，但日志/回执带上「观察到在飞」证据（区分「压根没提交」） <!-- aidcp-edge cbe2db9 偏离：证据落在**边缘日志**，未新增回执字段——加字段要动 action.completed 载荷形状（跨仓契约），超出本 change「不碰协议」的范围；分诊已可用（日志 + 新 outcome 分档）。要结构化上报另开 change -->
- [x] 2.8 **预算复算并写进注释**：以云端 `max(28s, 18s+220ms×字数)` 为上界，核对「逐字输入 + 就地窗」最坏总额仍在其内（超出 → 云端 timeout → 不打去重 → 下轮真重复评论） <!-- aidcp-edge cbe2db9 复算写进 DEFAULTS 注释：短评论(≤45字)边缘≈24.4s<28s地板；长评论(120字)≈32.6s<44.4s；云端 220ms/字 vs 边缘输入 110ms/字 → 越长越宽裕，短评论是最紧那端 -->

## 3. aidcp-edge — 测试

- [x] 3.1 单测：被拒行形态（`… 16小时 已拒绝 查看反馈`，2 个按钮，无服务器 id）MUST NOT 判成功，且落新 reason（**本 change 的核心回归**） <!-- aidcp-edge cbe2db9 jsdom 真机形态 + 执行器级两条；另加「数字 comment_id 绝不算服务器确认」 -->
- [x] 3.2 单测：正常行形态（服务器 base64 id / 具名赞+回复）仍判成功（零回归） <!-- aidcp-edge cbe2db9 另加「只有赞没有回复 → 不算 ack」 -->
- [x] 3.3 单测：在飞行（`发布中...`，0 按钮）不落任何终态；窗口耗尽后落 ambiguous 且带在飞标记 <!-- aidcp-edge cbe2db9 -->
- [x] 3.4 单测：押审徽章否决仍生效（不被本次改动破坏）；`identity_unknown` 不提交仍生效 <!-- aidcp-edge cbe2db9 -->
- [x] 3.5 回归：确认段不再产生任何 `Page.reload`（断言 CDP 桩未收到 reload） <!-- aidcp-edge cbe2db9 成功/失败/慢渲染三条路径均断言 reloads===0 -->
- [x] 3.6 `npm run test:acceptance` → `npm test` → `npm run typecheck` 全绿 <!-- aidcp-edge cbe2db9 acceptance 22/22、全量 1605/1605、typecheck 0 错 -->
- [x] 3.7 **（随 1.5 补）** 单测：正文含「已拒绝」/「发布中」的**正常**评论绝不被误判（剥正文回归）+ `stripSubmittedText` 长正文用例 <!-- aidcp-edge cbe2db9 -->



## 4. aidcp-cloud — 新增一档 outcome（参照 `pending_group_approval` 既有形态）

- [x] 4.1 `src/comment-agent/comment-scheduler.ts`：`mapFacebookSubmitOutcome` 加一档，映射边缘新 reason；**绝不**塌进 `verification_ambiguous` / `submit_failed` 默认分支 <!-- aidcp-cloud 07643ef reason/outcome 同名 comment_rejected -->
- [x] 4.2 `comment-scheduler.ts`：`reallySubmitted` **不得**包含该档（红线：被拒 MUST NOT 打去重、目标帖不烧掉） <!-- aidcp-cloud 07643ef 该闸本就是白名单(ok||verification_ambiguous)，新档天然在闸外=不去重（安全侧）；未改逻辑，只在闸上写死契约注释防后人「顺手」加档 -->
- [x] 4.3 `src/comment-agent/facebook-comment-audit-store.ts`：outcome 枚举加该档 <!-- aidcp-cloud 07643ef -->
- [x] 4.4 结果卡文案：明确「平台已拒绝该评论（未上墙，需人工处理）」，黄卡不染绿；`joinCommentReceipt` 合并卡同步 <!-- aidcp-cloud 07643ef 文案「Facebook 已拒绝该评论（未上墙，需人工处理）」；合并卡走同一 commentOutcomeReason，一处即覆盖 -->
- [x] 4.5 `npm run test:acceptance` → `npm test` → `npm run typecheck` 全绿；单测断言该档不打去重、不计成功 <!-- aidcp-cloud 07643ef acceptance 54/54、全量 2350 pass 0 fail、typecheck 0 错；另断言文案不得含「无法确认」（那读作可能已发出） -->

## 5. 探针回写（不做则下次仍测不到「发布中」）

- [x] 5.1 `aidcp-edge/scripts/fb-comment-verify-probe.ts`：每帧存 `nodeText`（现仅存 `nodeTextLen`，正是上轮「发布中」测不到的结构性原因） <!-- aidcp-edge cbe2db9 -->
- [x] 5.2 同上：时间戳选择器回落到 `a[href*="story_fbid="]` 短文本（现写死 `abbr, time, [data-tooltip-content]`，真机 FB 把时间渲染成普通 `<a>` → `firstTimeElMs` 恒 null，上轮已记「需再调」未调） <!-- aidcp-edge cbe2db9 -->
- [x] 5.3 判决对象加 `rejectedObserved` / `inFlightObserved`，让下次跑一眼能读出三态 <!-- aidcp-edge cbe2db9 另加 firstInFlightMs/lastInFlightMs（对齐 candidateAckMs 看点头与落定间隔）+ 在 note 里写明 pendingObserved 恒 false 属预期、reloadPersisted=false 未必是真相 -->

## 6. 集成与验收

- [x] 6.1 edge / cloud 分别 land 到各自 master（rebase 后 ff，push 遇 non-ff 一律 rebase 重来、绝不 force） <!-- aidcp-edge d4c081f (主 checkout 已 ff 同步) / aidcp-cloud 07643ef -->
- [x] 6.2 cloud 按默认序列部署 dev（备份 → rsync → restart → healthcheck）；edge 侧运营机需 pull + 重建安装包才生效（打包属用户显式触发，不进自动收尾） <!-- 2026-07-17 deployed dev。偏离：cloud **主 checkout 有他人未推送 WIP 4 提交**（client-content-workspace-navigation），land 脚本 ff 失败；按 CLAUDE.md §6「严禁从脏共享工作区上线」改用 `git archive origin/master` 干净快照部署，md5 已核对等于 origin/master；他人 WIP 未动。备份 cloud.bak.20260717-114459.tar.gz + .env.bak；healthcheck：active / 8787 / 8090 / 飞书长连接已建立 / DB 0 错 / 同机 isales 四服务未受影响 -->
- [x] 6.3 真机验收项登记 `docs/real-machine-acceptance-backlog.md`（桩测盲区，见下节） <!-- 簇 88（沿用参与审批闸同环境同链路）新增 88.6-88.10 -->
- [x] 6.4 `openspec validate facebook-comment-lifecycle-verify --strict` 通过 → archive <!-- 2026-07-17 validate 通过 -->

> **归档口径**：代码 landed（edge `d4c081f` / cloud `07643ef`）+ cloud 已部署 dev。真机项（§7）按项目惯例解耦到 `docs/real-machine-acceptance-backlog.md` 簇 88（88.6-88.10），**不阻塞归档**。⚠️ **edge 侧需重打安装包运营机才生效**——打包属用户显式触发，不进自动收尾。

## 7. 真机验收（桩测盲区，MUST NOT 以单测全绿冒充）

- [ ] 7.1 被拒评论：真机构造/等到一条被拒评论 → 边缘 MUST NOT 判成功、落新档、**不打去重**；云端出黄卡不染绿；journalctl 关键字核对
- [ ] 7.2 正常评论零回归：约 3 秒内确认成功（真机实测点头 2.8s），不再有任何 reload
- [ ] 7.3 在飞态：`发布中` 期间不被误判成任何终态
- [ ] 7.4 逐字措辞收口：坐实**越南语**「已拒绝 / 查看反馈 / 发布中」的真实原文（现仅有简体中文样本），把正则从「语义高置信超集」升到「逐字确认」
- [ ] 7.5 不误伤：正常行的「查看翻译 / 分享」等控件 MUST NOT 被误判成拒绝或在飞
