## Why

Facebook 加群走**两次边缘调用**：① observe-only（`GroupJoinPayload.click` 缺省）——边缘 `Page.navigate` 到群页、观测、回传观测给云端、不点；② 云端裁判观测安全后下 `click=true` 命令——边缘**再次 `Page.navigate` 到新页**、重新观测就绪、点加入。第二次调用在**新页**用自己的词表（`classifyCtaLabel` / Join 关键词）**重新定位**加入按钮点击。若某语种的「加入」按钮文案不在词表内，第二次调用**定位不到 → 加群失败**——这是 pin（[[facebook-locale-pin-en-us]]）与结构后置校验（[[facebook-join-structural-verify]]）都治不了的**点击动作定位**语言相关缝。本 change（分层方案 L2）把点击动作**解耦**：云端把裁定为安全的那个候选的**精确原文 + 序号**随 `click=true` 回传，第二次调用在新页按**精确串**（逐字，非词表分类）重定位该候选点击，语言无关。

**定位**：这是**触协议热点**（`GroupJoinPayload` 加字段 → 两份 `protocol.ts` parity + 云端回传接线）的 change，按 §2 四处同步 + §7 单写者纪律**须与其他动协议/加群命令的 change 串行**。且相对结构后置校验（L3，已独立成 change 先上消灭重复加群），本 change 的收益是**思辨性**的——只在「某语种 Join 按钮文案不在词表、第二次调用定位失败」真机复现时才有实证价值。故：**保持 deferred，先上 L3 + 作用域前置（change [[facebook-join-candidate-scope-guard]]），本 change 待真机坐实失败模式后再实装**。

### 2026-07-12 修订（真机证据评审后，超越以下各点）

2026-07-11 合成 + 真机探针（21/21 真页决策正确、零自残）+ 一轮多视角对抗评审对本 change 提出 5 处必改，实装前**须以本块为准**：

1. **作用域是承重前置，不是 Open Question（超越 D3 序号消歧）**：真页坐实「同字面异群」——目标群自身 Join 与侧栏推荐群 Join 字面逐字相同（「加入小组」），且当目标状态在两次调用间翻成 pending 时字面相等集合里全是推荐群按钮。故 `clickTarget` 字面相等匹配**必须**在**目标群自身动作区作用域内**进行（由前置 change [[facebook-join-candidate-scope-guard]] 提供 `inTargetScope`）；作用域外的字面相等一律 `stale_target`。**序号跨导航不成立**（推荐栏动态重排 + 探针按 `label||aria` 去重后「多个字面相等候选」根本不同时上报），降级为诊断字段、绝不作选取依据。
2. **L4 云端候选裁定 = 本 change 的云端半，随本 change 落地（非可选冷层）**：本 change 前提「云端把裁定候选原文回传」在其目标场景（自身 CTA 词表判不出）下，判官确定性路径不触发、LLM 兜底只回 verdict 无候选。故判官须加**候选裁定模式**（全候选清单进 prompt、返回选中候选的字面串或 fail-safe 弃权 -1、置信门控），产出即 `clickTarget`。探针已证此半可行（合成 111/111 + 真机 21/21，fail-safe 被遵守）。无此步本 change 在其立论场景不可实装。
3. **管道指向订正**：`group.join` 信封**不走 command-bridge 动作映射**（`grep 'group.join' command-bridge.ts` 零命中），在 `facebook-group-join-edge-steps.ts` 直接构造下发。`clickTarget` 回传须接**判官 → scheduler → edge-steps 信封**链，非 command-bridge。
4. **候选 schema 分 `text`/`aria` 两字段（非合并 `text||aria`）**：真页点赞/评论类控件语义在 `aria`、可见 `text` 只是计数；`clickTarget` 须标明匹配的是哪个源字段，两侧同源字段同 normalization。
5. **触发门重述（界面语言随账号、非随群）**：C1 钉新号英文 + 存量号中文皆词表覆盖，「未知语种 Join 文案」在现役 fleet 大概率不复现；真正复现的失败是**状态词缺口 + 推荐栏干扰**（分别由 [[facebook-join-pending-label-audit]] 与 [[facebook-join-candidate-scope-guard]] 即时修，与本 change 解耦）。本 change 触发门改为「真机坐实**新页重定位保真度**失败（跨导航候选身份对不上）」，而非「Join 文案词表缺失」。deferral 本身保留（协议热点成本真实）。

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

- 代码（**协议热点，串行**；以「2026-07-12 修订」块为准）：
  - edge+cloud 两份 `src/comm/protocol.ts`：`GroupJoinPayload` 加可选 `clickTarget`（含匹配源字段标记 text/aria；序号仅诊断）；逐字一致。
  - cloud 加群**判官**（`src/agents/facebook-group-join-judge.ts`）加**候选裁定模式**（全候选进 prompt、返回选中候选字面串或 fail-safe -1），`clickTarget` 经**判官 → scheduler → `facebook-group-join-edge-steps.ts` 信封**回传（**非** command-bridge——`group.join` 不走 command-bridge 动作映射，修订 3）。
  - edge `src/facebook/join-executor.ts`：observe 候选原文无条件上报（分 `text`/`aria` 字段 + `inTargetScope`）；第二次调用按**作用域内字面串相等**重定位（作用域由前置 change [[facebook-join-candidate-scope-guard]] 提供）+ 失配诚实 `stale_target`；序号绝不作选取依据。
  - 测试：edge+cloud `AC-PROTO` round-trip 断言 for `clickTarget`（专门护可选字段漂移）。
- 部署：edge dev land + cloud dev（安全序列；协议改动后先 `test:acceptance` 含 `AC-PROTO-*` 再全量 `test` 再 `typecheck`）。
- 真机验收：落 backlog（`clickTarget` **作用域内**精确串重定位稳、反自残 + 反错群闸不误点、缺 token 回落不回归）——本 change 实装**待真机坐实「新页重定位保真度」失败模式**后再启动（触发门重述，修订 5）。
- 依赖：**前置 change [[facebook-join-candidate-scope-guard]]（作用域）+ [[facebook-join-pending-label-audit]]（状态词）**——二者先落、即时修现网危害；本 change 的字面相等匹配必须在其作用域内进行。
