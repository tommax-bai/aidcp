# Tasks

## 1. 规范落地（文档 / 契约）

- [x] 1.1 spec delta：`deployment-environments` 新增「发布分支改动必须回流主干」需求（含工件指针例外与「回流不成必须登记」） <!-- aidcp (本 change) -->
- [x] 1.2 `CLAUDE.md` §6 加入该铁律（与「打包 fix 必 forward-port」同处收口，指向同一失效模式） <!-- aidcp (本 change) -->
- [x] 1.3 `docs/deployment-environments.md` 同步 <!-- aidcp (本 change) -->

## 2. 清偿存量（把已经搁浅的发布分支修复全部回流）

- [x] 2.1 edge `36fe38f`（建号环境归属客户：attach 必须 await，否则刚建的环境在随后刷新可见集时看不见）→ master `3a737e6`（冲突解决：master 已有 fire-and-forget 版，取其 await 版本） <!-- aidcp-edge 3a737e6 -->
- [x] 2.2 edge `5ee9d2d`（客户端「更新人设」按钮）→ master `2f69cc9`（**重新实现**：原提交叠在 `210f386` 上，与主干新的人设三态闸 9 处冲突，机械 cherry-pick 是错的工具） <!-- aidcp-edge 2f69cc9 -->
- [x] 2.3 edge `1300f5b`（FB 联系评论确认）→ 核验**内容已在主干**（补丁空应用），弃掉、不造空提交 <!-- verified 2026-07-14 -->
- [x] 2.4 edge `210f386`（人设弹窗竞态）→ 已被主干更强的三态不变量取代（其「自动弹出的窗在权威已绑到达时自动收起」行为已折入），无需再 port <!-- superseded by aidcp-edge 9761448 -->
- [x] 2.5 cloud `e36eddd`（token 记账读 PG env，否则 OL 连错库）→ master `7bae1e5` <!-- aidcp-cloud 7bae1e5 -->
- [x] 2.6 cloud `e2e9f88`（飞书群选项从已验证存储恢复）→ master `ecefe7c`（冲突解决：与主干新增的图片上传测试为干净 union） <!-- aidcp-cloud ecefe7c -->
- [x] 2.7 console `958384f`（FB 上传 nginx 限额）→ 核验**内容已在主干**，弃掉 <!-- verified 2026-07-14 -->
- [x] 2.8 回归：edge 1183 pass + acceptance 19、cloud 1940 pass + acceptance 50、双 typecheck 干净；两次 push 撞 non-ff 均 rebase 重来（未 force） <!-- 2026-07-14 -->
- [x] 2.9 cloud 部署 dev（`ecefe7c`）：备份 → `git archive origin/master` 干净快照 rsync → restart → 健康检查（active / 8787+8090+8091 在听 / 人设存储就绪 / 飞书长连接已建立 / 零 error）。**注**：`e36eddd` 在 dev 上是 no-op——`resolveEnvPgConfig` 在 env 未设时回落同一组默认值，而 dev 的 PG 恰好就在 `127.0.0.1`；它真正修的是 OL（PG 在远端，硬编码默认值＝连错库） <!-- 2026-07-14 deployed -->
- [x] 2.10 已记录的注意事项：边缘改动需重启桌面客户端才生效；回流当时 canonical `aidcp-edge` 工作区被并发 session 占用（有未提交改动），故未做 ff 更新——内容已在 `origin/master`，下次在那里跑 `electron:dev` 前先 `git pull` 即可。 <!-- 2026-07-14 -->

## 3. 工件指针（例外条款）—— 已由 `downloads-manifest-from-host` 根治

- [x] 3.2 console `7a1b718` / `88ce4c8`（下载页 0.3.18 → 0.3.20）：**已作废，无物可回流**。用户定案走根治路线——下载页版本不再写死在源码里，改由云端**现扫该机 downloads 目录**得出（change `downloads-manifest-from-host`，cloud `38f3082` + console `aa3461d`，已部署 dev）。同一份代码在 dev 显示 0.3.18、在 OL 显示 0.3.20，各自都是真话；「版本号该不该回流主干」这个问题从此不存在。 <!-- 2026-07-14 -->
- [x] 3.1 edge `e5a4d1d`（`package.json` → 0.3.20）：**不作废，但也不照搬**。它是**构建版本**、合法地属于源码（不是「哪台机器上放了哪个包」）。master 现有内容已超过 0.3.20，冒充 0.3.20 会让「同版本号、不同内容」的包流出去。纪律照旧（见 [[edge-mac-dmg-build-flow]]）：**出包前先抬版本，且必须严格高于已分发的 0.3.20 → 下次出包用 ≥0.3.21**。不在本 change 里改（打包属用户显式触发的动作）。 <!-- 2026-07-14 -->
- [x] 3.3 「工件指针例外」的现状已在本 change 的 tasks 与 [[release-forward-port-rule]] 记忆里写清：**真正的工件指针（下载页版本）已被 `downloads-manifest-from-host` 消灭**，例外目前只剩「edge `package.json` 的构建版本号」一类。spec 措辞保持通用（未来若再出现同型指针仍适用），不收窄。 <!-- 2026-07-14 -->

## 4. 后续（可选，已登记）

- [x] 4.1 **决定不做（YAGNI，非无限期搁置）**：给「发布分支改动必须回流主干」加机械守卫：切下一个 release 分支前跑一次 `git cherry -v origin/master origin/release/<上一个>`，凡 `+` 必须逐条给出「已回流 / 已被取代 / 工件指针」的结论。可挂进 `scripts/` 与 `task-preflight` 同级的检查位。**本 change 只立法、不实现**（YAGNI：下一次切 release 才用得上，且法条已写进 CLAUDE.md §6 与 spec，人工照单执行即可）。
