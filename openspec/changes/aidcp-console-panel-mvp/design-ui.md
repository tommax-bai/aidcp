# AIDCP Console — MVP UI 设计文档（最终稿）

> 范围：AIDCP 内部运营管理后台（3–10 个小红书账号 / 1–5 人运营）。非公开 SaaS。
> 事实源：`docs/product-dashboard.md §1-2`（IA + 逐页 JSON）＋ `openspec/changes/aidcp-console-panel-mvp/design.md`（D1–D11 + 红线）＋ AntD v5 设计语言 ＋ `/api/version`（运行时 enum/颜色源）。
> 栈（契约 §3 固定，不另议）：React + Vite + TS、AntD、`echarts-for-react`、TanStack Query、react-router；独立新仓 `../aidcp-console`，Nginx 静态托管，反代 `/api` + `/ws`（单一全局 panel-WS）。

---

## 0. Figma 决策

**结论：skip-figma（不引入、也不做轻量 Figma）。**

**理由（四条要害）：**

1. **契约文档已是 wireframe 级**。`docs/product-dashboard.md §1-2` 同时给了 IA 树、逐页区块拆分、以及每页的具体 JSON 载荷（dashboard summary / account 字段 / monitor 帧 / content 队列）。再画一份 Figma 只会以更低信息密度重编码同一份事实，并立刻开始与 spec 和 API DTO 漂移。
2. **AntD 本身就是设计系统**。栈一旦由契约固定，间距 / 配色 / 字体 / Table / Form / Badge / Tag / Steps 就都定了。在 Figma 里临摹 AntD 组件是转录、不是设计，是公认的时间黑洞——只有专职设计团队才划算。
3. **无专职设计师、1–5 人团队**。Figma 的核心 ROI 是「设计师↔开发」交接边界与异步签字。同一两个人既写 spec 又写代码时，这条边界根本不存在。
4. **本 UI 的难点不是视觉而是状态正确性不变量**：两个独立风控徽标、写操作不乐观、refused-vs-success、`recorded, 0 edges online`、归因待补 banner、online/stale/offline 三态、运营暂停 vs 验证码暂停。Figma 既表达不了也强制不了这些——它们活在代码、类型和红线里。一张漂亮 mockup 反而会把 frozen 态或 refused 写渲染成 happy path，主动误导。

**何时才值得：** 加入专职设计师 / 团队超过 ~5 人且出现真实交接边界；console 从内部工具升级为外部 / 多租户产品（像素与客户签字成为验收标准）；出现 AntD 覆盖不好的全新非表格界面（如 V2 Analytics 阈值带图的交互需先想清再写）——此时一张**一次性** Excalidraw 草图即可，仍不必维护 Figma 工程；需要非技术 stakeholder 异步签字时，跑起来的 app 截图 / 短录屏比 Figma 更便宜。

**替代流程（即本文档采用的）：**
- 把 spec 当 wireframe，直接按 `product-dashboard.md §1-2` 的 IA + 区块 + 逐页 JSON 实现，让数据结构驱动布局。
- 先用 AntD 布局原语搭薄 code-first 原型（Layout 外壳 + 顶栏全局筛选 + 左导航 → 各页用 Table/Descriptions/Tag/Badge/Steps + mock 数据打桩），再接真 `/api`。这个原型就是产品本身。
- **以「UI 状态清单」替代设计稿做评审件**：每屏枚举 loading / empty / error + 红线态（两个独立徽标；写按钮 loading→round-trip；refused-vs-success；`recorded, 0 edges online`；归因待补 banner + `—` 列；online/stale/offline；运营暂停 vs 验证码暂停）。
- 用 `ConfigProvider` 一次性钉死 theme token，所有 enum 值 + 颜色从 `/api/version` 拉（D11），让视觉一致性由代码而非维护一份设计文件来保证。
- 保留一个极小 `components/` kit（`RiskStatusBadge` / `QuotaTierBadge` / `EdgeOnlineState` / `AttributionPendingBanner` / `HonestWriteResult`），把红线编码一次、各处复用。

**设计事实源优先级（唯一权威链）：**
(1) `docs/product-dashboard.md §1-2` IA + 逐页 JSON →
(2) `design.md` D5/D8/D9/D10/D11 + 红线 UI 约束（语义正确性）→
(3) AntD v5 设计语言（一切纯视觉）→
(4) `/api/version`（运行时 enum 值 + 颜色，防三处漂移）。
跑起来的 React+AntD app 即最高保真产物，不存在会漂移的第二份设计文档。

---

## 1. 设计原则

1. **这是日用型内部 ops 工具，不是产品官网**。一切服务于「5 秒答出系统健康吗 / 哪个账号需要我」。视觉中性（AntD 默认蓝品牌色），密度优先，无营销式留白。
2. **AntD 即设计语言**。不自创视觉规范；间距 / 配色 / 字体走 AntD token。唯一自定义层是把红线封装成的几个 typed 组件（见 §7）。
3. **红线即设计约束，不是品味问题**。每屏必须 honor：
   - **两个独立徽标**：风控 STATUS 与 QUOTA-TIER 是两个独立字段，永远两个 Tag，绝不合并成一个徽标 / 下拉（D5）。
   - **写操作不乐观**：按钮 → loading → round-trip → 渲染服务端真态。绝不在服务端确认前显示成功（D10）。
   - **诚实结果**：审批返回 `{written}` 或 `{alreadyDecided:<v>}`，**绝不 `published`**（D8）；到达 0 在线 edge 的写须说 `recorded, 0 edges online` 而非 `done`；状态机拒绝的迁移渲染为 `refused`、明显区别于成功（V1）。
   - **归因待补**：每个按账号切片在 MVP 标「全部账号 / 归因待补」（banner + 列内 `—`），绝不把全局数字冒充成按账号（D3/D4）。
   - **edge online = inMap AND staleness 校验**：渲染 online / stale / offline 三态，绝不渲染会撒谎的二元（D9）。
   - **运营暂停（durable, `accounts.status`）≠ 验证码传输暂停（`pausedEdges`）**：不同词 / 图标，绝不共用一个含糊「paused」徽标。
4. **YAGNI 贯穿**。无 Redux（TanStack Query 即 store）、无 monorepo、无虚拟化除非实测卡顿、无 PageHeader / 无 Cascader（见 §7 修正）。

---

## 2. 设计系统 token

> 单一 enum / 颜色源 = console `src/types/aidcp-enums.ts`（镜像 cloud `src/risk/types.ts`）+ 对 `/api/version` 断言（D11）。下方颜色为 AntD v5 preset 名，不在页面硬编码偏离调色板。

