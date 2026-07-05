## MODIFIED Requirements

### Requirement: 定向评论目标定位——搜索驱动精确匹配、绝不导航存量链接
定向评论 SHALL 以该笔记标题（截断至有界长度以守单步时限）为搜索词发起平台搜索，并 SHALL NOT 在 `search.execute` 中下发 `sort` 或 `timeWindow` 参数；平台默认的综合排序与不限时间窗 SHALL 通过省略筛选参数获得，而不是通过驱动原生筛选面板获得。定向评论 SHALL 在返回卡片中按 noteId 精确匹配目标；命中后 SHALL 打开该卡片并以详情上报的 noteId 校验一致后方可评论。MUST NOT 导航存量 source_url（xsec_token 过期风险）、MUST NOT 由裸 noteId 伪造链接、MUST NOT 在未命中时退而评论「相似」笔记。搜索定位 SHALL 有界重试（不超过 2 次搜索尝试），用尽未命中 SHALL 以 note_not_found 诚实结束。

#### Scenario: 精确命中后才开笔记评论
- **WHEN** 搜索结果卡片中存在与目标 noteId 精确相等的卡片
- **THEN** 打开该卡片、校验详情 noteId 一致后进入撰写；校验不一致则不评论

#### Scenario: 定向搜索不驱动原生筛选控件
- **WHEN** 定向评论发起目标搜索
- **THEN** 搜索命令不携带 `sort` 或 `timeWindow`，边端不得因此打开或点击搜索结果页筛选控件；平台默认综合排序与不限时间窗用于召回，保证非当日老笔记可被检索

#### Scenario: 有界重试后诚实失败
- **WHEN** 两次搜索尝试的返回卡片均无目标 noteId
- **THEN** 任务以 note_not_found 终态结束并如实上报，MUST NOT 换目标补发

#### Scenario: 红线反例——导航存量笔记链接（禁止）
- **WHEN** 有实现以精选行存量 source_url 直接导航、或以裸 noteId 拼详情链接打开笔记
- **THEN** MUST 视为违规不予合入；目标定位只允许搜索驱动+卡片点击路径
