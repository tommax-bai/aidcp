## Why

dev 在 2026-08-04 切到三服务后，管理后台的 `/api` 由派生的 `aidcp-api` 进程提供。该进程的入口是**手写**的（组装根从不自动同步），装配面板能力清单时漏了一批：单体那份挂 49 项，手写这份只挂 29 项。

面板对缺失能力的处理是逐路由如实回 503（`*_unavailable`），不是假装有数据——这一半是对的。但运营侧的表现是整页「加载失败」，且**没有任何东西会报警**：进程健康、端口在听、大多数路由 200，只有具体那几页打不开。2026-08-05 dev 实测（带真 token 逐条打）确认下列七处后台功能全挂：

| 后台位置 | 端点 | 现状 |
| --- | --- | --- |
| 设置页 · 平台配置 | `GET/PUT /api/config/model`、`PUT /api/config/credential` | `model_config_unavailable` |
| 设置页 · 视频号权限 | `GET /api/config/interaction-permissions` | `interaction_permissions_unavailable` |
| 角色页 · 角色与提示词 | `GET /api/roles`、`PUT /api/roles/{id}/config`、`GET /api/roles/{id}/prompt` | `role_config_unavailable` / `role_prompt_preview_unavailable` |
| 角色页 · 分类默认 | `GET /api/categories`、`PUT /api/categories/{id}/config` | `category_config_unavailable` |
| 用量成本页 | `GET /api/llm-usage`、`POST /api/llm-usage/prices/refresh` | `token_usage_unavailable` |
| 精选库页 | `GET /api/curated/*`、行级动作 | `curated_unavailable` |
| 配额页 · 热帖引流 | `GET/PUT /api/hot-lead-config` | `hot_lead_config_unavailable` |
| FB 群策略 | `GET/PUT /api/facebook/groups/comment-policy` | `facebook_group_comment_policy_unavailable` |
| 验证码协助页 | `GET/POST /api/captcha-assist/*` | `captcha_assist_unavailable` |

还有两项不走路由、因而**连 503 都不会给**的静默能力缺失：待审稿件的正文编辑与授权前版本预检（`publishDraft` / `preflightApprovePublish`），以及客户离场卡的产出回调（`onClientOffboardCreated`）。这类缺席比 503 更难发现——调用点写的是可选依赖，没有就什么都不发生。

漏接的**大部分并不需要新设计**：单体组装根里已经写好了 `mode === 'api'` 分支（待审稿件编辑、发布预览通知），或者依赖本来就全是接口域属主（平台配置、角色、分类、热帖引流、FB 群评论策略、视频号权限）。它们是纯粹的搬运遗漏。真正需要开跨进程通道的只有五族：模型探活、用量成本、精选库、FB 发帖图片（内容域），验证码协助与发布下发前置（自动化域）。

## What Changes

- **接口服务补齐本进程属主的面板能力**：平台配置视图与凭据写、角色配置、分类默认、角色提示词预览的接口域部分、热帖引流、FB 群评论策略、视频号权限只读总览、待审稿件编辑与发布预览通知。
- **开跨进程通道**：内容侧新增模型探活、用量成本与账单价刷新、精选库读与行级动作、FB 发帖图片四族窄口；自动化侧新增验证码协助、授权前置与下发在途两族窄口。各按既有「服务端注册 + 类型化客户端 + 路径常量」三件套形态落地。
- **写路径不因探活缺席而降级**：模型 / 角色 / 分类的写仍 MUST 先探活，探活通道不可用时诚实拒写，MUST NOT 跳过探活直接落库。
- **新增装配对账门**：把「面板声明的可选能力」与「本进程实际装上的」做差集，差集内每一项 MUST 有具名理由，否则测试红。防的是本次这一类——手写组装根静默少装，且没有任何机械手段会提醒。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `console-panel-api`: 新增「面板能力装配完备性必须可对账」要求——服务面板的进程 MUST 装满能力清单，未装项 MUST 逐条具名并写明理由与用户可见后果，MUST NOT 靠「逐路由 503」当作缺席的默认答案。

## Impact

- `aidcp-api/src/server.ts`（手写组装根，主改动面）+ 本仓属主存储的构造与外观装配。
- `aidcp-content` / `aidcp-automation` 的手写组装根：注册新增窄口路由。
- `aidcp-cloud`：新增跨进程客户端与路径常量（派生源，经 `scripts/sync-split-repos` 同步进 `aidcp-transport` 与派生仓）。
- 不改协议 v2、不改数据库形状、不改 console 前端（前端调用面不变，只是后端从 503 变成真答）。
- 不改单体在 OL 上的行为：新增的都是 api 模式下的装配与新窄口，单体路径原样。
