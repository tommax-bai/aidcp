## Why

小红书在 07-22 切 Native 页面智能（aidcp-edge `317cd47`）时，宿主侧同时被删掉了三个长跑监测体（阻断浮层监测、登录墙看护、运行期身份看护）与它们的云端上报点；07-23（`4f04e9c`）补回的那份监测从第一行就写死只服务 Facebook（`src/native-page-engine/browse-session.ts:492` 与周期探针 `:460`、`:476`），至今没有任何小红书替代物——今天全仓唯一活着的阻断上报点只对 Facebook 开火，小红书遇到验证码不再通知云端、远程协助不会被唤起、账号风控态不迁移。

同一次搬家里还丢了三类保证：小红书四处「不可逆写入期间不许被抢占」的提交窗口（迁前 `317cd47^:src/browse/browse-session.ts:2578/3104/3158` + 发布提交），现在 Rust 的小红书执行入口根本没有窗口参数（`native/page-engine/src/engine.rs:598`），宿主也只在平台是 Facebook 时才把窗口处理器传下去（`src/native-page-engine/browse-session.ts:237-239`）；验证码协助的「有没有真打字」被改成按请求里带没带文本推断（`src/main.ts:1015`），使云端专为防假成功设的探测器（`aidcp-cloud/src/comm/captcha-assist.ts:259`）永远不会响；逐命令回执诊断与在场感事件被平台判据包住（`src/native-page-engine/browse-session.ts:349-357`），一次小红书浏览闭环在日志里只剩启动与失败两行。

上述能力之所以能整批静默消失而无人察觉，是因为 `4f04e9c` 没有删除旧装配，而是把入口条件改成恒假（`src/main.ts:1043` `if (false && …)`，块尾 `:1213`），并在文件头用类型影子声明（`:88-105`）让编译通过——typecheck、剪枝、单测全绿，没有任何一道闸提示这段能力已经不再执行。同一机制已付过一次代价：块内的 Facebook 软限流上报直到 `54ae5b2`（07-26）才在 Native 会话补回，其间限流文案不产生阻断上报。

## What Changes

- 在 Native 浏览会话里把周期性阻断观测改成按平台装配，小红书恢复到「检出验证码/登录墙 → 本地停手 → 上报云端 → 自愈后配对上报清除」的既有语义。
- 明确小红书低置信「未知阻断」桶在缺少真正的阻断分类器前是**声明缺席**而非用「页面类型识别不出」冒充，避免造出一台误报机。
- 把提交窗口请求下沉到实际执行写入的运行时：小红书评论提交、通知分类消费（评论 / 点赞关注）、发布提交各自开窗；窗口拿不到即诚实判「未开始」，不得静默照写。
- 验证码协助回执的键入取证改为由真正派发字符的执行体产出并逐字段透传；`inputMode` 只反映实际动作，不得由请求载荷推断。
- 逐命令回执诊断与会话生命周期诊断改为平台中立，使小红书侧排障有可看证据。
- 清除恒假短路的宿主装配与其影子声明，逐条对账块内每项能力（已有 Native 归属 / 已登记缺口），并加一道机械闸禁止再次引入「编译期不可达 + 影子声明」这种无信号的保留方式。

## Capabilities

### New Capabilities

- `native-browse-host-integrity`: 宿主侧 Native 浏览运行时的排障证据平台对称性，以及「不得保留编译期不可达装配」的处置口径。

### Modified Capabilities

- `captcha-incident-handling`: 把阻断监测与上报的义务从 Facebook 一家扩到每个由 Native 驱动的浏览平台，并把协助键入取证的来源钉死在真实执行体上。
- `edge-task-execution-coordination`: 把提交窗口保护的义务钉在实际执行写入的运行时上，并补齐小红书四处不可逆写入的开窗契约。
- `account-identity-resolution`: 明确「持续校验」必须由真的在跑的周期校验体承担，只在启动与唤醒各读一次不算满足。

## Impact

- `aidcp-edge/src/native-page-engine/browse-session.ts`
- `aidcp-edge/src/main.ts`
- `aidcp-edge/native/page-engine/src/engine.rs`（小红书执行入口接入提交窗口请求器、验证码回执补取证字段）
- `aidcp-edge/test/native-page-engine/`
- 不碰 `aidcp-edge/native/page-engine/src/xhs-command-router.js`（另一 change 的单写区）。
- 不改协议消息类型与两份 `protocol.ts` 的 `MessageType` 穷举；`captcha.assist.click_result` 只是把既有可选字段真正填上。
- 不含部署、不含出安装包、不含真机写动作；真机才能定论的项集中在 tasks 的验收节并标注。
