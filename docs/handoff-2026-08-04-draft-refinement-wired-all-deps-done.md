# 交接：23 个客户端依赖全部接通，下一拍是清账（2026-08-04 21:00–22:50）

> **新 session 从这份看起。**
> 上一份 `handoff-2026-08-04-interaction-wired-draft-refinements-next.md` 写的那件事**已经做完**，
> 它剩下的价值只是背景（那些坑仍然有效）。再往前的全貌在
> `handoff-2026-08-04-client-auth-dependency-recovery.md`，切流当天在
> `handoff-2026-08-04-derived-services-cutover.md`，都只用于追溯。

---

## 0. 一句话现状

dev 上跑三个派生服务，单体已停且已 disable。
桌面客户端的 **23 个依赖全部接了**，`client-auth-deps-inventory` 的缺席表**是空的**。

**接手先做三件事，别信下面任何数字：**

```bash
# ① 三服务 + 端口 + 就绪度 + 单体必须是 disabled
ssh -i ~/codes/dev-0722.pem root@121.89.85.150 \
  'for s in api automation content; do printf "%-12s %s NRestarts=%s\n" "$s" \
     "$(systemctl is-active aidcp-$s)" "$(systemctl show aidcp-$s -p NRestarts --value)"; done;
   printf "cloud        %s/%s\n" "$(systemctl is-active aidcp-cloud)" "$(systemctl is-enabled aidcp-cloud)";
   ss -ltn | grep -cE ":8787|:8090|:8091|:8092|:8093|:8094";
   T=$(grep -m1 "^AIDCP_AUTOMATION_INTERNAL_TOKEN=" /opt/aidcp/automation/.env | cut -d= -f2-);
   curl -s -X POST -H "Authorization: Bearer $T" -H "Content-Type: application/json" -d "{}" \
     http://127.0.0.1:8094/internal/automation/sync-read/readiness'

# ② 六仓对账（硬要求，理由见上一份 §3.1）
scripts/sync-split-repos

# ③ 还差哪几个依赖（这张表是权威；现在应当是空的）
cd ../aidcp-api && grep -n "DELIBERATELY_ABSENT" -A 3 test/acceptance/client-auth-deps-inventory.test.ts
```

22:44 实测：三服务 active、`NRestarts=0`、六端口在、就绪 `state=ready` `blockers=[]`、
`aidcp-cloud` = `inactive/disabled`、isales 四服务未碰。

各仓 head：`aidcp-cloud@01fe8a9` / `aidcp-kernel@030d805` / `aidcp-transport@7e6cba4` /
`aidcp-api@8ed0aa7` / `aidcp-automation@1c770ff` / `aidcp-content@bd56379`。
openspec change `deploy-derived-services-to-dev` 的记录在 tasks **8.8 / 8.9 / 8.10**。

---

## 1. 这一拍做了什么

### 1.1 稿件精修接通（两个方向，不是一条通道）

- **方向 A（api→content）**：作业队列四方法。
- **方向 B（content→api）**：worker 的落稿写口。store 与 worker 两个文件此前**全仓零 `new`**，
  所以只补通道不够，属主侧也接了：store + 队列路由 + worker + 1.5s 有界泵（每轮最多 3 条）。
- 两族写在**同一个传输文件** `transport/draft-refinement-http.ts`（CLAUDE §8.4 硬要求）。

**`refreshPreview` 那道判断题的答案**：绑在 **api 那次属主写**上，content 侧那一格是显式空实现。
理由与好处见 tasks 8.8；顺带堵掉了单体留的一个洞（置完成失败时稿子已改而预览不推）。

**`loadForDispatch` 刻意不新开路由**，复用既有的 publish-log 那条；端口完整性改由 content
组装根那处对象字面量在编译期钉。

### 1.2 三处跨进程保真（都做过变异测试，10 次全红且点名）

| 会悄悄坏掉的 | 坏了长什么样 | 闸 |
| --- | --- | --- |
| `Map` 直接 JSON 化成 `{}` | 待审稿列表每条都显示「没精修过」，**没人会报障** | AC-REFINE-03 |
| `23505` 冲突码丢了 | 「已经在调整了」变成 500「服务器错误」 | AC-REFINE-04 |
| 「写已提交、应答丢了」被压成普通失败 | 回执说「原稿未变化」——**那是假话** | AC-REFINE-06 + worker 两条 |

第三条是拆进程新增的一态。重投本身安全（写口是 `expectedVersion` 的 CAS），**要治的只是回执说了假话**。

### 1.3 配置变更（部署时别忘）

content 的 `.env` 新增 `AIDCP_API_INTERNAL_TOKEN`（与 api 侧同名项同值）。
**启动期必需**：不带令牌只会一律 401，而 401 在 worker 眼里与「api 拒绝了这次改稿」同形。
ol 若将来部署，这一项必须同样补上，否则 content 直接拒绝启动。

---

## 2. 同步读老雷：撞了、恢复了、**根因也找到并修掉了**

> 时间线：22:33 撞上（8787 停 10 分钟）→ 22:43 推版本恢复 → 23:20 找到根因并修复部署。
> 下面前半段是机理（仍值得读，它解释了为什么这类问题零信号），后半段是根因与现状。

**它不是数据问题，是一条纯拆仓回归。**

- automation 一重启就以 `same_cursor_payload_drift` **永久拒收**两条流
  （`account_persona` cursor=2345、`automation_account_projection` cursor=462240），
  启动期 fail-closed ⇒ 业务入口不放行 ⇒ **8787 消失**（api / content 全程正常，很容易误判成别的问题）。
