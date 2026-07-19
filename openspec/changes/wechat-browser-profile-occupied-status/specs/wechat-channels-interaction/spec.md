## ADDED Requirements

### Requirement: 视频号启动鉴权必须优先复用已保存 API 会话

视频号 Edge 启动时 SHALL 先读取本地加密会话，并在浏览器关闭状态下校验平台身份与所有已启用只读探针。只有这些硬门禁全部通过，授权态才 SHALL 进入 API-only 正常运行；该路径 MUST NOT 启动浏览器。加密记录存在但身份或探针未通过时，MUST NOT 仅凭记录存在宣称鉴权成功。

#### Scenario: 有效记录无需浏览器即可鉴权通过

- **WHEN** 本地加密会话可读、平台身份与绑定一致，且所有已启用只读探针通过
- **THEN** Edge SHALL 上报 `status=active`、`browserState=closed`、`reasonCode=null`
- **AND** MUST NOT 调用浏览器 provider

#### Scenario: 失效记录不得冒充成功

- **WHEN** 本地加密会话存在但平台返回登录失效，或身份/已启用只读探针未通过
- **THEN** Edge MUST NOT 上报鉴权通过
- **AND** 只有需要补授权的结构性结果才 SHALL 进入既有浏览器重认证路径

### Requirement: 补授权浏览器被占用必须进入明确可重试真态

视频号因会话失效而需要浏览器补授权时，若 provider 明确返回 profile 被占用，授权协调器 SHALL 结束本次 `authenticating`，进入 `reauth_required`，上报 `browserState=unavailable` 与 `reasonCode=INTERACTION_BROWSER_PROFILE_IN_USE`。该状态下历史内容 SHALL 保持可查看，所有平台写能力 MUST 保持关闭；系统 MUST NOT 自动强制抢占、MUST NOT 宣称仍在鉴权或鉴权成功。

Cloud SHALL 接受、持久化并通过客户 API 原样投影该原因码。客户工作区 SHALL 显示“浏览器环境被占用”、说明解除占用后重试，并提供显式重新鉴权入口；客户 API 与 UI MUST NOT 暴露原始占用邮箱。动作 accepted 只表示重试请求已受理，只有后续 auth status 回到 `active` 才表示恢复完成。

#### Scenario: 启动补授权时 profile 被占用

- **WHEN** 已保存会话校验为登录失效，且 `browser-profile/start` 明确拒绝原因为 profile 被占用
- **THEN** Edge SHALL 上报 `status=reauth_required`、`browserState=unavailable`、`reasonCode=INTERACTION_BROWSER_PROFILE_IN_USE`
- **AND** Cloud SHALL 原样持久化和投影该状态
- **AND** 客户工作区 SHALL 显示占用提示、历史可读与写操作暂停，并显示“重试打开浏览器”入口
- **AND** Edge、Cloud、客户 API 与 UI MUST NOT 暴露原始占用邮箱

#### Scenario: 解除占用后显式重试恢复

- **GIVEN** 当前授权原因码为 `INTERACTION_BROWSER_PROFILE_IN_USE`
- **WHEN** 客户解除外部占用并触发既有重新鉴权动作，provider 成功打开 profile，身份与已启用只读探针通过
- **THEN** Edge SHALL 保存新会话并回到 `status=active`
- **AND** UI 只有读回新的 active 状态后才 SHALL 显示鉴权通过

#### Scenario: 占用状态不做高频自动抢占

- **WHEN** profile 占用持续存在且客户尚未触发重试
- **THEN** Edge MUST NOT 高频重复调用 start、stop 或执行强制抢占
- **AND** 授权状态 SHALL 保持 fail-closed，等待显式重试或新的真实状态证据
