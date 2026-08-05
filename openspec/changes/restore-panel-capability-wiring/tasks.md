# Tasks

> 事实基线：2026-08-05 dev 实测。接口进程 `panelDeps` 29 键 vs 单体 49 键；七处后台功能整页失败，两项静默能力缺失。
> 分类判据见 `design.md` §2（A 纯搬运 / B 单体已有 api 分支 / C 跨属主 / D 跨多域拼装）。

## 0. 开工前

- [x] 0.1 `git worktree list` 确认四个派生仓 canonical 都停在 `master`，本 change 的四个 worktree 已建（`../aidcp-{api,automation,content,cloud}.wt/restore-panel-capability-wiring`）。
- [x] 0.2 各 worktree 装依赖（内网 registry 会劫 `@types` 域，用 `npm ci --userconfig /dev/null --prefer-offline`）。
- [x] 0.3 记下开工时 dev 的实测缺口清单（本文件顶部表），收尾时逐条复打对照。

## 1. aidcp-api — A 类：本进程属主，纯搬运遗漏

- [x] 1.1 平台配置视图：在手写组装根里就地实现 `buildModelConfigView`（读本进程的模型配置存储 + 凭据存储 + kernel 厂商登记表），装上 `panelDeps.modelConfig.getView`。**MUST NOT** 复制单体那份跨段取用闸——它包的是历史位置，不是真跨域。
- [x] 1.2 凭据写：装上 `setCredential`（主密钥缺失时 `{ok:false}` 诚实可辨，绝不假成功）。
- [x] 1.3 角色配置外观：构造并装上 `roleConfig`（探活口先留占位，批次 3 接真探活；**在探活可用前 MUST 让写路径诚实拒绝，MUST NOT 放行不探活的写**）。
- [x] 1.4 分类默认外观：同 1.3，装上 `categoryConfig`。
- [x] 1.5 热帖引流：构造存储 + 外观，装上 `hotLeadConfig`。
- [x] 1.6 FB 群评论策略：构造存储，装上 `facebookGroupCommentPolicy`。
- [x] 1.7 视频号权限只读总览：由本进程的面板用户表 + 授权配置直接构造，装上 `interactionPermissions`。
- [x] 1.8 四个新构造的存储进启动 `init()` 批，并确认镜像版本推送口（`mirrorVersionBumper`）与既有三张配置表口径一致。
  <!-- aidcp-api 640f7f1（rebase 后 02e2237）批次 1 + 2 一并落。
       两处与预想不同、已就地纠正：
       ① 群评论策略存储要的是 `executionTarget` + `schemaProber`（不是 `schemaEnsurer`），
          且必须带上两个 legacy env 回落，否则一次拆进程会把运营早先配的窗口悄悄改回默认。
       ② 1.3 写的「探活口先留占位」没有执行：占位无论回什么都是编的（回 ok=放行不探活的写，
          回 model_unavailable=说用户输错了）。改为与批次 3.1 同批落真探活，无中间态。 -->

## 2. aidcp-api — B 类：单体已有 api 分支，照搬

- [x] 2.1 待审稿件正文编辑 `publishDraft`：照搬单体 `mode === 'api'` 那三个方法（编辑走本进程发布台账、活版本走台账读、已决判定走审批读客户端）。
- [x] 2.2 发布预览变更通知 `notifyPublishPreviewChanged`：照搬 api 分支（经本进程的预览产出口推送；产出口缺席时按单体口径记一行告警，不静默）。
- [x] 2.3 客户离场卡回调 `onClientOffboardCreated`：确认其产出方在本进程，装上；确认不了则记入具名缺席表并写清后果。
  <!-- 产出方在本进程（客户鉴权面已有同一条派发客户端，只是面板这侧没接）。edgeId 由属主进程解析，
       本进程只给 accountId；accountId 为 null = 已受理未物化，MUST NOT 猜一个。 -->

## 3. aidcp-content — C 类：内容域窄口