- **机理**：这两条流的 cursor 就是 api 库 `config_mirror_version` 里 `persona_config` / `account_status`
  两行的版本号（经 cantor 配对；实测 cantor(0,67)=2345、cantor(0,960)=462240 逐位对上），
  而载荷读的是 `persona_config` / `accounts` 两张表。**有人改了表却没推版本** ⇒
  同一个 cursor 上载荷变了 ⇒ 消费方按设计正确拒收，且这个拒收是永久的。
- **属主自带的 `config-mirror/apply-bump` 路由帮不上忙，而且它拒绝得对**：
  这两个键与版本表同库，按设计只能走属主写入同事务里的 `bumpInTx`。

**恢复办法（用户 2026-08-04 裁定，已验证 20 秒内自愈）**：在 api 库把那两行版本号各 +1。
这与仓里 `0091_*_snapshot_revision` / `0108_*_snapshot_revision` 两条迁移是同一件事。

```sql
UPDATE config_mirror_version SET version = version + 1
 WHERE mirror_key IN ('persona_config','account_status');
```

### 根因（已修，tasks 8.10）

**派生 api 自己手写的 `main()` 把七个属主存储的镜像版本推进器全丢了。**

`writeWithMirrorBump(pool, bumper, key, run)` 的第一行是 `if (!bumper) return run(pool)`：
**推进器缺席时写照常提交、版本一动不动、不报错也不告警**。
单体给这七个**全都**传了（逐个核过），派生 main() **一个都没传**。
这正是拆仓红线里那条「裸 `?.` 静默吞掉」——单体里那一格恒有，拆完读到 `undefined` 就没了。

其中三个的原注释写着「本进程只读这三张表，缺省语义即不推版本」。
**那句话把一条静默缺省当成了一个决定**，而那三张表的写口就在管理后台的模型配置页上、
后端正跑在这个进程里。「今天只读」永远不是理由：读写归属会变，而变的那天没有任何东西会提醒人。

**闸**：`test/acceptance/mirror-bump-wiring.test.ts`（api 与 automation **各一份**）。
覆盖面**从事实源读出来**（扫 `src/` 找「选项里有推进器」的存储类，再回组装根逐个核），
不手抄名单。两边都装是因为只装一边就会留下「守卫只覆盖作者在治的那条道」——
**而它在 automation 上第一次跑就抓到一个真的**（edge-access 自建的第二个节奏配置存储没接）。

**现状已验（决定性，不是「起来了」）**：经产品自己的写口做一次幂等 upsert →
`account_status` 961→962（修复前纹丝不动）；**紧接着重启 automation**（修复前必炸的那一步）
→ `ready`、8787 在、drift 报错 0 次。

**仍未了**：automation→api 的失效信号**中继**没接线（自动化侧写的是 outbox 行，
今天没有东西把它推给 api）。MUST NOT 读成「补完就全通了」。

---

## 3. 没验到的（**别声称它们好了**）

1. **没有从真客户端走过一次真精修。** 503 那条分支现在**结构上不可能**
   （那一格由必需 env 无条件构造，且依赖清单闸盯着），但「用户点一次精修真能跑完」
   需要一条真待审稿 + 一台在线边缘，两者都不具备。
2. **边缘从切流至今一台都没连上**（8787 上 established 恒 0）。任何需要在线边缘的行为
   端到端一次都没被真实执行过。
3. **上一批（互动能力）那两条未验项原样有效**：没有一次真的走到自动化进程的收件箱；
   「用户的客户端现在好了」仍然要用户在客户端上点一次才算数。

---

## 4. 部署时顺手带上去的别人的东西（如实记）

`aidcp-automation` 的 master 在本拍之前已被另一个 session 推到 `40b66d2`
（`restore-automation-risk-quota-inputs: wire the quota and nurture inputs into risk judgement`）。
本拍按惯例把 master 部署到 dev，**因此那条改动也一并上了 dev**，本 session 未测过它。
它的控制仓 change 目录 `openspec/changes/restore-automation-risk-quota-inputs/` 至今**未提交**。

---

## 5. 下一拍的候选

1. **接上 automation→api 的配置失效信号中继**（§2 末尾那条仍未了的）。
   自动化侧已经在写 outbox 行了，但没有任何东西把它推给 api ⇒
   凡是自动化属主的那几张限频配置表，改了之后 api 侧的镜像同样不会刷新。
   形态与刚修掉的那条同源，只是方向相反。
2. **tasks 8.2**：更新 backlog 簇 60，真验到的划掉、没验到的补「为什么没覆盖到」。
3. **tasks 8.4**：`openspec validate deploy-derived-services-to-dev --strict` → 归档，
   归档前把仍未了的债搬进 backlog。
4. 让用户在客户端上点一遍（慢启动 / 今日进展 / 发布队列 / 收件箱 / **稿件精修**）。

---

## 6. 指针

| 东西 | 在哪 |
| --- | --- |
| 本批的逐条记录 | `openspec/changes/deploy-derived-services-to-dev/tasks.md` 8.8 / 8.9 |
| 上一批（互动能力）与那六个坑 | `docs/handoff-2026-08-04-interaction-wired-draft-refinements-next.md` |
| 依赖补齐这条线的全貌 | `docs/handoff-2026-08-04-client-auth-dependency-recovery.md` |
| 精修两族的契约与保真理由 | `aidcp-cloud/src/transport/draft-refinement-http.ts` 文件头 |
| 本进程服务哪些路由（**权威**） | 各仓 `test/acceptance/served-route-inventory.test.ts` |
| 拆仓不变量 | `CLAUDE.md` §8（OVERRIDE 级） |
| 部署序列 | 属主域先起、接口域后起（content → automation → api） |
