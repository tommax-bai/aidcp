## Context

管理后台 `/persona` 页把空文本 `PUT /api/persona/:accountId` 解释为显式解绑，最终调用 Cloud `PersonaStore.clear(accountId)` 删除 `persona_config` 并在成功后清除内存镜像。首作新人资格独立持久化在 `first_post_onboarding`；其唯一账号键保证普通更新、重复绑定与解绑后重绑不会重复展示引导。

当前两个状态没有在后台清空动作中一起收口，因此管理员虽然看到账号已“未绑定”，旧首作行仍会阻止下一次建立人设返回 `firstPostOnboarding:true`。客户侧环境级人设 API要求非空人设，不存在清空入口；本变更只需修改后台现有单写路径。

## Goals / Non-Goals

**Goals:**

- 后台显式清空人设后，把账号恢复成“未绑定人设且未建立首作状态”的初始化状态。
- 两张状态表的删除要么全部成功，要么全部不变；API 不返回部分成功。
- 数据库成功后再清内存人设镜像，保持热路径与持久态一致。
- 下一次成功建立人设复用现有 `armFirstBind()` 原子建行与 Edge 引导回执，不新建第二套新人流程。

**Non-Goals:**

- 不让普通人设编辑、重复持久化、客户端解绑或自动补齐隐式重置首作状态。
- 不清理发布记录、精选内容、浏览计数、风控状态、账号主数据或平台侧内容。
- 不新增 Console 按钮、API、数据库表或 Edge 安装包。

## Decisions

### 1. 在后台人设单写存储内用单条 PostgreSQL 语句原子删除两类状态

`PersonaStore.clear(accountId)` 使用一个 data-modifying CTE，同时删除目标账号的 `persona_config` 与 `first_post_onboarding`，并在语句成功返回后才删除内存镜像。PostgreSQL 单条语句天然原子；任一表写失败时整个语句回滚，镜像也保持不变。

备选方案是在 `PersonaFacade` 中先调用 `PersonaStore.clear()`、再调用 `FirstPostOnboardingStore.reset()`。该方案跨两个 pool 调用，第二步失败会留下“已解绑但首作未复位”的部分状态，除非引入共享事务接口，复杂度更高，因此否决。

### 2. 仅复用后台空文本解绑入口，不扩大客户侧 API 语义

现有 Console 已允许清空编辑器并保存，Cloud panel route 也只有在 JWT 鉴权后调用同一 facade。客户侧 `/capi/environments/:envKey/persona` 仍要求非空 `soulYaml`，旧 Edge `persona.persist` 也只负责建立/更新人设。因此不新增请求字段或公开 reset endpoint，避免客户误触生命周期重置。

### 3. 重置只恢复首作资格，不伪造首作已触发

后台清空成功后不提前插入 `first_post_onboarding`。账号保持无行；只有下一次人设真实持久化成功且首作链路可用时，现有 `INSERT ... ON CONFLICT DO NOTHING` 才建立 `searching` 状态并返回 `firstPostOnboarding:true`。这样“已重置”与“已触发引导”保持分离。

## Risks / Trade-offs

- [首作状态表不可用时后台清空会失败] → 保持原人设与镜像不变并返回诚实失败，避免只解绑未复位；修复数据库后可重试。
- [管理员误清空会让账号再次获得首作资格] → 该入口本来就是显式清空并保存的管理员操作，继续使用现有确认和 JWT 边界，不新增隐式触发。
- [账号正在运行时被清空] → 继续复用既有 `onChanged` 推送与无人设入口闸；本变更不扩大运行中解绑语义。

## Migration Plan

1. 发布 Cloud 代码，无 schema migration；现有 `first_post_onboarding` 表继续使用。
2. 用单元与验收测试覆盖双删除、失败不清镜像、普通更新不复位和重新建立人设再触发。
3. 从干净 `master` 部署 dev，核对 Cloud、监听、健康与 PostgreSQL；不对真实账号执行破坏性清空验收。
4. 回滚时恢复旧 `PersonaStore.clear()`；已经由管理员明确清空的账号保持重置后的真实状态，不自动重建旧首作行。

## Open Questions

无。
