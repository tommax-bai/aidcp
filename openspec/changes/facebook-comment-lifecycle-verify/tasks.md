# Tasks

> 按仓分节。红线：任何一步都 MUST NOT 让「被拒 / 在飞 / 押审」判成成功。
> 真机证据来源见 `design.md` Context；改动集中在 edge 单文件确认段。

## 1. aidcp-edge — 状态判据基座（先做，后面都依赖它）

- [ ] 1.1 加「已拒绝」文案正则 `FB_COMMENT_REJECTED_RE`（中英覆盖：`已拒绝` / `查看反馈` / `rejected` / `declined` / `see feedback`；留越南语扩展缝），并导出同源纯函数断言（对齐既有 `isFacebookPendingApprovalText` 形态，供脱离 DOM 单测）
- [ ] 1.2 加「发布中」文案正则 `FB_COMMENT_IN_FLIGHT_RE`（`发布中` / `發佈中` / `Posting` / `Sending`；留越南语缝）+ 同源纯函数断言
- [ ] 1.3 加「具名赞/回复控件」判别助手：在评论行内按 `aria-label`/文本识别**赞**控件与**回复**控件（中英覆盖），替代裸 `role=button` 计数；与页内 JS 同源
- [ ] 1.4 回归断言：`FB_COMMENT_REJECTED_RE` MUST NOT 命中正常行文案（`1 分钟 赞 回复`），`FB_PENDING_APPROVAL_RE` MUST NOT 命中 `已拒绝 查看反馈`（两词表互不串味）

## 2. aidcp-edge — 确认段改造（`src/facebook/comment-executor.ts`）

- [ ] 2.1 `buildAckVerifyJs`：成功判据由 `hasServer || reactions>=2` 改为 `hasServer || (具名赞控件 && 具名回复控件)`；**删除按钮计数判据**（红线：被拒行有 2 个按钮）
- [ ] 2.2 `buildAckVerifyJs`：加 `rejected` 与 `inFlight` 两个回传位（与既有 `pendingApproval` 同层级，均在「本人+文本」收窄之后判）
- [ ] 2.3 `inPlaceAckConfirm`：返回 `{confirmed, pendingApproval, rejected, inFlight}`；命中 `rejected` 立即停止轮询（终态，不再等）；`inFlight` 不停、继续等
- [ ] 2.4 `submitComment` 确认段：`rejected` → 新 reason（终态失败，`submitted:true`、`serverConfirmed:false`）；顺序上 `rejected` 与 `pendingApproval` 的判定优先于「窗口耗尽 → ambiguous」
- [ ] 2.5 **删除刷新腿**：移除 `Page.reload` 调用、`reloadScopedConfirm`、`buildScopedVerifyJs` 及其 `waitAfterReloadMs` / `reloadVerifyRounds` / `reloadVerifyIntervalMs` 配置项（红线依据：真机假阴性 + 只认本人+文本必假绿 + 刷新毁押审证据）
- [ ] 2.6 就地窗预算吸收刷新腿的额度（`inPlaceVerifyRounds` 约 32 → 约 63，间隔 300ms 不变，≈19s），**总提交后预算保持不变**；轮询仍按迭代次数限界 + 注入 sleep（不用 wall-clock）
- [ ] 2.7 窗口耗尽仍 `inFlight` → 回 `verification_ambiguous`，但日志/回执带上「观察到在飞」证据（区分「压根没提交」）
- [ ] 2.8 **预算复算并写进注释**：以云端 `max(28s, 18s+220ms×字数)` 为上界，核对「逐字输入 + 就地窗」最坏总额仍在其内（超出 → 云端 timeout → 不打去重 → 下轮真重复评论）

## 3. aidcp-edge — 测试

