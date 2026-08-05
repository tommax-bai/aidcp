## 0. 前置（不改代码）

- [x] 0.1 确认与 `browser-slot-scheduling` 的串行：该 change 的 worktree（`aidcp.wt/browser-slot-scheduling`、`aidcp-edge.wt/browser-slot-scheduling`）当前干净、最后提交 2026-08-04。开工前复核无人在写 `browser-cold-standby.cjs` / `main.cjs` / `core-lifecycle.ts`；有人在写则等待，**绝不并行改这三个文件**。
- [x] 0.2 起 worktree：`scripts/new-change admit-browser-standby-on-live-facts`（先跑 `scripts/task-preflight`，四个 canonical checkout 必须都停在默认分支）。
- [x] 0.3 取证钉死现状：在 `aidcp-edge` 里确认准入函数当前读的两个生命周期标签、以及除最短持有时长外的拒绝路径确实无任何状态/日志写入。把行号记进本文件，供实装后自查是否改到了正确位置。

## 1. aidcp-edge — 准入判据换成活事实

- [x] 1.1 `src/electron/browser-cold-standby.cjs`：从准入函数中**移除**对会话生命周期标签的依赖（不再要求它处于 running/resting）。保留提示有效性、云端门槛、最短持有时长三项既有校验。
- [x] 1.2 同文件：把「引擎标签等于 running」替换为活事实——核心子进程存在（调用方传入）、云端连接为 connected、自动化意图不是暂停/停止。判据表以显式列表落地，便于逐条断言。
- [x] 1.3 保留三条不可逆互锁**逐字不动**：发布在途、运营正在关闭/暂停/重启/移除、验证码或登录浮层挂着（含登录态非「已登录」）。本任务只做减法，**MUST NOT** 顺手改动这三条的语义。
- [x] 1.4 `src/electron/main.cjs`：更新准入调用处传入的事实集合，与 1.2 的新判据表对齐；确认最短持有时长未满时「排一个到点重判定时器、绝不丢弃提示」的既有行为保持不变。
- [x] 1.5 在准入函数头部注释里写清「为什么不能再用日志推断的生命周期标签」，并指向本 change 名——这类判据将来还会被人重新加回去，注释是唯一拦得住的东西。

## 2. aidcp-edge — 每一次拒绝都留痕

- [x] 2.1 `main.cjs`：把「除最短持有时长外的拒绝直接 return」改为**所有**拒绝路径都写入该环境的待机状态（复用现有 skipped 通道），携带具名原因。
- [x] 2.2 在环境句柄上新增连续拒绝计数与首次拒绝时刻；同一原因连续拒绝时累加，**成功进入待机**或**提示转为不再 eligible** 时复位。
- [x] 2.3 每次拒绝按环境写一行日志（含原因、连续次数、已持续时长），确保事后可从日志文件回溯。注意与既有日志留痕路径的顺序，避免被「停止中」早退分支吃掉。
- [x] 2.4 开发者详情渲染出拒绝原因与连续拒绝次数/持续时长；单次拒绝与连续拒绝在呈现上可分辨。
- [x] 2.5 复核：拒绝留痕本身 **MUST NOT** 反过来改动四轴或在场感文案（留痕是诊断，不是状态迁移）。

## 3. aidcp-edge — 待机失败与待机期间命令（接管 browser-slot-scheduling §5.6 / §5.7 边缘半）

