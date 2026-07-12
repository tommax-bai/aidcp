## MODIFIED Requirements

### Requirement: 人设写入经 soul 加载器校验，非法人设诚实拒绝绝不静默接受

写入某账号人设时，系统 MUST 用 soul 加载器（`loadSoulFromValue`）做保存前校验，仅在校验通过后写库。校验失败 MUST 拒绝写入、返回诚实原因（`persona_invalid`），MUST NOT 把非法人设落库、MUST NOT 刷新内存镜像、MUST NOT 返回成功。**空人设保存 MUST 被解释为显式解绑**：系统 SHALL 清除该账号的人设绑定，使该账号后续解析为「无人设」（null）并被既有浏览 / 发布 / 评论入口闸诚实拒绝，MUST NOT 回落任何默认人设，MUST NOT 保留一个空白但看似已绑定的人设行。

#### Scenario: 非法 YAML 被诚实拒绝

- **WHEN** 面板提交无法解析 / 缺必要字段的人设内容
- **THEN** 返回 `persona_invalid` 与诚实提示，库与镜像均不变

#### Scenario: 空人设保存解绑账号

- **WHEN** 面板或 API 直连提交空 / 全空白人设
- **THEN** 系统清除该账号的人设绑定，返回写后真态 `source=none`，该账号后续任务被未绑人设入口闸拒绝，MUST NOT 回落默认人设

### Requirement: 后台账号人设页受 JWT 守护且写非乐观

账号人设接口（`GET /api/persona`、`GET /api/persona/:accountId`、`PUT /api/persona/:accountId`）MUST 与其它 `/api/*` 一样受 JWT 守护。管理后台 SHALL 提供人设页（`/persona` 路由 + 导航）：列出账号、按账号编辑其人设并保存，回显当前生效值与来源——来源为**已绑定（override）/ 未绑定（none）**两态，**不存在「回落默认」态**；未绑定账号 MUST 以醒目标注提示（该账号会被拒绝运行）。前端 MUST 允许操作员清空编辑器并保存为解绑，保存成功后以服务端返回真态显示「未绑定」；前端 MAY 对非空内容做格式提示，但 MUST NOT 用必填校验阻止显式解绑。写操作 MUST 非乐观——返回服务端写后真态（含生效人设 / 来源 + `updatedBy` + `updatedAt`），并用诚实文案（已保存 / 已解绑 / 人设格式无效无法保存），MUST NOT 返回乐观假态。

#### Scenario: 未鉴权被拒

- **WHEN** 未带有效 JWT 请求任一 `/api/persona*`
- **THEN** 返回 401，不读不写

#### Scenario: 写后回真态含审计字段

- **WHEN** 面板成功保存某账号人设
- **THEN** 响应含服务端写后生效人设与 `updatedBy` / `updatedAt`，前端以真态刷新（非乐观）

#### Scenario: 未绑定账号在列表醒目标注

- **WHEN** 人设页列出一个无人设行的账号
- **THEN** 该行来源显示「未绑定」红标（而非「回落默认」），提示其任务会被拒绝运行

#### Scenario: 清空编辑器保存为未绑定

- **WHEN** 操作员在人设页把某账号编辑器内容清空并保存
- **THEN** 后台调用写接口完成解绑，页面刷新为「未绑定」状态，MUST NOT 在前端提示必填并阻止保存
