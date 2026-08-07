## MODIFIED Requirements

### Requirement: 续场重开会话后必须主动重新驱动边端浏览闭环

浏览闭环的实际推进由**边端结构化上报**驱动；会话结束后边端浏览循环停止、不再上报。因此云端**续场重开会话**后 MUST 主动下发一条引导浏览命令，重新驱动边端浏览循环重报卡片、使决策环得以继续；MUST NOT 仅在云端激活新会话而不向边端发任何命令（否则边端无输入、循环空转）。所有主动重驱 MUST 复用既有滚动通道（动作 `scroll` → 消息 `{platform}.feed.scroll`；Facebook 会话钉住 Reels 面时为 `facebook.reels.scroll`——本次要恢复的浏览面由命令名的面段承载，不再有 `targetSurface` 载荷字段），使用统一的 `reason:'resume_redrive'`。系统 MUST NOT 为此新增协议消息类型；两份 TypeScript 协议、命令映射、Native 严格解码与协议文档 MUST 保持一致。

#### Scenario: 续场后云端主动下发统一重驱命令

- **WHEN** 自动续场经启动闸重开了一场新会话（`feed.entered{trigger:'session_start'}`）
- **THEN** 云端按该场钉住的目标浏览面下发一次 `{platform}.feed.scroll{reason:'resume_redrive'}`（Facebook 会话钉住 Reels 面时为 `facebook.reels.scroll{reason:'resume_redrive'}`）
- **AND** 边端据此重新驱动浏览循环并重报 `page.cards`，决策环继续

#### Scenario: 续场引导不新增协议消息

- **WHEN** 实现续场后的边端重驱
- **THEN** 系统复用既有滚动通道（动作 `scroll` → `{platform}.feed.scroll` / `facebook.reels.scroll`）与边端主动命令白名单，MUST NOT 新增协议消息类型
- **AND** 重驱要恢复的浏览面由命令名的面段在 Cloud、Edge、Native 与协议文档中保持一致

#### Scenario: 非 Facebook 重驱保持兼容

- **WHEN** 非 Facebook 平台收到 `xiaohongshu.feed.scroll{reason:'resume_redrive'}`
- **THEN** Edge 按既有普通滚动语义执行，不因 `resume_redrive` reason 改变滚动行为