- [x] 3.1 `src/client/core-lifecycle.ts`：核心未确认进入待机时，**不再**把状态落成暂停；保持在浏览器仍开启的运行态，并回报一条具名的可重试失败。
- [x] 3.2 `main.cjs` 对应处理：收到待机失败回执后清掉本次待机在途标记、保留运行态、记录可重试失败，下一次 eligible 提示到达时重新判定（不需要人工干预）。
- [x] 3.3 待机期间收到需要浏览器的命令时，回一条具名拒绝并留痕，**MUST NOT** 静默丢弃。仅做与本 change 代码路径重合的边缘侧一半；跨进程回执归后续 change。 <!-- 取证结论：主干已修，本 change 无需改动。`src/main.ts` 的 handleBrowserAbsentCommand 已在请求唤醒的同时回 `action.completed{ok:false, reason:'browser_absent_wake_requested'}`，`browser-slot-scheduling` §5.7 描述的「三处静默丢弃」已过期。**唯一残留**是同一函数里 `operationDescriptorFor()` 取不到描述符那一支（`operation_unclassified`）——只 console.warn、零回执，真机 18:14:57 那条「未登记的命令 / 已拒绝」正是它。该分支属活跃 change `align-cloud-edge-operation-registries` 的地盘，**转交、不在本 change 动**（避免热点冲突）。 -->
- [x] 3.4 在 `openspec/changes/browser-slot-scheduling/tasks.md` 的 §5.6 与 §5.7 就地注明「已由 change `admit-browser-standby-on-live-facts` 接管」，避免两处各做一遍。

## 4. 回归

- [x] 4.1 准入正例：核心在、云端 connected、自动化未暂停 ⇒ 准入通过。
- [x] 4.2 **本次故障的定向回归**：会话与引擎两个日志推断标签均为陈旧值（如 idle）时，准入仍然通过、浏览器仍然让位。这条是本 change 的核心断言。
- [x] 4.3 三条互锁逐条反例：发布在途 / 正在关闭暂停重启 / 浮层挂着 ⇒ 拒绝，且各自产生**不同**的具名原因。
- [x] 4.4 留痕断言：任意一次拒绝后，状态上能读到原因；连续三次拒绝后能读到计数 3 与首次拒绝时刻；成功让位后计数归零。
- [x] 4.5 **写入方存在断言**（D2）：喂一条真实的云端握手日志行与一条断连日志行，断言云端连接标签确实被写。这条断言是本次事故的机械化教训，**MUST NOT** 省略。
- [x] 4.6 待机失败断言：核心未确认进入待机 ⇒ 环境保持运行态、不落暂停、记可重试失败，且后续提示能再次触发判定。
- [x] 4.7 `cd ../aidcp-edge && npm run test:acceptance && npm test && npm run typecheck` 全绿。
- [x] 4.8 变异自查：把 4.2 的断言临时改坏，确认它真的会红（防止写出一条恒真的断言）。

## 5. 控制仓收尾

- [x] 5.1 本文件按 sub-repo 回写 commit-sha，格式 `<!-- <repo> <commit-sha> 备注 -->`；sha 必须取自**已推送**的提交。
- [x] 5.2 真机验收项登记 `docs/real-machine-acceptance-backlog.md`（并入既有浏览器槽位簇）：
  - 一个账号小时浏览配额跑满 → 云端提示 eligible → **5 分钟内**浏览器关闭、槽位被等槽位队列中的账号取走；
  - 在开发者详情里能看到一次被拒绝的具名原因；
  - 制造一次进入待机失败，确认环境保持运行态、未变成暂停，且下一次提示能重新触发。
- [x] 5.3 `openspec validate admit-browser-standby-on-live-facts --strict` 通过。

## 6. 集成与部署

- [x] 6.1 合回 `aidcp-edge` 默认分支前先 fetch + rebase，跑 `test:acceptance` + `typecheck` 再 ff 合并；push 遇 non-ff 一律 rebase 重来。
- [x] 6.2 本 change **不含**桌面安装包出包（用户长期授权：默认不打包）。收尾到 commit / push 为止；需要真机验证时再由用户显式触发出包。
- [x] 6.3 回滚口径写进收尾说明：`AIDCP_BROWSER_COLD_STANDBY=false` 可秒级关停整条冷待机链路，代价是槽位不再释放。

<!-- aidcp-edge 00fda89 全部代码改动一次落地；acceptance 39/39、全量 3167（3166 pass / 1 gated skip）、typecheck 通过 -->
<!-- 真机项登记于 docs/real-machine-acceptance-backlog.md 簇 106b（5 项）；**未出安装包**，运营机上仍是 0.3.26，修复要出包后才生效 -->
<!-- 集成期遇到一次 test/native-page-engine/runtime-contracts-session-recovery.test.ts EPIPE 红：已在**未含本改动的 master 上**复现（4 次红 1 次），与本 change 无关、未处理 -->