### 2.1 风控 STATUS 徽标族（warm，filled 实心 Tag，前缀 `Status:`）

| value | AntD color | 含义 | 形态 |
|---|---|---|---|
| `normal` | `green` | 健康，按档位发布允许（RiskController 状态机单写，risk-control §7.1） | filled green + 盾/心跳图标 |
| `warned` | `gold` | 疑似限流，强制降保守档 ×0.7、warned 窗口内暂停发布，7d 无新信号自动回 normal（→ alert P1/P2） | filled gold |
| `restricted` | `volcano` | 确认限流，仅浏览、停全部互动、禁发布，≥3d 干净后回 warned（时间门控，拒绝须渲染 refused）（→ P0） | filled volcano（配文字以区别 frozen-red / P0-red） |
| `frozen` | `red` | 功能受限 / 疑似封号，全停、需人工，**不自动恢复**（仅 `manual_unfreeze`→restricted）（→ P0） | filled red + 锁图标 |

### 2.2 风控 QUOTA-TIER 徽标族（cool，**outlined/ghost** Tag，前缀 `Tier:`）

| value | AntD color | 含义 |
|---|---|---|
| `conservative` | `blue` | 最低日配额（like 20/d、browse 80/d，risk-control §1.1/§6） |
| `normal` | `geekblue` | 标准配额（like 50/d、browse 150/d）。**关键碰撞**：`normal` 同时是 STATUS 值——此徽标用 geekblue + outlined + `Tier:` 前缀，永不与 green-filled 的 status-normal 混淆 |
| `aggressive` | `purple` | 最高配额（like 100/d、browse 300/d）。紫色刻意避开 red/volcano，激进档绝不被误读为危险状态 |

> **构造级分离**：tier 徽标用显式 `<Tag bordered color={blue|geekblue|purple}>` props，**不挂 status 语义 token**——两族在色相（warm vs cool）+ 形态（filled vs outlined）上双重分离，灰度下也能区分。

### 2.3 告警分级（V1；MVP 仅空态占位）

| value | color | 含义 | 图标 |
|---|---|---|---|
| `P0` | `red` | 账号级不可逆 / 高损：封号 / 确认限流（status restricted/frozen），立即停账号 + 风控降级 + on-call，飞书 @owner + SMS | stop / 感叹（最强视觉权重，列表 P0 置顶） |
| `P1` | `orange` | 需及时人工：验证码 / 滑块 / 登录态过期，暂停相关任务、保留现场 | 感叹 |
| `P2` | `gold` | 系统性故障但可自动重连：CDP 断连 / 页面改版，自动重连 + 必要时暂停 | info |
| `P3` | `default` | 瞬态抖动，自动重试足矣：网络抖动 / 偶发弹窗，静默自愈、仅 Web log | 中性灰（不与 P0–P2 抢视觉） |

### 2.4 Edge online 三态（AntD `<Badge status>` + 永远配文字 + tooltip）

| value | Badge status | 含义 |
|---|---|---|
| `online` | `success`（绿） | inMap **AND** `now-last_seen < N×heartbeat`（唯一断言「真可达」的态，D9） |
| `stale` | `warning`（琥珀） | 仍 inMap 但无近心跳（无关闭帧而死的连接）。**红线**：绝不并入二元 online/offline；独立第三态，dead-but-mapped 永不显示为 online。tooltip：「stale = in-map, no recent heartbeat」 |
| `offline` | `default`（灰） | 根本不在 session Map（干净断连 / 从未连 / 未绑定 / 未启动） |

### 2.5 like-rate 健康带（15%–35%，risk-control §1.1）

- **聚合 / 徽标形态**：算 likeRate，三带分类——BELOW(<15%) gold「low engagement」/ HEALTHY(15–35%) green / ABOVE(>35%) gold→volcano「over-liking, machine-like」。用与 status 同族 palette（green/gold/volcano）但**永远配数字 `26%` + 带标签**，绝不色相单独。
- **图表形态**（`echarts-for-react`，Analytics 为 V1）：`markArea` 在 y=0.15–0.35 画半透明绿带 + `markLine` 标 0.15/0.35，带外点高亮 gold/volcano。伴随轨：collect-rate < like-rate、follow-rate < 5%。
- **归因警示**：MVP 为全局聚合，标「全部账号 / 归因待补」，不把按账号 like-rate 当真（V1）。

### 2.6 密度（compact）

表格密内部工具。全局 `ConfigProvider componentSize="small"`；Table `size="small" bordered` + sticky header + `pagination={false}`（行数少，不分页不虚拟）。`compactAlgorithm` 收紧垂直节奏。两个徽标（status + tier）同 cell 内联但视觉分离（前缀 + 族色）。目标：不滚动即在 ~5s 答出健康判断。

### 2.7 AntD theme token（`ConfigProvider`，v5 algorithm-based）

```
{ cssVar:true, hashed:true,
  algorithm:[theme.defaultAlgorithm, theme.compactAlgorithm],
  token:{ colorPrimary:'#1677ff', borderRadius:4,
          controlHeight:28, controlHeightSM:24, fontSize:13,
          sizeStep:3, sizeUnit:4, wireframe:false,
          colorSuccess:'#52c41a', colorWarning:'#faad14', colorError:'#ff4d4f' },
  components:{
    Table:{ cellPaddingBlockSM:4, cellPaddingInlineSM:8, headerBg:'#fafafa', rowHoverBg:'#f5f5f5', fontSize:13 },
    Tag:{ defaultBg:'#fafafa', borderRadiusSM:3 },
    Layout:{ headerHeight:48, headerPadding:'0 16px' },
    Card:{ paddingLG:12 } } }
```
- volcano `#fa541c` 仅用于 status `restricted`（经 `<Tag color="volcano">`、非 token），与 frozen-red / P0-red 区分。
- **TIER 徽标的 blue/geekblue/purple 不是 token**——是显式 Tag color props，刻意不挂 status 语义 token，构造级分离两族。
- 暗色模式 MVP 不需要（白天内部工具）。

### 2.8 可访问性（a11y）

