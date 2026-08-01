# 交接：第九轮（2026-08-01 深夜）

> 上一轮入口是 `docs/handoff-2026-08-01-round8.md`，**它仍然有效**，本文只接着写。
> 起手三件事（preflight / `openspec list` / 确认 sub-repo 在本机）照旧看那份 §0。
>
> ⚠️ 数字都是当时的快照，一律以 CLI live 为准。

---

## 0. ✅ 已解决（23:48）—— dev 恢复正常，跑的是主干

> **结局先说**：属主流在 23:44–23:48 把三处遗漏全部修掉并成功部署，
> **dev 现在跑主干、健康**（8787 + 8090 监听、外部 WebSocket 握手成功、无启动失败行、isales 未受影响）。
> 三个修复提交：`a0ee197`（自举名单按属主派生）、`1fa71d2`（基线投影逐字段构造）、
> **`c0de08b`（补迁移 `0106_automation_sync_read_facebook_operation_policy.sql`）**——
> 最后这条正是本文 §1 定位的根因。
>
> **下面 §0 / §1 的原文保留供追溯**（当时 dev 确实停了约一小时），
> 但**别再照着执行回滚**：那是停机期间的临时手段，现在不需要了。
> 接手时先跑一句判当下：`ss -ltnp | grep -E ":8787|:8090"` 应有两条。

---

## 0'（历史）当时的处置：dev 曾跑在**回滚版本**上

> ⚠️ **23:45 更新：dev 又掉了，不是我弄的，也别急着回滚。**
> 我在 23:39 回滚到 `534af19` 并验通（8787/8090 监听、WS 握手成功、飞书长连接、PG 就绪），
> 但 **23:43 有另一个 session 覆盖部署了带批 E-2 的代码**（`.deployed-commit` 被抹掉、
> `server.ts` 换新、启动即撞 §1 的第 ③ 条 DB 约束）。**那条流的属主正在活跃迭代**，
> 此刻再回滚只会和他们打架。**接手时先看 `ss -ltnp | grep 8787` 判断当下状态**：
> 若仍未监听且属主已收工，就照下面的方式回滚保服务。

**回滚保服务的做法（我 23:39 用过、验通过）**：

```bash
cd ~/codes/aidcp-cloud            # 主 checkout，干净树
STAGING=$(mktemp -d); git archive 534af19 | tar -x -C $STAGING
rsync -az -e 'ssh -i ~/codes/dev-0722.pem' --exclude .env --exclude node_modules --exclude .git \
  $STAGING/ root@121.89.85.150:/opt/aidcp/cloud/
ssh -i ~/codes/dev-0722.pem root@121.89.85.150 \
  'cd /opt/aidcp/cloud && npm install --no-audit --no-fund && systemctl restart aidcp-cloud.service'
# 30s 后验：ss -ltnp | grep -E ":8787|:8090"   —— 必须两条都在
```

**23:39 那次回滚后的实测状态（可作为「好了长什么样」的参照）**：

| 项 | 值 |
| --- | --- |
| 跑的提交 | **`534af19`**（批 E-2 之前），**不是** master |
| 8787 边-云 | 监听中，外部 WebSocket 握手成功 |
| 面板 8090 | 监听中 |
| 飞书 | 长连接已建立 |
| PG | 就绪 |
| isales | 四个服务全程未受影响 |

**为什么是回滚版本**：云端主干 `a0ee197` **在 dev 上起不来**（详见 §1）。
dev 停了约一小时，先回滚保服务，主干的修复留给属主流。

**机器上现在有这两个备份**（都在 `/opt/aidcp/`）：
`cloud.bak.20260801-224105.tar.gz`（我动手之前）、`cloud.bak.20260801-233557.tar.gz`（部主干之前）。

**新增了一个文件：`/opt/aidcp/cloud/.deployed-commit`**，内容是提交 sha + 时间。
**请下次部署继续维护它** —— 今晚有近一半时间花在「猜机器上到底跑的是哪一版代码」上，
而这个信息本来一行就能记下。它现在写着 `534af19 ROLLBACK-for-outage`。

---

## 1. 主干为什么起不来（三个错误，同一个根）

按我实际撞到的顺序：

1. `monolith_sync_read_not_ready` … `facebook_operation_policy` **uninitialized**
   —— 自举流名单是手抄的，批 E-2 步骤 2 新增了第八条流、名单还是七条。
   **属主已在 `a0ee197`（23:04）修掉**（改成按属主从流定义派生）。
