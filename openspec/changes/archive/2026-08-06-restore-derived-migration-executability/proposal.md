## Why

拆仓后**没有任何一个在跑的服务能执行数据库迁移**，因此**新环境无法从零建库**。

两个独立缺陷叠加：① 三个派生仓的迁移 CLI 引用了一个在派生仓里不存在的模块，全部起不来 —— 今天唯一能跑迁移的是按 §8.0 **永不部署**的 `aidcp-cloud`；② 13 条迁移没有属主归属，被计入全部三个属主并复制进三仓，其中一条在任何单一属主库里都不可能跑通。

这不是理论风险，是 2026-08-05 空库实跑的结果（content 1/20、automation 13/57、api 20/70 后全线停止）。既有环境感觉不到，只因为它们的库早就建好了。

它还挡着两件已排期的事：schema 契约门默认转 `enforce`（门一拦、新环境又建不出库 = 把自己锁在门外）与删除过渡期自建旋钮。

## What Changes

- **修复派生仓迁移 CLI**：三仓 `scripts/migrate.ts` 对 kernel 的两处相对引用改为包引用（`aidcp-kernel/...`）。
- **把 `scripts/` 纳入拆仓同步覆盖**：`scripts/sync-split-repos` 现覆盖 `src/` 与 `test/`、对 `migrations/` 只报不改，**完全不覆盖 `scripts/`** —— 该文件自拆仓当日手工搬过去后即无人管，这是根因而非表象。能修它的说明符改写器早已存在，只是从未作用到该目录。
- **属主归属改为显式声明**：新增迁移头字段声明该迁移属于哪个属主库。**BREAKING（对迁移文件格式）**：残留推断（「无对象声明 ⇒ 计入全部属主」）MUST 被显式声明取代；缺声明且无法由对象声明定位属主的迁移 MUST 判失败，MUST NOT 静默计入全部属主。
- **拆分真跨属主的那条迁移**：`0030_panel_hardening_indexes` 在两个属主的表上各建索引，按属主拆成两条。
- **新增静态闸**：断言每条迁移在它被分配到的每个属主库里都可执行 —— 判据是「它触及的每一张表，都由同样在该库运行的迁移创建」。这条闸是本 change 唯一能防止同类缺陷复发的东西。
- **不做**：不动既有账本行、不动已应用迁移的校验和语义、不碰 dev/ol 共库。

## Capabilities

### New Capabilities

- `derived-migration-executability`: 迁移在派生（多仓多库）形态下的可执行性 —— 属主归属的显式声明、每属主库的可执行性判据、派生仓迁移 CLI 与其同步纪律。

### Modified Capabilities

（无。姊妹 change `cloud-schema-migration-executor` 尚未归档，其 `cloud-schema-migration` 能力仍是 delta；本 change 不改它已声明的任何 requirement，只补它成文时尚不存在的派生形态约束。）

## Impact

- **代码**：`aidcp-api` / `aidcp-automation` / `aidcp-content` 各自的 `scripts/migrate.ts`；`aidcp-cloud` 的迁移归属判据与迁移目录；控制仓 `scripts/sync-split-repos`。
- **迁移目录**：13 条补属主声明，1 条拆成 2 条（三仓 `migrations/` 随同步重新分发）。
- **解除阻塞**：`cloud-schema-migration-executor` 的 5.9（全新空库拉起验证）第一次具备执行条件；其 6.5（契约门转 `enforce`）与 5.11（删过渡旋钮）依赖本 change 先落地。
- **不影响运行中的环境**：dev / ol 的库早已建成，本 change 不产生任何需要在既有库上执行的 DDL。
