## Context

运行期身份校验体（`aidcp-edge/src/browse/identity-watcher.ts`）每 30s 调 `readSelfIdentity(cdp,{allowNavigate:false})`（`src/cdp/self-identity.ts`）就地重读消费端「我」锚点，与握手基线 id 比对：等于→健康、不等→换号、读不出→登出。防抖阈值 2。判失效即触发 `reestablishIdentity`（`src/main.ts`）：停监测/停浏览→`client.close()` 断云端→重读身份，读不出即停在无身份态待人工。

现状根因（2026-07-03 真机两次复现，法证级证据）：浏览循环与指令驱动发布**共用同一张 CDP 标签页**（都建在 `session.cdp` 上）；发布经 `Page.navigate` 把该标签页整页跳到 `creator.xiaohongshu.com/publish/publish`（`src/flows/publish-command-handlers.ts:200,326`）——不同子域、无消费端「我」锚点。身份校验**不看当前 URL**，两次连续探测都落在创作页读不到锚点→误判「登出」→断云端→自愈又在同一无锚点页找「我」→失败→**停摆待人工**。且 `client.close()` 早于在途发布回执、`reestablishIdentity` 从不排空 `inFlightPublishes`→云端收不到该发布结果、干等。

用户实测订正：`creator.xiaohongshu.com/publish/publish` 是**登录门禁**页——未登录访问会被重定向到 `creator.xiaohongshu.com/login`。故创作子域自带登录信号，不必当盲区。

约束：改动落身份红线相邻代码，求最小、守「绝不静默假成功」；不动协议（两份 `protocol.ts` / `command-bridge.ts`）；本地 edge 自跑、连线上云端。

## Goals / Non-Goals

**Goals:**
- 发布（或任何把标签页带离消费端 feed）期间，身份校验 MUST NOT 把健康登录账号误判成登出并停摆。
- 引入分域判据的同时**不漏判真登出**：消费端真登出、创作子域被弹 `/login` 都仍判 `lost`。
- 「无法确认」成为一等状态：既不误杀也不假愈，可观测。
- 自愈能从创作页/弹层态真恢复；断连不再把在途发布结果吞掉。

**Non-Goals:**
- **不**重构「浏览/发布共用一张标签页」的根因碰撞（发布跳走打断在途浏览动作、看图卡 1/10）——属浏览/发布编排层，与活跃 change `publish-trigger-and-apply` 交叠，另行处理。本 change 靠分域判据即可阻止误判停摆。
- **不**在创作子域解析账号稳定 id（换号检测仍归消费端路径）。
- **不**改边-云协议、不改云端路由/风控。
- **不**改防抖阈值/轮询周期的默认值（正交，不在本 change 动）。

## Decisions

**D1：判据「按页面上下文分域」，而非「一律消费端锚点」。**
取当前 `location.href`，按子域/路径分三支：① 消费端有「我」锚点→读稳定 id（现状，判 lost/changed/healthy）；② 创作子域→登录门禁判据（真实创作页=健康、`/login`=lost）；③ 其它无锚点页→inconclusive。
- 备选 A（弃）：**发布期间由发布器挂起身份监测**。需在发布/监测间引入耦合与状态传递，且「发布在途」标志可能残留（发布崩溃留标签页在创作页则监测永久挂起）。URL 是**自描述**的、无状态残留风险，更稳、更少耦合——用户的登录门禁洞察正好让 URL 足以自证，故不需这层耦合。
- 备选 B（弃）：**只要读不出锚点就一律 inconclusive 跳过**。会在创作子域真登出时变盲区（漏判真登出）。分域后创作子域用 `/login` 信号，堵住这个洞。

**D2：inconclusive 是独立三态，既不进防抖计数也不重置基线。**
`IdentityWatcher.check()` 现在两分支（健康清零 / 失效+1）。新增第三分支：inconclusive → 既不 `consecutive=0`（不假愈）也不 `consecutive+=1`（不误杀），直接 return + 日志。守双向红线。

