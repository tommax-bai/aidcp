## Why

账号那串「关联群聊引流码」在数据层本就是一个**原样存储的可选文本**（不裁剪、不截断、无格式约束），上层逻辑只是「非空则贴到评论末尾、为空则 fail-closed 不发」。当前命名把它锁死在「群聊 / 群码」这一种载体上，属过度具体：小红书用群码，后续要装微信号、电话，Facebook 侧可能是 Zalo 号 / 电话——它们都只是一段字符串。把这个概念正名为平台无关的「联系方式」（contact info），是让命名对齐它真实承担的职责，为多平台承载去掉命名负债。

## What Changes

- **术语泛化**：全栈把「群聊引流码 / 群码 / 引流」正名为「联系方式」（contact info / `contactInfo` / `contact_info`）。数据语义、fail-closed 行为、「审=发」红线一律不变。
- **命令语法** — **BREAKING**：`/comment <昵称> group:on/off` 改为 `/comment <昵称> --contact`（干净切换，不保留 `group:on` 别名）；飞书帮助文本与结果卡里写死的旧命令文案一并更新。
- **底层物理名也改** — **BREAKING（需协调迁移）**：
  - DB 列 `accounts.group_chat_info → contact_info`：schema-qualified 幂等 guard（旧列存在且新列不存在才 RENAME）+ `SET lock_timeout`，作为协调单写迁移（非自愈），新增前向迁移文件、不改历史迁移文件名。
  - 协议 wire 字段 `groupChatCode → contactInfo`：两份 `protocol.ts` 逐字同源同 commit；过渡版本 cloud 同发两键 + edge 双读 `payload.contactInfo ?? payload.groupChatCode`，edge/cloud 协调同波，确认运营机全升级后再删旧键——绝不硬切（防「静默漏贴」红线）。
- **邻接「群评」调度特性一并正名**为「带联系方式评论」：`groupComment*`→`contactComment*`、action `'group_comment'`→`'contact_comment'`、`group_comment_*` 列/表族、`hasGroupCode`→`hasContactInfo`、console「自动群评」列文案。
- **跨仓契约同波**：panel DTO 字段 / HTTP 路由 `/group-chat-info`→`/contact-info` / 错误码 `*_group_*`→`*_contact_*`，cloud + console 同一波上线（先 cloud、console 紧随），路由与错误码过渡期新旧双认，DTO 字段与 `version.ts` 指纹硬同波。
- **文档补缺**：`docs/protocol.md` 现根本未记录 `interaction.comment` 的注入字段，本次补记（新增，非 find/replace）。

**明确排除（绝不改）**：`group_label` / `GroupRoute` / `setGroupLabel`（按团队通知路由）、`chatType:'group'`（飞书会话类型）、facebook 那个语义相反的「contact info」校验器（它是**拒绝** AI 文案里的联系方式，与本次**注入**联系方式相反，不可合并、不可误杀）、`notification-contact-registry`（通知联系人名册）、历史 change slug / archive 目录 / 迁移文件名。

## Capabilities

### New Capabilities
<!-- 无。本 change 是既有能力的术语泛化 + 契约改名，不引入新能力。 -->

### Modified Capabilities
- `group-chat-injection`：owner spec，6 条需求全部把「群聊引流码 / group:on」正名为「联系方式 / --contact」；命令语法从 `group:on/off` opt-in 改为 `--contact` 干净切换。（capability 目录 id 保留为历史标识，只重写需求文案——见 design 决策）
- `console-write-operations`：账号「关联群聊信息」编辑需求、内容排期群评字段硬校验（一码一号）需求，正名为联系方式；DB 列 / 路由 / 错误码随之更新。
- `content-schedule`：「覆盖发帖、评论与群评」「定时自动群评经同一评论机器」两条需求正名为「带联系方式评论」。
- `curated-note-actions`：「定向评论两型——内容评论与带群评论共用撰写链」正名为「带联系方式评论」，错误码 `group_code_missing`→`contact_info_missing`。

## Impact

- **aidcp-cloud**：账号存储（列 + 方法 + 类型）、飞书命令解析与帮助/结果卡文案、评论调度 / 撰写 / 边侧步骤适配、`comment-task-runner` 的 `CommentTaskSteps` 接口、panel API（DTO / 路由 / reason / `version.ts` 指纹）、自动排期「群评」特性、精选内容 `withGroup` 云端接收端、协议 `protocol.ts` wire 字段、新增前向迁移文件、整套相关单测。
- **aidcp-edge**：`protocol.ts` wire 字段（与 cloud 逐字同源）、`browse-session` 评论注入的内部参数与双读兜底、probe 脚本文案。
- **aidcp-console**：账号表「群聊引流」列 → 「联系方式」、`PanelAccount` DTO 字段、账号页路由 / 请求体、错误码文案、内容排期页「自动群评」列与校验文案、精选内容页 `withGroup`、相关测试。
- **aidcp（控制仓）**：本 change 的 spec deltas（4 个能力）、`docs/protocol.md` 补记注入字段、真机验收 backlog 登记。
- **部署**：cloud（内部+DB，一波）→ cloud panel + console（强制同波）→ edge（wire 过渡与 cloud 协调）。dev 默认目标，走安全序列，绝不碰同机 isales。
- **风险面**：不在数据/语义，在跨仓/跨端契约的原子性（wire 字段、DTO、路由、reason、DB 列）——已用「保留旧名过渡 + 双读/双发 + 同波部署」收口。
