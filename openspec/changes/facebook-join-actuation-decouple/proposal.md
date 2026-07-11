## Why

Facebook 加群走**两次边缘调用**：① observe-only（`GroupJoinPayload.click` 缺省）——边缘 `Page.navigate` 到群页、观测、回传观测给云端、不点；② 云端裁判观测安全后下 `click=true` 命令——边缘**再次 `Page.navigate` 到新页**、重新观测就绪、点加入。第二次调用在**新页**用自己的词表（`classifyCtaLabel` / Join 关键词）**重新定位**加入按钮点击。若某语种的「加入」按钮文案不在词表内，第二次调用**定位不到 → 加群失败**——这是 pin（[[facebook-locale-pin-en-us]]）与结构后置校验（[[facebook-join-structural-verify]]）都治不了的**点击动作定位**语言相关缝。本 change（分层方案 L2）把点击动作**解耦**：云端把裁定为安全的那个候选的**精确原文 + 序号**随 `click=true` 回传，第二次调用在新页按**精确串**（逐字，非词表分类）重定位该候选点击，语言无关。

**定位**：这是**触协议热点**（`GroupJoinPayload` 加字段 → 两份 `protocol.ts` parity + `command-bridge`）的 change，按 §2 四处同步 + §7 单写者纪律**须与其他动协议/加群命令的 change 串行**。且相对结构后置校验（L3，已独立成 change 先上消灭重复加群），本 change 的收益是**思辨性**的——只在「某语种 Join 按钮文案不在词表、第二次调用定位失败」真机复现时才有实证价值。故建议：**先上 L3、本 change 待真机坐实该失败模式后再实装**（proposal 已入库、设计已定，实装排在 L3 与真机验证之后）。

## What Changes

- **`GroupJoinPayload` 加候选引用**（**协议，additive、向后兼容**）：`click=true` 命令可携带云端裁定候选的**精确原文**（`clickTarget`），供第二次调用在新页按字面串重定位。缺省时边缘回落既有词表定位、不回归。
- **observe 期候选无条件全报**：第一次 observe 调用把每个 Join/候选控件的**原文标签**无条件写入观测（松类型通道），MUST NOT 因标签语种不在词表内而 `continue` 丢弃候选——否则云端拿不到该候选、无从回传。
- **第二次调用按精确字面串相等重定位——字面相等即反自残硬闸（两轮评审纠正）**：收到 `clickTarget` 时，在新页重新观测的候选里按**精确字面串相等**（两侧同一 normalization，非词表分类）找回候选、点它。**字面相等本身就是反自残闸**——Join 与 Leave/取消在任何语种都是不同字面串，Leave 永不等于被批准的 Join 字面串 → 永不解析 → 永不点（比原「Join-kind 结构复核」正确：结构复核分不出同结构的 Join/Leave）。**序号只在多个字面相等候选间消歧、绝不位置兜底**；新页无字面相等候选 → 诚实 `stale_target` / `no_button`，绝不盲点 index N。
- **协议 parity 靠 round-trip 断言把关（评审揪出）**：`GroupJoinPayload` 的可选字段漂移 **`typecheck` 的 `Record<MessageType,true>` 穷举抓不到**；须补一条 edge+cloud 两侧的 `AC-PROTO` round-trip 断言（镜像既有 `AC-PROTO-*`）专门护 `clickTarget` 编解码一致。
- **不做（YAGNI）**：不用观测期页内 DOM 句柄当 token（第二次调用已 re-navigate 新页、句柄必失效，评审证）；不做跨导航 token 持久化；不给按钮上视觉；不删词表（回落用）。

## Capabilities

### New Capabilities
<!-- none -->

### Modified Capabilities
- `facebook-group-join-resilience`: 新增「点击动作解耦」要求——`click=true` 命令可携带云端裁定候选的精确原文，第二次调用在新页按**精确字面串相等**重定位点击（字面相等本身即反自残硬闸、Leave 永不匹配、序号只在字面相等候选间消歧绝不位置兜底、失配诚实 `stale_target` 不盲点）；候选原文无条件上报；缺 `clickTarget` 回落既有词表定位不回归。

## Impact

- 代码（**协议热点，串行**）：
  - edge+cloud 两份 `src/comm/protocol.ts`：`GroupJoinPayload` 加可选 `clickTarget`（精确原文；如需消歧可带序号）；逐字一致。
  - cloud `command-bridge` / 加群裁判：回传裁定候选的 `clickTarget`。
  - edge `src/facebook/join-executor.ts`：observe 候选原文无条件上报；第二次调用按**字面串相等**重定位（字面相等即反自残闸）+ 序号只消歧 + 失配诚实 `stale_target`；`edge-client.ts` 主动命令路由确认放行（若走独立下发）。
  - 测试：edge+cloud `AC-PROTO` round-trip 断言 for `clickTarget`（专门护可选字段漂移）。
- 部署：edge dev land + cloud dev（安全序列；协议改动后先 `test:acceptance` 含 `AC-PROTO-*` 再全量 `test` 再 `typecheck`）。
- 真机验收：落 backlog（判定准确率门：`clickTarget` 精确串重定位稳、反自残闸不误点、缺 token 回落不回归）——本 change 实装本身**待真机坐实「词表定位失败」失败模式**后再启动。
- 依赖：无新增。