- **永不色相单独**：每个 status/tier/severity/edge-state/like-rate 都「颜色 + enum 文字 + 必要时图标」三重编码。
- **两徽标可达**：`Status: normal`（green filled）vs `Tier: normal`（geekblue outlined）——共享字面量 `normal` 永远带前缀且形态不同（filled vs outlined），灰度下也分得开。
- **族用形态区分**：status filled / tier outlined，不只靠 warm/cool 色相。
- **severity 阶梯**：携 `P0..P3` 文字 + 图标权重 + 排序（P0 置顶）。
- **edge 三态**：Badge status 永远配 `online/stale/offline` 词 + tooltip，绝无裸色点。
- **诚实结果**：审批显示字面 `written` / `already decided: <v>`（绝不 `published`）；0 edge 显示 `recorded, 0 edges online`；状态机拒绝显示 `refused`（中性灰、非成功绿）。
- **归因警示纯文本**：`—` + banner，不靠样式暗示。
- **对比度**：选用 preset Tag 色在浅底满足 WCAG AA（fontSize 13）；load-bearing 信息不用低对比 default 灰（仅 P3/offline 噪声用）。
- **暂停区分**：`Paused by operator` vs `Paused: captcha`，不同词 / 图标，绝不共用一个含糊 paused 徽标。

---

## 3. 信息架构与全局外壳

IA（`product-dashboard.md §1`）：`Dashboard / Accounts(列表+详情) / Content / Monitor / Settings`。Analytics（涨粉 / 互动率图）与 Alerts 为 V1。

### 3.1 全局账号筛选器——诚实化范围（must-fix）

> **MVP 红线**：归因未落地前，按账号 metrics / like-rate / Monitor 流全是「归因待补」。若顶栏筛选器选了「账号 X」却让全局聚合纹丝不动，运营会不信任工具。故 MVP 把筛选器**只作用于诚实可切的 roster 表**（用真实身份字段：nickname / group / edge），对 metrics / like-rate / Monitor 流**可见但中性化**。

- 控件：单个**分组 `<Select>`**（`Select.OptGroup`），含显式「All accounts」+ 每分组项 + 每账号项。**不用 Cascader**（严格父子下钻与「all / 整组 / 单账号」三平行模式不符，且 3–10 账号过重）。
- 值存 React context + URL `?scope=all|g:<id>|a:<id>`，全页共享、无逐页副本。
- **作用域诚实化**：
  - Dashboard 状态表 / Accounts 列表 → 真过滤（按真实身份）。
  - Today metrics 卡 / like-rate 卡 / Monitor 流 → 选单账号时显示内联注「per-account scope lands with attribution (V1)」，不假装切片。
  - **删掉 Dashboard 状态表内重复的 `[scope: All ▾]`**——一屏两个范围控件正是要避免的不一致；顶栏筛选器是单一范围源。

### 3.2 归因待补 banner 规则

凡按账号切片之处：页顶 `<Alert type="info" banner showIcon message="all accounts / attribution pending"/>` + 列内 `—` + tooltip；Monitor 流内 `acc?` / `unattributed`。banner 由 API 显式 `unattributed` flag 驱动（D3/D4），**不由值是否存在驱动**（防数据 present-but-not-attributed 时静默回归真按账号数字）。

---

## 4. 页面设计（逐页）

> 约定：`[ Btn ]`=Button、`( o )`=radio/segmented、`▣`=checkbox、`▾`=Select、`●`绿/`◐`琥珀-stale/`○`灰=edge Badge 点、`«…»`=Tag。全局 `<ConfigProvider componentSize="small" theme={{…§2.7}}>` + 单一 `<App>` wrapper（供 `App.useApp()` 的 theme-aware message/notification）。

---

### PAGE 1 — Login (`/login`)

```
+----------------------------------------------------------------------+
|                    +------------------------------+                  |
|                    |        AIDCP Console         |                  |
|                    |     internal ops console     |                  |
|                    |  ..........................  |                  |
|                    |  Username [________________] |                  |
|                    |  Password [________________] |                  |
|                    |  [x] keep me signed in       |                  |
|                    |  [        Sign in        ]   |   <- loading     |
|                    |  ! invalid credentials       |   <- error row   |
|                    +------------------------------+                  |
|                  build a1b2c3 · /api healthy ●                       |
+----------------------------------------------------------------------+
```

**AntD 映射**
- 居中 → `<Layout>` 全高 flex center；卡 → `<Card style={{width:320}}>`。
- Form → `<Form layout="vertical" size="small">`；字段 → `<Input/>` / `<Input.Password/>`；keep → `<Checkbox/>`。
- 提交 → `<Button type="primary" htmlType="submit" block loading={mutation.isPending}/>`（`POST /api/auth/login`）。
- 错误行 → `<Alert type="error" showIcon banner/>` 仅 `isError` 时渲染。
- 页脚 build/health → `<Typography.Text type="secondary">` 读 `/api/version`。

**四态**
- loading：按钮 `loading`、输入 `disabled`；无 skeleton（无数据视图）。
- empty：n/a。
- error：`401`→内联 `<Alert type="error">invalid credentials</Alert>`；网络/`5xx`→`notification.error("cannot reach /api")`（经 `App.useApp()`）。
- 写反馈（登录即写）：**非乐观**——按钮 `loading` 直到 JWT round-trip，仅 `200` 后路由 redirect `/`，无 pre-redirect「welcome」。

**红线**
- JWT 不渲染进 DOM；存储**按 design Open-Q（倾向 httpOnly cookie，in-memory 为保守备选，实现时定）**。若 cookie：状态变更 POST（approve/reject、pause）需 CSRF 防护（cookie 自动带）；若 in-memory：刷新即重登。不把开放问题当已闭合。
- 非乐观鉴权：服务端确认 token 前绝不进外壳。

---

### PAGE 2 — App Shell（包裹 3–7）

```
+======================================================================+
| AIDCP  | Accounts: [ All accounts ▾ (grouped Select) ] | 🔔 | user ▾ |
+========+=============================================================+
| Dash    |                                                            |
| board   |              <  ROUTED PAGE CONTENT (<Outlet/>)  >          |
|---------|                                                            |
| Accounts|                                                            |
| Content |                                                            |
| Monitor |                                                            |
| Setting |                                                            |
| ......  |                                                            |
| WS ●live|  <- panel-WS 状态钉在 nav 底部                              |
+=========+============================================================+
```

**AntD 映射**
- `<Layout><Header/><Layout><Sider/><Content/></Layout></Layout>`；header 48（token `Layout.headerHeight`）。
- 品牌 → `<Typography.Text strong>`；左导航 → `<Menu mode="inline" theme="light">` 由 `useLocation` 驱动。
- **全局账号筛选器** → 分组 `<Select>`（`Select.OptGroup`，§3.1），值入 context + `?scope=`，全页共享、客户端过滤。
- user → `<Dropdown>`（当前用户 + Sign out → `/api/logout`）。
- 🔔 → `<Badge dot>` over `<BellOutlined/>`（MVP 开空态 alerts popover——alerts 是 V1，**不接 `/api/alerts`**）。
- panel-WS 状态 → `<Badge status="success|warning|default" text="live|reconnecting|offline"/>` 绑 WS readyState。

