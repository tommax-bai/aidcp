## Why

视频号 workspace 的环境生命周期控件（启动 / 恢复 / 暂停 / 关闭）在 AdsPower 环境下**每一次动作都谎报失败**：动作其实已经真的执行了，界面却显示「启动失败：这条互动已不可用，或不属于当前环境。」，并且主进程回传的真实状态**永远不会被应用**。

根因是一次改了一半的标识符拆分。workspace 里并存两个标识、分属两套口径：

- **云端环境键**（裸分身 ID，如 `k1eoujd8`）——用于一切 customer API 往返；
- **本机运行时 ID**（`ads-<分身ID>`）——用于本机 lifecycle IPC，是主进程环境表的键。

`0d4d714` 建控件时加了一道「回包环境必须等于当前环境」的守卫，当时两个标识尚未分家、两侧同为云端环境键，自洽。`09bf813`（属另一个 change `wechat-channels-browser-foreground-control`）正确地把两个标识拆开，把**发送侧**改成本机运行时 ID，却漏改了紧邻 3 行、同在一个 diff hunk 内的**比对侧**——从此本机口径的回包永远比不过云端口径的键，AdsPower 环境下恒不相等、必抛。

这是仓库红线「MUST NOT 静默假成功」的**镜像面：假失败**。同样是诚实性缺陷——系统对已经发生的既成事实作出了相反的回报。

回归未被任何机械手段抓住：`09bf813` 同批新增的测试只断言**发送侧**参数（`lifecycleCalls == ['ads-k1eoujd8']`），桩回包随即触发守卫抛错，异常被 catch 吞成失败提示，而测试从不检查提示内容 → 全绿。两个标识都是裸 `string`，typecheck 无感。

## What Changes

- 本机 lifecycle IPC 回包的作用域校验改为按**本机运行时 ID** 比对，与发送侧同口径；校验通过后 MUST 应用回包真态。
- 本机运行时 ID 缺失时 MUST 诚实拒绝该次动作，MUST NOT 回落成云端环境键——回落会让主进程查表落空、静默改对**另一个**环境执行生命周期动作（一枚上膛的「静默打错目标」雷，本次一并拆除）。
- 补齐回归断言：动作成功后必须断言真态被应用（回包状态被下游消费、提示为成功文案），而不只断言发出去的参数。测试夹具 MUST 使用主进程真实造得出的标识形状（本机 ID 恒带 `ads-` 前缀），不得把两个口径设成同值——现夹具正是因此构造性致盲。
- 明确两个标识的口径边界，使「跟云端说话用环境键、跟本机主进程说话用运行时 ID」成为可检查的条款，而非靠下一个改动者的记忆。

## Capabilities

### New Capabilities

- `wechat-lifecycle-status-honesty`: 定义视频号 workspace 本机生命周期动作的作用域校验口径、真态应用义务，以及「不得把已执行的动作回报为失败」的诚实边界。

### Modified Capabilities

<!-- None. 拥有该控件的父 change `wechat-channels-interaction-management` 与引入回归的 `wechat-channels-browser-foreground-control` 均未归档，其 delta 尚未进入基线，故本 follow-up 按 `wechat-sync-timestamp-honesty` 的既定成例做成 additive capability，不对非基线 spec 写 delta。 -->

## Impact

- Edge: `src/electron/renderer/interaction-workspace.js` 的 `changeLifecycle` 作用域校验与兜底；`test/electron/interaction-workspace.test.ts` 的夹具形状与回归断言。
- 不改：云端、协议、command routing、风控写入边界、凭证与发送门禁、浏览器 sidecar 生命周期语义。云端 customer API 的作用域校验（比云端回包的 envKey 与云端环境键，同口径）本就正确，不在本 change 范围内。
- 无 spec 基线依赖：本 change 可独立归档，不阻塞也不被阻塞于上述两个父 change。