2. `automation_sync_read_apply_failed … reason=invalid_envelope`
   —— 跨进程载荷按**精确键集**校验，浏览面缓存比契约多带两个字段。
   代码注释里写着这条已按「逐字段构造」修过，**但 `a0ee197` 上仍然复现**，说明还没修干净。
3. `new row for relation "automation_sync_read_consumer_checkpoint" violates check constraint
   "automation_sync_read_consumer_checkpoint_stream_check"`
   —— **这条最说明问题**：DB 侧那张检查点表的 `stream` 列有 CHECK 约束，
   **约束里没有 `facebook_operation_policy` 这个值**。

### 根因已坐实：缺一条迁移

`migrations/0083_automation_sync_read_consumer_checkpoint.sql` 建表时把 `stream` 列写成
**枚举式 CHECK，硬列了 7 条流**：

```
'account_persona', 'client_environment_automation', 'automation_account_projection',
'content_schedule', 'hot_lead_config', 'facebook_comment_config',
'facebook_group_join_automation_config'
```

批 E-2 步骤 2 在代码里加了**第 8 条** `facebook_operation_policy`，
**但没有配套迁移去扩这条约束**（`grep -rl facebook_operation_policy migrations/` 只命中
`0100` / `0103`，那两条是策略配置表本身，与本约束无关）。
于是自举一写检查点就被 DB 拒掉，启动路径当场抛错。

**要做的**：加一条迁移，drop 掉 `automation_sync_read_consumer_checkpoint_stream_check`
再按 8 条流重建（`api` 侧那张 `0082` 表同理，先确认它的名单要不要一起扩）。
**迁移号别硬猜**：`0105` 是当前最大，但并行流手上可能已经占了 `0106`
（`0082` 的文件头就记过一次「0081 被并行 change 占用」的先例），落号前先 `ls migrations/` 并对一遍在飞的分支。

**注意这是共库操作**：按根 CLAUDE.md §2，DEV/OL 长期共用 PostgreSQL。
扩 CHECK 是**加法、向后兼容**（只放宽允许值，OL 上跑的旧代码不会写这个流），
但仍属 schema 变更，走迁移执行器、别手工 `ALTER`。

**我没有代做这条迁移**，两个理由：它是 `split-cloud-automation-production-runtime` 的地界，
且那条流的 session **今晚仍在活跃部署**（23:43 又部了一次、撞的正是这条约束）——
此时插一条同域迁移，撞号与撞工作面的概率都高于收益。

（顺带留个坑给下一位：ECS 上直接连库读约束**没走通** —— `psql` 与 node 两条路都被
`Ident authentication failed for user "aidcp"` 挡住，说明应用的连法与我拼的不一样。
真要读线上 schema，先弄清 `.env` 里那几个 PG 变量的实际组合方式。）

### 这里有一条比 bug 本身更值得记的

**这三个错误全都发生在启动路径上，而部署前 `typecheck` + 验收 184 + 全量 4086 条全绿。**
这条「同步读自举」链路**零测试覆盖**：名单写全没写全、载荷键集对不对、DB 约束认不认，
三样都只有真起一次进程才知道。属主流已经为它连着两次改代码，
每次都是靠「部到 dev 上炸一次」发现的。**要么给它补一条能在 CI 里跑的启动自举用例，
要么把它从启动路径上挪走**（今天它在 `server.start()` 之前，所以失败＝端口永不监听）。

---

## 2. 今晚还发生了一件事：机器上的 `/dev/null` 变成了目录

**症状**（同时出现，很好认）：
SSH 与 8787 都是「**TCP 连得上、握手前被立刻断开**」，而 nginx（8088）与 isales（80）完全正常。
分界线是「这个服务要不要为每个新连接现开资源」—— nginx 是预开进程的静态服务，所以不受影响。

**修法**（用户从阿里云控制台做的，23:31 生效）：
```bash
ls -ld /dev/null            # 开头是 d 即确诊
rm -rf /dev/null && mknod -m 666 /dev/null c 1 3 && chown root:root /dev/null
systemctl restart sshd
```

**起因不明。** 我没有运行过任何会创建它的命令，是在回滚那一步第一次看到报错；
在那之前几分钟远程用到 `2>/dev/null` 时还是正常的。**下次再见到「SSH 握手前被断 + 某个服务同时也这样」，
先查这个**，别先怀疑限流或封禁 —— 我一开始判成 fail2ban，白等了十几分钟。

---

## 3. 因果订正（我一开始说错了一次）

我最初告诉用户「是我部署主干把 dev 弄挂的」。**不对，实测如下**：

- 带 bug 的代码**早在 20:51 就被同步到机器上了**（`server.ts` 落盘时间为证），但**没有重启**，
  进程还跑着 16:49 起的旧内存版本，所以看起来一切正常。
