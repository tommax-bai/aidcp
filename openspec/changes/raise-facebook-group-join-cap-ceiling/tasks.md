# Tasks: raise-facebook-group-join-cap-ceiling

> 顺序铁律：**先迁移放宽约束、后代码放宽校验**。反过来会在两次部署之间留一个必然失败的写入窗口。
> 误改红线：契约层里自动加群常量与**联系评论常量相邻、当前值都是 10**。一律按符号名定位，禁止按行号。

## 1. aidcp-cloud — 数据库约束

- [x] 1.1 新增迁移 `migrations/0098_facebook_group_join_daily_cap_50.sql`（序号已核：现最大 0097）。内容为「按显式约束名删除旧 CHECK（不存在也不报错）→ 新增 `daily_cap BETWEEN 0 AND 50` 的同名 CHECK」，写成可重复执行。 <!-- aidcp-cloud 196b2d3 照 0094/0039 先例按 pg_constraint 动态查名循环 DROP；含 undefined_table 兜底 -->
- [x] 1.2 迁移头部按仓内既有格式补 `-- aidcp:kind=` 与 `-- aidcp:objects=` 元信息行，并注明「自愈建表模板对已存在的表不生效，故必须显式 ALTER」。 <!-- aidcp-cloud 196b2d3 偏离：objects 必须声明 table: 而非 constraint:，否则属主归属反推不出、落进残留分支被计入全部属主库（门禁 sync-read-checkpoint-migration 抓到） -->
- [x] 1.3 确认现网旧约束的**真实名字**（自动生成名在不同环境可能不一致）。若不可预知，迁移改为「按 `information_schema` 查出该表上引用 `daily_cap` 的 CHECK 并逐个删除」再新增，避免删不掉旧约束导致两条约束并存、严格者继续生效。 <!-- aidcp-cloud 196b2d3 采动态查名方案（走 pg_constraint 而非 information_schema，与仓内先例一致） -->

## 2. aidcp-cloud — 契约常量与写入校验

- [x] 2.1 契约层平台常量：自动加群日上限硬上限 10 → 50，**按符号名定位**。 <!-- aidcp-cloud 196b2d3 -->
- [x] 2.2 逐字核对：同文件相邻的联系评论硬上限常量仍为 10，未被顺带修改。 <!-- aidcp-cloud 196b2d3 两个常量各补了一段注释写明为何刻意不同值 -->
- [x] 2.3 核对加群配置存储的自愈建表模板：确认它按常量插值、插值结果为 `BETWEEN 0 AND 50`；确认写前校验复用同一常量、无第二处写死数字。 <!-- aidcp-cloud 196b2d3 已核，模板与校验均单点派生 -->
- [x] 2.4 全仓搜一次自动加群日上限的其它写死表达（含测试、夹具、注释里的断言），逐处判定是跟随还是保留。 <!-- aidcp-cloud 196b2d3 命中 4 处需跟随：store 测试 2 处、platform-registry 测试 1 处、schema 版本常量 1 处；migrations/0067 基线保留原值（历史快照，由 0098 覆盖） -->

## 3. aidcp-cloud — 测试

- [x] 3.1 新增/更新单测：日上限 50 写入成功；51 被整块拒并回可诊断原因，**不静默截断为 50**。 <!-- aidcp-cloud 196b2d3 越界样本改用 MAX+1 而非写死 51，硬上限再变时不会退化成测合法值 -->
- [x] 3.2 新增回归断言：联系评论日上限 11 仍被整块拒（硬上限保持 10）——这条专门用来挡住 2.1 的误改。 <!-- aidcp-cloud 196b2d3 store 测试与 platform-registry 测试各一处 -->
- [x] 3.3 新增断言：账号配置 50 而风控日额度为 3 时，当日至多加入 3 个群并记录可诊断拒因（验证「抬天花板不放大实际跑量」这一不变量未被破坏）。 <!-- aidcp-cloud 196b2d3 偏离：该不变量由排期调度器既有用例覆盖（取小逻辑未被本次触碰），本 change 未新增重复用例；规格侧已补该场景 -->
- [x] 3.4 跑 `npm run test:acceptance` → `npm test` → `npm run typecheck`（顺序按控制仓 §4 回归纪律）。 <!-- aidcp-cloud 196b2d3 acceptance 166/166、全量 3835 pass 0 fail、typecheck clean -->

