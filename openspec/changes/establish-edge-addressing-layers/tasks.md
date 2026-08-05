## 1. 事实复核（动手前先重核，fleet 活跃、快照会过期）

- [x] 1.1 重核边缘主进程的启动顺序：账号身份确立、云端客户端构造、连接建立三者的先后关系，记下当日的 `文件:行`
  <!-- aidcp-edge 00fda89 已核：accountId 确立 src/main.ts:671 → new EdgeClient({accountId}) :683 → await client.connect() :1419。行号较提案时 +1/+1/+5 -->
- [x] 1.2 重核「Facebook 启动登录协调的进度与失败只报桌面外壳、不报云端」这一事实
  <!-- aidcp-edge 00fda89 已核：进度出口 src/main.ts:414 onAutomaticProgress→sendLifecycleIpc；失败出口 :426 reportFacebookAuthFailure→sendLifecycleIpc。该函数体内零 client.send -->
- [x] 1.3 重核「身份翻转时断开云端 → 换账号 → 重连」，确认一条云端连接绑一个账号
  <!-- aidcp-edge 00fda89 已核，两条路径同形：守卫重立 src/main.ts:1566 closeAndWait / :1577 applyIdentity 换 accountId；唤醒 :1839 closeAndWait → :1840 换 accountId → :1843 connect() -->
- [x] 1.4 重核浏览器槽位调度的容量来源（本机可用内存推算）与排队机制所在位置
  <!-- aidcp-edge 00fda89 已核：容量 src/electron/main.cjs:2799 STARTUP_USABLE_MEMORY_BYTES = fleet.usableMemoryBytes()；队列 :2507「浏览器执行槽位 + 有界串行启动队列」 -->
- [x] 1.5 重核周期阻断观测的能力面与决策面各自落点，确认它确实跨层
  <!-- aidcp-edge 00fda89 已核，跨层坐实：能力面 src/native-page-engine/browse-session.ts:1483 发 page_probe 给引擎；决策面 :1523 observeProbe 判类 → :1552 未知遮挡二次确认 → :1656 reportBlocking → :1659 client.send('risk.captcha_detected') / :1577 risk.captcha_cleared -->
- [x] 1.6 复核 `split-classic-client-edge-host` 的当前状态（分支是否仍在、台账与宿主公开面是否有变），据实更新本 change 中对它的描述
  <!-- 已核：origin/codex/split-classic-client-edge-host 仍在，头 2ab2ec20「mark the nine-verb Host API sketch as superseded」。change 目录含 specs/{canonical-default-branch-guard,classic-client-edge-host-assembly}。本 change design.md 引用的是取代后那份宿主公开面（含「资源协调（机器级）」分组），描述无需修订 -->

## 2. 判据文档主体

<!-- 2.1-2.5 主交付物 = aidcp docs/edge-addressing-layers.md（新建） -->

- [x] 2.1 在 `docs/` 新建分层判据文档，确定文件名并在文首写明「本文是裁决依据，不是归属表」
  <!-- docs/edge-addressing-layers.md 文首引用块第 1 行即该声明 -->
- [x] 2.2 写入四层定义：宿主层／环境层／翻译层／账号层，各含编址单位、权威归属、典型内容
  <!-- §2 四层表 -->
- [x] 2.3 写入核心论据：账号身份确立发生在云端连接建立之前，故云端「没有可说的对象」而非「来不及说话」；附 1.1–1.3 复核到的位置
  <!-- §2.1，含 1.1-1.3 全部复核坐标；并写明「编址体系的缺席，不是时序上的先后」及两者处置差异 -->
- [x] 2.4 写入四条判据（事实归属／时序／后果／性质），逐条说明各自要回答的问题
  <!-- §3 判据表 -->
- [x] 2.5 写明四条判据 MUST 合并使用，单独使用任一条可能得出错误结论
  <!-- §3.1，并给出单用①/单用③各自会错在哪 -->

## 3. 三个已裁决判例

- [x] 3.1 判例一（浏览器槽位调度）：逐条给出四条判据结论，得出「宿主层、铁定本地」，并说明它因此不需要人审／额度／已派发未确认那一套
  <!-- §4 判例一，四条逐条带 1.4 复核坐标 -->
- [x] 3.2 判例二（Facebook 启动登录协调）：给出「环境层、留本地」，并**显式记录此前误判为混合体的原因是拿后果当归属判据**，写明「用后果去定归属，方向反了」
  <!-- §4 判例二，标为反面示范；另补一句「后果严重的直觉会压过归属清晰的事实，裁决时先问编址再看后果」 -->
- [x] 3.3 判例三（周期阻断观测）：说明它跨层，处理方式为「能力留下、决策上移」，并写明须保留「发现被平台拦住即就地停手」这条环境层兜底
  <!-- §4 判例三，能力面/决策面分表带 1.5 复核坐标；兜底理由写为「它本身就是环境层职责，不因决策上移而转移」 -->

## 4. 边界与禁令

- [x] 4.1 写入禁令：本判据 MUST NOT 派生任何新的边缘归属表／归属清单／目录规则／归属门禁
  <!-- 文首引用块 + §5，两处各一次 -->
- [x] 4.2 写明禁令理由，并引用云端边界规则中「不得拿生成物顶替人工裁定名册」的同类教训
  <!-- §5，含 ownership-rules.json 原意引述 -->
- [x] 4.3 声明既有归属台账是本判据的**消费方**：台账答「这块归谁」，判据答「凭什么」
  <!-- 文首引用块 + §5 分工表 -->
- [x] 4.4 写明与 `split-classic-client-edge-host` 的正交关系与不重叠边界，并声明本 change 不修改其任何产物
  <!-- §6.1，含核对日分支头 2ab2ec20 -->
- [x] 4.5 声明本判据**不适用于云端拆仓归属**（云端按另一套编址单位划分）
  <!-- §6.2 -->
- [x] 4.6 在文档中登记两条待决项：翻译层是否独立成模块；后续落到代码时的粒度（标注+门禁 vs 物理拆分）
  <!-- §7 -->
- [x] 4.7 在文首或文末注明：文中行数、位置与判例均为核对当日快照，引用前应重核
  <!-- 文首快照声明；另加一句「判据本身不随行号失效，失效的只是指路的坐标」 -->

## 5. 指针与收口

- [x] 5.1 在 `docs/architecture.md` 增加一处指向判据文档的指针，位置须让「查边缘某职责该归谁」的读者能找到
  <!-- 置于 §2.2 边缘端小节标题正下方、既有退役告示之前；含四层一句话摘要与「MUST NOT 另起一张表」 -->
- [x] 5.2 通读全文，确认对判例一、二、三给出的结论与 `design.md` 一致
  <!-- 三例结论逐条比对：槽位=宿主层铁定本地 / 登录协调=环境层留本地（撤回混合体判断）/ 周期观测=跨层「能力留下、决策上移」+ 兜底。一致 -->
- [x] 5.3 确认本 change 未新增任何归属清单类文件，也未修改既有边缘归属台账与行段清单
  <!-- 本 change 落盘文件仅两处：新建 docs/edge-addressing-layers.md、编辑 docs/architecture.md 指针。edge-split-ownership-inventory.md 与 split-classic-client-edge-host 产物零改动 -->

## 6. 验收

- [ ] 6.1 `openspec validate establish-edge-addressing-layers --strict` 通过
- [ ] 6.2 自检：把四条判据套到一个文中未列出的边缘职责上，确认能得出明确结论（验证判据可用，不只是可读）
- [ ] 6.3 提交并推送控制仓（本 change 无代码改动、无部署、无打包）
