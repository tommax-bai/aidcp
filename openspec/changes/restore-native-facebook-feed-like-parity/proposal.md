## Why

Facebook Feed 点赞在 Native-only 切换后仍能解析到目标卡和按钮坐标，但初次提交被统一成 CDP 坐标点击；这没有保留旧 Feed 执行器对 React 帖级控件使用页内 DOM 点击的已验证行为，导致命令大量落入 `like_unconfirmed`。需要恢复精确目标、React 兼容提交和同卡后验，避免“找到按钮但实际未点赞”以及误点相邻卡。

## What Changes

- 为 Facebook Feed 点赞建立独立 Native 提交路径，在动作发生前重新按命令身份解析唯一目标卡。
- 仅接受与帖级评论控件同动作栏的唯一反应控件，排除反应计数、评论反应和相邻卡控件。
- 首段提交使用目标控件自身的 DOM `click()`；仅在首段打开目标反应选择器时，使用受限浮层坐标完成第二段“赞”提交。
- 将后验绑定到被作用的同一目标卡，并在卡消失、身份变化、控件未翻转或目标不唯一时返回诚实的未开始或不确定结果。
- 增加失败优先的路由特征测试和 Native 引擎路由约束测试；不改变 Cloud 概率、配额、协议和风控记账。

## Capabilities

### New Capabilities

<!-- No new capabilities. -->

### Modified Capabilities

- `facebook-note-scoped-targeting`: 明确既有精确卡、同卡验证、控件滚动和两段 Feed 点赞契约在 Native-only 路径中的执行与结果语义。

## Impact

- `aidcp-edge/native/page-engine/src/facebook-command-router.js`
- `aidcp-edge/native/page-engine/src/engine.rs`
- `aidcp-edge/test/native-page-engine/`
- Native command envelope and Cloud-facing result shapes remain unchanged.
- No Edge installer, deployment, or live-account verification is included.
