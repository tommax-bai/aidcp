## Why

Native 引擎迁移把页面智能搬进 Rust 二进制，同时把一批「声明」和「常量」拆成了两份互不校验的副本。命令清单给每条命令写了「会发哪些回执」，但全仓对这一列的引用只有一处类型声明、零处断言（`aidcp-edge/test/native-page-engine/command-manifest.test.ts:14` 是唯一出现，Rust 侧 `native/page-engine/src/` grep 零命中）——开帖声明会发详情与动作完成两种回执，而边缘一次执行只产出一个输出、详情分支直接返回（`src/native-page-engine/browse-session.ts:310-329`），动作完成永不发出；这类缺口在声明层白纸黑字写着，却没有任何东西去读它。同一份清单还已经和命令枚举漂了一条：枚举 43 个变体、清单 42 条，差集是页面探测命令，而那条名叫「枚举与冻结清单逐条一致」的测试比的是手写数组和清单（`native/page-engine/src/command.rs:1033-1049`），从没碰过枚举。

提交窗口的三个毫秒预算两端各写死并做**相等断言**：`native/page-engine/src/facebook/capability.rs:36-47` 与 `src/native-page-engine/client.ts:854-857` 各一份，不等即判协议非法并终止引擎（`client.ts:500-508`）。只改一侧不是预算变了，而是每次加群/评论/发帖在按下按钮前把引擎杀掉——这是本轮跨语言常量里危害最集中的一处，且方向与其他条相反：不是静默降级，而是响亮但归因完全错误的自杀。同类双写还有 Facebook 评论提交预算：云端与边缘各写一份同样公式，边缘那份已改成按「正文 + 换行 + 群聊码」的完整串算（`aidcp-edge 745b754`），云端仍只把正文传给预算函数（`aidcp-cloud/src/comment-agent/facebook-edge-steps.ts:367-370`），于是带后缀的长评论上云端会先判超时、不打去重标记，正是那处云端注释声称要防的重复评论。

故障侧同样有结构性缺口：引擎进程一死，边缘缓存的会话对象不查传输存活即返回（`src/native-page-engine/runtime.ts:129-131`），后续每条命令立刻抛「引擎已退出」；而云端命令面能撬动恢复的动作只有结束会话（本地释放会话持有者的唯一入口是 `browse-session.ts:164/182/193` 的三处停止/关闭路径），其收尾写在成功路径上（`src/native-page-engine/browse-session.ts:141-142`，`await active` 之后、`catch` 之前），引擎已死时这条命令必然失败、收尾整段被跳过——自愈通道被故障本身堵死。重连则复用建会话那一次取到的调试端点，选目标只按平台加端口（`native/page-engine/src/engine.rs:206-207`、`src/endpoint.rs:214-226`），没有任何分身身份证据；重连后的重试跑在超时包裹之外（`engine.rs:509-528`），可远超命令预算并占死唯一命令槽位（`native/page-engine/src/main.rs:251-263`）。

## What Changes

- 把命令清单的回执列、请求契约列、效果列、取消列变成机械断言：每条命令声明的回执必须与该命令成功路径上可达的发出点逐条对齐（跨平台取并集、排除失败路径），声明得到而实现发不出的，要么补上发出、要么改掉声明。
- 命令词表的一致性检查改为从引擎自己的命令类型穷举导出，而不是与一份手写数组比对；枚举里不进清单的命令必须进一张有断言、有理由的显式排除表。
- **BREAKING** 提交窗口的标签与预算改为单一事实源：宿主侧是预算权威，引擎按标签请求、由宿主给出预算；两侧数字不一致时的结论是构建期/契约期失败，运行期 MUST NOT 以匿名协议非法把引擎整个终止。
- 结束会话的收尾改为无论该命令成功失败都执行；缓存的会话句柄在传输已死时不得复用，下一条命令重建引擎。
- 重连时重新向浏览器提供方取端点，选目标必须带分身身份证据；拿不到身份证据时诚实失败，MUST NOT 接管同机另一个分身的浏览器。
- 重连后的重试纳入同一条绝对截止线，超过即释放唯一命令槽位并如实回报超时。
- 页面规则取根节点在导航瞬间取不到有效根时诚实回「未开始」，不得把空根交给遍历；解码诊断从 Facebook 单点扩到小红书与页面探测两条入口；逐字输入的焦点守卫区分「守卫求值本身失败」与「焦点确实丢了」。
- Facebook 评论提交预算改为由一侧算出并随命令传输，另一侧据传输值派生，取代云端与边缘各写一份同样公式的现状。

## Capabilities

### New Capabilities

- `native-engine-runtime-contracts`: 定义 Native 引擎的声明-行为对账、跨语言常量单一事实源、能力握手覆盖面，以及引擎故障后的自愈、重连绑定与预算约束。

### Modified Capabilities

- `pluggable-browser-provider`: 明确统一句柄给出的 CDP 端点在会话全生命周期内仍是权威，消费方不得长期持有建会话那一次的快照，且目标选择须带分身身份证据。

## Impact

- `aidcp-edge/native/page-engine/src/command.rs`
- `aidcp-edge/native/page-engine/command-manifest.json`
- `aidcp-edge/native/page-engine/src/engine.rs`
- `aidcp-edge/native/page-engine/src/endpoint.rs`
- `aidcp-edge/native/page-engine/src/facebook/capability.rs`
- `aidcp-edge/native/page-engine/src/xhs.rs`、`src/probe.rs`、`src/input.rs`
- `aidcp-edge/native/page-engine/src/facebook-router/00-shared.js`（取用层空 root 防护）、`20-feed.js`（`currentDetail` 的无空判取根）；`40-group-join.js` 的兜底取根经实读为空安全，除交叉核对外预计不改
- `aidcp-edge/src/native-page-engine/client.ts`、`runtime.ts`、`browse-session.ts`
- `aidcp-cloud/src/comment-agent/facebook-edge-steps.ts`
- 本 change **不含**：部署（dev/ol 均不含）、出安装包与签名公证、任何真机写动作、Cloud 协议 v2 消息增删、风控与配额口径改动、Console 改动。
- 本 change **不含**产物新鲜度与构建期闸门（能力摘要输入范围、开发态重编判据、打包态产物校验、Electron 侧期望摘要）——那一整片由并行 change `enforce-native-engine-artifact-gates` 拥有，本 change 不动 `build.rs`、`scripts/build-native-page-engine.mjs`、`scripts/ensure-native-page-engine-dev.mjs`、`src/electron/native-page-engine-artifact.cjs`。
- 本 change **不含**对 `openspec/specs/native-page-engine/` 的任何修改——那是只读探针期规格，不承载生产运行时行为。
