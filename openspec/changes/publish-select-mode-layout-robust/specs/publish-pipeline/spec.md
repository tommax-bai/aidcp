# publish-pipeline Specification (delta)

## ADDED Requirements

### Requirement: 发布模式选择须跨双布局稳健且失败诚实

下发段第二步「选择图文发布模式」（边缘 `select_mode`：在创作发布页点「上传图文」从默认的上传视频切到图文编辑）MUST 对创作发布页的**宽/窄双布局**稳健。该页与消费端首页/搜索页同机理：tab 栏**重复渲染两套**（一套可见、一套隐藏），DOM 里常同时存在多个文本同为「上传图文」的元素。据此该步 MUST 满足：

- **取可见、非取首个**：MUST 只点**可见**候选 tab（可见性判据 `offsetParent !== null || getClientRects().length > 0`，与消费端一致、兼容窄布局 `position:fixed`），MUST NOT 盲取第一个文本匹配元素（可能是隐藏副本、点之无效）。
- **幂等早退且保守**：点击前 MUST 先判「是否已在图文模式」——以**保守信号**（当前激活 tab 文本含「图文」不含「视频」）为准，已在则直接成功、不重复点击；该判据 MUST 保守，仍是视频模式时 MUST NOT 谎报图文（不静默假成功）。
- **有界等待渲染**：MUST 容忍创作页冷加载 tab 晚渲染——以有界重试「出现即点」而非一次性点击；边缘该步总执行时长 MUST **严格低于云端单指令超时（非配图步 30s）**，绝不因放宽等待把本步拖到云端超时中断。
- **失败诚实分类**：始终无可见「上传图文」tab 且未在图文模式 → MUST 回 `no_target`；点了但图文模式始终未激活（点到隐藏副本 / 点击无效）→ MUST 回 `post_validate_failed`；两者皆 MUST NOT 伪造 `ok:true` 往下走（承发布下发段「MUST NOT 静默假成功」红线）。

窄布局下「上传图文」的精确元素形态（是否收成图标 / 换文案）MUST 经一次运营机实机 CDP 校准后再收紧选择器；校准前以 best-effort 候选（可见 + 文本语义）匹配，未命中 MUST 诚实 `no_target` 而非猜测命中。

#### Scenario: 双布局取可见 tab、躲开隐藏副本
- **WHEN** 创作发布页 DOM 同时存在隐藏副本与可见的「上传图文」tab（隐藏副本在文档顺序更靠前）
- **THEN** `select_mode` MUST 点**可见**的那个 tab（`offsetParent!==null || getClientRects().length>0`），MUST NOT 点在前的隐藏副本

#### Scenario: 已在图文模式 → 幂等成功、不重复点击
- **WHEN** 进入该步时页面已处于图文模式（激活 tab 文本含「图文」不含「视频」）
- **THEN** `select_mode` MUST 直接回 `ok:true`，MUST NOT 因「找不到待点的视频→图文切换」而误报 `no_target`

#### Scenario: tab 冷加载晚渲染 → 有界重试点中
- **WHEN** 创作页刚导航、「上传图文」tab 在最初若干轮轮询时尚未渲染，稍后才出现
- **THEN** `select_mode` MUST 在有界窗口内「出现即点」并确认模式激活后回 `ok:true`；整步耗时 MUST < 云端 30s 单指令超时

#### Scenario: 始终无可见 tab 且未在图文模式 → 诚实 no_target
- **WHEN** 有界窗口内始终没有可见的「上传图文」tab 可点，且页面并非已在图文模式
- **THEN** MUST 回 `ok:false, error:'no_target'`，MUST NOT 伪造成功

#### Scenario: 点了但模式没切上 → 诚实 post_validate_failed
- **WHEN** 点击了候选 tab，但图文模式激活后置校验在窗口内始终不满足（点到隐藏副本 / 点击未生效）
- **THEN** MUST 回 `ok:false, error:'post_validate_failed'`，MUST NOT 谎报模式已切上

#### Scenario: 红线反例——取隐藏副本或保守判据缺位谎报模式（禁止）
- **WHEN** 有实现盲取第一个文本匹配（可能隐藏副本），或用宽松信号在仍是视频模式时早退回 `ok:true`
- **THEN** MUST 视为违规、不予合入；模式选择 MUST 取可见、幂等判据 MUST 保守、失败 MUST 诚实分类
