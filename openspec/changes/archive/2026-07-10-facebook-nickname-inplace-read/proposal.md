## Why

Facebook 账号在后台**只显示数字 id、读不到昵称**（真机实测：dev 库 `accounts.nickname` 对多个 FB 账号为空 → 控制台按 `nickname→label→accountId` 回退到那串数字 id）。根因在边缘 Facebook 身份读取（`aidcp-edge/src/facebook/identity.ts` 的 `readFacebookIdentity`）：

- **主取名来源是"跳转到 `/me` 个人主页再读一遍"**——这步既**突兀**（把账号的活标签页整页导航走、读完不回原页），又**不可靠**：真机日志出现 `/me nickname probe failed: CDP 命令超时: Page.navigate`（离开页触发 `beforeunload` 类弹窗、而边缘全代码无 JS 弹窗处理器 → `Page.navigate` 命令挂到 10s CDP 命令级超时），名字读空；**还会读错**——一次把该账号关联的**主页名**（`việc làm hà nam`）当成了本人昵称。
- **降级链会捞到垃圾**：当前 `cleanFacebookDisplayName` 只挡纯 `Facebook`/几个通用词，`(4) Facebook`（浏览器标签栏带未读数的标题）能穿过被当昵称；仅因"库里已有昵称不覆盖"侥幸没落库，换成空昵称新号就会把垃圾名焊死。

真机 CDP 实测证明**昵称本就在首页 DOM 里、零交互可读**：顶栏头像是一个锚点，`href` 精确等于本账号数字 id（`profile.php?id=<accountId>`）、`aria-label` 为「`<本人昵称>的头像`」（实测 `Tianxing Bai的头像`）。该锚点属 Facebook 持久外壳，**任意页面都在**（在群页面上同样读到），无需进首页、无需展开菜单、无需导航。

## What Changes

- **去掉 `/me` 跳转取名机制**：`readFacebookIdentity` 不再 `Page.navigate` 到 `/me`；那步的 10s 卡死与"读到关联主页名"两类问题一并消除。
- **改为就地、id 锚定读昵称**：从当前页扫到的本人 profile 锚点（`href` 的数字 id === 握手已确立的账号 id，或 `/me` 自链）里，取 `aria-label` 去掉「…的头像 / 's profile picture」这类头像后缀 → 本人昵称。id 锚定 ⇒ 自校验，绝不把别人/别页的名字写成自己。
- **页面标题类信号（title/og:title/h1）仅在"当前页就是本人主页"时才作为昵称来源**：在首页/信息流/群页面等**非本人主页**上，这些一律是页面标题而非本人名字，MUST NOT 用作昵称（这是 `(4) Facebook`、群名等垃圾的来源）。
- **收紧昵称清洗**：`cleanFacebookDisplayName` 剥离前导未读数 `(N) ` 并把 `(N) Facebook`、账号菜单/「你的个人主页」等通用标签一律判空——**宁可留空，绝不写垃圾名**（自愈不自残红线）。
- **就地有界重试 + 诚实留空**：昵称随顶栏异步渲染，按次数上界就地轮询等它出现（替代原 `/me` 兜底）；读不到就诚实留空、不阻断身份确立、不再跳转、不再拿标签标题兜底。库内为空的账号后续每次重连仍会再试一次（沿用云端"仅昵称为空时落库"），一次读到即固化。

## Capabilities

### New Capabilities
- `facebook-identity`: Facebook 登录账号身份与昵称的边缘读取契约——数字 id 由 cookie/profile 锚定确立（既有行为），昵称改为**就地、id 锚定**从头像锚点 `aria-label` 读取、绝不导航 `/me`、非本人主页页不取页面标题、清洗拒绝标签标题类垃圾、读不到诚实留空。

## Impact

- **仅边缘**（`aidcp-edge`）：只改 `src/facebook/identity.ts`（扫描 JS 增采 profile 锚点 `aria-label`、`deriveFacebookIdentity` 按 id 锚定选名 + 非本人主页页不用页面标题、`cleanFacebookDisplayName` 收紧、`readFacebookIdentity` 删 `/me` 跳转改就地有界重试）。**不动协议、不动云端、不动数据库**——云端"握手 hello 昵称仅在库内为空时落库"（`connection-runtime.ts`）已在 dev 生效，昵称一旦就地读到即经既有 hello 通道落库。
- **不改身份 id 派生**：数字 id 的 cookie/profile 锚定逻辑逐字不变（真机 `source=facebook-cookie` 路径不受影响）；本 change 只改**昵称**这一路 best-effort 来源。
- **红线**：找不到昵称报诚实空（不猜、不回落 default、不写标签标题），符合"MUST NOT 静默假成功"。
- **兼容边界**：id 锚定依赖头像锚点 `href` 为 `profile.php?id=` 或 `/me`；采用 vanity 用户名头像链接的账号本轮仍可能读空（诚实留空、无回归），列为已知限制、后续可扩。
- **真机验收**：dev 部署后用现有 FB 测试号复验昵称能稳定就地读到、垃圾名不再落库；登记真机 backlog。
