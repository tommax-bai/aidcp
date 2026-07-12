# Design — edge-client-env-scope-and-logout

## Context / 现状（带 `文件:行`）

- 加入面板列表数据源：`aidcp-edge/src/electron/main.cjs` `ipcMain.handle('ads:listProfiles')`（~2613）→ `adsApi.listProfiles()`（`ads-local-api.cjs:107`）拉本地 `user/list` **全量**分身，`normalizeProfile`（`ads-local-api.cjs:289`）产出 `{ userId, name, platform, serialNumber, groupName, proxy, ... }`（`userId` = 分身 ID = 归属键 env_key）。渲染在 `renderer.js` `populateEnvs`（~2019）逐行铺开。
- 客户可见集：`allowedProfileIds`（`main.cjs:251`）—— `null` = 未 gated 不过滤；`Set<envKey>` = gated。由 `refreshAllowedEnvironments`（`main.cjs:308`）从 `/my-environments` 拉取，`p.envKey` 装集。运行期过滤在 `syncEnvHandles`（`main.cjs:684`）：`if (allowedProfileIds && !allowedProfileIds.has(env.profileId)) return;`。**但 `ads:listProfiles` 无此过滤** —— 即本 change 要补的漏。
- 客户端登出既有链路：`ipcMain.handle('client-auth:logout')`（`main.cjs:2498`）→ `clientAuthFetch('/logout')` + `onSessionInvalid()`（清会话→`syncEnvHandles` 拆全部环境→关主窗→`createLoginWindow`）。preload 已暴露 `clientLogout`（`preload.cjs:62`）。**已接线处仅托盘菜单「退出登录」**（`main.cjs:1185`，`clientAuthEnabled()` 时才加）。窗口内无入口。
- per-环境「重新登录」：设置抽屉 `#relogin`（`index.html:544`）→ renderer `fields.relogin` 点击（`renderer.js:2419`）→ `auth:relogin`（`main.cjs:2473`）→ `relogin(handle)`（`main.cjs:2362`）→ `stopAndRestart`（重启当前环境核心）。与客户端登录无关。
- 测试范式：`main.cjs` 带顶层副作用不可 `require`，`test/electron/*.test.ts` 用**源码契约断言**（读文本、regex 锁模式/顺序，见 `cloud-env-selector.test.ts`）。

## Goals / Non-Goals

- Goals：(1) 加入列表只显示归属当前客户的环境（gated 时）；(2) 窗口内给清晰的客户端登出/重登入口。
- Non-Goals：不改协议 / 云端 / console；不重绘其他界面；不改 per-环境「重新登录」的行为（仅补 title）；不动「手动填分身 ID」兜底路径的运行期语义（其非归属输入仍由 `syncEnvHandles` 挡启动——本 change 只治**展示**）。

## Decisions

- **D1 收窄点选在 main 的 `ads:listProfiles`（唯一权威数据出口），只收窄**显示**、不在 renderer 过滤。** 渲染层只渲染拿到的那份 → 「已加入」标记 / 删除 / 改平台等行为天然只作用于归属环境；且与 N2「客户可达读只有 scoped 那份」一致（防篡改渲染层绕过）。
- **D2 fail-closed 铁律：客户鉴权启用时绝不返回本机全量列表。** 只有两种安全出口——① 会话有效 → 先 `refreshAllowedEnvironments()` 拉最新可见集（用户点「刷新」的语义就是拉最新，后台刚分配的环境即时出现），再收窄；② 无有效会话 / 刷新 401 / 刷新中会话翻失效（`allowedProfileIds` 被置 `null`）→ `onSessionInvalid()` 并诚实回 `{ok:false}`。**关键：不把过滤 gate 在 `hasValidSession()` 上**（否则令牌到期但未清理时——维护定时器在 `!hasValidSession()` 早返回、无东西关窗——整块被跳过，`return result` 回落全量泄漏他人环境，即首轮评审 Finding 1/3 的 fail-OPEN）。故 gate 只用 `clientAuthEnabled()`，块内先判 `!hasValidSession()` 直接登出，再判 `!ok || !(allowedProfileIds instanceof Set)` 登出，最后才收窄。网络抖动（非 401）→ `refreshAllowedEnvironments` 保留上次已知集、返回 true → 按上次已知集收窄（不清空、不误登出、不泄漏）。`clientAuthEnabled()` 为假（未 gated）→ 跳过、原样返回=零回归；`ok:false` 错误结果原样透传。
- **D3 只收窄显示、孤儿剔除按物理存在解耦。** 收窄的 `profiles` 同时流入渲染层的 `pruneOrphanRoster`（本为按**本机物理**列表剔「AdsPower 已删」的残留）；若拿收窄列表剔孤儿，会把「云端降范围但本机仍在」的环境误当云端已删而销毁花名册项、破坏管理员再授权的自动恢复（首轮评审 Finding 2）。故 `ads:listProfiles` gated 时**另带 `physicalUserIds`**，渲染层 `pruneOrphanRoster` 按它判物理存在（`pruneOrphanRoster(liveIds)`）：物理删除才剔、降范围不剔；未 gated 时该字段缺省、回落用 `profiles` 自身 id（零回归）。`reconcileRosterNames` 仍吃收窄 `profiles`（只回填归属成员名，归属名都在收窄列表里，无损）。`live.size===0` 空守卫保留（物理列表空时绝不剔）。
  - **D3a `physicalUserIds` MUST 收窄到 `allowed ∪ roster`，绝不带他人 id（二轮评审 M3 修复）。** 若直接 `profiles.map(userId)`（在收窄前），多租户同机时会把他人环境的**分身 id** 透过 IPC 回渲染层——分身 id 本身就是 N2 保护维度，且能被拿去删/改他人环境（见 D6）。故 `physicalUserIds = 物理 id ∩ (allowedProfileIds ∪ settings.environments 的 profileId)`：这些 id 渲染层本就合法知晓（归属集来自收窄显示列表、花名册来自本地 settings），零新增泄漏；foreign id 不在该集、本就不与花名册成员相撞、不影响剔孤儿；降范围但在册的环境仍在 `roster` 里 → 仍不被误剔（保 D3/M2）。
