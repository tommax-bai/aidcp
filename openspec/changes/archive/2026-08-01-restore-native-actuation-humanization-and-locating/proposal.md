## Why

把页面智能迁进 Native 引擎的公开动机是防反编译，但落地方式削弱的恰好是反检测这一面，且三处都能在代码里坐实。

**第一，云端算好的动作前犹豫与离页停留在 Native 侧几乎无人消费。** Rust 侧这两个字段共 28 处命中，全部是结构体字段声明或填 `None`，零读取点；TypeScript 侧只有 Facebook 首页翻页一条命令真按下发值等待（`aidcp-edge/src/native-page-engine/browse-session.ts:264`），而切换前小红书会话对开帖 / 点赞 / 关注 / 返回逐条等待（`git show 317cd47^:src/browse/browse-session.ts` L509-L560）。风控降速旋钮在 Native 路径上被整体丢弃：宿主已把握手快照、重连快照、唤醒快照三处都接到了会话的快照应用入口（`src/main.ts:588`、`:732`、`:1422`），但 Native 会话的那个入口是空方法体（`browse-session.ts:213`，两个参数以下划线前缀声明为未使用）；会话中途的节奏更新命令在常规路径上更早一步就被丢掉（`browse-session.ts:121` 直接 return）。

**第二，点击原语是坐标瞬移的三条裸事件，且按下失败时抬起永不发出**（`aidcp-edge/native/page-engine/src/facebook/shared.rs:802-820`），左键会保持按下、此后所有移动都变成拖拽框选——退役实现专门用 try/finally 堵过这个洞（`aidcp-edge/src/browse/cdp-util.ts:250-259`），Native 版把它丢了。更硬的一条：已归档的 `facebook-note-scoped-targeting` 已经把"反应浮层提交走拟人化贝塞尔移动的 CDP 坐标点击、移动起点须落在『控件→浮层』走廊、且不得 overshoot"写成生效要求，而当前 Rust 点击原语的签名只有目标坐标、连起点都无法表达（`shared.rs:802`），两处浮层提交调用点（`feed_like.rs:123`、`:193`）因此结构上无法满足该要求。

**第三，频次最高的写动作前置手势仍是机器味最重的一种。** 首页点赞前把控件对齐进视口用的是按控件位置精确算出的单帧滚轮加固定 250 毫秒等待（`native/page-engine/src/facebook/feed_like.rs:263-275`），短视频推进的兜底滚轮距离取自墙钟毫秒求余、滚前也无光标移动（`native/page-engine/src/facebook/reels.rs:215-224`），而带惯性的共享滚轮手势只有两个消费者（`facebook/feed.rs:563`、`facebook/comment.rs:90`）。

**同时 DOM-first 定位三道闸没有搬进新引擎**：Rust 侧无锚点缓存与晋升机制（全仓锚点相关命中只有评论锚点 id：`command.rs:308`/`706`/`708`、`model.rs:272`/`399`），唯一出现"升级"结论的是允许清单内的遗留步骤路径，它在单次尝试后即报升级（`native/page-engine/src/xhs-command-router.js:242`），而旧定位层及其全部生产消费方已被列入生产产物禁入表（`aidcp-edge/scripts/prune-production-dist.mjs:64-68`），生产链路上等于不存在。

本 change 直接承接迁移主 change 至今未勾的 3.2（定位三闸移植）与 3.3（输入原语按当前拟人化边界实现，指针与滚轮部分）。

## What Changes

- 让 Native 运行时真正消费云端随指令下发的动作前犹豫与离页停留：所有携带这两个字段的命令在动作前等待、在离开内容前补足停留，并保持"相同中心值产出不同实际时序"。
- 建立"转发即消费"的一致性门禁：某条命令若把时间字段转发进 Native，就必须有对应的消费点；只转发不消费视为回归。
- 恢复节奏兜底在 Native 路径上的接线：握手下发的兜底档位与每类操作下限重新生效，缺时间字段时回落非零下限，云端已烘入档位的值不再二次放大。
- 把 Native 指针原语从"坐标瞬移 + 三条裸事件"改成多帧拟人轨迹（起点可由调用方指定以守住既有的走廊约束），并保证按下与抬起在任何失败路径上都配平、原始错误不被抬起失败掩盖。
- 把按下前后划成不可取消的原子区：取消与截止检查只允许出现在按下之前；按下之后才置位的取消不得对外表现为"未开始"，必须如实报成"已派发、结果待定"，避免云端把一次既成的写当成可安全重放的失败。
- 把首页点赞前的对齐滚动与短视频推进的兜底滚动改用共享拟人滚轮手势（含滚前光标移动），取消"按控件偏移精确算出的单帧位移"与"固定间隔重探"。
- 在 Native 生产路径上恢复定位三道闸：写动作后必须按同一绑定目标校验业务结果、重试有上限且耗尽后诚实升级、新锚点先暂存并连续确认成功才晋升主缓存、任一次后置校验失败即丢弃。
- **BREAKING** "升级"这一结论此后只表示重试上限已耗尽，单次尝试失败不得再报升级。当前唯一违反此语义的实现点在允许清单内的遗留步骤路径（`native/page-engine/src/xhs-command-router.js:242`），而该文件是并行 change `restore-native-xiaohongshu-action-honesty` 的单写区——本 change 只立语义要求，代码由该 change 落地（或以删除该分支达成），本 change 不代改。

