## ADDED Requirements

### Requirement: 面板把搜索展示为账号风险动作

Cloud `/api/version` 的风险动作全集、配额 API、`GET /api/dashboard/summary` 的全局/按账号今日活动、day 上限与饱和标记 SHALL 包含 `search`。Console SHALL 同步镜像 search 枚举、标签与排序，在配额页和今日账号活动中显示“搜索”，并继续对未知动作做中性回落；漂移哨兵 SHALL 以 live Cloud 枚举检出 Cloud/Console 不一致。

#### Scenario: 今日活动显示搜索用量与上限

- **WHEN** 某账号今日已真实执行 2 次搜索且生效 day 上限为 10
- **THEN** 总览按账号活动显示 search 用量 2、上限 10，并按真实窗口状态显示是否饱和

#### Scenario: 搜索枚举漂移被哨兵检出

- **WHEN** Cloud `/api/version` 已包含 search，而 Console 镜像缺失
- **THEN** 枚举漂移测试失败，阻止把不完整看板当作兼容成功

### Requirement: 单场搜索预算使用行为术语

Console 配额页中同时包含浏览/搜索与互动动作的会话预算分组 SHALL 命名为“单场行为预算”，MUST NOT 继续把其中的搜索误称为“互动”。该文案调整不改变 `budget.searches` 的数值、扣减时机或服务端契约。

#### Scenario: 配额页准确描述搜索预算

- **WHEN** 运营打开配额页查看包含搜索的单场预算
- **THEN** 页面显示“单场行为预算”，搜索仍作为独立一项展示

