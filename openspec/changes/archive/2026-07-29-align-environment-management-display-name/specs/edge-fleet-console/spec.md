## MODIFIED Requirements

### Requirement: 客户端环境身份锚点统一解析显示名与来源

客户端所有表达“当前环境 / 当前账号”的身份锚点 SHALL 复用同一个主进程与 renderer 共用的环境显示名解析器，至少覆盖左栏环境行、标题栏、互动工作区、内容工作区、环境处理引导、人设浮层、桌面人设提醒、浏览器内人设横幅，以及环境管理列表与该列表派生的批量选择可访问名称、代理弹层/预览、平台修改提示和删除确认。解析器 SHALL 返回显示名与来源，优先级固定为人工昵称 → 真实平台昵称 → AdsPower / 花名册环境名 → 环境尾号兜底。标题栏仅在来源为真实平台昵称时加 `@`；人工昵称 MUST NOT 冒充平台身份。来源为尾号兜底且账号 ID 已知时，标题栏 MAY 保留“账号 …尾4位”的既有上下文语义。

评论/私信参与者、内容作者及其他第三方业务对象的昵称不属于环境身份锚点，MUST 继续读取各自经过验证的业务 DTO，MUST NOT 被当前环境的人工昵称替换。运行中的 Electron renderer 不具备源码热加载能力；交付与验收 SHALL 明确需要重启客户端后才可观察新解析规则。

共享解析器 MUST 在项目根目录 `type: module` 约束下提供明确的 CommonJS 加载边界，使 Electron 31 / Node 20 主进程可以从同步启动链直接 `require()`；renderer SHALL 通过普通 script 复用同一实现。自动化验证 MUST 包含不经过 `tsx` 或其他 loader、使用项目 Electron 内置 Node 直接加载主进程依赖的启动冒烟。

环境管理 SHALL 以 AdsPower profile ID / 环境 key 关联 fleet 或花名册后解析显示名；解析结果只用于可见文案与可访问名称。加入、移出、平台修改、代理保存和删除 SHALL 继续以稳定 profile ID / 环境 key 寻址，MUST NOT 使用可能变化或重复的显示名决定动作目标。

#### Scenario: 人工昵称覆盖所有当前环境锚点
- **WHEN** 环境 `Tianxing Bai` 被人工改为 `Tianxing Bai1`，同时平台身份仍上报 `Tianxing Bai`
- **THEN** 左栏、标题栏、互动/内容工作区、引导、人设浮层、桌面提醒、浏览器内人设横幅与环境管理均显示 `Tianxing Bai1`
- **AND** 标题栏不为该人工昵称添加 `@`

#### Scenario: 环境管理动作保持稳定身份
- **WHEN** 人工昵称与 AdsPower 实时名不同，运营在环境管理中选择、修改代理或平台、移出或删除该环境
- **THEN** 行和相关提示显示统一解析后的昵称，但动作载荷仍使用该环境的稳定 profile ID / 环境 key，MUST NOT 以昵称匹配目标

#### Scenario: 清除人工昵称后同步回落
- **WHEN** 运营清除某环境的人工昵称
- **THEN** 左栏与已打开或随后打开的环境管理均按真实平台昵称、AdsPower / 花名册环境名、环境尾号的既有优先级同步回落

#### Scenario: 没有人工昵称时仍显示真实平台昵称
- **WHEN** 当前环境没有人工昵称但已读到真实平台昵称
- **THEN** 所有环境身份锚点显示真实平台昵称，标题栏可用 `@` 表明其平台来源

#### Scenario: 第三方昵称不被环境别名污染
- **WHEN** 评论或私信列表展示参与者，或内容记录展示作者
- **THEN** 该位置继续显示业务 DTO 中的真实参与者 / 作者昵称，MUST NOT 替换为当前环境人工昵称

#### Scenario: 旧进程不会热加载新规则
- **WHEN** Electron 客户端启动时间早于包含新解析器的代码提交或构建时间
- **THEN** 验收必须先重启到新代码，再判断人工昵称是否生效，MUST NOT 把旧 renderer 的结果归因于新解析器

#### Scenario: Electron 原生 CommonJS 启动链可加载共享解析器
- **WHEN** 在根目录 `type: module` 配置下，由项目 Electron 31 内置 Node 20 且不使用 `tsx` loader 同步加载 `persona-notice.cjs`
- **THEN** 共享环境显示名解析器成功加载，进程以零状态退出，MUST NOT 抛出 `ERR_REQUIRE_ESM`
