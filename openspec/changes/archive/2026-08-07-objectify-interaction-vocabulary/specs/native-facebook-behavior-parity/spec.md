## MODIFIED Requirements

### Requirement: Native-only Facebook preserves the established platform command boundary

The Facebook Native-only adapter SHALL implement only commands covered by the Facebook platform contract. Supported behavior SHALL include identity and page probes, Feed/Reels browse, search, note detail, exact-target like (`facebook.note.like` / `facebook.video.like`), Reel follow (`facebook.user.follow`), comment (`facebook.note.comment`), group join, and the existing Facebook publish atom subset. Facebook collect, comment-like, carousel browse, comment scroll, notifications, and author-profile browse MUST be refused before any page actuation: the platform-scoped rename makes all of them structurally xiaohongshu-only (`xiaohongshu.note.collect` / `xiaohongshu.comment.like` / `xiaohongshu.note.browse_images` / `xiaohongshu.note.scroll_comments` / `xiaohongshu.notification.*` / `xiaohongshu.profile.open`) so the platform-segment gate rejects them at the edge entrance before dispatch, and no platform-generic interaction command name remains. The hand-maintained Facebook unsupported-command set is retired with the last two shared names; platform nonsupport SHALL be derived from the name table plus the platform-segment gate, not from a second hand-copied list. A command name carrying another platform's segment MUST NOT create an implicit Facebook capability.

#### Scenario: Unsupported command does not touch the page

- **WHEN** a Facebook Native session receives `xiaohongshu.note.collect`, `xiaohongshu.comment.like`, `xiaohongshu.note.browse_images`, `xiaohongshu.note.scroll_comments`, a `xiaohongshu.notification.*` command, or `xiaohongshu.profile.open`
- **THEN** Edge refuses the command at the platform-segment gate at the edge entrance (`platform_mismatch`) — without router evaluation, navigation, scrolling, clicking, typing, or risk accounting

#### Scenario: Supported command stays Native-only

- **WHEN** a supported Facebook command is executed
- **THEN** the Rust Native Page Engine owns CDP inspection, actuation, and verification, and Edge MUST NOT invoke the retired TypeScript Facebook page executor or a JavaScript fallback process
