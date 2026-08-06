# Tasks — collapse-facebook-global-policy-target-column

> **前置（两条，性质不同，都不得引用本文件里的实测快照）**
>
> 1. **归档顺序**：本 change MODIFY 的地基能力 `facebook-global-policy-single-scope` 由
>    `unify-facebook-global-policy-across-targets` 引入。**那条归档之前，本条 MUST NOT 归档**，
>    否则 delta 合并会 `Aborted. No files were changed.`（本 change 的 delta 全部是 `## ADDED`，
>    但 ADDED 到一份尚不存在的能力上会写出一份悬空规格 —— 属「依赖序倒置」，validate 与 archive 都不报错。）
> 2. **上线顺序**：迁移只有在**全部**在跑的属主进程都已切读合并行之后才可执行。
>    2026-08-06 实测 dev 与 OL 的 `aidcp-api` 均已跑该版本（作用域常量存在、5 处引用），
>    但**执行时 MUST 重测**——期间任何一次从旧发布分支发版都会让这个前置失效。

## 1. 前置坐实（动手之前必须先有结论）

- [ ] 1.1 逐环境实测「已切读单份」：在 dev 与 OL 上各确认 `aidcp-api` 进程跑的构建含作用域常量且被读写路径引用。判据是**进程实际在跑的那份代码**，不是分支名、不是台账。
- [ ] 1.2 列出当前所有 `release/*` 分支，逐条判定是否已含本 change；未含者在本 change 上线后 MUST NOT 再发往任一环境。产出一份具名清单写进 7 组的部署任务。
- [ ] 1.3 重跑三条数据前置并记录当次数值（不得引用 design 里的快照）：
  `all` 未覆盖的 `env_key` 数 / `all` 行内 `env_key` 重复数 / `all` 完成时刻晚于任一旧行的环境数，三者必须全为 0。
- [ ] 1.4 确认审计表现状仍是「历史行跨目标有重复 revision」：若已不重复，D3 的论证需重新走一遍再决定是否收紧（**默认仍不收紧**，理由见 design D3 第二段）。

## 2. aidcp-cloud — 收缩迁移（**只做 contract 段**）

- [ ] 2.1 新增 contract 迁移，头部按仓内约定声明 `aidcp:kind=contract` 与全部 `aidcp:objects`（三张主表 + 被删的 CHECK 约束 + 新增的单例约束）。**约束名 MUST ≤63 字节**——`0110` 曾因自动名 65 字节被 PG 截断、按全名 DROP 不命中且不报错而整体回滚。
- [ ] 2.2 迁移开头逐条断言 1.3 的三条数据前置，任一不成立即抛错使整条回滚；**MUST NOT 只删通过检查的那部分行**。
- [ ] 2.3 删除三张主表中作用域不是 `all` 的行。
- [ ] 2.4 两张策略表：加 `singleton boolean NOT NULL DEFAULT true`，改 `PRIMARY KEY (singleton)` + `CHECK (singleton)`，再删 `execution_target` 列及其 CHECK。顺序不可颠倒（删列会先带走现有主键）。
- [ ] 2.5 冷启动完成表：主键改 `(env_key)`，再删 `execution_target` 列及其 CHECK。**先删旧行（2.3）再改键**——同一 `env_key` 在 dev 与 ol 各有一行时 `(env_key)` 不成立。
- [ ] 2.6 **审计表零改动**：两张 `*_audit` 的 `execution_target`、CHECK、唯一约束一个字节都不动。迁移里 MUST NOT 出现针对它们的 DDL。
- [ ] 2.7 `npm run migrate status` / `verify` 在 dev 上确认本迁移声明的对象与实际一致。

## 3. aidcp-cloud — 存储与路由

