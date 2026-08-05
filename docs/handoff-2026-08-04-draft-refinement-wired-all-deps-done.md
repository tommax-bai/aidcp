# 交接：客户端 23 个依赖全部接通 + 同步读老雷根因已修（2026-08-04 21:00–23:30）

> **新 session 从这份看起。**
> 上一份 `handoff-2026-08-04-interaction-wired-draft-refinements-next.md` 交代的那件事
> （`draftRefinements`）**已经做完**，它剩下的价值只是背景——那些坑仍然有效。
> 再往前：依赖补齐全貌在 `handoff-2026-08-04-client-auth-dependency-recovery.md`，
> 切流当天在 `handoff-2026-08-04-derived-services-cutover.md`，都只用于追溯。

---

## 0. 现状与接手动作

dev 上跑三个派生服务，单体已停**且已 disable**。
桌面客户端鉴权的 **23 个依赖全部装配**，缺席表**是空的**。
昨晚那颗「重启即炸」的同步读老雷，**根因找到并修掉了**（§2）。

**先跑这四条，别信本文任何数字**（fleet 活跃，快照会过期）：

```bash
# ① 三服务 + 端口 + 就绪度；单体必须是 disabled
ssh -i ~/codes/dev-0722.pem root@121.89.85.150 \
  'for s in api automation content; do printf "%-12s %s NRestarts=%s\n" "$s" \
     "$(systemctl is-active aidcp-$s)" "$(systemctl show aidcp-$s -p NRestarts --value)"; done;
   printf "cloud        %s/%s\n" "$(systemctl is-active aidcp-cloud)" "$(systemctl is-enabled aidcp-cloud)";
   ss -ltn | grep -cE ":8787|:8090|:8091|:8092|:8093|:8094";
   T=$(grep -m1 "^AIDCP_AUTOMATION_INTERNAL_TOKEN=" /opt/aidcp/automation/.env | cut -d= -f2-);
   curl -s -X POST -H "Authorization: Bearer $T" -H "Content-Type: application/json" -d "{}" \
     http://127.0.0.1:8094/internal/automation/sync-read/readiness'

# ② 六仓对账（硬要求：派生 src 是重放，漂移只有对账看得见）
scripts/sync-split-repos

# ③ 客户端还差哪几个依赖（这张表是权威；现在应当是空的）
cd ../aidcp-api && grep -n "DELIBERATELY_ABSENT" -A 3 test/acceptance/client-auth-deps-inventory.test.ts

# ④ 镜像版本推进器有没有又漏（§2 那颗雷的闸，两个仓各一份）
cd ../aidcp-api && npx tsx --test test/acceptance/mirror-bump-wiring.test.ts
cd ../aidcp-automation && npx tsx --test test/acceptance/mirror-bump-wiring.test.ts
```

**23:25 实测**：三服务 active、`NRestarts=0`、六端口全在、就绪 `state=ready` `blockers=[]`、
`aidcp-cloud` = `inactive/disabled`、isales 四服务未碰。

**各仓 head**（本 session 收尾时，全部已推送）：

| 仓 | head | 本 session 改了什么 |
| --- | --- | --- |
| `aidcp`（控制） | `1b8eaede` | tasks 8.8/8.9/8.10 + 本文件 + 传输清单登记 |
| `aidcp-cloud`（事实源） | `01fe8a9` | 精修两族传输 + worker 三态 + 两组测试 |
| `aidcp-kernel` | `030d805` | 未动 |
| `aidcp-transport` | `7e6cba4` | 同步入包（精修两族） |
| `aidcp-api` | `8ed0aa7` | 精修接线 + **七个存储的镜像推进器补回** + 两张清单闸 |
| `aidcp-automation` | `1c770ff` | 共享包 pin + 镜像推进器闸（并修好它抓到的一处） |
| `aidcp-content` | `bd56379` | 精修 store + 队列路由 + worker + 有界泵 |

