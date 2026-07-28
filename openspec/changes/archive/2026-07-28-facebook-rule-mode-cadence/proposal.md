## Why

Facebook 自动浏览目前以账号人设做内容选择，并由活跃时段控制何时运行；系统没有一种在冷启动结束后按已确认浏览量稳定触发互动的账号级模式。需要增加一个仅限 Facebook、与冷启动互斥、无需人设内容判断但继续服从全部风控的规则模式，避免把计数节奏塞进人设提示词或另造不受控的定时器。

## What Changes

- 为 Facebook 账号增加显式规则模式：在账号活跃时段内顺序浏览，不做人设兴趣、偏好或强制互动规则判断；非 Facebook 不展示、不接受也不运行该模式。
- 固定首版规则为每累计 10 个已确认、稳定身份且未在当前规则批次重复的内容，创建一个规则批次；批次串行尝试一次点赞和一次“加群评论（联系）”，不提供任意脚本或自由组合规则。
- 冷启动拥有绝对优先级：权威慢启动投影为 `active` 时规则模式不启动、不计规则进度；慢启动事实未知或环境绑定冲突时 fail-closed。只有 `off` 或 `graduated` 且其它入口闸通过时规则模式才可运行。
- 规则浏览绕过的仅是人设相关性与互动偏好判断；登录、身份、页面/目标唯一性、敏感内容安全、已访问/已赞、动作后验证、账号暂停、活跃时段和浏览器单飞继续生效。账号仍须满足现有绑定人设入口闸，评论正文继续使用账号现有 Facebook 评论配置、联系方式与审批策略。
- 每个规则批次的 `view`、`like`、`join_group`、`comment` 分别经过 Cloud 权威风控预闸；风控拒绝形成可见的 `risk_suppressed` 终态，不下发、不假成功，也不积累为额度恢复后的历史欠账。
- 规则进度与批次终态持久化并按账号、规则版本、唯一内容和部署目标去重；进程重启、Edge 重连或重复上报不得重算浏览或重复创建批次。
- 复用 `facebook-join-contact-first-post` 定义的加群后联系评论链，不新增第二条加群/评论执行路径。仅在 Facebook 规则模式、冷启动未激活且平台确认刚加入目标群后，允许该批次继续联系评论；普通群覆盖仍保留既有暖群约束。

## Capabilities

### New Capabilities

- `facebook-rule-mode`: 定义 Facebook 账号规则模式的配置、冷启动优先级、固定 10 条浏览批次、持久进度、串行动作、逐动作风控与诚实投影。

### Modified Capabilities

- `facebook-dev-autobrowse-policy`: 将账号级规则模式纳入 Facebook 生命周期启动来源，并继续禁止用部署环境或进程环境变量授权浏览。
- `facebook-feed-browse`: 规则模式改为不经人设相关性选择的顺序浏览，同时保留唯一内容、页面身份、安全检查、节奏和动作验证。
- `mandatory-account-persona`: 为已绑定人设账号增加窄例外——规则模式浏览与点赞不读取人设做内容/偏好判断；未绑定账号仍不得启动，评论链仍沿用现有人设与评论配置要求。
- `content-schedule`: 在统一账号自动化入口增加 Facebook 规则模式配置和进度投影，并让规则运行继承账号有效活跃时段而不复用小时格内容动作触发。
- `facebook-group-comment-coverage`: 为规则批次的 caller-pinned、平台确认刚加入群增加范围化同日联系评论例外；普通覆盖选择器的暖群、冷却和单飞语义保持不变。

## Impact

- **Control**：新增上述 OpenSpec 能力与 delta，记录对 `facebook-join-contact-first-post` 的依赖及与未来 `add-managed-automation-runtime` Trigger/Task 模型的迁移映射。
- **Cloud**：增加账号规则配置、规则进度/批次持久化、慢启动真态仲裁、非人设浏览选择器、逐动作风险准入、规则批次调度与诚实结果投影。
- **Console**：在 Facebook 账号自动化视图增加规则模式开关、固定规则说明、当前 `0..9/10` 进度、批次动作状态及阻断原因；其它平台无入口。
- **Edge**：复用现有 Facebook 浏览、点赞、加群和评论原子能力；规则模式不得引入新的本地授权事实。`facebook-join-contact-first-post` 所需的 `note.open` 扩展仍由其自身变更交付。
- **Data**：需要服务端迁移承载账号规则配置、唯一浏览 checkpoint 和批次终态；持久可认领记录继续带服务端注入的 `execution_target`。
- **Dependency**：加群联系评论纵切在 `facebook-join-contact-first-post` 未实现、验证和集成前不得启用。本变更不授权 Edge 打包、OL 部署或真实账号写入验收。