- [ ] 3.1 两张策略表的读写改为直取单行：去掉作用域参数与 `WHERE execution_target=$1`。
- [ ] 3.2 冷启动完成事实的读写改为按 `env_key` 直取，去掉作用域参数。
- [ ] 3.3 作用域常量文件在全部引用消除后删除；**MUST NOT 留一个恒为 `'all'` 的常量继续传参**——那等于把分行维度改名留在代码里。
- [ ] 3.4 视图里 `executionTarget` 那一格**保持不变**（它表示「通过哪个目标的接口读」，面板对它有 `['dev','ol']` 硬闸）。本 change MUST NOT 改它的语义或取值。

## 4. aidcp-cloud — 测试

- [ ] 4.1 单测：插入第二行全局策略必然失败（单例约束真的在库层面拦住，而不是靠写入方只写一行）。
- [ ] 4.2 单测：同一 `env_key` 的第二条完成事实必然失败或幂等合并。
- [ ] 4.3 迁移用例：断言三条数据前置逐条被断言且任一不成立时整条失败；**把断言删掉后该用例必须变红**。
- [ ] 4.4 迁移用例：断言迁移**不含**任何针对两张审计表的 DDL（守住 D3）。
- [ ] 4.5 反回归：断言代码里不再有以运行目标为键读写这三张表的路径，也不存在恒为 `'all'` 的替代常量。
- [ ] 4.6 两仓回归：`test:acceptance` → `npm test` → `typecheck` 全过。

## 5. aidcp-api — 派生仓同步

- [ ] 5.1 `scripts/sync-split-repos --apply --repo aidcp-api` 同步属主文件；组装根不派生，需手写的部分单独确认。
- [ ] 5.2 派生仓 `test/` 不在同步器覆盖范围内：受影响的用例逐个手工对齐，对齐前先确认与云端同源（该仓的副本是手工适配过的，整份覆盖会静默还原它的适配）。
- [ ] 5.3 派生仓 `typecheck` + 全量测试通过。

## 6. aidcp-automation — 零改动验证

- [ ] 6.1 该域经同步读镜像消费策略，载荷本就是「一份」，预期零改动；**但 MUST 实测验证不因属主侧去掉分行列而漂移**：对比收缩前后镜像载荷逐格相同。
- [ ] 6.2 若确有漂移，MUST 在本 change 内修完，MUST NOT 留给「反正镜像会自己刷新」。

## 7. 部署与迁移执行

- [ ] 7.1 迁移前备份：三张表各导出一份，记录导出时刻与文件位置。**这是本 change 唯一的回滚路径**（删列之后代码回滚救不了），MUST NOT 当作流程装饰。
- [ ] 7.2 dev 部署 + 迁移；healthcheck 含「重启后真的起来了」，不只是部署前 active。
- [ ] 7.3 OL 部署：MUST 从含本 change 的发布分支执行，且执行前把 1.2 那份分支清单再核一遍。
- [ ] 7.4 迁移记录写清：执行时刻、三条数据前置的当次实测值、删除的行数（按表）、备份文件位置、**回滚方式＝从备份恢复**。
- [ ] 7.5 上线后逐环境确认接口进程重启一次仍能起来，且策略读数与收缩前逐格相同（收缩不改任何数值，读数变了就是出事了）。

## 8. 验收（缺一不可）

- [ ] 8.1 三张表的 `execution_target` 列与 dev/ol 旧行确实不存在。
- [ ] 8.2 试插第二行全局策略在真库上被拒。
- [ ] 8.3 两张审计表的列、CHECK、唯一约束与收缩前逐字节相同。
- [ ] 8.4 两侧后台读到的策略与收缩前逐格相同（含 revision）。
- [ ] 8.5 自动化侧镜像载荷与收缩前逐格相同。
- [ ] 8.6 真机 / 长周期观察项登记进 `docs/real-machine-acceptance-backlog.md`。

## 9. 归档前置

- [ ] 9.1 `unify-facebook-global-policy-across-targets` 已归档（见文件头前置 1）。
- [ ] 9.2 `openspec validate collapse-facebook-global-policy-target-column --strict` 通过。