openspec change `deploy-derived-services-to-dev`：本 session 的记录在 tasks **8.8 / 8.9 / 8.10**。

---

## 1. 稿件精修（tasks 8.8）

### 1.1 它为什么是 23 个里最贵的一个：断的是两个方向

- **方向 A（api→content）**：作业队列四方法，transport 里原本零通道。
- **方向 B（content→api）**：worker 的落稿写口，同样零通道；而 store 与 worker 两个文件
  此前**全仓零 `new`** ⇒ 只补通道不够，属主侧也得接线。

两族写在**同一个传输文件** `src/transport/draft-refinement-http.ts`（CLAUDE §8.4 硬要求：
拆成两份会各自演化，两侧都编译过、都测试过，只有真跑起来才 404）。

### 1.2 两个判断题的答案（下次改这条链路前先读）

**`refreshPreview` 归谁**：绑在 **api 那次属主写**上，content 侧那一格是**显式空实现 + 注释**。
本仓 api 早有这条不变量（每次属主写成功产出一份单向预览）。
顺带堵掉单体留的洞：单体在作业**置完成之后**才推预览，置完成失败时稿子已改而预览不推
⇒ 桌面端继续显示旧稿、用户以为没保存上。绑在写上没有这个洞。

**`loadForDispatch` 不新开路由**：复用既有的 `api-direct/publish-log/v1/load-for-dispatch`。
端口完整性改由 content 组装根那处**对象字面量**在编译期钉（端口加方法则当场缺属性），
路由表用 `Exclude<…, 'loadForDispatch'>` 显式声明这个分工。两条同义路由只会各自演化。

### 1.3 三处跨进程保真（都做过变异测试，共 10 次，全红且点名）

| 会悄悄坏掉的 | 坏了长什么样 | 闸 |
| --- | --- | --- |
| `Map` 直接 JSON 化成 `{}` | 待审稿列表每条都显示「没精修过」，**没人会报障** | AC-REFINE-03 |
| pg 的 `23505` 冲突码丢了 | 「已经在调整了」变成 500「服务器错误」 | AC-REFINE-04 |
| 「写已提交、应答丢了」压成普通失败 | 回执说「原稿未变化」——**那是假话** | AC-REFINE-06 + worker 两条 |

第三条是**拆进程新增的一态**，单体没有。重投本身安全（写口是 `expectedVersion` 的 CAS，
真落了会拿到 `version_conflict`），**要治的只是回执说了假话**：
现在出的是「已提交但没能确认，请刷新查看当前版本，不要重复发起」。

### 1.4 配置变更（**部署 ol 时别忘**）

content 的 `.env` 新增 `AIDCP_API_INTERNAL_TOKEN`（与 api 侧同名项**同值**）。
**启动期必需**：回落到不带令牌只会一律 401，而 401 在 worker 眼里与
「api 拒绝了这次改稿」同形——每条精修都失败，且失败原因指向错的地方。
缺它时 content **直接拒绝启动**。

---

## 2. 同步读老雷：撞了、恢复了、根因也修了（tasks 8.9 / 8.10）

> 时间线：22:33 部署重启撞上（8787 停 10 分钟）→ 22:43 推版本恢复 → 23:20 根因修复并部署。

### 2.1 现象与机理（值得读——它解释了这类问题为什么零信号）

automation 一重启就以 `same_cursor_payload_drift` **永久拒收**两条流，启动期 fail-closed
⇒ 业务入口不放行 ⇒ **8787 消失**，而 **api / content 全程正常**（极易误判成别的问题）。

两条流的 cursor 就是 api 库 `config_mirror_version` 里 `persona_config` / `account_status`
两行的版本号（经 cantor 配对；实测 `cantor(0,67)=2345`、`cantor(0,960)=462240` 逐位对上），
载荷却读 `persona_config` / `accounts` 两张表。**表变了而版本没动** ⇒ 同一 cursor 上两种载荷摘要
⇒ 消费方按设计正确拒收，且该拒收是**永久**的（只有 cursor 真前进才解）。

