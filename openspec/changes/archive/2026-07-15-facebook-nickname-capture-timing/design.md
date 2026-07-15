# Design — facebook-nickname-capture-timing

## 决策：复用小红书那套时机机器，只在触发点按平台分叉读法

小红书的采集时机由云端 `NicknameEnricher` 拥有，是**平台无关的结构**，只被两道闸挡在 FB 之外：

1. 准入闸 `isCaptureEligible`（写死仅小红书）；
2. 触发后的读法（`self.profile.capture` → `profile_open{direct}` → 边缘**导航进本人主页**读 `profile.detail`）——这是小红书的读法。

时机部分（挂在 `page.cards.arrived{startupId}`、同代号只采一次、采空有界重试、~20s 超时、`browseSuspended` 让位）本就通用。**放开准入闸即让 FB 走同一套时机**；读法在边缘按平台分叉即可。

## 为什么不新造协议 / 不走 edge 自采

- 边缘 FB 会话**已经**处理 `profile.open{direct}`（`facebook-session.ts` 有 handler），也**已经**能上报 `profile.detail`（`reportProfileDetail`），`profile.open` 也**已在** edge 主动命令白名单里。链路齐全，缺的只是「读法」——把导航换成就地读。
- 采集完成判定 `onDetailArrived` 用 `detail.authorId === 连接 accountId` 判本人，race-free；FB 就地读回自己的数字 id，天然满足，**采集完成逻辑一字不改**。
- 若改走「edge 在首个 page.cards 自采 + 新上报通道」，会：把时机逻辑复制到边缘（与云端两套、易漂移）、新增协议消息（碰两份 `protocol.ts` 热点）、要么碰 `main.ts`。**违反「时机统一」与「不过度设计」**。故否决。

## 采集后的 `back` 对 FB 无害

采集完 `onDetailArrived` 发 `feed.entered{back_to_feed}` → 派发 `back` → FB `backToFeed()` 走**幂等 `ensureFeed`**（已在 feed 且无弹层则不导航）。就地读从未离开 feed，故 `back` = 空操作 + 重新播种游标（同 `startupId`，`armStartupCapture` 已消费、不重复武装）。**无整页重载**——这对 FB 的重载抖动敏感性很关键。

## 就地读的三种结果 → 诚实上报

`openDirectProfile`（direct 自采）改为调 `readFacebookIdentity(cdp, allowNavigate:false)`：

- **ok + 非空昵称**：上报 `profile.detail{authorId=就地读到的 id, nickname}` → 云端差异写库。
- **ok + 空昵称**：上报 `profile.detail{authorId=就地读到的 id, nickname 省略}` → 云端计一次采空、进有界重试、下个启动代号再试。
- **读失败**：上报 `profileFallback(命令携带的 authorId)`（空昵称）→ 同样计采空重试。

上报 `authorId` 用**就地读到的 id**（非命令携带值）→ 自校验：读到别的 id 则 `authorId≠accountId`、云端安全忽略（绝不把错 id 的名写进本账号）。

## 保留 hello 昵称

`main.ts` 的 hello 昵称路径不动：幂等、无害、幸运时更早写上；移除要碰正在被并发编辑的 `src/main.ts`。可靠且统一的时机由本 change 落到首个 feed 卡片，hello 降为机会主义早写。二者皆差异写库、无竞态。

## 不在本 change 范围

- FB 头像标签**多语言覆盖**（`AVATAR_ARIA_SUFFIX_RE` 仅中英文）——属「读法」健壮性、非「时机」；单独留待（可并进跨语言识别计划）。
- 冷待机唤醒是否重采：`startupId` 目前是进程级，冷待机唤醒（同进程）不换代号 → 与小红书**现状一致**（同不采）。本 change 只对齐 FB 到小红书现有时机，不改动 `startupId` 语义（改它才是过度设计）。
