# facebook-nickname-capture-timing — Facebook 昵称采集时机对齐小红书（首个 feed 卡片触发）

## Why

Facebook 账号后台常常只显示数字 id、启动后不更新真实昵称。根因是**时机**：FB 的昵称只搭「启动握手 hello」这一趟车，而这趟车很脆——

- 握手时刻是贴上页面**立刻**读顶栏头像（AdsPower 首读 `allowNavigate=false`），顶栏常在 3s 内还没水合完 → 读空；
- 首启若走「等登录门」，登录成功后云端握手决策**不带昵称**（`decideHandshakeIdentity` 只回 id+source），启动首读结果被丢弃 → 永远不带昵称；
- 头像标签识别只覆盖中英文，别的语种读空。

而 FB **会话内不再补读昵称**：补采角色 `NicknameEnricher` 的准入闸写死只放小红书（`role-dispatcher.ts` `isCaptureEligible`），FB 零扰动。于是启动那一下没读到，整段会话都不会有，后台一直只剩数字 id。

小红书**早已有一套设计过的、稳的时机**：每个完整浏览器启动代号（`startupId`）下的**首批 `page.cards` 到达**时武装一次采集，同代号只采一次、采空有界重试、~20s 超时兜底（spec `account-identity-resolution` 已定义）。这个时机天生比「握手那一瞬间」可靠——feed 起来时顶栏早已水合。

**用户定案：时机统一到小红书这套；获取方式各平台保留自己的（FB 就地读、XHS 进主页读），方式不统一、不新造抽象。**

## What Changes

把「首个 feed 卡片触发一次昵称采集」这套现成的时机机器**放开给 Facebook**，触发那一刻按平台走各自的读法：

- **cloud**：`NicknameEnricher` 的准入闸 `isCaptureEligible` 从「仅小红书」放宽到「小红书 + Facebook」。FB 连接也在「首批 `page.cards{startupId}`」这同一个点被武装、去重、有界重试、超时兜底——**与小红书逐字同一套时机**。
- **edge**：FB 对云端下发的本人昵称采集命令（`profile.open{direct}`）**改为就地读取**（`readFacebookIdentity`，不导航），把就地读到的 id + 昵称按既有 `profile.detail` 上报。当前该命令的实现是**导航到 `profile.php?id=`**——既与 `facebook-identity`「取昵称绝不导航」的既有契约相悖（潜在违规、目前因未被触发而蛰伏），又会在采集后触发一次多余的整页重载。改为就地读后：无导航、无重载，采集完的 `back` 经幂等 `ensureFeed` 变成空操作。

**复用既有链路、零协议改动**：`profile.open{direct}` 命令、`profile.detail` 上报、采集完 `feed.entered{back_to_feed}` → `back` 全部沿用，采集完成判定（`onDetailArrived`：`detail.authorId === 连接 accountId` 才是本人）对 FB 天然成立（FB 就地读回自己的数字 id）。不新增消息类型、不动 `command-bridge` 动作映射、不动 edge 主动命令白名单、**不碰 `src/main.ts`**。

**hello 昵称保留不动**（`main.ts` 那条读到就带的路径）：它幂等、无害、能在幸运时更早写上；且移除它要动正在被并发编辑的 `src/main.ts`。可靠且统一的采集时机由本 change 落到「首个 feed 卡片」，hello 只作机会主义的早写，不再是唯一依赖。

**顺带白捡的修复**（换时机的自然结果，非额外做事）：启动 3s 时机赛跑、等登录门丢昵称——两者都不再是采集的依赖路径，被绕过。

## Impact

- Specs：
  - `account-identity-resolution` — MODIFIED「昵称采集只在完整浏览器启动后的首个 feed 卡片触发」：从「For XHS accounts」放宽到 XHS + Facebook，明确**时机统一、读法按平台分叉**。
  - `facebook-identity` — ADDED「Facebook 启动期本人昵称采集经就地读取、由首个 feed 卡片触发」：云端触发的本人采集命令 FB 侧 MUST 就地读、MUST NOT 导航。
- Code：
  - cloud `src/orchestrator/role-dispatcher.ts`（`isCaptureEligible` 放宽）。
  - edge `src/facebook/facebook-session.ts`（`openDirectProfile` 改就地读）。
- 不改协议、不改风控/配额/节奏；`profile.open{direct}` 自采集不触风控/预算/节奏（沿用既有约束）。
- 真机验收：FB 号（尤其导入号 / 换语言号）启动后昵称随首批 feed 自动写库。