**D3：判据 helper 放 `self-identity.ts`、做成纯函数可单测。**
新增「读当前页登录上下文」轻量 helper（读 `location.href`→分类 `consumer | creator-app | creator-login | unknown`）。分类是纯函数（吃 href 出枚举），CDP 只负责取 href。沿用该文件既有「信号采集与纯判定分离、脱浏览器单测」的模式（如 `deriveInPlaceSelfId`）。
- 判据口径（初版，真机校准）：host `creator.xiaohongshu.com` 且 path 含 `/login`→`creator-login`；host `creator.xiaohongshu.com` 其它→`creator-app`；host 消费端→交现有锚点读取；其它 host/about:blank 等→`unknown`。

**D4：`reestablishIdentity` 先归位再判。**
断连后、`readSelfIdentity` 前，先做「回到可读页面」：关弹层 / `Page.navigate` 回消费端首页（复用现有导航能力），或在创作子域直接用 D1 登录门禁判据免跳。仅当归位后仍无任何登录信号才 halt→park（保留红线：绝不回落 default）。

**D5：断连前排空在途发布、诚实回执。**
`reestablishIdentity` 在 `client.close()` **之前**遍历 `inFlightPublishes`、逐条送 `[recycled]` 失败 `publish.command.result`（复用 `main.ts:295-311` 已登记的 recycled 回调形状），再断连。语义与 `edge-node-supervised-recycle` 既有「回收撞在途发布→诚实判失败」一致，此处补齐身份翻转这条路径。注意送回执必须在 WS 仍连时做。

## Risks / Trade-offs

- **[创作子域 `/login` 判据基于单次人工实测]** → 落地前在真机固化：未登录访问 `creator.xiaohongshu.com/publish/publish` 确会 302 到 `/login`（登记真机验收项）；判据用「path 含 `/login`」而非精确串，容忍 query/子路径。
- **[创作子域只确认登录在场、不判账号身份]** → 换号（`changed`）在创作页期间检测不到；可接受：换号本就靠消费端锚点，回到消费页即恢复检测；创作页停留是短时发布窗口。
- **[inconclusive 可能掩盖"停在无锚点页时发生的真登出"]** → 该态不判健康、仅跳过本轮；一旦浏览器回到可判域（发布结束回消费页、或被弹 `/login`）即恢复判定。真登出不会永久停在无法确认域。
- **[归位导航自身可能失败/超时]** → 归位是 best-effort：失败则回落现有诚实 halt（停摆待人工），不比现状更坏；且分域判据已让绝大多数误判在源头不发生、极少走到自愈。
- **[与 `publish-trigger-and-apply` 共享 `main.ts`]** → 集成串行：合回 master 前 fetch+rebase 到最新，`main.ts` 的 `reestablishIdentity` / `inFlightPublishes` 段落若被并发方动过则手工并轨，再跑 `test:acceptance`+`typecheck`。

## Migration Plan

1. 本地 `aidcp-edge` worktree 开发；`npm run typecheck` + `npm test`（含身份校验单测：分域判定纯函数、inconclusive 不计数、真登出仍判 lost、断连前排空在途发布）。
2. 集成到 master 前 rebase 最新、跑 `test:acceptance`（`AC-*` 安全红线全过）+ `typecheck`。
3. edge 本地构建重启即生效（无云端部署）；真机验收四项（见 proposal Impact）在 `docs/real-machine-acceptance-backlog.md` 登记后择机核。
4. 回滚：本 change 纯 edge 局部逻辑、无协议/数据迁移，`git revert` 单 commit 即回旧行为。

## Open Questions

- 消费端"无锚点页"的判定：是仅按 URL（`/search_result_ai` 等）列举，还是「读不出锚点 + 非创作域」即归 inconclusive？倾向后者（更鲁棒、无需穷举路由），URL 分类只用于把创作子域摘出来做登录门禁判据。实装时以此为准，除非真机发现消费端存在"应判 lost 却被误当 inconclusive"的页面。
- 归位目标页：回 explore 首页还是 `session` 记录的上次 feed URL？倾向 explore 首页（最稳、必有「我」锚点）。
