# comment-search-command Specification

## Purpose
TBD - created by archiving change comment-search-nav-confirm. Update Purpose after archive.
## Requirements
### Requirement: 搜索采卡前 MUST 确认已到达搜索结果页，未到诚实回失败且不得把 feed 当结果

命令评论的搜索在采集/上报结果卡片之前，边端 MUST 以**实时页面 URL** 确认当前已处于搜索结果页（小红书 `search_result` / `search_result_ai` 一类结果页 URL）。当导航未确认到达结果页时（回车未提交、提交兜底失败、仍停在首页 feed 或其它页），边端 MUST NOT 采集/上报当前页卡片、MUST NOT 把首页 feed 当作搜索结果上报，且 MUST 跳过对错误页的原生筛选重试；边端 MUST 发一条诚实的搜索失败回执 `action.completed{action:'search', ok:false, reason:'not_on_search_page'}`。到达确认 MUST 以采卡时刻的实时 URL 为准，MUST NOT 仅凭一个可能滞后的「已导航」布尔与 URL 取 AND（避免把「其实已到结果页但确认稍慢」误杀成不上报）。此判定 MUST 仅作用于命令/搜索采卡路径，MUST NOT 影响自治浏览对首页 feed 的合法卡片上报。

#### Scenario: 未导航到结果页 → 不报卡 + 诚实回失败
- **WHEN** 边端执行搜索后实时 URL 仍非搜索结果页（如停在 `/explore` 首页 feed）
- **THEN** MUST NOT 上报任何卡片、MUST NOT 把当前 feed 卡当搜索结果
- **AND** MUST 发 `action.completed{action:'search', ok:false, reason:'not_on_search_page'}`
- **AND** MUST 跳过对该错误页的原生筛选重试

#### Scenario: 已到达结果页 → 照常采卡
- **WHEN** 边端执行搜索后实时 URL 已是搜索结果页
- **THEN** MUST 照常应用原生排序/时间筛选并采集、上报结果卡片

#### Scenario: 搜索执行抛错 → 走失败分支，不 fall through
- **WHEN** 搜索执行过程抛出异常
- **THEN** MUST 视为未到达结果页、走诚实失败回执分支，MUST NOT fall through 去上报当前页卡片

#### Scenario: 红线反例——把 feed 当搜索结果上报（禁止）
- **WHEN** 有实现在导航未确认时照常 `reportVisibleCards` 把首页 feed 卡当搜索结果上报
- **THEN** MUST 视为违规、不予合入；这会让云端选中与搜索词无关的幻影候选（静默假成功红线）

### Requirement: 云端 MUST 消费搜索导航失败回执并真实归因失败原因

云端命令评论的搜索步在等待结果时 MUST 同时监听结果卡片到达与搜索失败回执（竞速 `page.cards.arrived` 与 `action.completed{action:'search'}`）；收到 `ok:false` 时 MUST 立即以空候选快速失败，MUST NOT 干等满单步超时（消除多搜索词各等一遍超时的空转）。云端对「搜索未导航到结果页」MUST 用**独立、真实**的结论呈现，MUST NOT 沿用「（超时/边端离线）」措辞、MUST NOT 折叠进「无匹配笔记 / 无强相关候选」（那会把导航失败误报成内容缺失）。此外，命令评论的 `read_failed` 回执 MUST 携带真实失败原因（对齐 `post_failed` 的 reason 呈现），MUST NOT 一律硬编码「（边端超时或离线）」——边端在线的诚实失败绝不误报成离线。

#### Scenario: 收到搜索失败回执 → 快速失败 + 真实归因
- **WHEN** 云端搜索步收到 `action.completed{action:'search', ok:false, reason:'not_on_search_page'}`
- **THEN** MUST 立即以空候选返回、不等满单步超时
- **AND** 回执/日志 MUST 呈现「搜索未导航到结果页」的真实结论，MUST NOT 说「超时/边端离线」，MUST NOT 说「无匹配笔记」

#### Scenario: read_failed 回执带真实原因
- **WHEN** 命令评论以 `read_failed` 结束且结果带有 reason（如复检目标不可用）
- **THEN** 回执 MUST 呈现该真实 reason，MUST NOT 一律硬编码「（边端超时或离线）」

#### Scenario: 红线反例——把在线诚实失败误标为离线（禁止）
- **WHEN** 边端在线且诚实回报了搜索/开笔记失败，但云端把它对运营呈现为「边端超时或离线」
- **THEN** MUST 视为违规、不予合入（假归因红线）；MUST 区分「未导航到结果页 / 无结果 / 真离线」并如实呈现

