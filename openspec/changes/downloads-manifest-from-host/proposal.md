## Why

安装包的版本号被**写死在 console 源码里**（`src/config/downloads.ts` 的 `version` + 三个文件名），可它描述的其实是「**这台机器的 `/opt/aidcp/downloads/` 里放了哪个包**」——一个每台机器各不相同的部署状态。把部署状态写进源码，产生了一个无解的两难：

- master 停在 `0.3.18`（dev 有这个包）→ 部署 console 到 OL，会把线上下载页**回退**到 0.3.18，而 OL 上实际躺着 0.3.20。
- master 抬到 `0.3.20`（OL 有这个包）→ 部署 console 到 dev，下载页会给出**指向不存在文件**的死链（dev 的 downloads 目录里根本没有 0.3.20）。

两个方向都错，因为源码里的那个数字**无论填什么，对另一台机器都是谎话**。这也正是「发布分支的版本号 bump 该不该回流主干」永远吵不清的根源（`7a1b718` / `88ce4c8` / `e5a4d1d` 至今搁浅），并已在新的回流铁律里被迫开了一个「工件指针」例外——这个例外本身就是设计缺陷的影子。

顺带的既有伤害：改包必须改源码 + 重新构建部署 console，一步忘了就是死链或错版本；而下载页**没有任何机制能发现自己在撒谎**。

## What Changes

- **让每台机器自己说真话**：云端面板新增 `GET /api/downloads`，**现扫该机 downloads 目录**并按文件名解析出平台与版本，返回真实存在的安装包清单。页面从此**只可能提供确实存在的文件**——死链在构造上不可能。
- **console 源码里不再有版本号**：`downloads.ts` 的硬编码 `version` / `items` 删除，改为消费该 API。
- **拿不到清单就诚实说没有**：API 失败 / 目录为空 / 无可识别包 → 下载入口显示「暂无可用安装包」，**绝不回落到一个写死的版本号**（那正是今天这个 bug 的形态：宁缺毋假）。
- 目录路径可配（`AIDCP_DOWNLOADS_DIR`，默认 `/opt/aidcp/downloads`），`.bak-*` 等非发布文件一律忽略；同平台多版本共存时取**最高语义版本**。
- 随之而来的收益：**「版本号回流主干」这个问题从此不存在**——它不再是源码。发布新包 = 把包放到那台机器上，页面自动跟上，不需要改代码、不需要重新构建 console。

## Capabilities

### New Capabilities

### Modified Capabilities
- `console-panel-api`: 新增 downloads 清单端点（按机器现扫、诚实为空）。
- `edge-desktop-packaging`: 发版流程不再要求改 console 源码的版本号。

## Impact

- `aidcp-cloud`: `src/panel/panel-server.ts`（新端点）、新增 downloads 清单扫描模块。
- `aidcp-console`: `src/config/downloads.ts`（去硬编码）、`src/pages/AppShell.tsx`（改为取 API + 空态）。
- 部署：cloud + console 都要重新部署 dev 才生效。
- 发版流程：`scripts/release-desktop-macos` 里「改 console 源码版本号 + 重新构建部署 console」这一步可以删掉（本 change 只去掉必要性，脚本清理另计）。
