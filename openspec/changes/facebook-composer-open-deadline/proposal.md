## Why

Facebook 发帖第 2 步「打开发帖框」在页面尚未渲染时**只探一眼**就判终局失败，连爆两稿即触发发布熔断、停掉该账号整批已批草稿。

dev 实测（2026-07-16，账号 `61591753702668`，edge `ads-k1ei3dbi`）：草稿 119 / 120 连续 `failedAt={"seq":1,"kind":"select_mode","error":"no_target"}` → 熔断开启。**失败耗时是判据**：

| record | acquired → 结束 | 结果 |
| --- | --- | --- |
| 110 / 119 / 120 | **3–4s** | `no_target` |
| 111（同账号 7/15） | **69s** | ✅ published |

3 秒 = 导航后固定 `settleMs=2000` + 一次快照探测。它从未等待过。同账号 7/15 真发出过帖子 ⇒ 能力是通的，这是时机竞态，不是坏死。**XHS 同名步 `runSelectMode` 早已修过这一课**（change `publish-select-mode-layout-robust`：「有界重试『出现即点』容忍冷加载晚渲染，整步窗口 20s」）——FB 没 port。

**同批必须一起修的安全前提**：入口文案表含 `write something`，而这正是 FB **小组页**发帖框的文案。今天的 fail-fast 歪打正着挡住了「停在小组页 → 点到小组的发帖框 → 帖子发进错误的小组」。**只加轮询而不先坐实「真的在首页」，等于把一个安全的失败换成一次发错地方的成功**——比现状更糟。故「确认在首页」是加轮询的前置条件，不是可选项。

## What Changes

- **打开发帖框改 deadline 驱动的有界等待**：预算由云端按指令下发（复用 `fb-publish-fill-deadline` 已建的机制），边缘据此自我掐表、先于云端答复。用户定案「FB 比较慢，时间翻倍」= **整步 40s**（找入口 ~20s + 点击后等编辑器 ~20s）。
- **云端仅对 FB 的 `select_mode` 下发 `timeoutMs=40_000`**，云端等 `40s + resultSlackMs(8s) = 48s`，不再撞 30s 默认常数墙。**XHS 路径逐字节不变**（不带预算 → 仍走 30s 默认）。
- **导航后置校验从「域名是不是 facebook.com」改为「真的落在首页」**。浏览时域名本就是 facebook.com，旧判据对「到底跳走没有」**零分辨力**（停在旧页面照样报成功）。改后检查点页 / 同意浮层 / 限流页能被如实分类，不再伪装成下一步的 `no_target`。
- **发帖入口 MUST 只在确认落在首页后才可点击**（防发进错误小组）。
- **修死护栏**：云端下发 `{optionKind:'target', optionValue}`，边缘守卫读的却是 `params.value` → 恒为空、**永不触发的死代码**；单测喂的是生产从不产生的 `{value:...}` 形状 = **假绿**（`unsupported_target` 全仓测试零命中）。
- 诚实闸不变：找不到入口仍如实 `no_target`，MUST NOT 静默假成功。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `facebook-post-publish`: 新增 4 条要求——① 打开发帖框的有界等待与云端下发预算；② 发帖入口只在首页语境下可点击（防发错小组）；③ 导航后置校验必须能分辨「未落地」；④ 目标护栏必须读取云端实际下发的字段。均为 **ADDED**，与在飞的 `fb-publish-fill-deadline`（其 delta 只 ADD 了「正文填写预算」「正文校验回读」两条）**无文本重叠**；两 change 同 capability，归档需按落地序串行。

## Impact

- **cloud** `src/publish-agent/platform-profile.ts`：FB 分支给 `select_mode` 带预算下发。非热点文件；但与 `fb-publish-fill-deadline` 同文件、需注意落地序。
- **edge** `src/facebook/publish-executor.ts`：`navigate()` 后置校验、`openComposer()` 改 deadline 驱动、护栏字段修正。
- **edge** `test/facebook/publish-executor.test.ts`：现有桩**恒把入口摆在页面上**，晚渲染路径零覆盖（假绿根源）；需补晚渲染 / 非首页 / 预算耗尽三类用例，并修掉喂错参数形状的那条。
- **观测**：这一步全程不打日志，「没渲染完」vs「压根没跳过去」vs「检查点页」从日志上分不出来——本 change 的导航分类顺带补上该洞。
- **不涉及**协议消息增删（`timeoutMs` 是 `PublishCommandPayload` 既有可选字段）、不涉及角色注册、不涉及风控状态机。
- **真机验收**：需 dev + FB 环境跑通「浏览闭环正忙时发帖」这一原始失败场景。