- [x] 3.1 模型探活窄口：内容侧注册模型探活路由，出参判别式，分类与单体 `probeModelResult` 逐字同源。
  <!-- aidcp-content 3362619（rebase 后 0b92cfd）。路由名走内部 HTTP 的 route 名（`model-probe/probe`），
       不是自拟的 REST 路径。**注册点特意放在 publish-generation 之后**：验收 `curated content absence
       cannot disable persona or publish` 用「精选库守卫到 publish-status 之间不许出现 return」当代理，
       本回调体内的 return 是内层函数的、与那条不变量无关，但会把代理打成误报。挪出该区间比放宽守卫便宜。 -->
- [ ] 3.2 用量成本窄口：注册用量查询 + 账单价刷新两条，形状取自面板既有两个方法。
- [ ] 3.3 精选库窄口：注册列表 / 筛选面 / 删单条 / 清空壳行 / 读单行五条（`account_id` 一律进 WHERE 防越权，跨进程后这条 MUST 由属主侧保证，MUST NOT 交给调用方自觉）。
- [ ] 3.4 FB 发帖图片窄口：注册列表 / 上传 / 重排 / 改组 / 删组五条；**上传是大载荷**（单张原图上限 10 MiB、Base64 后约 14 MiB），跨进程连接的体积上限与超时须显式设置，MUST NOT 用默认值撞上限后回一个看不出原因的失败。

## 4. aidcp-automation — C 类：自动化域窄口

- [ ] 4.1 验证码协助窄口：注册面板五个端点所需的方法面（含短命图像字节；**图像 MUST NOT 落日志**，跨进程后这条约束在两侧都要成立）。
- [ ] 4.2 授权前置 `preflightApprovePublish` 窄口。
- [ ] 4.3 下发在途 id `publishDispatcher.getInFlightRecordIds` 窄口；若既有同步读镜像已覆盖，改为复用镜像并在本文件记明，不新开通道。

## 5. aidcp-cloud — 派生源：跨进程三件套与契约

- [ ] 5.1 新增 `src/transport/*-http.ts`：探活 / 用量 / 精选库 / FB 发帖图片 / 验证码协助 / 发布下发前置，各含路径常量 + 服务端注册 + 类型化客户端。路径常量**只此一份**。
- [x] 5.2 面板契约 `src/panel/types.ts` 新增运行时能力名册 `PANEL_CAPABILITY_KEYS`，并用 `Exclude<keyof PanelDeps, 名册项> extends never` 钉死完备性。
- [x] 5.3 新增覆盖断言工具：入参为 deps 对象 + 本进程具名缺席表，缺项即抛。
- [x] 5.4 单体自身照旧编译通过、行为不变（新增的是 api 模式装配与新窄口，单体路径不改）。
  <!-- aidcp-cloud 1750f6d。含 boundaries:refresh 生成物（两个新文件各自 inherit 到 api / automation）。
       cloud 全量 4244 用例 0 失败。 -->
- [x] 5.5 控制仓 `scripts/sync-split-repos` 的 `TRANSPORT_MEMBERS` 登记新增 transport 文件；跑一次不带参数的对账确认六仓全绿。
  <!-- 控制仓的这处改动被并发 session 的 `git add -A` 卷进了 5446beb4（内容无误、归属记在这里）。
       aidcp-transport f4b1e2c；三个消费仓 pin 同批抬到它（api e09079b / automation ce7a292 / content 33b8ecb）。
       六仓对账全绿（唯一「差异」是两个组装根，本来就只报不改）。 -->

## 6. aidcp-api — 接线跨进程客户端 + 打开写路径

- [ ] 6.1 装上内容侧四族客户端：`tokenUsage`、`billingPriceRefresh`、`curatedContent`、`curatedActions`、`facebookPublishMedia`。
- [ ] 6.2 装上自动化侧：`captchaAssist`、`preflightApprovePublish`、（如未复用镜像）`publishDispatcher`。
- [x] 6.3 三处写路径接真探活客户端（无占位中间态，见 1.8 注）。**三处共用同一个探活口。**
- [x] 6.4 装上覆盖断言（5.3），填本进程具名缺席表。
  <!-- 缺席表当前 13 条，逐条写了「为什么不装 + 后台上的表现 + 归哪个批次」。
       断言在启动期跑：api 起得来本身就是这张表与实际装配一致的证据。 -->