- **D6 写侧归属校验（`ads:deleteEnv` / `ads:updateEnvProxy` 未按归属设闸）本 change 不收口，转专项（三轮评审 critical 结论）。** 曾尝试加 `ensureEnvOwnedForClient(userId)` 用 `allowedProfileIds` 核对归属，但三轮评审确证**该本地集可被渲染层污染**：`settings:save` 的乐观自动归属（landed edge-client-customer-auth 的「乐观即时可见」）对渲染层提交的 `environments` 数组里任何新 `profileId` **无条件** `allowedProfileIds.add(...)`，云端 attach 结果被 `void` 忽略。故恶意渲染层可先 `saveSettings` 注入他人 id 污染本地集、再 `deleteEnv` 过闸。且 D3a 收窄后合法流只会传归属 id、该闸对合法流零作用——即「只在被攻击时生效、又恰在被攻击时可绕」= 假安全，无真实收益，故**移除**。正确的写侧隔离需：① 云端 attach 权威化（拒绝认领他客户已归属环境）+ ② 边缘写请求 fail-closed 的每请求权威复核 + ③ 花名册按客户隔离（`settings.environments` 现跨客户登录共享，`settings:get` 会把上一客户的 id 暴露给下一客户）——跨 edge+cloud 的安全设计，值得独立 change + 独立评审，不在本 change 内仓促 bolt-on。已登记 backlog（见 §4 及真机 backlog 安全项）。**本 change 只保证不新增泄漏**（D3a 关掉了自己引入的 `physicalUserIds` 泄漏）。
- **D3b `clientAuthFetch` 加 12s 有界超时（`AbortSignal.timeout`）。** `refreshAllowedEnvironments` 现随每次「刷新」列表调用，面板挂起时裸 `fetch` 会无限吊住按钮；超时按 `status:0`（非 401）处理，与网络抖动同路径（保留上次已知集、不误登出）。
- **D4 设置「重新登录」按钮换成「退出登录」，复用既有 `client-auth:logout`，零新后端。** 设置抽屉页脚放 `#client-logout`（`.hidden` 默认），renderer 初始化查 `clientSession()`：`enabled` 为真才 unhide 并显示 `当前客户：<name>`。点击走**二次确认**（arm→「确认退出?」4s 回退→再点才真登出，与删除按钮一致），因为登出会停掉全部在跑环境。`clientAuthEnabled()` 为假（内部/运营无鉴权）时该入口不出现、页脚为空 → 零回归。
- **D5 移除设置里的 per-环境「重新登录」按钮，但保留其后端 IPC（`auth:relogin` / `relogin()` / preload 桥）。** 用户定案：设置里不再要 per-环境「重新登录」（`#relogin` 元素 + `fields.relogin` 注册 + 其点击 handler 一并删）。**但 `auth:relogin` 有第二个消费者**——通知巡视引导流的「重检」（renderer 直接 `window.aidcpEdge.relogin(envId)`，非本按钮），它仍需重启单环境运行内核；故只删设置按钮那条链，后端 IPC / `relogin()` / preload `relogin` 保留（`stopAndRestart` 亦为「恢复 / 保存 / 换云」多处共用，保留）。

## Risks / 对抗性自检

- **R1 字段名过滤炸空**：若误用 `profileId` 而非 `userId` 过滤，会全部落空→列表空。已坐实 `normalizeProfile` 出 `userId`（`ads-local-api.cjs:293`）、`syncEnvHandles` 侧是 `env.profileId`（settings 花名册字段），两者都 = 分身 ID；`ads:listProfiles` 侧用 `p.userId`。契约测试断言字段名。
- **R2 truncated 交互**：列表分页截断（`truncated:true`）时归属环境可能落在未取页 → 过滤后仍可能缺。这是既有截断限制、非本 change 引入；归属集通常很小，不放大问题。保持 `truncated` 诚实（不因过滤翻转）。
- **R3 刷新引入的登出副作用**：`ads:listProfiles` 里调 `onSessionInvalid()` 会关主窗、开登录窗——发生在真 401（会话确失效）时，属正确行为；返回的 `{ok:false}` 给正在关闭的 renderer 无害。
- **R4 二次确认竞态**：arm 态 4s 定时器与面板关闭 → 用 disarm 清理，参照既有 `makeDeleteBtn`。
- **R5 未 gated 零回归**：内部运营（无 `AIDCP_CLIENT_AUTH_*`）时 `clientAuthEnabled()`=false → 列表不过滤、登出入口不显示 → 行为与今日完全一致。契约测试锁 null 分支 passthrough。