## 4. aidcp-console — 夹具同步

- [x] 4.1 `src/pages/ContentSchedulePage.test.tsx` 里 `join_group` 的 `maxDailyCap` 由 10 改为 50（现位于 :204；同文件 :44 与 :203 的 `contact_comment` 保持 10 不动）。 <!-- aidcp-console ff07b8a -->
- [x] 4.2 确认前端无其它写死的加群上限：输入框上限来自服务端下发的平台动作声明，**不需要改业务代码**。 <!-- aidcp-console ff07b8a 已核，仅夹具与一处展示断言（分母 / 10 → / 50） -->
- [x] 4.3 跑 console 测试与 typecheck。 <!-- aidcp-console ff07b8a 297 pass 1 skipped、typecheck clean -->

## 4b. 门禁遗留记录（实装中被红线抓到、值得后来人知道）

- [x] 4b.1 运行时 DDL 棘轮**连注释文本一起数**：在常量注释里写一句字面的建表语句就会把冻结基线顶上去。注释改用功能性描述即可。 <!-- aidcp-cloud 196b2d3 -->
- [x] 4b.2 迁移顺序闸的表名正则**不含点号**：写 `public.<表>` 会被截成表名 `public`，误报成「引用了尚未建出的表」。仓内约定不写 schema 前缀。 <!-- aidcp-cloud 196b2d3 -->
- [x] 4b.3 `KNOWN_MAX_SCHEMA_VERSION` 抬到 0098，**REQUIRED 刻意不抬**：放宽方向的约束替换不构成硬依赖，旧库仍能正常跑。 <!-- aidcp-cloud 196b2d3 -->
- [x] 4b.4 aidcp-console 的 `package-lock.json` 被 gitignore，新建 worktree 里没有，`npm ci` 会直接失败；需从 canonical checkout 拷一份。 <!-- aidcp-console ff07b8a -->

## 4c. 集成

- [x] 4c.1 aidcp-cloud ff 推送到 origin/master。 <!-- aidcp-cloud 196b2d3 -->
- [x] 4c.2 aidcp-console ff 推送到 origin/master。 <!-- aidcp-console ff07b8a -->

## 5. 执行与验收（dev）

> **更正**：起草时记的「云端无迁移执行器、全靠人工按序执行」是错的。`npm run migrate` 是正规执行器：
> 整批 advisory lock 互斥、逐条单事务、校验和比对、账本记账；校验和不符 / 乱序 / 缺 kind 整批拒绝。
>
> 顺序按 design D3：**先部署代码、再立即跑迁移**（执行器与迁移文件都住在部署树里，不同步上去就没得跑）。
> 中间窗口内写入大于 10 的值会被库拒绝并回明确错误——方向安全、可重试，不是数据损坏。

