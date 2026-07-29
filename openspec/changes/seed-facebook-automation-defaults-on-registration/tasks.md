# Tasks: seed-facebook-automation-defaults-on-registration

> **范围铁律**：只对**真正首次登记**的账号种入。存量账号一个不碰。
> 判据 MUST 是「本次写入真的插入了新行」，**MUST NOT** 写成「配置侧表没有该账号的行」——
> 后者对 37 个存量账号同样成立，写错了会静默把它们全部种上，且单账号测试看不出来。

## 1. aidcp-cloud — 账号存储的注入点

- [x] 1.1 在账号主表存储的构造选项里新增一个**可选**回调：参数为账号 id 与已归一的平台，在登记**真的插入了新行**之后调用。缺省不注入时行为与今天逐字一致。 <!-- aidcp-cloud a96ac34 构造选项加 onAccountRegistered；缺省不注入 = 逐字零回归 -->
- [x] 1.2 回调**只在调用方显式声明了平台**时才触发。平台参数缺省会回落成小红书，此时 SHALL NOT 触发，并留下具名日志说明「因平台未声明而未种入」。 <!-- aidcp-cloud a96ac34 以入参 platform 是否存在为准，非归一化后的值；不种时打 [account-seed] 具名日志 -->
- [x] 1.3 回调异常 MUST 被捕获、MUST NOT 向上抛：登记本身照常成功。日志用一个**可检索的具名前缀**，便于事后捞出所有种入失败的账号。 <!-- aidcp-cloud a96ac34 seedAutomationDefaults 内 try/catch，前缀 [account-seed] 种入失败 -->
- [x] 1.4 账号存储 MUST NOT 新增对排期存储或加群配置存储的 import——回调由组装根接线，存储本身不认识这两个配置域。 <!-- aidcp-cloud a96ac34 已核：account-store.ts 未新增任何 config 域 import -->

## 2. aidcp-cloud — 组装根接线

- [x] 2.1 在组装根把回调接到两个既有写入方法上（排期存储与自动加群存储），并确认二者构造顺序早于账号存储的使用点。 <!-- aidcp-cloud a96ac34 两个 store 构造在 :2111/:2123，账号存储在 :2774，顺序天然满足 -->
- [x] 2.2 平台分支：`facebook` → 种两行；其余平台 → 不种、直接返回。视频号四个动作在平台目录里全不支持，为它写任何正上限都会被写前校验整块拒。 <!-- aidcp-cloud a96ac34 经 newAccountAutomationDefaultsFor 返回 null 即 return，无条目 = 不种 -->
- [x] 2.3 种入取值：总开关开；发帖开 + `review` + 5；评论开 + `review` + 20；加群开 + 20。**联系评论不种**（保持关闭）。 <!-- aidcp-cloud a96ac34 值放 kernel 目录常量 NEW_ACCOUNT_AUTOMATION_DEFAULTS；只传模式列（开关列由 store 派生） -->
- [x] 2.4 两次写入分别判结果：任一失败只记该行的具名日志，不影响另一行、不影响登记。日志要能分辨是排期行还是加群行失败。 <!-- aidcp-cloud a96ac34 两次写入各自判 ok，失败分别打「排期行/加群行种入被拒」 -->
- [x] 2.5 确认两个写入方法都自带镜像版本推进（已核：均走同一个带版本推进的写入包装），因此**不需要**在本 change 里另行处理跨进程缓存失效。 <!-- aidcp-cloud a96ac34 已核：两处均走 writeWithMirrorBump，本 change 不另处理缓存失效 -->
- [x] 2.6 写入署名（`updatedBy`）用一个可辨识的系统来源值，与运营手工写入区分，便于事后追溯哪些行是种出来的。 <!-- aidcp-cloud a96ac34 署名 system:new-account-seed，测试断言 ^system: -->

## 3. aidcp-cloud — 测试

- [x] 3.1 新账号 + 平台为 facebook → 种入两行，取值逐字符合 2.3，且联系评论保持关闭。 <!-- aidcp-cloud a96ac34 platform-registry.test.ts 逐字断言取值 + 断言无 contact 键 -->
- [x] 3.2 **存量账号防扩散断言**（专挡最危险的那个误实现）：账号已存在于主表、且配置侧表无任何行 → 再次登记时**不种入**。 <!-- aidcp-cloud a96ac34 account-store.test.ts「存量账号防扩散」：RETURNING 空 → 钩子零调用 -->
- [x] 3.3 平台为小红书 / 视频号 / 未声明 → 均不种入；未声明那条另断言有具名日志。 <!-- aidcp-cloud a96ac34 未声明平台不触发钩子；其余平台 newAccountAutomationDefaultsFor 返回 null -->
- [x] 3.4 种入失败（配置存储抛错）→ 登记仍成功、异常不外抛、有具名日志；且**不重试**。 <!-- aidcp-cloud a96ac34 钩子抛错后 getPlatform 仍命中缓存，证明登记已成功 -->
- [x] 3.5 未注入回调时，登记行为与今天逐字一致（零回归）。 <!-- aidcp-cloud a96ac34 不注入钩子的零回归用例 -->
- [x] 3.6 跑 `npm run test:acceptance` → `npm test` → `npm run typecheck`。 <!-- aidcp-cloud a96ac34 acceptance 166/166、全量 3847 pass 0 fail、typecheck clean -->

## 4. 部署与验收（dev）

- [x] 4.1 部署 cloud 到 dev（控制仓 §5 安全序列：备份 → rsync → restart → healthcheck）。无数据库迁移。 <!-- 2026-07-29 备份 cloud.bak.20260729-161247.tar.gz；重启后 8787/8090 均在听；三个 schema 门全过；无迁移 -->
- [x] 4.2 部署后立即复核存量计数：Facebook 账号数、其中有排期行的数量、加群配置行数——**与部署前一致**即证明存量未被波及。部署前基线（2026-07-29 实测）：FB 账号 40、有排期行 3、加群配置行 2。 <!-- 2026-07-29 部署前后逐位一致：FB 账号 40、排期行 10（全平台合计；其中 FB 3）、加群行 2、署名为 system: 的种入行 0 —— 存量零波及已实证 -->
- [ ] 4.3 观察一个真正的新账号首次登记，确认两行被种出、取值正确、`updatedBy` 是系统来源值。**此项需要一个真实的新账号首连，无法在不造假数据的前提下由开发侧触发**——留给下一次真机上新号时确认。捞取方式：日志搜 `[account-seed]`，或查两张配置表里 `updated_by` 以 `system:` 开头的行。
- [ ] 4.4 确认该新账号**没有**因为种入就立刻开跑——它仍应被人设绑定等既有闸拦住。同 4.3，随真实新号一并确认。

## 5. 交接说明

- [x] 5.1 写明：37 个存量 Facebook 账号仍然完全不自动，本 change 刻意不碰。若后续要处理，另起 change 并自带分批与观察窗口。 <!-- 见 proposal / design：37 个存量 FB 账号仍完全不自动，本 change 刻意不碰 -->
- [x] 5.2 写明：种入失败没有自动补种路径，这是为满足「存量不碰」必然付出的代价，**不是待修缺陷**。 <!-- 见 proposal「已知不做补救的一处缺口」与 account-store 注释 -->
- [x] 5.3 写明：评论的审批模式默认取需人审是设计判断而非用户明确要求；要改成免审只需改种入取值那一处。 <!-- 见 design Open Questions：改种入取值那一处常量即可 -->
