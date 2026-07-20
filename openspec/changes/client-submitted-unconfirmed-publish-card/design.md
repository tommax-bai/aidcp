## Context

Cloud 与 Edge 已通过既有 `publish.state = submitted` 表达“提交动作已被平台页面接受，但尚未取得公开 `postId/postUrl`”。Electron 的 `publishView` 也会为该状态生成一条活动记录，但随后复用终态回退逻辑，卡片本体继续显示旧 `lastPublish` 或空态，因此最新动作只在活动流中短暂可见。

本变更只调整 Edge Electron 的只读投影，不改变发布执行、状态落库、协议枚举或平台确认规则。

## Goals / Non-Goals

**Goals:**

- 让 `submitted` 成为发布卡可见的独立状态，并优先显示本次稿件。
- 用“已提交、公开结果确认中”表达不确定性，禁止冒充 `published`。
- 保留既有活动流记录、旧 `lastPublish` 数据和收到 `published` 后的转换行为。

**Non-Goals:**

- 不新增即时发布的 postId/postUrl 对账机制。
- 不改变 cloud hello 快照对 submitted 的恢复范围。
- 不构建或发布 Electron 安装包。

## Decisions

1. **在 `publishView` 中先于历史态回退处理 `submitted`。** 返回独立 `mode: 'submitted'`，使用本次 `publish.title/code/at`，避免旧历史覆盖。相比改写 `lastPublish`，独立模式不会把未确认提交污染成已发布历史。
2. **提交确认态保持展开。** `publishDock` 对 `submitted` 与进行中 `flow` 一样返回展开，确保最新且仍未收敛的状态不会藏在旧历史薄条后面。
3. **第四节点保持 calm current，而不是 done。** 前三步已经完成，第四步表示公开结果仍待确认；文案使用“已提交，平台确认中”和“公开结果确认后会更新”，不出现“已发布”。
4. **继续生成 submitted 活动流记录。** 卡片承载当前状态，活动流保留发生过的提交事实；既有按环境签名去重不变。

## Risks / Trade-offs

- [客户端重启后 cloud 未重放 submitted，卡片仍可能回到旧历史] → 本次明确保持范围为现有事件投影；后续如需跨重启恢复，应单独扩展 cloud 快照并按最新记录排序。
- [“平台确认中”可能长期停留] → 这是数据库真实状态的直接呈现；在没有可靠对账前不设置虚假自动完成时间。
- [新增 mode 影响收展或样式] → 复用现有蓝色封面与 calm 当前节点，只对纯函数和 dock 分支做窄改，并以聚焦测试锁定。