- [x] 5.1 确认数据库连接目标：dev 与 ol 是否共用同一实例（**未查实**）。若共库，须先明确本次是同时改两套环境的约束（放宽方向对既有数据恒安全）。 <!-- 2026-07-29 已查实：dev 三个属主 URL 均已设、物理拆库，0098 只落 api 属主（content/automation 各自 0 条待应用）。dev↔ol 是否共库仍未查实，但本迁移放宽方向对既有数据恒安全，且实测现网 daily_cap>10 的行数为 0 -->
- [x] 5.2 部署 cloud 代码到 dev（按控制仓 §5 安全序列：备份 → rsync → restart → healthcheck）。 <!-- 2026-07-29 备份 /opt/aidcp/cloud.bak.20260729-134834.tar.gz（6.3M）+ .env.bak；rsync 排除 .env/node_modules/.git/dist；restart 后 8787 与 8090 均在听；飞书长连接已建立；isales 未被触碰 -->
- [x] 5.3 立即在 ECS 上跑 `npm run migrate status` 确认 0098 待应用，再跑 `npm run migrate up` 应用。 <!-- 2026-07-29 status 显示 api 属主待应用 1 条；up 后 applied 0098 (kind=expand, 5ms) -->
- [x] 5.4 跑 `npm run migrate verify` 对账；并直接查该表上 `daily_cap` 的 CHECK 定义，确认恰好一条、为 0..50。**返回两行 = 旧约束没删干净，严格者仍在生效**——只看写入成功与否会漏掉这种情况。 <!-- 2026-07-29 三属主库 verify 均「缺失对象：0」；约束条数=1，定义 CHECK ((daily_cap >= 0) AND (daily_cap <= 50))，旧约束已删净 -->
- [x] 5.5 后台验收：加群日上限输入框上限显示 50；填 50 保存成功；填 51 被拒并有可诊断提示。 <!-- 2026-07-29 偏离：改用库侧边界实证替代 UI 点击（事务内探针、结束即 ROLLBACK、残留 0 行）。10/20/50 接受，51/100 被 23514 拒于具名约束 facebook_group_join_automation_config_daily_cap_range。UI 层单测已在 aidcp-console ff07b8a 覆盖；真人点一遍后台仍建议由运营在下次巡检时顺带确认 -->
- [x] 5.6 **预期线上加群量不变**——这是正确结果，不是回归。记录一次当日实际加群数作为基线。 <!-- 2026-07-29 现网 daily_cap>10 的配置行数为 0，即无任何账号已配到新区间，故加群量必然不变；基线待运营调配额后再测才有意义 -->

**部署后一条值得记的观察**：schema 契约门日志显示 api 属主「账本最高版本 0097（所需 0097，本构建认识到 0098）」并判通过——这正是 4b.3 那个「只抬 KNOWN_MAX、不抬 REQUIRED」决定的预期表现：构建领先账本不阻塞启动。

## 6. 交接说明（本 change 不做、但决定 50 是否产生效果）

- [x] 6.1 在 change 收尾说明里写明：要让 50 产生实际效果，运营须在后台配额配置页调整**风控档位的当日加群额度**与**单场会话加群预算**。两者均热加载、不需发版、不属本 change。 <!-- 2026-07-29 实测发现运营**已经调过**：普通档加群日额 20、单场会话加群预算 15（均非代码回落默认）。故本条从「待办提醒」变为「已由运营完成」；下面 6.2 记实测值 -->
- [x] 6.2 查实并记录生产库各档位当日 `join_group` 额度与单场会话加群预算的真实值。 <!-- 2026-07-29 dev 实测，见下表 -->

### 6.2 实测结果（dev，2026-07-29）

限额表**在 automation 属主库**（api 库没有这张表），且已被运营覆盖过，**不再走代码回落默认**：

| 档位 | 动作 | 日额 | 每分钟 | 每小时 |
|---|---|---|---|---|
| conservative | join_group | 1 | 1 | 1 |
| **normal** | **join_group** | **20** | 2 | 10 |
| aggressive | join_group | 35 | 1 | 7 |
| conservative | comment | 1 | 1 | 1 |
| **normal** | **comment** | **8** | 2 | 10 |
| conservative | publish | 0 | 0 | 0 |

单场会话预算：加群 15、评论 6、时长上限 30 分钟。

**三条对下一波有直接影响的推论**（生效值取账号配置与风控日额的较小者）：

1. **加群**：账号配置 20 × 风控普通档 20 → 生效 **20**，两者刚好对齐，不卡。但单场会话上限 15，一天要跑 ≥2 场会话才可能触到 20。
2. **评论**：账号配置 20 × 风控普通档 8 → **生效只有 8**。要让 20 生效，必须把普通档 comment 日额抬到 ≥20（后台改、热加载）。
3. **发帖**：限额表**没有** publish 的 normal / aggressive 行 → 回落代码默认（普通档 1）。账号配置 5 × 1 → **生效只有 1**。要让 5 生效，必须给 publish 补 normal 行。

以上三条属运营侧配额调整，不需发版、不属本 change 范围，记录在此供决策。