- 我 22:41 的 `systemctl restart` 是 20:51 之后的**第一次重启**，于是第一次让它生效。
- 换句话说：**这颗雷是潜伏的，任何人重启、或机器重启，都会踩到。**

**教训**：`rsync` 完不重启 = 把一次失败推迟到未来某个不确定的时刻，
而那时候动手的人会以为是自己弄坏的。**同步完就重启并验证，别留半态。**

---

## 4. 原本要收口的三条 change，现在各是什么状态

三条都卡在「部署 dev」这一步，本轮**一条也没能勾掉**，但卡点从「没人试过」变成了具名原因：

| change | 差的那一步 | 现在的结论 |
| --- | --- | --- |
| `platform-specific-identity-commands` 15/16 | 4.5 部 dev 并验证 | **闸已解除**（23:48 主干已部 dev 并健康）——本条现在可以直接验证收口 |
| `client-xhs-environment-schedule` 12/14 | 4.3 / 4.4 集成 + 部 dev | **部署这一半的闸已解除**；4.3 还含「集成 feature 分支」，先核那部分是否已完成 |
| `fix-cloud-multi-service-deploy-script` 4/5 | 2.3 用三进程脚本部 dev | **主动不做，理由已坐实**：见下 |

**三进程那条为什么不做**：`split-cloud-automation-production-runtime` 的 tasks.md 里明写
「`aidcp-api` 的手写入口**还没构造** Facebook 运营策略存储，故它今天供的是一个当场抛具名错误的实现。
**三进程真跑之前必须补上**，否则 automation 拉这条流会拿到 502」。
今天切三进程 = 把这条流打成 502。**这个前置比「脚本能不能跑」更靠前，得先解。**

顺带：**dev 当前是单体拓扑**（`aidcp-cloud.service` 一个进程带 8787 + 8090），
多服务单元文件在 `aidcp-cloud/deploy/multi-service/` 里备着但没启用。
那个脚本有 `check`（纯探测不改状态）/ `healthcheck` / `rollback` 三个安全子命令，探测过是好用的。

---

## 5. 本轮在事故之前完成的工作（都已推送）

- **归档 `native-page-engine-production-cutover`**（迁移主线，控制仓 `2c0ff416`）。
  归档红线要求的两项前置都做了；delta 通读只抓到一处越权断言（打包那条声称有 **Windows 签名流程**，
  实测 Windows 侧完全没有签名），已按平台各写各的实情。
- **`extend-native-postcondition-coverage` 37/37 归档**（控制仓 `b8617ad8`，edge 四次落地）。
  后置校验盘点从 22 达标 / 3 不达标 / 16 未读，做到 **40 达标 / 1 不达标 / 0 未读**。
- **修掉 E3 / E5 / E9 三条真缺陷**（edge `c0bdc34` / `20fc70a`）：
  feed 刷新与通知三个分类浏览不再「点了就算成功」，配图上传判据绑定到本次上传。
- **合并了两条重复登记**：我登记的 E13 / E14 其实是清单里早有的 E3 / E5，
  原因是新登记时没通读整张清单。已合并并把这条教训写进文件。

---

## 6. 下一步（按价值）

1. ~~让主干在 dev 上能起来~~ **已解决（23:48，属主流补了迁移 0106）。**
2. **三条 change 的部署任务现在可以收口**（§4）：前两条的闸已解除，第三条（三进程）仍卡在
   `aidcp-api` 那条 Facebook 运营策略存储没构造上，与本次停机无关。
3. 给「同步读自举」补一条能在 CI 里跑的用例（§1 末尾那段）—— 不补的话，
   下一批新流还会用同样的方式炸一次 dev。
4. 迁移修复四条线继续（见上一轮 handoff §3②）。
5. 出包 + 一次真机 session，仍然只有用户能做（真机 backlog 936 条）。

---

## 7. 给下一位的操作提醒

- **部署铁律照旧**：只从主 checkout 的干净快照（`git archive HEAD`）部，绝不从 worktree；
  先备份、失败即回滚；**绝不碰同机 isales**（今晚全程只读确认过四次，未受影响）。
- **部署完必须验端口再走**。`systemctl is-active` 显示 `active` **不代表在服务** ——
  今晚三次失败启动全都是「进程活着、日志在滚、端口从未监听」。判据要用 `ss -ltnp`
  加一次真实 WebSocket 握手，别信 `is-active`。
- **SSH 密集重连会被限流**（表现同样是握手前断开），排查时别拿连击当诊断手段。
