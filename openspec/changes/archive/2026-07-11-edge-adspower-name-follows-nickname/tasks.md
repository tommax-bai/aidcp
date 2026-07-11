# Tasks — edge-adspower-name-follows-nickname

> 纯 edge-only（全部落 `aidcp-edge`，无 cloud / 无 ECS）。实装前先 rebase 到最新 `master`，避开与 `self-contained-ads-runtime` 在 `ads-create-flow.cjs` / `main.cjs` 的热点重叠。
> 实装完成：edge master `7b3cea4`（rebase 到 `da5a6f3` 后 ff 合并）；与并发落地零文件重叠。全量 edge 1009/1009 + acceptance 16/16 + typecheck 全绿。

## 1. aidcp-edge — 写客户端改名封装（allowlist 窄放宽）

- [x] 1.1 `src/electron/ads-write-api.cjs` 新增 `renameProfile({ userId, name })`：只构造 `{ user_id, name }` 两键 body 经 `post('user/update', …)`；缺 userId / 空 name 诚实返回 `{ ok:false }`，绝不发出。 <!-- edge 7b3cea4 renameProfile 两键封装（空/纯空白 name 拒发） -->
- [x] 1.2 导出 `renameProfile`（与 `updateProfileProxy` 并列），复用同一 ≥1s 串行节流单链。 <!-- edge 7b3cea4 走 post() 复用同一 throttledRequest 单链 -->
- [x] 1.3 更新回归断言：改代理封装 body 仍严格两键 `{ user_id, user_proxy_config }`；新增改名封装 body 严格两键 `{ user_id, name }`，两者互不混入 `fingerprint_config` / `remark` / 对方键；生命周期端点仍直接抛错的断言保持不变。 <!-- edge 7b3cea4 test/electron/ads-write-api.test.ts 新增 renameProfile 两键断言（硬塞 proxy/fingerprint/remark 进不了 body）+ 缺参拒发；原 allowlist 抛错 / 改代理两键断言不变 -->

## 2. aidcp-edge — 建号不写死模板名

- [x] 2.1 `src/electron/ads-create-flow.cjs`：`createProfile` 调用不再传 `name: templateKey`（标准建号路径 name 缺省 → AdsPower 默认命名）；FB 批量导入路径的显式 name 保持不动。 <!-- edge 7b3cea4 createProfile 调用改传 name（缺省 undefined），createProfile 内 `if(name)` 才下发 -->
- [x] 2.2 建号回执 `name` 字段改为「实际写入的名字或空」，`main.cjs` 的 `ads:createEnv` 回执与新建即选中入册允许空名（回归前行为）。 <!-- edge 7b3cea4 createEnvironment 返回 name: name||''（标准路径空、FB 路径带回显式名）；FB 单账号导入自动选中回执 name 不变 -->
- [x] 2.3 更新 `ads-create-flow` 相关用例：标准建号不再断言回执 name==templateKey；FB 导入路径仍断言显式 name 原样下发。 <!-- edge 7b3cea4 test 改断言 r.name==='' + body.name===undefined（标准路径）；FB 导入 name 透传断言保留 -->

## 3. aidcp-edge — 登录读昵称后渐进改名

- [x] 3.1 `src/electron/main.cjs` 身份事件分支（`evt.account`，约 1852-1855）：当 `source` 表明为真实平台昵称、且该环境当前 AdsPower 名与昵称不一致时，经 `renameProfile` 改名；名已一致则跳过（幂等去抖）。 <!-- edge 7b3cea4 身份分支挂 maybeRenameEnvToNickname（fire-and-forget）；helper 内 nick===handle.name 跳过 -->
- [x] 3.2 改名失败（不可达 / `code≠0` / 撞限速）诚实降级：保持原名、记一次可观测日志、不重试风暴、不阻塞该环境浏览闭环；下次身份事件再试。 <!-- edge 7b3cea4 maybeRenameEnvToNickname try/catch 吞错 + console.warn 观测；不 await、不改会话 -->
- [x] 3.3 改名成功后同步本地 handle/花名册名（令下次显示与 `user/list` 回填一致），单写、不与 `reconcileRosterNames` 双落盘竞态。 <!-- edge 7b3cea4 成功后 handle.name=nick + status.account.name=nick；renamingTo 标记防在途重发 -->

## 4. aidcp-edge — 左栏显示名优先真实昵称

- [x] 4.1 显示优先级改为：真实昵称（`status.account` 且 source 为平台真实昵称）→ 花名册/环境名 → 「环境 …末4位」。优先把该逻辑下沉进纯函数 `src/electron/renderer/ui-logic.js` 的 `railDisplayName`（便于单测）；`renderer.js` 的 `railDisplayName`（原 1198-1199）随之委托或对齐。 <!-- edge 7b3cea4 ui-logic.js 新增纯函数 railDisplayName（source!=='env' 为真实昵称）+ 导出；renderer.js railDisplayName 委托 uiLogic、内联兜底逐位一致 -->
- [x] 4.2 确保「实时名回填把已知昵称环境的花名册名刷成模板名」时，左栏仍显示昵称、不回退模板名。 <!-- edge 7b3cea4 真实昵称档优先于 row.name，回填模板名不遮蔽；测试锁此回归场景 -->

## 5. aidcp-edge — 测试（关键行为少数用例，桩验不了的转真机）

- [x] 5.1 单测：改名封装 body 严格两键 + 改代理封装不被污染 + 生命周期端点仍抛错（1.3 的断言）。 <!-- edge 7b3cea4 ads-write-api.test.ts -->
- [x] 5.2 单测：`railDisplayName` 显示优先级三态（昵称优先 / 回落环境名 / 末4位兜底；含「回填模板名不遮蔽昵称」回归场景）。 <!-- edge 7b3cea4 ui-logic.test.ts 三用例 -->
- [x] 5.3 单测：建号不写死模板名（标准路径回执空名 + body 无模板名）；FB 导入路径 name 透传。 <!-- edge 7b3cea4 ads-create-flow.test.ts；改名去抖/降级为主进程 fire-and-forget 逻辑、按 test-restraint 由真机簇 57.4/57.5 坐实、不桩 main.cjs -->

## 6. aidcp-edge — 验证与收口

- [x] 6.1 `cd ../aidcp-edge && npm run test:acceptance && npm test && npm run typecheck` 全过。 <!-- edge 7b3cea4 acceptance 16/16 + 全量 1009/1009 + typecheck 绿（rebase 后复跑亦绿） -->
- [x] 6.2 登记真机验收 backlog（`docs/real-machine-acceptance-backlog.md` 新簇）：① AdsPower `user/update` 带 `name` 改名生效；② 建号不传 name 时 AdsPower 默认命名形态；③ 存量环境登录后左栏与 AdsPower 名逐步变昵称；用 tom 分组测号，运营机 pull master 后核。 <!-- aidcp 簇 57（57.1~57.6）已登记 docs/real-machine-acceptance-backlog.md -->
- [x] 6.3 提交 + push `master`；本 change 不触发 dev/ECS 部署（edge-only），客户端改动随下次安装包/`electron:dev` 生效。 <!-- edge master 7b3cea4 已 push；edge-only 无部署 -->

## 7. 归档

- [x] 7.1 全部 task 勾选、`openspec validate edge-adspower-name-follows-nickname --strict` 通过后 archive（delta 合并进 `openspec/specs/adspower-environment-provisioning` 与 `edge-fleet-console`）。 <!-- aidcp 归档，见 openspec/changes/archive/2026-07-11-edge-adspower-name-follows-nickname/ -->
