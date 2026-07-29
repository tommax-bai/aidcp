## Why

把 Facebook 页面逻辑搬进 Native Page Engine（edge `4f04e9c`，2026-07-23）时，feed 就地读只搬了**输出结构**、没搬**行为**：现在 `note.open{surface:'feed'}` 只把卡片上已渲染的文字抓走就返回，不点展开控件、不校验正文是否真的变长、不做展开无效的诚实失败、不做环境变化回落详情，也不设按正文长度的读后停留地板；同时 Native 收下云端下发的 `thinkMs` 后从头到尾没有任何消费点。这三件事都是**已生效规格的现行要求**（`facebook-feed-browse` 的「就地读全文」、`command-pacing` 的「`thinkMs` 执行前等待」与「就地读 read floor 第三锚点 / Native MUST NOT 接收字段后静默丢弃」），当前实现逐条违反。

后果分两层。**行为层**：账号在 feed 上不再有展开动作、停留还因正文被截短而同步缩水，两头一起往机器味上走。**决策层**：人设模式打开后那道内容质量粗筛吃的是折叠段而非全文，深读 / 评论 / 点赞整条链建在残缺文本上；规则模式虽不调模型，但它的「已确认浏览」是直接兑换点赞与加群评论的凭证，用一次零交互的 DOM 抓取换真实互动，正撞红线「MUST NOT 静默假成功」。

这类回归**没有任何机械手段会报警**：`native-facebook-behavior-parity` 逐条列举了 Native 必须保住的行为，唯独漏了就地读与节奏消费，于是迁移任务被勾成完成、编译与单测全过、只有真机才看得出来——与小红书那次迁移复盘同型。

## What Changes

- Native Facebook 的 feed 面 `note.open` 恢复完整就地读：按规范帖身份锁定唯一顶层卡片 → 正文已在 DOM 内仅被视觉截断时走免点击捷径 → 否则只点该卡消息容器内锚定的展开控件（绝不点链接、用页内点击）→ 校验展开前后 URL、弹层数、目标卡序号未变 → 读全文上报。
- 恢复两条诚实终态：点了展开但正文长度未增 → 报「展开无效」而非当成功；展开过程中环境变化（URL 变 / 弹层出现 / 目标卡位移）→ 中止就地读、回落详情页导航、以 detail 面诚实上报。无展开控件的短帖读到什么算什么，是正常成功、不是 `no_target`。
- 恢复就地读的边缘本地停留地板：按读到的正文长度（叠 `tempo`）算 read floor，锚在就地读开始时刻，与云端 `dwellMs` 的新卡锚点**取 max、不相加**。
- Native 执行层消费 `thinkMs`：在动作前等待抖动后的时长，与最小间隔取 max、不相加；MUST NOT 再出现「映射层收下字段、执行层丢弃」。
- 顺带修正同一条路径上的动作名漂移：Facebook 页面规则脚本里 feed 面开帖失败回的是 `open`，而云端角色关联的规范名是 `open_note`（脚本里其余动作名——`like` / `comment` / `back` / `join_group` 等——都已对齐，只有这一个漏了）。不修的话本次新增的「展开无效」终态会以云端不认识的名字回上去。
- 补 Native 行为级回归测试，把上述四条钉死；并把「就地读 / 节奏字段消费」写进 Native 行为对等的必测清单，堵住同类回归再次静默通过。
- **不做**按模式分叉：规则模式与人设模式共用同一条执行路径，客户端不感知模式。云端两侧（`aidcp-cloud`）零改动。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `native-facebook-behavior-parity`: 增加两条 Native 必须保住的行为——feed 面就地读的完整展开语义与诚实终态、云端节奏字段（`thinkMs` / 就地读 read floor）的实际消费；并把二者纳入 Native 行为级回归测试的必测清单。

## Impact

- **Edge**：`aidcp-edge/native/page-engine` 的 Facebook 路由（feed 面 `note_open` 分支、共享读取助手）恢复展开与校验；Rust 执行层消费 `think_ms`；`aidcp-edge/src/native-page-engine/browse-session.ts` 恢复就地读 read floor 锚点并接入既有 max 语义。行为参照已退役的 TypeScript 就地读（`src/facebook/inline-reader.ts`、`src/facebook/facebook-session.ts` 的 read floor 计算），该实现仍在仓内可读、但已编译期不可达且不进打包产物。
- **Cloud**：零改动。云端已按 `surface:'feed'` 下发、已在规则模式关闭质量粗筛、已在「帖子详情」上报的唯一入口记浏览与规则进度，正文变完整后自动受益。
- **Console**：无。
- **Data / 协议**：无新增消息类型、无字段变更、无迁移。
- **可观测后果（预期内，非缺陷）**：规则模式每篇多一次点击与更长停留 → 攒满 10 条的时间拉长 → 规则批次触发频率下降；恢复「展开无效」诚实失败后会出现今天不存在的打开失败终态，该卡在本会话内已被标记选过、不再重选，等于偶尔白烧一张卡；环境变化回落会偶尔多一次详情页往返。
- **验收**：本地可覆盖到「免点击捷径 / 点击展开 / 展开无效 / 环境变化回落 / read floor 与 dwell 取 max / thinkMs 前置等待」的判定层；真实 Facebook 长帖的展开控件形态与折叠语义须真机确认，按既有约定登记进 `docs/real-machine-acceptance-backlog.md`。
- **不在范围**：Native 迁移是否还丢了**其它**行为（本次只处理就地读与节奏两类）；`command-pacing` 要求的「操作类命令最小间隔 gating」在 Native 路径同样缺失（`applyPacingSnapshot` 目前是空实现），本次只接 `thinkMs` 与就地读 read floor，最小间隔单列后续处理并登记；桌面安装包出包。
