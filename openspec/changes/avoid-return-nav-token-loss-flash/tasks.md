## 1. aidcp-edge — 根因·返回导航修复

- [ ] 1.1 `src/browse/browse-session.ts` `navigateBack`（约 1364-1396）：在 `safeCloseModal()` 之前先抓一次 `modalWasOpen = await this.deps.modalCtrl.isModalOpen()`
- [ ] 1.2 关浮层 + `humanPause` 后重算 `onList`（feed 用 `EXPLORE_FEED_RE`、search 用 `/\/search_result/`），用三分支替换现有 `onProfile` 单条判据：已在列表→不后退不重载；不在列表+有浮层→`history.back()`（保滚动位）；不在列表+无浮层→直接 `Page.navigate` 回来源列表（feed→`exploreUrl`，search→搜索结果）
- [ ] 1.3 既有健康校验兜底（约 1386-1393）判据改用重算的 `onList` 后原样保留当安全网；`back ok:true` 回执与 `reportVisibleCards` 契约不变
- [ ] 1.4 复核不引入新依赖 / import，全用现成 `modalCtrl` / `exploreUrl` / 常量

## 2. aidcp-edge — 纵深防御·低置信 unknown 上报确认闸

- [ ] 2.1 `src/main.ts` `watcherSupervisor` overlay 上报分支（约 412-445）：`to==='unknown'` 时不立即发 `risk.captcha_detected`，改延后约 2×pollMs 后复核 `overlayMonitor.state` 仍为 `unknown` 才发
- [ ] 2.2 `captcha` / `login` 分支保持即时 fail-CLOSED，MUST NOT 经确认闸延后
- [ ] 2.3 补 `detected`/`cleared` 配对位：仅当真发过 `detected` 才在自愈时发 `cleared`（现役 `cleared` 逻辑 `main.ts:433-441` 复用、不新写），被抑制的瞬时 `unknown` 消失不发孤儿 `cleared`、不遗留已发未清的 `detected`
- [ ] 2.4 本地停手闸（`waitWhileBlocked` 读 `.state`、`isBlockingKind` 含 `unknown`）不动——瞬时 `unknown` 期间仍本地短暂停手、自愈即恢复

## 3. aidcp-edge — 测试

- [ ] 3.1 事故回归单测：看笔记→开通知→返回，边缘直接 `Page.navigate` 回 feed（不 `history.back`）、不经/不闪 300031、不发 `risk.captcha_detected`、账号维持 `normal`
- [ ] 3.2 单测：搜索来源无浮层返回回到搜索结果；有浮层返回仍走 `history.back`（保滚动位、不重载）；仍落坏页时兜底 `Page.navigate` 并上报 `page.cards`（不静默死锁）
- [ ] 3.3 overlay 上报单测：单轮瞬时 `unknown` 被抑制不上报、账号不迁移；持续 `unknown` 确认后照报一次；`captcha`/`login` 即时不被延后；被抑制的瞬时遮罩消失不发孤儿 `cleared`
- [ ] 3.4 回归纪律：`npm run test:acceptance`（AC-PROTO 消息数仍 44、AC-RISK 全绿）→ `npm test` → `npm run typecheck`

## 4. aidcp-cloud — 无代码改动（显式记录）

- [ ] 4.1 显式确认云端零改动：`kind→signal→state` 映射、传输层暂停 / 恢复、告警语义不变；两份 `protocol.ts`、`docs/protocol.md`、`command-bridge`、主动命令白名单均不动

## 5. aidcp（控制仓）— 校验 · 真机验收 · 归档

- [ ] 5.1 `openspec validate avoid-return-nav-token-loss-flash --strict`
- [ ] 5.2 真机验收（gated，真机分身、勿本地起 cloud）：跑「开笔记→开通知→返回」确认无 300031 闪现、地址栏直接回 `/explore`、云端收不到 `captcha_detected`、账号维持 `normal`
- [ ] 5.3 反向对照：人为造一堵**持续**未知遮罩确认经确认延迟后仍照常上报并暂停；真滑块确认即时暂停 + `restricted`（证明真阻断未被弱化）
- [ ] 5.4 回填 tasks 标 `[x]`（带 commit-sha / 偏离说明）→ 打包边缘部署 → `/opsx:archive`
