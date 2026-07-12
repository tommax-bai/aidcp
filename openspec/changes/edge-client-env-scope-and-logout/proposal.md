# Proposal — edge-client-env-scope-and-logout

## Why

两处对外客户端（edge 桌面）体验缺口，均属已归档能力 `client-customer-auth` 的补漏：

1. **「添加环境 → 加入现有环境」列表未按登录客户过滤。** 该列表直接列出本机指纹浏览器里的**全部**环境（`ads:listProfiles` → 本地 API `user/list` 全量），不分归属。运行期过滤（`syncEnvHandles` 只对归属当前客户的环境建 handle）虽然挡住了非归属环境**真启动**，但列表仍把它们**显示**出来：
   - 客户能看到不属于自己的环境的名字 / 分组 / 代理 / 分身 ID —— 与隔离不变量 N2（客户可达环境信息只应是自己 scope 内那份）相悖；
   - 用户会误把非归属环境「加入」进花名册，之后它静默永不启动（轻度「静默假成功」）。
   用户明确要求：**添加环境里取消非归属环境的展示**。

2. **窗口内没有「重新登录客户端」入口，且设置里的「重新登录」语义易被误解。** 设置抽屉里的「重新登录」实为「按当前设置重启**当前这个环境**的运行内核」（用于社媒账号在指纹浏览器里掉登录后接上），与「客户端 name+key 登录」是两个层。真正的客户端登出（清客户会话→回登录门）目前**只在系统托盘菜单「退出登录」**里、窗口内找不到，用户据此发问「重新登录能不能用来重新登录客户端」。**用户定案**：把设置里的「重新登录」直接**换成「退出登录」**（作用=退出客户端登录、回登录门重新登录账号），**设置里不再保留 per-环境「重新登录」按钮**。

## What Changes

- **收窄「加入现有环境」列表到归属当前客户的环境**（edge，`ads:listProfiles`）：客户鉴权启用且有会话时，先刷新该客户可见集（用户点「刷新」也应让新分配环境即时出现）、会话失效则登出，再把返回列表按 `allowedProfileIds` 收窄；未启用鉴权（`allowedProfileIds == null`）时**不过滤**（零回归）。语义与 `syncEnvHandles` 的运行期过滤对齐（fail-closed 空集=只显示零个，绝不误显他人环境）。
- **设置抽屉「重新登录」按钮换成「退出登录」**（edge，renderer）：作用=退出当前 name+key 客户端登录、回登录门重新登录账号，复用既有 `client-auth:logout`（清会话→拆全部环境→回登录门）。仅客户鉴权启用时显示、展示当前客户名、点击二次确认。**原 per-环境「重新登录」设置按钮移除**；其 `auth:relogin` IPC / `relogin()` / preload 桥**保留不变**——通知巡视引导流的「重检」仍走这条路径、与本按钮无关。**不改协议、不改云端、不新增后端**。

## Impact

- Affected specs: `client-customer-auth`（ADDED 2 条需求：加入列表按客户收窄；窗口内客户端登出入口）。
- Affected code（edge only）：`src/electron/main.cjs`（`ads:listProfiles` 收窄显示 + `physicalUserIds` 收窄到归属∪花名册 + `clientAuthFetch` 超时）、`src/electron/renderer/index.html`（移除 `#relogin`、页脚换「退出登录」）、`src/electron/renderer/renderer.js`（`pruneOrphanRoster` 按物理 id + 移除 relogin handler + 退出登录 wiring）、`src/electron/renderer/styles.css`、`test/electron/`（新契约测试 + 移除失效 relogin 用例）。
- **发现（非本 change 修复）**：三轮对抗评审揭出**既有**写侧租户隔离缺口（写出口未按归属设闸 + 乐观自动归属可被渲染层污染 + 花名册跨客户共享），需 edge+cloud 专项安全 change，见 tasks §4.4 / design D6。本 change 只保证不新增泄漏。
- 不动热点文件（两份 protocol.ts / command-bridge / role-catalog / risk-state-machine 均不涉及）；不改协议、云端、console。
- 客户端行为变更 → 运营 / 客户机需重建安装包后方生效（登记真机验收 backlog）。