**四态**
- loading：外壳立即渲染；首个 `/api/version` 解析时顶部薄 `nprogress`/`<Spin>`。
- empty：账号列表空 → 筛选器仅「All accounts」。
- error：`/api/version` 失败 → `notification.warning("enum/version unavailable — badge colors may be stale")`；WS 掉 → nav badge 翻 `warning "reconnecting"` 自动重连。
- 写反馈：n/a（除 logout 外无写）。

**红线**
- 全局筛选器是单一范围源，下游按账号切片 honor 归因警示（§3.1：选单账号仍标「全部账号 / 归因待补」）。
- WS 状态诚实三态（live/reconnecting/offline），绝非撒谎二元。

---

### PAGE 3 — Dashboard home (`/`)

```
+----------------------------------------------------------------------------+
| (i) Aggregates are ALL ACCOUNTS · per-account attribution pending          | <-banner
+----------------------------------------------------------------------------+
| HEALTH: 6/8 online · 1 warned · 0 frozen · like-rate 26% healthy           | <-一行健康判词
+----------------------------------------------------------------------------+
| TODAY (global)                                                             |
| +----------+----------+----------+----------+----------+----------+        |
| |Accts on  | Views    | Likes    | Collects | Comments | Follows  |        |
| |  6 / 8   |   920    |   240    |    88    |    22    |    31    |        |
| +----------+----------+----------+----------+----------+----------+        |
| | Publishes| Sessions | Edges on | Like-rate «26% HEALTHY (15-35%)» |      | <- /api/analytics/like-rate
| |    3     |    19    |   4      |  (green, 数字+带, 自有 query key) |      |
+----------------------------------------------------------------------------+
| PER-ACCOUNT STATUS   (severity-sorted: frozen/restricted/stale first)      |
| nick      grp     edge        STATUS          TIER          age            |
| ---------------------------------------------------------------------------|
| 阿美      food    (none)  ○   «Status:froz🔒» «Tier:aggress» D31           |
| 小李种草  beauty  edge-07 ◐   «Status:warned» «Tier:conserv» D 4/7         |
| 小张测评  beauty  edge-03 ●   «Status:normal» «Tier:normal»  D12           |
| ...                                                       quota: — (V1)    |
+----------------------------------------------------------------------------+
| ALERTS                                                                     |
|   ( empty-state )  No alerts wired yet — alerts land in V1                  |
+----------------------------------------------------------------------------+
```

**AntD 映射**
- banner → `<Alert type="info" banner showIcon/>`。
- **一行健康判词**（5s 一眼）→ 顶部 `<Typography.Text>` 由 summary 算出（`6/8 online · n warned · n frozen · like-rate <band>`）。
- Today 卡 → `<Row gutter>` of `<Col><Card size="small"><Statistic/></Card></Col>`（`/api/dashboard/summary`）；like-rate 卡 → `<Statistic>` + `<Tag color={band}>`，**自有 query/cache key 源 `/api/analytics/like-rate`**，永远印数字 `26%` + 带词。
- 状态表 → `<Table size="small" bordered rowKey="accountId" pagination={false}>`：
  - **行按 severity 排序**（frozen/restricted → stale-edge → warned → normal），眼睛先撞麻烦。
  - edge → `<Badge status={online?'success':stale?'warning':'default'}/>` 三态。
  - **STATUS 列** → `<Tag color={statusColor}>Status: {v}</Tag>` filled（normal 盾 / frozen 锁图标）。
  - **TIER 列（独立 cell）** → `<Tag bordered color={tierColor}>Tier: {v}</Tag>` outlined。两者**绝不合并**。
  - age/cold-start → `Day n` / `Day n/7`（**真实**，由 `createdAt`→`ageDays`/`coldStartDay`）。
  - quota → 折叠为单条 `—  (V1)` 注，**不占整列全是破折号的列**（稀释密度）。
- Alerts → `<Empty description="alerts land in V1"/>`（**不接任何 endpoint**）。

**四态**
- loading：卡 → `<Card loading>`（loading 边界在 Card，包住 Statistic——Statistic 无 loading prop）；表 → `<Table loading>`。
- empty：零账号 → `<Empty>`；零计数 → `<Statistic value={0}/>`（真零，非 skeleton）。
- error：`/api/dashboard/summary` 失败 → `<Alert type="error" action={<Button onClick={refetch}>retry</Button>}/>`。
- 写反馈：无（只读页）。

**红线**：两个独立徽标（filled vs outlined + 前缀，撞名 `normal` 视觉分开）；归因警示（banner + quota `—`）；stale 态独立呈现；like-rate 数字+带、非色相单独。

---

### PAGE 4a — Accounts 列表 (`/accounts`)

```
+----------------------------------------------------------------------------+
| Accounts                                  search [____]  group [All ▾]      |
+----------------------------------------------------------------------------+
| ▸ Group: beauty (3)                                                        |
|   nick      xhsId    edge        online   STATUS         TIER       actions |
|   --------------------------------------------------------------------------|
|   小张测评  5f..e2   edge-03 ●   online   «Status:normal»«Tier:normal»[Pause]|
|   小李种草  7a..11   edge-07 ◐   stale    «Status:warned»«Tier:cons.»[Pause]|
|   小王      (—)      (none)  ○   offline  «Status:normal»«Tier:cons.»[Resume]|
|        ^ 运营暂停行显示 «Paused by operator»（非 captcha）                  |
| ▸ Group: food (2)                                                          |
|   阿美      9c..00   edge-09 ●   online   «Status:froz🔒»«Tier:aggr»[Pause] |
+----------------------------------------------------------------------------+
| 行点击 -> /accounts/:id                                                     |
+----------------------------------------------------------------------------+
```

**AntD 映射**
- 分组展示 → **一个 `<Table>` per group 包进 `<Collapse>` 面板**（分组标题用可空 `group_label`）；**或**单扁平 `<Table>` 加 group 列 + 排序/筛选（≤10 行足矣）。**不用「rowKey 造 group header 行」**（AntD v5 Table 无原生 row grouping）。
- search → `<Input.Search>`；group → `<Select>`（默认读全局 scope）。
- online → `<Badge status/>` 三态；STATUS/TIER → 两个独立 `<Tag>`。
- actions → `<Button size="small">Pause/Resume</Button>`（`POST /api/accounts/:id/command`，切 `accounts.status`）；运营暂停 → `<Tag>Paused by operator</Tag>` 区别于传输 `<Tag color="gold">Paused: captcha</Tag>`。
- 行 → `onRow.onClick` 导航。