属主自带的 `config-mirror/apply-bump` 路由对这两个键**主动拒绝**，而且**拒绝得对**：
它们与版本表同库，按设计只能走属主写入同事务里的 `bumpInTx`，跨域中继信号不该碰。

### 2.2 应急恢复（若下次仍撞上，这条依然有效）

在 api 库把相应的版本号 +1。与仓里 `0091_*_snapshot_revision` / `0108_*_snapshot_revision`
两条迁移做的是同一件事，不碰任何业务数据，消费方 20 秒内自愈。

```sql
UPDATE config_mirror_version SET version = version + 1
 WHERE mirror_key IN ('persona_config','account_status');
```

### 2.3 根因：**派生 api 手写的 main() 把七个存储的推进器全丢了**

`writeWithMirrorBump(pool, bumper, key, run)` 的第一行是 `if (!bumper) return run(pool)`：
**推进器缺席时写照常提交、版本一动不动、不报错也不告警**。
单体给这七个**全都**传了（逐个核过 `aidcp-cloud/src/server.ts`），派生 main() **一个都没传**。
这正是 CLAUDE §8.5 那条「裸 `?.` 静默吞掉」——单体里那一格恒有，拆完读到 `undefined` 就没了。

其中三个的原注释写着「本进程只读这三张表，缺省语义即不推版本」。
**那句话把一条静默缺省当成了一个决定**——那三张表的写口就在管理后台的模型配置页上，
而后端正跑在这个进程里。**「今天只读」永远不是理由**：读写归属会变，变的那天没有东西会提醒人，
而接上它在没有写发生时代价为零。

后果两层，第二层才是这次停摆：
① 消费方镜像永远不刷新 —— 昨天写进去的 **12 条人设、11 个新账号对自动化进程根本不存在**（零信号）；
② 同一 cursor 两种摘要 ⇒ 自动化重启即 fail-closed。

### 2.4 闸与证据

**闸**：`test/acceptance/mirror-bump-wiring.test.ts`，**api 与 automation 各一份**。
覆盖面**从事实源读出来**（扫 `src/` 找「选项里有 `mirrorVersionBumper`」的存储类，
再回组装根逐个核），**不手抄名单**，于是日后新增的存储自动进闸。
`AC-MIRROR-01` 专门钉「扫不到东西时本闸会全绿」这件事本身。

两边都装是有意的：只装 api 会留下「守卫只覆盖作者在治的那条道」——
**而 automation 那份第一次跑就抓到一个真的**（edge-access 自建的第二个节奏配置存储没接推进器）。
那一格改成**必填**而非可选：静默跳过的那条路不配有一个看起来像决定的写法。

**证据（决定性，不是「起来了」）**：按修复前必炸的顺序走了一遍 ——
经产品自己的写口做一次幂等 upsert（业务字段零变化）→ `account_status` **961→962**
（修复前纹丝不动）；**紧接着重启 automation** → `state=ready`、8787 在、drift 报错 **0 次**。

### 2.5 仍未了

**automation→api 的失效信号中继没接线**：自动化侧已经在写 outbox 行了，
但没有任何东西把它推给 api ⇒ 自动化属主的那几张限频配置表改了之后，
api 侧的镜像同样不会刷新。**形态与刚修掉的这条同源，只是方向相反。**
MUST NOT 把 2.3 读成「补完就全通了」。

---

## 3. 没验到的（**别声称它们好了**）

1. **没有从真客户端走过一次真精修。** 那条 503 分支现在**结构上不可能**
   （该格由必需 env 无条件构造，且依赖清单闸盯着），但「用户点一次精修真能跑完」
   需要一条真待审稿 + 一台在线边缘，两者都不具备。
2. **边缘从切流至今一台都没连上**（8787 上 established 恒 0）。
   任何需要在线边缘的行为，端到端一次都没被真实执行过。