## Capabilities

### New Capabilities

- `native-actuation-primitives`: 定义 Native 执行原语的跨平台契约——时间指令消费、指针轨迹与按键配平、原子区边界。
- `native-locating-gates`: 定义 Native 生产路径上的定位三道闸——后置校验、有界重试与升级、锚点先暂存后晋升。

### Modified Capabilities

- `facebook-humanized-scroll`: 把共享拟人滚轮手势的边界从"信息流翻页与评论区找编辑框"扩到写动作前的对齐滚动与短视频推进的兜底滚动。

## Impact

- `aidcp-edge/native/page-engine/src/input.rs`（新增指针原语；滚轮原语复用）——与并行 change `harden-native-engine-runtime-contracts` 重叠，需串行
- `aidcp-edge/native/page-engine/src/facebook/shared.rs`（点击原语改接指针原语）
- `aidcp-edge/native/page-engine/src/facebook/feed_like.rs`（对齐滚动改用共享手势）
- `aidcp-edge/native/page-engine/src/facebook/reels.rs`（兜底滚动改用共享手势）
- `aidcp-edge/native/page-engine/src/command.rs`、`engine.rs`、`facebook/runtime.rs`（时间字段的消费接线）——`command.rs` 与 `runtime.rs` 与 `restore-native-facebook-residual-parity`、`engine.rs` 与三个并行 Native change 重叠，需串行
- `aidcp-edge/src/native-page-engine/browse-session.ts`、`command-mapper.ts`（节奏兜底接线与转发即消费门禁）——`browse-session.ts` 与 `harden-native-engine-runtime-contracts`、`restore-native-xiaohongshu-session-guards` 重叠，需串行
- `aidcp-edge/test/native-page-engine/`、`aidcp-edge/native/page-engine/tests/`（回归门禁）
- （2026-07-28 覆盖漏洞收口新增）`aidcp-edge/native/page-engine/src/engine.rs` 的小红书分发**新增命令特化分支**，把小红书的文本输入与滚动接到已存在的逐字输入 / 惯性滚轮原语（tasks §8）——该入口与 `restore-native-xiaohongshu-action-honesty`、`restore-native-xiaohongshu-session-guards` 共写，需串行；**不改** `native/page-engine/src/xhs-command-router.js`
- （2026-07-28 覆盖漏洞收口新增）`aidcp-edge/native/page-engine/src/facebook-router/00-shared.js` 的通用点击助手去掉瞬移滚动（tasks 3.7），并加脚本文本静态契约检查
- （2026-07-28 覆盖漏洞收口新增）验证码协助落点循环改用指针原语并单列高审查节奏档（tasks 2.9）；其回执诚实性的代码落点在 `aidcp-edge/src/main.ts`，属他人单写区，本 change 只加合约测试并与属主对齐（tasks 2.10）
- 云端协议、命令信封、结果形状、风控记账与配额均不变。
- 本 change **不含**：`aidcp-edge/native/page-engine/src/xhs-command-router.js`（另一 change 的单写区，只受本 change 的升级语义要求约束）、`aidcp-edge/src/main.ts`（已有的三处快照注入点无需改动，且该文件归 `restore-native-xiaohongshu-session-guards`）、`aidcp-edge/scripts/prune-production-dist.mjs`（归 `enforce-native-engine-artifact-gates`，本 change 只做只读断言）。
- 本 change **不含**：云端节奏中心值算法改动、任何 openspec/specs 目录下的直接编辑、Edge 安装包打包与签名、dev/ol 部署、真机写动作验收。
