## Why

运行期身份持续校验当前**只认消费端首页的「我」锚点**，且**不看浏览器此刻停在哪个页面**就每 30s 就地重读一次。当发布把共用标签页整页跳到创作平台（`creator.xiaohongshu.com/publish/publish`，与消费端不同子域、无「我」锚点）时，两次连续探测都读不到锚点 → 误判「登出/过期」→ 断云端、退回无身份态；自愈又在同一张没有锚点的页面上找「我」→ 失败 → **停在无身份态、要人工重登+重启**。这是一次**把健康登录账号误杀成"引擎异常退出"**的假阳性——2026-07-03 同一账号（工程师大白，`63e2ff05…49ce`）**当天复现两次**（重启后又中招，报错堆栈逐字一致），且断连早于在途发布回执 → 云端收不到结果、干等。属系统性、会反复发作，光重启治不了。

关键订正（用户实测）：创作发布页**本身是登录门禁的**——未登录访问会跳 `creator.xiaohongshu.com/login`。所以创作子域**不是盲区**，它自带登录信号：停在真实创作页=已登录，被弹到 `/login`=真登出。据此可把"在哪个页面"从误判来源转成**分域的正确判据**。

## What Changes

- **身份持续校验改为「按页面上下文分域判定」**（三信号，替代当前单一消费端锚点判定）：
  - **消费端页面且有「我」锚点** → 读稳定 id（现状路径，能判 `lost` 也能判换号 `changed`）。
  - **创作子域 `creator.xiaohongshu.com`** → 停在真实创作页（非 `/login`）= **已登录、健康**，MUST NOT 判 `lost`；被重定向到 `creator.xiaohongshu.com/login` = **真登出**，SHALL 判 `lost`。此路只确认"登录在场"、不解析账号 id，**换号检测仍归消费端**。
  - **其它取不到锚点的页面**（如 AI 搜索结果页 `/search_result_ai` 叠弹层/看图态） → 判**「无法确认」inconclusive**：既不判 `lost`（不误杀）、也不判健康清基线（不假成功），**该轮直接跳过、不进防抖计数**，并**明确日志留痕**（可观测，不静默 no-op）。
- **自愈（重新确立身份）先把浏览器带回可读身份的页面再判定**：`reestablishIdentity` 在重读身份前 SHALL 先关弹层 / 回到消费端首页（或在创作子域改用分域登录判据），使**健康账号能真恢复**，而非在错页面上找不到入口就停摆。
- **退回无身份态断连前，先诚实回执在途发布**：断开云端链路前 SHALL 排空在途发布登记（`inFlightPublishes`）、为每条发指令回一条诚实的失败结果（`[recycled]` 形状），使云端不被无限期挂起（与 `edge-node-supervised-recycle` 既有「回收撞在途发布→诚实判失败」不变量一致，此处补齐**身份翻转断连**这条路径）。
- 协议不变（不动两份 `protocol.ts` / `command-bridge.ts`）；无云端强制改动（云端已能接收 `publish.command.result`）。

## Capabilities

### New Capabilities
<!-- none -->

### Modified Capabilities
- `account-identity-resolution`: 「身份可翻转、须持续校验」的校验口径改为**页面上下文分域判定**（消费端锚点 / 创作子域登录门禁 / 无法确认三态），新增「无法确认 MUST NOT 误判失效也 MUST NOT 假判健康」不变量；「翻转即退回无身份态重新确立」补充**自愈前先回到可读身份的页面**、以及**断连前先诚实回执在途发布**两条义务。

## Impact

- **代码**（均在 `aidcp-edge`，身份红线相邻、改动求最小、留干净扩展缝）：
  - `src/browse/identity-watcher.ts`：读身份前先取当前页上下文，按域分流；`inconclusive` 不进 `consecutive` 计数。
  - `src/cdp/self-identity.ts`：新增轻量「当前页登录判据」helper（读 `location.href` 判消费端/创作子域/`/login`；创作子域登录门禁判据）；`readSelfIdentity` 增一条创作子域分支或由调用方前置分流。
  - `src/main.ts`：`reestablishIdentity` 先导航回消费端/关弹层再重读；断连（`client.close()`）前排空 `inFlightPublishes` 诚实回执。
- **不影响**：协议、云端路由、风控、发布指令序列本身。
- **真机验收项**（登记到 `docs/real-machine-acceptance-backlog.md`）：① 创作发布页未登录确实跳 `/login`（用户已初验，需真机固化为判据）；② 发布期间身份监测不再误判；③ 真登出（消费端）仍能被判 `lost`；④ 自愈能从创作页/弹层态回到消费页恢复。
- **相关但不在本 change 范围**（YAGNI 边界，建议后续单独 change）：浏览循环与发布**共用同一 CDP 标签页**的根因碰撞——发布整页跳走会打断在途浏览动作（本次日志里的"看图卡在 1/10"）。本 change 靠分域判据已能**阻止误判停摆**，该碰撞属浏览/发布编排层，且与活跃 change `publish-trigger-and-apply` 交叠，另行处理。
