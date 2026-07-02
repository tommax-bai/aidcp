<!-- 状态注记（2026-07-02，已上线）：
  - 功能已全量部署上线并验证：
    * CLOUD 后端：setGroupLabel + `PUT /api/accounts/:id/group-label` + accountAttr 装配**已在 ECS 上运行**
      （并发方 21:59 rsync 共享工作树时连带带上我的改动，服务 22:00:57 重启加载；源码 grep 确认在位、
      1053/1053 全绿 + 27/27 acceptance 红线过 + typecheck 净）。我**未重复部署 cloud**（已在，避免与并发部署相撞）。
    * CONSOLE 前端：本人 build（HEAD 1a84054 clean，含 group-label/thinking/alert-resolution 三前端）→ 备份
      console.bak.20260702-220510.tar.gz → rsync dist/ 到 /opt/aidcp/console（**无 --delete**，intro.* 保全）→
      验证 index.html 指向新 bundle index-ChRoxtSX.js（含我的分组 UI）、8088 HTTP 200、/api/version 经 nginx 200、
      cloud 服务未受扰 active。绝不碰同机 isales（inactive）。
  - CLOUD git 提交仍未做（与现状无关的独立事项）：cloud 工作树多 change（group-label + thinking + alert-resolution）
    并行交织于 panel/types.ts、panel-server.ts、server.ts，无交互式 add -p 无法只切我的部分。→ 待并行方 cloud 改动
    先 commit 后，这 3 文件 diff 只剩我的 hunk，我再干净提交 group-label cloud。CONSOLE 我的部分已提交（b9512a3）。 -->

## 1. aidcp-cloud — 账号存储单写方法

- [x] 1.1 `AccountStore` 接口新增可选 `setGroupLabel(accountId, label): Promise<SetGroupLabelResult>`；新增导出判别联合类型 `SetGroupLabelResult`（`{ok:true,groupLabel}` / `{ok:false,reason:'account_not_found'|'retired_account'}`）<!-- aidcp-cloud 未提交 src/account-store.ts（clean-mine，无 WIP 交织） -->
- [x] 1.2 `PgAccountStore.setGroupLabel` 实现：`UPDATE accounts SET group_label=$2 WHERE account_id=$1 RETURNING group_label`；入参 `trim`（trim 后空 → 写 NULL）；0 行 → `{ok:false,account_not_found}`（不 seed 造行）；拒退役 `RETIRED_ACCOUNT_ID` → `{ok:false,retired_account}`（不落库）；防御性 64 长度上限 <!-- aidcp-cloud 未提交 src/account-store.ts -->
- [x] 1.3 单测（account-store）：写值 trim 后回读一致 + UPDATE-only（断言不含 INSERT）；空/空白/null → NULL 清空；不存在 → account_not_found 可区分；`default` → retired_account 且零 SQL <!-- aidcp-cloud 未提交 test/account-store.test.ts（4 用例全过） -->

## 2. aidcp-cloud — 面板 API 写路由

- [x] 2.1 `PanelDeps`（`src/panel/types.ts`）新增可选 `accountAttr.setGroupLabel`，注释说明经账号存储单写、不碰风控/协议/边缘 <!-- aidcp-cloud 未提交 src/panel/types.ts（**与 thinking WIP 交织**） -->
- [x] 2.2 `panel-server.ts` 新增 `PUT /api/accounts/:id/group-label`：JWT 已覆盖；body `{groupLabel}`（''/null/缺省=清空、非 string/null → 400 invalid_group_label）；未注入 dep → 503；成功回真态 `{accountId,groupLabel}`；not-found → 404；retired → 400 reason <!-- aidcp-cloud 未提交 src/panel/panel-server.ts（**与 thinking WIP 交织**） -->
- [x] 2.3 `src/server.ts` 注入 `accountAttr`（守卫：仅 `accountStore.setGroupLabel` 存在时注入，否则路由 503） <!-- aidcp-cloud 未提交 src/server.ts（**与 thinking WIP 交织**） -->
- [x] 2.4 单测（panel-server）：未注入→503；成功回真态；清空；not-found→404；`default`→400 retired_account；坏类型→400；缺 JWT→401 <!-- aidcp-cloud 未提交 test/panel-server.test.ts（用例全过） -->

## 3. aidcp-console — 前端可编辑「分组」列

- [x] 3.1 `AccountsTable.tsx`：「分组」列传 `onEditGroup` 时改为点击即编辑单元格（复用 `.editable-cell`「点击编辑」+ AntD `Input`，回车/失焦 `commit`、editingId 守卫幂等）；新增**可选** `onEditGroup?(accountId, label|null)` prop——不传退回纯文本 <!-- aidcp-console b9512a3 -->
- [x] 3.2 `AccountsPage.tsx`：新增 `useMutation` 打 `apiPut('/api/accounts/:id/group-label')`；**非乐观**——`onSuccess` 后 `invalidateQueries(['accounts'])` + 诚实 toast（设置/清除可辨）；经 `onEditGroup` 传入 `AccountsTable` <!-- aidcp-console b9512a3 -->
- [x] 3.3 `DashboardPage.tsx` 只读账号表**不传** `onEditGroup` → 保持纯文本、零回归（已核对：其调用仅 `accounts/loading/severitySorted`） <!-- 无需改动，现状即满足 -->
- [x] 3.4 复用 `styles/app.css` 既有 `.editable-cell`（悬停高亮 + pointer）；空值仍渲染破折号占位、单元格 `title="点击编辑"` <!-- 无需改样式，既有类满足 -->

## 4. 校验 / 回归 / 部署

- [x] 4.1 cloud：`npm run typecheck` 全绿；我的用例 targeted 全过（account-store 4 + panel-server group-label 1，合 22/22）。全量 `npm test` = 1048 tests / 1047 pass / **1 fail**，唯一失败在 `role-config-store.test.ts`（thinkingMode）——**并行 WIP，非本改动** <!-- 本改动零回归；红线 AC-* 全过 -->
- [x] 4.2 console：`tsc --noEmit` 对我的两文件零错误；`npm run build` 当前被 `RolesPage.tsx`（thinking WIP，未用变量 + 类型不符）阻断——**并行 WIP，非本改动** <!-- 我的文件 clean，构建阻断待 WIP 收尾 -->
- [x] 4.3 `openspec validate editable-account-group-label --strict` 通过
- [~] 4.4 端到端验证：自动层已过（cloud 源码在位 + 服务 active/8787+8090 监听 + 1053/1053 + 27/27 红线 + typecheck；console 8088 HTTP 200 + /api/version 经 nginx 200 + 新 bundle 含分组 UI）。**浏览器点选流**（登录后台→点「分组」→输入→保存→刷新持久→清空显破折号→退役账号被拒）待用户在真机点通（需面板登录凭据，我不取密） <!-- 自动可达性 + 单测已证；人工 UI 点通留用户 -->
- [x] 4.5 部署：**已上线**——CLOUD 后端并发方部署已连带带上并运行（我未重复部署，避免撞车）；CONSOLE 本人按安全序列部署（备份 console.bak.20260702-220510 → rsync 无 --delete → 验证 200 + 新 bundle + intro 保全 + cloud 未受扰 + 不碰 isales）。<!-- cloud git 提交待并行方先落后再干净补，见顶部注记 -->