**四态**
- loading：`<Table loading>` + 5 skeleton 行。
- empty：`<Empty description="no accounts (seed: default)"/>`。
- error：`<Result status="warning" extra={<Button>retry</Button>}/>`。
- **写（pause/resume）非乐观**：点击 → 按钮 `loading` → round-trip 渲染**真** `account.status`。0 在线 edge → `message.info("recorded — 0 edges online")`（durable 态仍翻）。拒绝/出错 → `message.warning("refused: <reason>")`，行不变。

**红线**：每行两个独立徽标（撞名 `normal` filled vs outlined + 前缀分开）；运营暂停（durable `accounts.status`）≠ 验证码暂停（`pausedEdges`），不同词/图标、绝不一个 paused tag；stale 独立态；pause/resume 非乐观、`0 edges online` 诚实回报。

---

### PAGE 4b — Account 详情 (`/accounts/:id`)

```
+----------------------------------------------------------------------------+
| < Accounts / 小张测评 (acc-01)                  [ Pause ]  (点击 loading)   |
+----------------------------------------------------------------------------+
| RISK (read-only in MVP — status/tier change is V1)                         |
|   Status:  «Status: normal»  (green, filled, shield)                        |
|   Tier:    «Tier: normal»    (geekblue, outlined)   <- 两个独立徽标         |
|   last downgrade reason: —    | recovery window: n/a                        |
+----------------------------------------------------------------------------+
| BASIC INFO                          | LOGIN STATE                          |
|  nickname   小张测评                |  logged-in: yes ●                    |
|  xhsUserId  5f..e2                  |  session age: 3h                     |
|  group      beauty                  |  edge online: edge-03 ● online       |
|  vertical   美妆个护                 |       (或 ◐ stale / ○ offline)       |
|  createdAt  2024-05 (age D12)       |  pause kind: «Paused by operator»?   |
+-------------------------------------+--------------------------------------+
| DEVICE BINDING (read-only)          | PERSONA (read-only)                  |
|  edgeId      edge-03                 |  personaRef: persona-zhang (YAML)    |
|  capabilities  ← 见红线（条件渲染） |  vertical/tone: (from version-ctrl) |
|  bind state  bound                   |  [edit in YAML — not editable here] |
+-------------------------------------+--------------------------------------+
| (V1 placeholder) [ Apply tier ▾ ] [ Manual downgrade ▾ ]  -- disabled, V1  |
+----------------------------------------------------------------------------+
```

**AntD 映射**
- header → **`<Breadcrumb>`（或 back `<Button type="link" icon={<ArrowLeftOutlined/>}>`）+ `<Flex justify="space-between">` 装 `<Typography.Title level={5}>` + Pause/Resume `<Button>`**。**不用 `<PageHeader>`**（v5 core 已移除）；**不为此拉 `@ant-design/pro-components`**。
- RISK → 两个独立 `<Tag>`（Status filled / Tier outlined）+ `<Descriptions size="small" column={1}>` 装 reason/recovery-window。
- BASIC/LOGIN/DEVICE/PERSONA → `<Descriptions size="small" bordered column={1}>`（compact、只读）。
- edge/login 点 → `<Badge status/>` 三态。
- V1 控件 → `<Button disabled>` + `<Tooltip title="V1">`；将来 tier 控件是与 status **分离**的 `<Select>`，绝不合并。

**四态**
- loading：每 Descriptions 块 `<Skeleton active/>`。
- empty：未绑定 → DEVICE `<Empty description="no edge bound"/>`，login「not logged in / offline」。
- error：`<Result status="error">` + retry。
- 写（pause/resume）非乐观，同 4a 契约（`written` / `recorded, 0 edges online` / `refused`）。

**红线**
- **两个独立只读徽标**（Status vs Tier）——独立性的标杆呈现处；V1 控件也是两个独立输入。
- 设备绑定 & 人设**只读**（人设留版本控制 YAML，`persona_ref` 指文件）。
- **capabilities 条件渲染**（must-fix）：源自 live edge 注册（hello handshake），bound edge 不在线时显示 `— (edge offline, capabilities unknown)`——bind state「bound」与 edge「online/stale/offline」是两个不同事实，独立两行；不为离线 edge 渲染固定能力列表（同属红线禁止的「撒谎二元」家族）。
- status/tier **写是 V1**——MVP 此处写仅 pause/resume；将来 refused 的 tier/status 迁移须渲染 `refused`（非绿）。
- **persona 块需 error/empty 态**（must-fix）：`persona_ref` 指向的 YAML 不可解析时显示「persona_ref unresolved」，而非渲染陈旧字段。

---

### PAGE 5 — Content (`/content`)

```
+----------------------------------------------------------------------------+
| (i) all accounts / attribution pending                                     | <-banner（补齐）
+----------------------------------------------------------------------------+
| PUBLISH QUEUE (in-flight, single slot)                                     |
|  +----------------------------------------------------------------------+  |
|  | c-101  "夏季测评..."  acct: — (attr pending)  status: publishing     |  |
|  | [#########.....] sim ✓ jaccard .42                                    |  |
|  | (或 stalled: edge stale, no progress >N min  ← 与 edge 三态联动)      |  |
|  | (无在途 -> Empty「no in-flight publish」)                             |  |
|  +----------------------------------------------------------------------+  |
+----------------------------------------------------------------------------+
| PENDING APPROVAL                                                           |
|  reqId     content        sim      requested        actions                |
|  --------------------------------------------------------------------------|
|  req-77   "护肤好物.."   ✓ .31    12:04           [Approve] [Reject]       |
|     -> 点击: 按钮 loading; 结果 ->                                          |
|        ✓ message.success "written"                                         |
|        ℹ message.info "already decided: approved" (alreadyDecided)         |
|        ⚠ message.warning "refused: <reason>"                              |
|        ℹ message.info "recorded, 0 edges online"                          |
|  req-78   "周末探店.."   ✗ .58    11:50           [Approve] [Reject]       |
+----------------------------------------------------------------------------+
| PUBLISHED HISTORY                                                          |
|  ts            title          note URL              receipt(真态,非常量)   |
|  --------------------------------------------------------------------------|
|  06-19 10:02  "早C晚A.."     xhs.../abc123 ↗        «published»           |
|  06-18 21:30  "测评合集.."   (no URL)               «no-receipt»          |
|  06-18 09:10  "草稿合集.."   (—)                    «recorded, 0 edges»   |
+----------------------------------------------------------------------------+
```

