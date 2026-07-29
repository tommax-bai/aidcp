## ADDED Requirements

### Requirement: Native feed-surface reads perform the full in-place expansion, not a rendered-text scrape

Native 的 Facebook feed 面 `note.open` SHALL 执行 `facebook-feed-browse` 已要求的完整就地读，而不是把卡片上当前已渲染的文字抓走就返回。它 SHALL 按命令携带的规范帖身份锁定**唯一**顶层卡片；当该卡消息容器的全文已在 DOM 内、仅被视觉截断时 SHALL 走免点击捷径；否则 SHALL 只点击该消息容器内锚定的展开控件（MUST NOT 点击链接，使用页内点击）。展开前后 SHALL 校验页面 URL、弹层数量与目标卡序号三者均未变化。

三条诚实终态 MUST 成立：① 点击展开后正文渲染长度未增长 → 报「展开无效」终态，MUST NOT 当成功；② 上述三项校验中任一发生变化 → 中止就地读、回落详情页导航、以 detail 面诚实上报该帖；③ 卡片本就没有展开控件的短帖，读到什么算什么，是正常成功、MUST NOT 报 `no_target`。

Native SHALL 对规则模式与人设模式采用同一条执行路径，MUST NOT 按账号浏览模式分叉，也 MUST NOT 在客户端持有模式事实。

#### Scenario: Clamped long post is expanded before it is reported

- **WHEN** feed 面 `note.open` 命中一条正文被折叠、且展开点击前后 URL / 弹层数 / 目标卡序号均未变化的长帖
- **THEN** Native 读到展开后的完整正文并作为该帖内容上报
- **AND** 上报的正文长度大于展开前的渲染长度

#### Scenario: Full text already present is read without a click

- **WHEN** 消息容器的全文已在 DOM 内、仅被视觉截断
- **THEN** Native 走免点击捷径读全文，MUST NOT 为取全文而额外点击展开控件

#### Scenario: Expansion without growth is reported honestly

- **WHEN** Native 点击了展开控件、但该卡正文的渲染长度没有增长
- **THEN** Native 返回「展开无效」终态，MUST NOT 上报帖子详情、MUST NOT 计入一次浏览

#### Scenario: Context change aborts the in-place read and falls back to detail

- **WHEN** 展开过程中页面 URL 变化、出现弹层、或目标卡序号位移
- **THEN** Native 中止就地读，改走详情页导航读取，并以 detail 面诚实上报该帖

#### Scenario: Short post without an expand control is a normal success

- **WHEN** 目标卡片没有任何展开控件
- **THEN** Native 以读到的正文正常成功上报，MUST NOT 返回 `no_target` 或展开无效

#### Scenario: Browse mode does not change the execution path

- **WHEN** 同一条 feed 面 `note.open` 分别发生在规则模式账号与人设模式账号上
- **THEN** Native 的锁卡、展开、校验与上报行为逐条相同

### Requirement: Native consumes the cloud pacing fields it accepts

Native 的命令映射层与执行层 SHALL 实际消费云端随决策指令下发的节奏字段，MUST NOT 出现「映射层收下字段、执行层静默丢弃」。收到带 `thinkMs` 的动作命令时，Native SHALL 在**执行该动作前**等待抖动后的时长；该等待与既有最小间隔语义测同一「now → 执行本动作」跨度，两者 SHALL 取 max、MUST NOT 相加。

Native 完成一次 feed 面就地读后 SHALL 按读到的正文长度（叠当前 `tempo`）确定一条边缘本地 read floor，锚在就地读开始时刻；随后离开该内容的 `page.scroll` SHALL 在该 read floor 与云端 `dwellMs` 的新卡锚点之间取 max、MUST NOT 相加，也 MUST NOT 因就地读比进详情页快而出现零延迟秒滚。

#### Scenario: thinkMs delays the action instead of being discarded

- **WHEN** Native 收到一条携带非零 `thinkMs` 的动作命令，且距上次操作完成的间隔尚未达到该字段值
- **THEN** Native 在触达页面前先等待抖动后的时长再执行

#### Scenario: thinkMs and the minimum action interval do not stack

- **WHEN** 同一次动作既受最小间隔约束又携带 `thinkMs`
- **THEN** 实际等待为两者的较大值，而非两者之和

#### Scenario: In-place read establishes a read floor before the next scroll

- **WHEN** Native 就地读完一条长帖，随即收到带 `dwellMs` 的 `page.scroll`
- **THEN** 实际停留不小于「就地读 read floor」与「新卡锚点 dwell 目标」中的较大者
- **AND** 两者 MUST NOT 相加

#### Scenario: A short in-place read never becomes a zero-delay scroll

- **WHEN** 就地读在极短时间内完成
- **THEN** Native 仍补足 read floor 后才发出下一条 `page.scroll`

## MODIFIED Requirements

### Requirement: Native parity is protected by behavior-level regression tests

The Edge repository SHALL contain focused Native tests derived from the established Facebook TypeScript behavior cases for Feed settling and continuation, blocker/consent classification, exact target selection, comment terminal classification, join readiness, publish integrity, unsupported command routing, **feed-surface in-place expansion with its honest terminal outcomes, and actual consumption of the cloud pacing fields**. Tests MUST assert externally meaningful state and reason codes rather than only checking that a selector exists or a router branch returns.

一条 Native 行为被判定为「已迁移」的判据 SHALL 是**行为对等**，MUST NOT 是「返回了同形状的投影结构」。任何把既有 TypeScript 页面行为搬入 Native 的任务，在其对应行为缺少上述判据的回归测试之前 MUST NOT 标记完成。

#### Scenario: Native cutover regression is rejected

- **WHEN** a Native implementation again treats loading/unreportable Feed as empty, falls back to the first post, uses a non-equivalent ambiguous reason, or actuates an unsupported Facebook command
- **THEN** a focused parity test fails before integration

#### Scenario: A rendered-text scrape cannot pass as an in-place read

- **WHEN** Native 的 feed 面 `note.open` 只返回卡片当前已渲染的文字、不做展开与校验
- **THEN** 一条聚焦的对等测试在集成前失败

#### Scenario: Silently dropping a pacing field fails a parity test

- **WHEN** Native 的映射层接收 `thinkMs` 或就地读 read floor 相关输入、执行层却不产生对应等待
- **THEN** 一条聚焦的对等测试在集成前失败