3. **上一批（互动能力）那两条未验项原样有效**：没有一次真的走到自动化进程的收件箱；
   「用户的客户端现在好了」仍然要用户在客户端上点一次才算数。

---

## 4. 测试基线（跑出这些红的**不是你弄的**）

- `aidcp-api` 540/540 全绿；`aidcp-content` 453/453 全绿；
  `aidcp-cloud` 全量 4215（0 fail，11 skipped）+ acceptance 204/204 全绿。
- `aidcp-automation` acceptance 274/274 全绿；**全量有 4 条既有红**（干净树上一样红）：
  发布填充预算 / 命令序列器（XHS `set_schedule` 两条）/ 抢占分档。
- ⚠ 跑 cloud 的 typecheck / 测试时可能看到并发 session 造成的红——**先看报错文件名**。

---

## 5. 部署配方（本 session 实走一遍，可照抄）

1. 三槽各自备份：`/opt/aidcp/<s>.bak.<ts>.tar.gz` + `.env.bak.<ts>`；
2. `rsync -az --delete --exclude .git --exclude node_modules --exclude .env --exclude '.env.bak.*'`；
3. 各槽 `rm -rf node_modules/aidcp-{kernel,transport}` + `npm install --userconfig /dev/null`
   （**ssh 要带 `-A`**；`--userconfig /dev/null` 绕开内网 registry 劫持 `@types` 域）；
4. **就地核共享包真装上了**：`ls node_modules/aidcp-transport/dist/transport/<新文件>.js`
   —— pin 改了而装的是旧 sha 时，编译照过、测试照过，只有真跑才不对；
5. ECS 上三槽各跑一次 `npm run typecheck`；
6. **属主域先起、接口域后起**：content → automation → api（同秒重启会撞出同步读启动竞态）；
7. healthcheck：三服务 active + 六端口 + 就绪 `state=ready` + `aidcp-cloud` 仍 disabled + isales 未碰。

**动 ECS 前先查 `systemctl is-enabled aidcp-cloud`，必须是 `disabled`**（上一拍踩过：
停了没 disable 的单体会在重启空窗里抢回锁与 8787）。

---

## 6. 下一拍的候选

1. **接上 automation→api 的配置失效信号中继**（§2.5）。同源问题、方向相反，
   现在正是上下文最热的时候。
2. **tasks 8.2**：更新 backlog 簇 60，真验到的划掉、没验到的补「为什么没覆盖到」。
3. **tasks 8.4**：`openspec validate deploy-derived-services-to-dev --strict` → 归档；
   **归档前把仍未了的债搬进 backlog**（归档会把 tasks.md 埋进 archive，
   只活在任务注释里的东西从此没有任何机制提醒人）。
4. 请用户在客户端上真点一遍（慢启动 / 今日进展 / 发布队列 / 收件箱 / **稿件精修**）。

---

## 7. 指针

| 东西 | 在哪 |
| --- | --- |
| 本 session 的逐条记录 | `openspec/changes/deploy-derived-services-to-dev/tasks.md` **8.8 / 8.9 / 8.10** |
| 精修两族的契约与保真理由 | `aidcp-cloud/src/transport/draft-refinement-http.ts` **文件头** |
| 镜像推进器闸 | `aidcp-api` 与 `aidcp-automation` 的 `test/acceptance/mirror-bump-wiring.test.ts` |
| 客户端还差哪些依赖（**权威**） | `aidcp-api/test/acceptance/client-auth-deps-inventory.test.ts` |
| 本进程服务哪些路由（**权威**） | 各仓 `test/acceptance/served-route-inventory.test.ts` |
| 上一批（互动能力）与那六个坑 | `docs/handoff-2026-08-04-interaction-wired-draft-refinements-next.md` |
| 依赖补齐这条线的全貌 | `docs/handoff-2026-08-04-client-auth-dependency-recovery.md` |
| 拆仓不变量 | `CLAUDE.md` §8（OVERRIDE 级） |