**AntD 映射**
- 队列 → `<Card>` 单在途槽；进度 → `<Progress>`；相似度 → `<Tag color={passed?'green':'gold'}>jaccard .42</Tag>`。无 job → `<Empty>`。
- 待审批 → `<Table size="small">`（`/api/content/queue`）；Approve/Reject 调**共享** `POST /api/publish/:requestId/approve`（同一 `requestId`，`writeApprovalSignal`，first-writer-wins，D8）。
- 已发布 → `<Table size="small">`（`/api/content/published`）；note URL → `<Typography.Link href target=_blank>`。

**四态**
- loading：队列 `<Skeleton>`；两表 `<Table loading>`。
- empty：队列 `<Empty>`；待审批 `<Empty description="nothing awaiting approval"/>`；历史 `<Empty>`。
- error：各 section `<Alert type="error">` + retry。
- **写（approve/reject）非乐观 + 诚实（D8）**：按钮 `loading` → round-trip：
  - `{written:true}` → `message.success("written")`，refetch 后行离开 pending。
  - `{alreadyDecided:<v>}`（first-writer-wins 输给飞书/重复）→ `message.info("already decided: <v>")`，行更新到**真**决定值——**绝不 published**。
  - refused/非法 → `message.warning("refused: <reason>")`。
  - 0 edge → `message.info("recorded, 0 edges online")`。

**红线**
- **Approve → `written`，绝不 `published`**（edge 对信号文件的动作才是真相）；`alreadyDecided` 渲染真实前值。
- 非乐观：行带 spinner 停在 pending 直到服务端确认；first-writer-wins 诚实呈现。
- **Popconfirm 规则统一**（must-fix）：低量内部审批队列——**两键都单击**，靠行的非乐观 loading + 诚实 `written`/`alreadyDecided` 做安全网（重复提交只返回 `alreadyDecided`）；不要只在 Reject 上挂 Popconfirm（当前是反的——Approve 才是释放发布的不可逆路径）。
- **归因警示补齐**（must-fix）：页顶 banner（同 Dashboard）；队列/历史若出现 acct 列 → `—` + pending tooltip。ASCII 已画出 banner。
- **receipt 列渲染真态、非常量 `ok`**（must-fix）：按 `publish_log` 真实逐行结果——有 note URL 时 `«published»`，无 URL 时 `«no-receipt»`/`«failed»`，`«recorded, 0 edges»`。绝不统一渲染 `ok`（否则同属红线禁止的假成功）。
- **在途槽 stalled 态**（must-fix）：与 edge 三态联动——`publishing` 中 edge 转 stale 且 N 分钟无进度 → 显示 `stalled (edge stale)`，不渲染会暗示 liveness 的滚动条。
- 共享飞书信号文件契约路径 `/tmp/aidcp-publish-approve-<requestId>.json`（同 `requestId`）。

---

### PAGE 6 — Monitor (`/monitor`)

```
+----------------------------------------------------------------------------+
| (i) account filter: per-account scope lands with attribution (V1)          |
| filters: account [All ▾]  outcome [▣success ▣no_target ▣escalated          |
|          ▣guard_blocked ▣error ▣other]   [ Pause stream (N buffered) ][Clear]|
|                                          stream: ● live (panel-WS)          |
+--------------------------------------+-------------------------------------+
| REAL-TIME LOG STREAM (bounded buffer) | ACTION TIMELINE                     |
|  12:04:01 acc? edge-03 like  success |  (live-derived · this session only · |
|  12:04:00 acc? edge-03 open  success |   no history/backfill in MVP)        |
|  12:03:58 acc? edge-07 like  no_target| session s-19 (since you opened tab) |
|  12:03:55 acc? edge-03 scroll success|   ├ 12:03 open  ✓ cache_hit_valid   |
|  ...(客户端过滤)...                  |   ├ 12:04 like  ✗ no_target          |
|  (acc? = unattributed / attr pending)|   ├ 12:04 retry→escalated           |
|                                      |   └ 12:05 back  ✓                   |
|                                      |  (空时: 「waiting for events…」)     |
+--------------------------------------+-------------------------------------+
| legend: «success»green «no_target»default «escalated»gold «guard»volcano    |
|         «error»volcano                                                      |
+----------------------------------------------------------------------------+
```

**AntD 映射**
- filters → `<Select>`（account，默认全局 scope；选单账号显示 V1 注）+ `<Checkbox.Group>`（outcome）。客户端过滤单一全局 WS 流（无 per-account WS 房间）。
- Pause stream / Clear → `<Button>`（暂停本地 append、非连接）；Pause 按钮带 **`paused — N buffered` 计数**（must-fix）。
- 日志流 → **bounded ring buffer（保留最近 ~500–1000 行、drop-oldest）** + 普通 `<List size="small">` / scroll 容器渲染。**不依赖「virtualized `<List>`」**（v5 List 无原生虚拟化）；实测卡顿才加 `react-window` 或换 `<Table virtual scroll={{y}}>`。
- 时间线 → `<Timeline>` 按 `sessionId` 分组，节点按 outcome 着色，三道闸阶段（cache-hit/LLM、post-verify/retry-escalate/anti-pollution）注在节点文字。
- stream 状态 → `<Badge status="success|warning|default" text="live|reconnecting|offline"/>`。

**四态**
- loading：首帧前 → `<Skeleton active>` +「connecting to live stream…」。
- empty：已连无事件 → `<Empty description="waiting for events…"/>`（**ACTION TIMELINE 默认即此空态**，不预填 session 列表）。
- error：WS 掉 → badge `warning "reconnecting"` + `<Alert type="warning" banner>live stream reconnecting…</Alert>`，退避自动重连；**missed-while-down 不回填**（单一全局流、无 replay），并明确标注让运营知道。
- 写反馈：无（只读流）。

**红线**
- **ACTION TIMELINE 标「live-derived · this-session-only · no history/backfill」**（must-fix）：MVP 无 `/api/monitor/interactions`（V1）；时间线只能由 live WS 流客户端重建，默认空态，**不预填 populated session**。
- alerts bell（PAGE 2）+ Dashboard alerts 块保持纯空态、**不接 `/api/alerts`**。
- **归因警示**：`accountId` 流通前行显 `acc?`/`unattributed`，account 筛选器标「attribution pending」，无假按账号路由。
- 诚实 outcome：`no_target`/`escalated`/`guard_blocked`/`error` 各自呈现，绝不并入 `success`。
- **outcome 过滤不静默吞**（must-fix）：outcome 集绑 `/api/version` live enum（或加 catch-all `other`），未建模 outcome 默认仍显示——客户端过滤绝不静默吞未建模 outcome。补 `error` kind 过滤。
- stream 状态诚实三态，无假装 live 的静默缺口。

