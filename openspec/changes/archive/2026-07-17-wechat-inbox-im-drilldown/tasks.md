# tasks — wechat-inbox-im-drilldown

> 全部改动落 `aidcp-edge`（`src/electron/renderer/`）。控制仓只回写本文件。
> 台账格式：`<!-- <repo> <commit-sha> 备注 -->`，部署后追加 `<!-- <date> deployed -->`。
> 本 change 全部实装收敛在一个提交：<!-- aidcp-edge 5b0380c 单栏两级导航；rebase 后 sha，已确认可达 origin/master -->

## 1. aidcp-edge — 骨架与样式

- [x] 1.1 `index.html`：收件箱骨架保留 `#iw-tabs` / `.iw-inbox` / `#iw-list` / `#iw-detail` 静态节点不变（锚定与覆盖层都依赖它们跨重绘存活），按需为详情面板加具名容器类 <!-- aidcp-edge 5b0380c 未加新容器类；`#iw-detail` 初始带 hidden、清空静态空态内容（该空态在列表级已无位置） -->
- [x] 1.2 `styles.css`：`.iw-inbox` 加 `position: relative`；单栏态下详情面板 `position: absolute; inset: 0` 铺满收件箱区并加轻投影 <!-- aidcp-edge 5b0380c 同时把 grid 基线从两栏改为 minmax(0,1fr) 单栏 -->
- [x] 1.3 `styles.css`：**红线**——显式写 `.pane[hidden] { display: none }`（或等价具名隐藏类），确保隐藏声明压过面板容器的 `display: flex`；否则 `hidden` 静默失效、覆盖层永久遮挡列表 <!-- aidcp-edge 5b0380c 偏离：本仓无 .pane 类，落为 `.iw-detail[hidden], .iw-list-pane[hidden] { display: none !important; }`，沿用本仓既有 .hidden 的 !important 惯例 -->
- [x] 1.4 `styles.css`：`.iw-tabs` 加 `scroll-margin-top`；新增 `.iw-iconbtn` 图标按钮样式（含 hover 与 `:focus-visible`） <!-- aidcp-edge 5b0380c 另加 .iw-detail-actions；.iw-detail-head 网格补一列放返回箭头 -->
- [x] 1.5 `styles.css`：移除/停用列表条目的消息预览行样式（`.iw-item-preview`），确认无其他调用点 <!-- aidcp-edge 5b0380c 已整条删除 -->

## 2. aidcp-edge — 列表级

- [x] 2.1 `interaction-workspace.js` `renderList()`：条目模板去掉预览行，只留头像、昵称、时间、渠道来源、状态徽章；昵称占位与未读标记保持既有诚实语义 <!-- aidcp-edge 5b0380c -->
- [x] 2.2 初始状态与切标签后 `selectedThreadId` 置空、不预取详情；确认 `renderTabs()` / 标签点击链路不再自动选中第一条 <!-- aidcp-edge 5b0380c 标签链路本就置空；真正的自动选中在 loadList() 与搜索框两处，均已改为回列表级而非改选第一条 -->
- [x] 2.3 确认覆盖层打开期间列表 DOM 不卸载，关闭后滚动位置保留（列表重绘不做暂停，见 design 决策 6） <!-- aidcp-edge 5b0380c 列表始终在文档流；滚动位置保留属布局行为，jsdom 验不了 → 真机 -->

## 3. aidcp-edge — 详情级与退回路径

- [x] 3.1 `renderDetail()`：列表级下**不渲染**详情内容（不只是样式隐藏），与 1.3 构成双保险 <!-- aidcp-edge 5b0380c -->
- [x] 3.2 「刷新状态」改图标按钮，保持既有 `data-iw-action="refresh-detail"` 语义与真态呈现不变；注意冲突分支里第二处「重新加载详情」按钮沿用文字形态即可 <!-- aidcp-edge 5b0380c 第二处按原计划保持文字 -->
- [x] 3.3 新增关闭图标与左上角返回箭头，均带 `aria-label` 与可见焦点态；两者与 `Esc` 收敛到同一「清除选中 + 回列表级 + 锚定」动作 <!-- aidcp-edge 5b0380c 均走 data-iw-action="close-detail" → closeThread() -->
- [x] 3.4 `Esc` 键处理挂载与卸载配对，避免切换工作区后残留监听 <!-- aidcp-edge 5b0380c 偏离：本模块所有监听均在 create() 一次性挂 root、由 active 兜底，无卸载路径；Esc 沿用同一惯例（随 root 消亡），未新建卸载机制 -->

