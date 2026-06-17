# deep-read-fidelity Specification

## Purpose
TBD - created by archiving change fix-browse-action-fidelity. Update Purpose after archive.
## Requirements
### Requirement: 评论滚动须真实执行并按实测位移如实回报

`scroll_comments` 动作 MUST 真正滚动评论区，并依据**实测 `scrollTop` 位移**回报结果，MUST NOT 仅凭"选择器命中"就无条件回报成功。边缘 SHALL 在运行时按 overflow 能力定位真正可滚动的容器（从评论节点上溯首个 `scrollHeight>clientHeight` 且 `overflowY` 为 `auto/scroll` 的祖先），而非依赖未校准的硬编码 class 名。

#### Scenario: 真实位移 → 如实回报滚动次数
- **WHEN** 评论区可滚动且执行滚动后 `scrollTop` 增大
- **THEN** 回报 `ok:true`，`reason` 反映**实际发生位移**的次数（如 `scrolled=N/total`）

#### Scenario: 命中但不可滚动 → 不假报成功
- **WHEN** 探测命中某容器但其不可滚动 / 已到底（`scrollTop` 无变化）
- **THEN** 回报 `ok:false reason:'no_scroll'`（区别于"找不到容器"的 `no_target`），MUST NOT 回报"滚动完成"

#### Scenario: 容器定位按 overflow 能力而非硬编码 class
- **WHEN** 真机评论区 DOM 的容器 class 与预设不符
- **THEN** 边缘仍能通过运行时 overflow 能力上溯找到真正可滚动容器并滚动

### Requirement: 深读动作节奏匹配真人滑动

评论区连续滚动的间隔 SHALL 采用快速微滚动节奏（`scroll` 时序预设，量级 ~0.4-2s），MUST NOT 误用卡片间隔 `cardGap`（3-12s）——后者既不拟人、又把"什么都没滚动"的耗时拉到数十秒。

#### Scenario: 评论滚动用 scroll 预设而非 cardGap
- **WHEN** 连续滚动评论 N 次
- **THEN** 每次滚动间隔取 `scroll` 预设量级，总耗时与真实滚动相称