---

### PAGE 7 — Settings (`/settings`)

```
+----------------------------------------------------------------------------+
| Settings                                                                   |
| +------------------+  +---------------------------------------------------+ |
| | (•) Feishu       |  | FEISHU INTEGRATION (read-only in MVP)             | |
| | ( ) Strategy     |  |  bound chats:  chat-aaa "运营群" bound ●          | |
| | ( ) About/Version|  |                chat-bbb "审批群" bound ●          | |
| +------------------+  |  approval signal path:                            | |
|                       |   /tmp/aidcp-publish-approve-<reqId>.json (shared) | |
|                       +---------------------------------------------------+ |
|                       | STRATEGY DEFAULTS (three tiers, read-only MVP)    | |
|                       |  conservative  like 20/d  browse 80/d «Tier:cons» | |
|                       |  normal        like 50/d  browse 150/d «Tier:norm»| |
|                       |  aggressive    like 100/d browse 300/d«Tier:aggr» | |
|                       +---------------------------------------------------+ |
|                       | ABOUT / VERSION (/api/version)                    | |
|                       |  build a1b2c3 · enums asserted ✓ vs committed     | |
|                       |  RiskStatus / RiskQuotaLevel / RISK_ACTIONS       | |
|                       +---------------------------------------------------+ |
+----------------------------------------------------------------------------+
```

**AntD 映射**
- 左子导航 → `<Menu mode="inline">` 或 `<Tabs tabPosition="left">`。
- 飞书 chats → `<Table size="small">` / `<List>`；bound 点 → `<Badge status="success"/>`；审批路径 → `<Typography.Text code>`。
- 策略三档 → `<Descriptions>` / `<Table>`；每档用 outlined `<Tag color={blue|geekblue|purple}>Tier: …</Tag>`（cool 族）——**此处无 status 颜色**。
- About/Version → `<Descriptions size="small">` 读 `/api/version`；enum 断言结果 → `<Tag color={ok?'green':'red'}>asserted ✓/✗</Tag>`（D11 单源检查呈现给运营）。

**四态**
- loading：每面板 `<Skeleton active/>`。
- empty：无绑定 chat → `<Empty description="no Feishu chats bound"/>`。
- error：`/api/version`/chat 失败 → `<Alert type="warning">version/enum source unavailable — badge colors may be stale</Alert>`（直接关联 enum 漂移红线）。
- 写反馈：MVP 只读（设置写是 V3/RBAC）——控件 `disabled` + V-tag tooltip。

**红线**
- **单一 enum 源**（`/api/version`）呈现 + 对 committed `aidcp-enums.ts` 断言；不匹配显示、不隐藏——防三处徽标/颜色漂移（D11）。
- tier 默认用 **cool tier palette only**（blue/geekblue/purple, outlined），tier 绝不读成危险状态。
- 共享飞书审批信号文件路径记为 Web 与飞书同写的同一契约。

---

## 5. 写操作交互规范

适用全部 MVP 写（login、pause/resume、approve/reject；V1 status/tier）。

1. **非乐观（D10）**：按钮 `loading` → 服务端 round-trip → 渲染真态。绝不在确认前显示成功，绝不写乐观更新。
2. **结果文案（经 `App.useApp()` 的 message/notification，theme-aware）**：
   - `{written:true}` → `message.success("written")`。
   - `{alreadyDecided:<v>}` → `message.info("already decided: <v>")`（真实前值，**绝不 published**）。
   - 状态机拒绝 → `message.warning("refused: <reason>")`（中性 / 灰处理，色相绝不暗示服务端拒绝处的成功）。
   - 0 在线 edge → `message.info("recorded, 0 edges online")`（durable 态已翻，但 0 edge 诚实说出，绝不 done）。
3. **Popconfirm 规则**：低量内部队列两键都单击，靠非乐观 loading + first-writer-wins 做安全网（重复提交返回 `alreadyDecided`）。规则二键一致，**不要只在 Reject 上挂 Popconfirm**。
4. **串行化（V1）**：风控写经每账号 async mutation queue（D7），手动覆盖与 live `quota_exceeded` 不互相覆盖；UI 不感知，但写返回的真态即串行后的 `getState()`。
5. **静态调用警告**：用 `const { message, notification } = App.useApp();` hook 形式，**不用** `message.*`/`notification.*` 静态 import（否则 v5 拿不到 theme token 且报 dev warning）。

---

## 6. 实时日志流交互（panel-WS）

- **单一全局流 + 客户端过滤**（无 per-account WS 房间、无订阅协议、无连接时历史回放）。
- **过滤**：account（默认全局 scope，归因前标 `acc?`）+ outcome `<Checkbox.Group>`；outcome 集绑 `/api/version` live enum 或加 `other` catch-all + `error` kind——**未建模 outcome 默认仍显示，客户端过滤绝不静默吞**。
- **暂停滚动**：Pause 暂停本地 append（非连接），按钮带 `paused — N buffered` 计数。
- **bounded ring buffer**：保留最近 ~500–1000 行、drop-oldest（多小时 shift 不涨内存）。
- **虚拟化**：MVP **不默认虚拟化**（YAGNI）——普通 `<List size="small">` + bounded buffer 即可；实测卡顿才加 `react-window` 或换 `<Table virtual scroll={{y}}>`。**不依赖 `<List>` 原生虚拟化**（v5 无）。
- **断连诚实**：WS 掉显示 `reconnecting`，missed-while-down **不回填**且明确标注（单一全局流无 replay）。
- **ACTION TIMELINE**：live-derived、this-session-only、无 history/backfill，默认空态 `waiting for events…`；by-session 互动历史是 V1（`/api/monitor/interactions`）。

---

## 7. 组件清单（AntD-native，标出修正与自定义）

**AntD v5 原生、开箱可用（保留）：**
`Layout/Sider/Header`（headerHeight token）、`Menu mode="inline"`（`useLocation` 驱动）、`Dropdown`、`Badge status="success|warning|default"`（edge / WS 三态）、`Badge dot` over `BellOutlined`、`Card`+`Statistic`、`Popconfirm`、`Empty`/`Result`/`Skeleton`、`Descriptions size="small" bordered column={1}`、`Progress`、`Tag` preset（green/gold/volcano/red/blue/geekblue/purple，filled-vs-bordered 族分）、`Form`/`Input.Password`/`Button block loading`/`Alert banner`、`Tabs tabPosition="left"`、`Typography.Text code`/`Link`、`ConfigProvider componentSize="small"` + `[defaultAlgorithm, compactAlgorithm]` + cssVar + component tokens。