## 7. rolePromptPreview — D 类：分域拼装

- [ ] 7.1 坐实三段依赖各自的属主：预览角色清单（自动化）、人设（接口）、发布 / 配图渲染闭包表（内容）。
- [ ] 7.2 各域各出一段窄口，接口侧只做拼装。**MUST NOT 把渲染闭包表复制进接口仓**——第二份实现在行为测试上原理不可见。
- [ ] 7.3 若拼装成本与收益不成比例（该页只是只读预览），改为记入具名缺席表 + 登记 backlog，并在本文件写清判断依据与用户可见后果。**不得静默留 503。**

## 8. 测试

- [x] 8.1 覆盖断言的单测：喂一个少装一项且未具名的 deps，断言抛错并指名；喂具名缺席的，断言放行。**闸恒真通过就没人能证明它还在**——用例必须包含违规输入。
- [x] 8.2 能力名册完备性的编译期判据用例（漏项即红）。
- [x] 8.3 探活不可用时三处写路径均拒写、且原因可区分于「模型不合法」「密钥缺失」。
  <!-- 逐值断言状态映射（404/503/400），并断言 probe_unavailable ≠ model_invalid ≠ provider_key_missing。 -->
- [ ] 8.4 精选库跨进程后账号隔离仍由属主侧保证的用例。
- [ ] 8.5 三仓 `npm run test:acceptance` → `npm test` → `npm run typecheck` 全绿；边界门禁 `boundaries` 相关用例不退化（豁免清单只准下降）。

## 9. 集成与部署

- [x] 9.1 四仓各自 rebase 到最新 `master`、跑完 8.5、ff 合并。
  <!-- rebase 是必要的：并发 session 在本 change 开工期间往 api / content master 各推了提交。
       rebase 后重跑 typecheck + acceptance 才合。 -->
- [x] 9.2 `scripts/sync-split-repos` 对账全绿（含两个共享包的 pin）。
- [x] 9.3 部署 dev（2026-08-05 14:2x）。**只发 content + api，没发 automation**：
  automation 这次只同步了一个它并不 import 的 transport 文件 + pin，重启它会白白打断边缘连接。
  <!-- 序列：deploy-target dev --check → 两槽备份（tar + .env）→ git archive 快照 rsync（不从工作区推）
       → 删 node_modules/aidcp-{kernel,transport} + npm install → **ECS 上两槽各跑 typecheck，全 CLEAN**
       → content 先、api 后重启。三服务 active、NRestarts 全 0、六端口全在、isales 未碰。
       api 起得来即证明装配对账门通过。 -->
- [x] 9.4 **逐条复打**顶部那张缺口表（dev，带真 token；8090 直打与 8088 外网口各打一遍）。
  <!-- 200：/api/config/model、/api/config/interaction-permissions、/api/roles、/api/categories、
            /api/hot-lead-config、/api/facebook/groups/comment-policy
       仍 503（具名缺席、非失败）：/api/llm-usage、/api/curated/*、/api/captcha-assist/*、
            /api/roles/:id/prompt —— 分别待批次 3 / 3 / 4 / 7。
       **写路径端到端实打**：同值回写 200（跨进程真探活跑通）；喂一个不存在的模型名回 400 model_invalid
       且配置未被写坏（复读仍是原值）。这两条一起才证明探活既没被绕过、也没把好值改坏。 -->
- [ ] 9.4a **OL 同样受影响，未修**（2026-08-05 12:59 OL 也切成三派生服务，钉的是切流前的发布分支）。
  实测 OL 的 `/api/config/model`、`/api/roles`、`/api/llm-usage` 同样 503。
  OL 部署须用户明确要求并走发布分支，本 change 不自行执行。
- [ ] 9.5 后台真人走一遍：设置页、角色页、用量成本、精选库、配额页热帖引流、FB 群策略、验证码协助页。真机项收拢进 `docs/real-machine-acceptance-backlog.md`。

## 10. 收尾

- [ ] 10.1 回写 `deploy-derived-services-to-dev` 的 task 6.2：指向本 change，写明它本该抓住这批。
- [ ] 10.2 `openspec validate restore-panel-capability-wiring --strict` 通过后归档。
