# curated-note-actions Delta

## ADDED Requirements

### Requirement: 行级动作 SHALL 按新类型约束可用性

精选行级动作 SHALL 按 `image_text|video|comment` 约束：参照洗稿仅对 `image_text` 行开放；`video` 与 `comment` 行的洗稿入口 MUST 置灰并禁止点击，后端直接调用也 MUST 拒绝。定向评论仅对源帖（`image_text|video`）开放；`comment` 行因不代表可打开的源帖目标 MUST 禁用并拒绝。所有动作仍 MUST 按行归属账号执行，保持账号隔离。

#### Scenario: 图文可洗稿

- **WHEN** 管理员对正文非空的 `image_text` 精选行触发参照洗稿
- **THEN** 端点可受理并进入既有发布链路

#### Scenario: 视频洗稿置灰并拒绝

- **WHEN** 管理员查看或直接调用 `video` 行的参照洗稿动作
- **THEN** 控制台按钮置灰不可点击；后端直接调用返回稳定拒绝原因，MUST NOT 进入发布链

#### Scenario: 评论行洗稿置灰并拒绝

- **WHEN** 管理员查看或直接调用 `comment` 行的参照洗稿动作
- **THEN** 控制台按钮置灰不可点击；后端直接调用返回稳定拒绝原因，MUST NOT 进入发布链

#### Scenario: 视频仍可作为定向评论目标

- **WHEN** 管理员对 `video` 精选源帖触发定向评论
- **THEN** 端点按源帖目标受理并沿既有定向评论链路搜索定位该笔记