**必须修正（不照原映射，已纠正）：**

| 项 | 原映射 | 修正 |
|---|---|---|
| 详情页 header | `<PageHeader>` | v5 core 已移除 → `Breadcrumb`/back-Button + `Flex` + `Typography.Title` + action Button；**不拉 pro-components** |
| 分组表格 | rowKey 造 group header 行 | v5 Table 无原生 row grouping → 一表/组 + `Collapse`（/accounts），**或** 单扁平表 + group 列（Dashboard 状态表，最简） |
| 全局账号筛选器 | `Cascader` | 父子下钻不符三平行模式 → 单分组 `Select`（`Select.OptGroup`） |
| 日志流 | virtualized `<List>` | v5 List 无原生虚拟化 → bounded ring buffer + 普通 List；卡顿才 `react-window`/`Table virtual` |
| 写结果 message | 静态 `message.*` | `App.useApp()` hook（theme-aware、消除 dev warning） |
| Card loading 边界 | — | loading 挂 `<Card loading>` 包 Statistic（Statistic 无 loading prop） |

**自定义组件 kit（封装红线一次、各处复用）：**
- `RiskStatusBadge`（filled warm Tag + `Status:` 前缀 + 图标）
- `QuotaTierBadge`（outlined cool Tag + `Tier:` 前缀）——与 status **typed 分离**，绝不合并控件
- `EdgeOnlineState`（online/stale/offline 三态 Badge + tooltip）
- `AttributionPendingBanner`（由 API `unattributed` flag 驱动，非由值存在驱动）
- `HonestWriteResult`（written / already-decided / refused / recorded-0-edges 的统一 message 映射，显式 `refused` 渲染路径，绝不出现 `published`/`done`）

**第三方：** 仅 `echarts-for-react`（like-rate `markArea`/`markLine` 健康带，Analytics V1）。**单一图表库，不引 Recharts**。

---

## 8. 落地建议

1. **设计事实源**：实现直接照 §0 优先级链。不维护任何会与 spec / API DTO / `/api/version` 漂移的第二份设计文件。UI 状态清单（§1 红线 + 每屏四态）是评审件，替代设计稿。
2. **与 task 6 console 脚手架衔接**（`../aidcp-console`，第 4 仓）：
   - `ConfigProvider`（§2.7 token）+ 单一 `<App>` wrapper 一次钉死。
   - committed `src/types/aidcp-enums.ts`（镜像 cloud `src/risk/types.ts`）+ 一个对 `/api/version` 断言的漂移测试（D11）。
   - 先搭 Layout 外壳 + 顶栏分组 Select + 左导航 + 各页空态打桩（mock 数据），再接真 `/api`。
   - 先落 §7 自定义 kit（红线编码一次），各页复用。
   - TanStack Query 管所有读 + 写 mutation；独立 panel-WS 客户端喂 live 流并 `invalidateQueries`/`setQueryData`。
   - 写绝不乐观；`status` 与 `quotaLevel` 两个独立徽标接两个端点。
3. **MVP 端点对齐**（防错接线）：
   - approve/reject → `POST /api/publish/:requestId/approve`（共享 `writeApprovalSignal`，同 `requestId`）。
   - pause/resume → `POST /api/accounts/:id/command`。
   - like-rate 卡 → `/api/analytics/like-rate`（自有 query/cache key，**非** summary）。
   - 只读：`/api/version`、`/api/dashboard/summary`、`/api/accounts(+/:id)`、`/api/content/queue`、`/api/content/published`。
   - **MVP 不接** `/api/alerts` / `/api/monitor/interactions`（V1）；alerts bell + Dashboard alerts 块纯空态。
4. **V1 增量（留干净缝）**：
   - **风控写控件**：status（经 `applySignal` + 枚举 `manual_restrict`/`manual_freeze`/`operator_override_recover`，后者需审计理由）与 quota（经新 `setQuotaLevel`）**两个独立控件**；时间门控拒绝渲染 `refused`（非绿）；每账号串行化（D5/D6/D7）。
   - **Monitor / Alerts 页**：接 `/api/monitor/interactions`（按笔记互动历史）+ `/api/alerts`（P0–P3 只读流）；ACTION TIMELINE 升级为有 history。
   - **真按账号切片**：归因（`accountId` 上 `interaction.occurred` + `noteId` 填充）落地后，移除「归因待补」标、上真按账号 metrics / like-rate / Monitor 路由；`AttributionPendingBanner` 由 API flag 自动关闭，无需改 UI 结构。

---

## 跨页总结（每页适用）

- **两徽标规则**：status = filled warm `«Status: …»`；tier = outlined cool `«Tier: …»`。撞名 `normal` 永远带前缀 + 形态不同（green-filled vs geekblue-outlined），绝非裸 token、绝非一个合并控件。
- **写不乐观**：按钮 loading → round-trip → 真态。结果 `written` / `already decided: <v>` / `refused: <reason>` / `recorded, 0 edges online`——绝不 published/done。
- **归因警示**：全局 `<Alert banner>` + 按账号 cell `—` + 流内 `acc?`，由 API `unattributed` flag 驱动。
- **edge 三态**：`<Badge status="success|warning|default">online|stale|offline</Badge>` + tooltip，绝非二元。
- **运营暂停 ≠ 验证码暂停**：`Paused by operator` vs `Paused: captcha`，不同词/图标。
- **密度**：`componentSize="small"` + compactAlgorithm + `<Table size="small" bordered pagination={false}>` + fontSize 13——5s 答出健康判断。
- **a11y**：颜色永远配 enum 词（+ 图标）；status filled / tier outlined 的形态分灰度下存活；severity 携 `P0..P3` 文字；refused 等态用中性灰，色相绝不暗示服务端拒绝处的成功。

---

相关文件（绝对路径）：
- `/Users/baitianxing/aidcp/docs/product-dashboard.md`（IA + 逐页 JSON，§1-2）
- `/Users/baitianxing/aidcp/openspec/changes/aidcp-console-panel-mvp/design.md`（D1–D11 + Open-Q JWT 存储 line 79）
- `/Users/baitianxing/aidcp/openspec/changes/aidcp-console-panel-mvp/proposal.md`（MVP/V1 范围 + 端点）