- [ ] 3.1 单测：被拒行形态（`… 16小时 已拒绝 查看反馈`，2 个按钮，无服务器 id）MUST NOT 判成功，且落新 reason（**本 change 的核心回归**）
- [ ] 3.2 单测：正常行形态（服务器 base64 id / 具名赞+回复）仍判成功（零回归）
- [ ] 3.3 单测：在飞行（`发布中...`，0 按钮）不落任何终态；窗口耗尽后落 ambiguous 且带在飞标记
- [ ] 3.4 单测：押审徽章否决仍生效（不被本次改动破坏）；`identity_unknown` 不提交仍生效
- [ ] 3.5 回归：确认段不再产生任何 `Page.reload`（断言 CDP 桩未收到 reload）
- [ ] 3.6 `npm run test:acceptance` → `npm test` → `npm run typecheck` 全绿

## 4. aidcp-cloud — 新增一档 outcome（参照 `pending_group_approval` 既有形态）

- [ ] 4.1 `src/comment-agent/comment-scheduler.ts`：`mapFacebookSubmitOutcome` 加一档，映射边缘新 reason；**绝不**塌进 `verification_ambiguous` / `submit_failed` 默认分支
- [ ] 4.2 `comment-scheduler.ts`：`reallySubmitted` **不得**包含该档（红线：被拒 MUST NOT 打去重、目标帖不烧掉）
- [ ] 4.3 `src/comment-agent/facebook-comment-audit-store.ts`：outcome 枚举加该档
- [ ] 4.4 结果卡文案：明确「平台已拒绝该评论（未上墙，需人工处理）」，黄卡不染绿；`joinCommentReceipt` 合并卡同步
- [ ] 4.5 `npm run test:acceptance` → `npm test` → `npm run typecheck` 全绿；单测断言该档不打去重、不计成功

## 5. 探针回写（不做则下次仍测不到「发布中」）

- [ ] 5.1 `aidcp-edge/scripts/fb-comment-verify-probe.ts`：每帧存 `nodeText`（现仅存 `nodeTextLen`，正是上轮「发布中」测不到的结构性原因）
- [ ] 5.2 同上：时间戳选择器回落到 `a[href*="story_fbid="]` 短文本（现写死 `abbr, time, [data-tooltip-content]`，真机 FB 把时间渲染成普通 `<a>` → `firstTimeElMs` 恒 null，上轮已记「需再调」未调）
- [ ] 5.3 判决对象加 `rejectedObserved` / `inFlightObserved`，让下次跑一眼能读出三态

## 6. 集成与验收

- [ ] 6.1 edge / cloud 分别 land 到各自 master（rebase 后 ff，push 遇 non-ff 一律 rebase 重来、绝不 force）
- [ ] 6.2 cloud 按默认序列部署 dev（备份 → rsync → restart → healthcheck）；edge 侧运营机需 pull + 重建安装包才生效（打包属用户显式触发，不进自动收尾）
- [ ] 6.3 真机验收项登记 `docs/real-machine-acceptance-backlog.md`（桩测盲区，见下节）
- [ ] 6.4 `openspec validate facebook-comment-lifecycle-verify --strict` 通过 → archive

## 7. 真机验收（桩测盲区，MUST NOT 以单测全绿冒充）

- [ ] 7.1 被拒评论：真机构造/等到一条被拒评论 → 边缘 MUST NOT 判成功、落新档、**不打去重**；云端出黄卡不染绿；journalctl 关键字核对
- [ ] 7.2 正常评论零回归：约 3 秒内确认成功（真机实测点头 2.8s），不再有任何 reload
- [ ] 7.3 在飞态：`发布中` 期间不被误判成任何终态
- [ ] 7.4 逐字措辞收口：坐实**越南语**「已拒绝 / 查看反馈 / 发布中」的真实原文（现仅有简体中文样本），把正则从「语义高置信超集」升到「逐字确认」
- [ ] 7.5 不误伤：正常行的「查看翻译 / 分享」等控件 MUST NOT 被误判成拒绝或在飞
