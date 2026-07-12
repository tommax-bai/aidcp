# Tasks — edge-client-env-scope-and-logout

## 1. aidcp-edge — 加入列表按客户收窄 + 写操作归属闸（`main.cjs`）
- [x] 1.1 `ads:listProfiles` **fail-closed**：gated（`clientAuthEnabled()`）时——`!hasValidSession()`→登出+`{ok:false}`；先 `refreshAllowedEnvironments()`，`!ok || !(allowedProfileIds instanceof Set)`→登出+`{ok:false}`；绝不存在返回全量路径。`null`（未 gated）不过滤=零回归；`ok:false` 透传。 <!-- aidcp-edge 36144c2 -->
- [x] 1.2 只收窄**显示**：`result.profiles` 按 `allowedProfileIds.has(p.userId)` 收窄；另带 `physicalUserIds = 物理 id ∩ (allowedProfileIds ∪ settings.environments.profileId)` 供孤儿剔除按物理判定（**绝不带他人 id**，二轮评审 M3 修复）。 <!-- aidcp-edge 36144c2 -->
- [x] 1.3 `clientAuthFetch` 加 `AbortSignal.timeout(12000)`（refresh 随每次刷新调用，防裸 fetch 吊死按钮）。 <!-- aidcp-edge 36144c2 -->
- [x] 1.4 ~~写操作归属闸~~：三轮评审确证 `allowedProfileIds` 可被 `settings:save` 乐观自动归属污染 → 边缘写闸=假安全，**移除**、转专项（见 §4.4 + design D6）。 <!-- aidcp-edge 36144c2 removed by design -->

## 2. aidcp-edge — 设置「重新登录」换成「退出登录」（renderer）
- [x] 2.1 `index.html` 移除设置抽屉的 per-环境 `#relogin` 按钮;页脚放 `#client-logout`「退出登录」（默认 `.hidden`）+ 当前客户名占位。 <!-- aidcp-edge 36144c2 -->
- [x] 2.2 `renderer.js` 删 `fields.relogin` 注册 + 其点击 handler;初始化查 `clientSession()`:`enabled` 才 unhide「退出登录」+ 填客户名;点击走二次确认（arm→确认→`clientLogout()`），参照 `makeDeleteBtn` 的 arm/disarm。 <!-- aidcp-edge 36144c2 -->
- [x] 2.3 保留 `auth:relogin` IPC / `relogin()` / preload `relogin`（通知巡视引导流「重检」仍用）;仅移除设置按钮那条链。 <!-- aidcp-edge 36144c2 -->

## 3. 测试与验证（aidcp-edge）
- [x] 3.1 新增源码契约测试 `test/electron/client-env-scope-logout.test.ts`（7 用例）:锁 `ads:listProfiles` gated **fail-closed** + 只收窄显示 + `physicalUserIds` 收窄到 roster∪allowed + `clientAuthFetch` 有界超时;锁设置移除 `#relogin`、`auth:relogin` IPC 保留、`#client-logout`「退出登录」+ `clientSession` 门控 + 复用 `clientLogout`。移除 `renderer-smoke.test.ts` 已失效 `#relogin` 用例。 <!-- aidcp-edge 36144c2 -->
- [x] 3.2 `npm run typecheck` + `npm run test:acceptance`(16) + `npm test`(1056) 全绿。 <!-- aidcp-edge 36144c2 -->
<!-- 对抗评审：3 轮 workflow（isolation/regression/renderer/honesty × verify）。R1 揪 2 major（fail-open leak + 错误 orphan-prune）已修；R2 确认 R1 修复 + 揪 M3（physicalUserIds 泄漏他人 id）已修（收窄 roster∪allowed）；R3 确认 M3 修复 sound + 揪 critical（写闸可被 settings:save 污染绕过）→ 移除假安全写闸、转专项 §4.4。 -->

## 4. 真机验收（登记 `docs/real-machine-acceptance-backlog.md`，簇 61）
- [ ] 4.1 GUI 真机:登录客户 A → 加入面板只列 A 的环境（非 A 的不显示）;后台给 A 新分配环境后点「刷新」即时出现。
- [ ] 4.2 GUI 真机:设置里「退出登录」（取代原「重新登录」）显示当前客户名,点击二次确认后回登录门,可重新登录账号;未启用鉴权时该入口不出现;通知巡视「重检」仍能重启单环境（不受影响）。
- [ ] 4.3 打包态:登录门 + 加入列表收窄在 asar 打包产物中同样生效（客户端行为变更需重建安装包）。
- [ ] 4.4 **（专项跟进，非本 change）** 写侧租户隔离缺口：`ads:deleteEnv`/`ads:updateEnvProxy` 未按归属设闸 + `settings:save` 乐观自动归属可被渲染层污染 `allowedProfileIds` + `settings.environments` 花名册跨客户登录共享（`settings:get` 泄漏上一客户 id）。正确修需云端 attach 权威化（拒认领他客户已归属环境）+ 边缘写请求 fail-closed 每请求权威复核 + 花名册按客户隔离。**登记为高优先级专项安全 change**（三轮对抗评审 critical 结论，2026-07-12）。
