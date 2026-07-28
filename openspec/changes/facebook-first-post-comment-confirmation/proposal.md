## Why

真机实证（2026-07-28，本地 AdsPower 账号 Hi He / `61591934100810`，三轮加群+首帖评论）证明：**「加群后无法在首个内容评论」不是评论没发出去，而是评论发出去了、系统结构上确认不了**。

1. **自动规则批次被写死跳过校验**。`aidcp-cloud/src/server.ts:6512` 在 `triggerFacebookRuleJoinContact`（`joinFirst` + `injectContact` 的自动流程）里无条件传 `fastReturnToFeed: true`。边端据此在 Enter 后固定 sleep 500ms → 导航回首页 → 直接回报 `verification_ambiguous`，**从不查看评论是否上墙**。现行 spec `facebook-scheduled-comment`「Facebook manual comment fast return」写明该模式 **When and only when** 手动 `--feed` 开关存在时才允许；自动路径带上它属于实现违规。实测日志：2026-07-28 04:53:18.660 下发 → 04:53:27.154 回 `verification_ambiguous`，间隔 8.49s < 边端确认轮询的 9s 下限，只可能走快返分支。

2. **即便进了确认轮询，判据也认不出真实页面的服务器 ID**。`native/page-engine/src/facebook-router/50-comment.js:78`（及死代码分支 `90-dispatch.js:153`、`src/facebook/comment-executor.ts:319`）要求 `comment_id` 以 `Y29tbWVudD`（base64 `comment:` 前缀）开头。真机实测该版式给出的服务器 ID 是**纯数字**：Enter 后 73ms 出现客户端占位 `client:46fd0dfd-…`，**4.29s 换成服务器 ID `1531497545657803`** 并出现点赞控件；「回复」控件在 3 分钟监控窗口内始终未出现，故 like+reply 兜底判据同样不成立。结果：确认窗口内两条判据全落空 → 必然 `verification_ambiguous`。

评论确实上墙的独立证据：Facebook 自身活动日志显示账号在 11:53（越南时间，= 系统 12:53）对 Liễu Vũ 的帖子发过评论；本次三轮真机测试的两条评论刷新后仍在墙上（`comment_id` = `943618058764369` / `1712490840033638`）。

后果不只是"看着像失败"：`comment-scheduler.ts` 对 `verification_ambiguous` 会**打去重标记**（防重复真发的白名单），于是目标帖被永久烧掉、覆盖冷却不落、当日配额不计——同一个群的首帖此后只会得到 `all_deduped`。这正是"持续无法评论"而非"偶发失败"的机械原因。

## What Changes

- Facebook 评论的服务器确认判据按**服务器已签发**的语义判定，而不是按单一编码形态：接受平台在该评论节点上给出的服务器 ID（base64 `comment:` 形态与纯数字形态皆可），继续拒绝客户端占位 ID（`client:` 前缀）与乐观渲染。待审徽章否决、拒绝态、控件计数不可作判据等既有红线一律不动。
- 自动化路径（排期 / 规则模式 / 热线索等非手动触发）MUST NOT 携带快速返回开关；快返仍只属手动 `--feed`。自动路径保留完整的就地确认生命周期（confirmed / rejected / pending / ambiguous）。

## Capabilities

### New Capabilities

_None._

### Modified Capabilities

- `facebook-comment-verification`：明确服务器 ID 的判定语义与已知的两种真机形态。
- `facebook-scheduled-comment`：明确快返开关只由手动 `--feed` 携带，自动触发路径不得传入。

## Impact

- Cloud：`src/server.ts` 规则模式加群+联系评论触发点去掉 `fastReturnToFeed: true`。
- Edge：native page engine 的评论确认判据（`facebook-router/50-comment.js`、`90-dispatch.js`）与遗留 TS 判据常量对齐；**需重新编译 native 引擎并重新打包桌面客户端后才在运营机生效**。
- 无协议消息、无数据库迁移、无 Console 改动。