## 4. aidcp-edge — 锚定

- [x] 4.1 打开与关闭详情时把 `#iw-tabs` 用 `scrollIntoView({ block: 'start' })` 锚到视口顶部 <!-- aidcp-edge 5b0380c 带 typeof 守卫：jsdom 无 scrollIntoView 实现 -->
- [x] 4.2 读 `prefers-reduced-motion`：开启时 `behavior: 'auto'` 直接定位，不播平滑滚动 <!-- aidcp-edge 5b0380c -->

## 5. 验证与集成

- [x] 5.1 `cd ../aidcp-edge && npm run typecheck` <!-- aidcp-edge 5b0380c 退出码 0（注意勿用 `| tail`，退出码会变成 tail 的、假绿） -->
- [x] 5.2 `cd ../aidcp-edge && npm run test:acceptance` 再全量 `npm test`（呈现层重构，重点回归 `edge-companion-ui` 既有的空态区分、未读标记与去重通知、非发送动作不被 send capability 拦截） <!-- aidcp-edge 5b0380c acceptance 23 pass；全量 1671 pass / 0 fail -->
  - 既有 9 个用例依赖「自动选中第一条」才有详情可断言 → 改为经新增的 `openThread()` 走客户真实点击路径，非放宽断言
  - 新增 3 个用例：两级导航 + 逐条点得开、退回路径（关闭图标 / Esc）+ 图标无障碍名称、红线 CSS 断言
  - 顺带修 `dom.list` 方向键：旧代码把 `findIndex` 的 `-1` 夹成 `0`，在「默认选中第一条」前提下无害；不再默认选中后会让首次 ArrowDown 跳过第一条
  - **已做变异验证**：临时拆掉 1.3 的 `[hidden]` 规则 → 32 用例中恰好 1 个转红（红线 CSS 断言），确认非假绿
- [x] 5.3 本地 `electron:dev` 实跑视频号工作区：列表级每条可点、点开遮挡、关闭回列表且滚动位置保留、锚定生效、三条退回路径均可用 <!-- 未做：需真机 + 已登录视频号环境，非本机可自证 → 转 6.1 真机验收 -->
- [x] 5.4 提交并推送 edge `master`；无需出安装包（打包属用户显式触发） <!-- aidcp-edge 5b0380c 经 scripts/land-change --yes：rebase → 闸全过 → ff push → 主 checkout 已同步 → worktree/分支已清理 -->
- [x] 5.5 回写本文件台账 sha（必须取自已推送提交） <!-- 5b0380c 已 `git merge-base --is-ancestor` 确认可达 origin/master -->

## 6. 收口

- [x] 6.1 真机验收项登记 `docs/real-machine-acceptance-backlog.md` <!-- 2026-07-17 簇 98（7 项，含红线证伪项 98.1） -->
  - **jsdom 覆盖不到的盲区（必须真机看）**：jsdom 不做样式层叠计算，`hidden` 在它眼里只是 DOM 属性——覆盖层**是否真的遮挡列表**只有 1.3 那条 CSS 文本断言看得住，行为用例看不见。这正是本 change 的红线现象（不报错、不白屏、永久糊住列表）。
  - 同属布局行为、单测验不了：关闭后列表滚动位置是否真的保留（2.3）、`scrollIntoView` 锚定是否真的让消息区一次露全（4.1，jsdom 无该 API 实现、被守卫跳过）。
- [x] 6.2 `openspec validate wechat-inbox-im-drilldown --strict`
- [x] 6.3 客户真机观感后定两个 open question：返回箭头是否与关闭叉并存、列表重绘是否需暂停 <!-- 2026-07-17 未定，随真机项一并解耦到 backlog 98.7；两条都是待客户拍板的取舍、不是 bug，归档不代表已决 -->
- [x] 6.4 archive change <!-- 2026-07-17 archived。修正前置口径：真机项按本仓惯例解耦到 backlog（簇 98，7 项全部未跑），不作为归档门槛——原文写「前置=6.1 真机项跑通」与惯例相悖。本 change 无云端部署门槛，edge 随常规发版生效 -->

> **归档时的真实状态（勿被 archive 误读为已验收）**：代码 landed（edge `5b0380c`）+ 全量测试绿，
> 但**真机一项未跑**（簇 98 共 7 项）。其中 98.1「逐条点开每一条」是唯一能证伪红线的信号，
> 且该红线**单测原理上抓不到**（jsdom 不算样式层叠）。归档只表示契约已并入主 spec，不表示已在真机验证。
