# text-card-rendering Specification

## Purpose
TBD - created by archiving change textcard-cover-form. Update Purpose after archive.
## Requirements
### Requirement: 确定性云端渲染栈与诚实降级

文字卡 SHALL 在云端进程内以纯 JS 排版引擎（satori）+ 预编译栅格库（@resvg/resvg-js）渲染，依赖版本精确 pin 并提交 lockfile；字体以子集化改名后的 OFL 字体连同码点/字宽清单（font-manifest）入仓，运行时 SHALL NOT 依赖主机字体或 fontconfig。同一（文案, seedKey）输入 SHALL 产出字节级一致的 PNG（逻辑网格 1080×1440，输出 1728×2304，与现役生成式配图像素一致）。渲染模块 SHALL lazy 加载，加载失败或字体 sha256 校验不过 SHALL 返回不可用（null）+ 显式告警：服务启动 MUST NOT 因渲染栈缺失而失败，text_card 请求 SHALL 诚实降级生成式并审计 `renderer_unavailable`。

#### Scenario: 同输入字节级一致
- **WHEN** 同一（文案, seedKey）渲染两次
- **THEN** 两次 PNG 字节全等（golden 测试以 pin 的精确版本为准）

#### Scenario: 渲染栈缺失服务不崩
- **WHEN** ECS 上原生栅格包加载失败或字体校验不过
- **THEN** 工厂返回 null + 显式告警，服务照常启动，text_card 请求走生成式封面且审计 `renderer_unavailable`

#### Scenario: 依赖变更批部署含生产安装与冒烟
- **WHEN** 部署批含 package.json 变更
- **THEN** 部署序列 SHALL 含 ECS 全量依赖安装步骤（`npm ci` 或 `npm install`，MUST NOT 使用 `--omit=dev`——服务以 tsx 直跑源码、tsx 在 devDependencies），且健康检查含渲染冒烟（golden 卡 1728×2304 非零字节断言，顺带验证预编译包与该机 glibc 兼容）

### Requirement: 字形覆盖与溢出红线

渲染前 SHALL 对全部码点做字体覆盖预检，未覆盖码点（含 emoji）SHALL 确定性剥离并记入审计（sanitized）；剥离后标题过短 SHALL 显式失败（invalid_copy）。标题 SHALL 走字号阶梯（116/100/84）与最多 3 行约束，最小字号仍超行 SHALL 在字形边界硬截加省略号并标记 truncated。垂直总高溢出 SHALL 经确定性缩减阶梯（要点行数 → 要点条数 → 丢标签行）逐级消解且每步记入审计（reductions）。断行/字号/缩减 SHALL 全部由自有纯函数依 font-manifest 的 advance 宽度决定（satori 只做盒子定位、每行 nowrap）；行宽预算 SHALL 内置 2-3% 安全系数吸收 Latin kerning/标点挤压等字形度量差，布局测试集 SHALL 含中英数字混排与全角半角标点相邻样例并断言渲染产物无越界像素。SHALL NOT 渲出未覆盖字形占位块（豆腐块）、SHALL NOT 静默裁切、SHALL NOT 发布溢出卡面；无法消解时 SHALL 显式失败回落生成式。

#### Scenario: emoji 与生僻字剥离及过短失败
- **WHEN** 文案含 emoji 与字体未覆盖的生僻字
- **THEN** 未覆盖码点被确定性剥离且 meta.sanitized 记录；剥后标题少于 4 个字形则返回 invalid_copy 显式失败、封面回落生成式

#### Scenario: 超长标题走字号阶梯与硬截
- **WHEN** 超长洗稿标题排版
- **THEN** 依次尝试 116/100/84 字号，84 仍超 3 行则末行字形边界截断加省略号且 meta.truncated 上审计

#### Scenario: 垂直溢出逐级消解全程记账
- **WHEN** 最坏组合（3 行标题 + 5×2 行要点 + 标签 + 页脚）总高超可用高
- **THEN** 缩减阶梯逐步消解且 meta.reductions 逐项记录，绝无静默丢内容

#### Scenario: 混排样例无越界像素
- **WHEN** 布局测试跑中英数字混合、全角半角标点相邻的 golden 样例
- **THEN** 渲染产物断言无越界像素（安全系数吸收字形度量差）

### Requirement: 主题确定性与反指纹

配色与版式 SHALL 只从本系统模板表（8 色板 × 2 版式 × 3 角部装饰的离散格点）确定性解析：账号哈希（FNV-1a(accountId)）定该账号的主配色对与版式（账号内视觉身份稳定），帖级种子（FNV-1a(accountId+sourceId)，缺 sourceId 用标题哈希；MUST NOT 含随机运行令牌）只定装饰选择。色板 hex SHALL 固定不抖，模板表全表文字/背景对比度 SHALL ≥4.5:1（离线单测全表校验）。同一（账号, 帖子）重试 SHALL 字节恒定。SHALL NOT 从参照图取色。卡面 SHALL NOT 渲染 AI 水印或任何固定水印（AI 标识走既有合规元数据与发布声明）。

#### Scenario: 账号视觉身份稳定
- **WHEN** 同一账号两篇不同笔记各自渲染
- **THEN** 主配色对与版式一致，产物因文案不同而字节互异

#### Scenario: 重试字节恒定
- **WHEN** 同一（账号, 笔记）发布重试再次渲染
- **THEN** 与首次产物字节全等（种子不含随机运行令牌）

#### Scenario: 模板表离线可证
- **WHEN** 离线单测遍历全部（色板, 版式, 装饰）组合
- **THEN** 对比度 ≥4.5:1 全过，任意两色板 hex 距离达下限

### Requirement: 渲染输入结构隔离（防搬运）

渲染器输入签名 SHALL 仅含洗稿产物文案（标题/要点/标签）与主题种子，SHALL NOT 存在原笔记图片像素、图片 URL、取色结果、版式坐标或 OCR 文本的任何入口（编译期类型层结构保证，非运行时相似度度量）。既有「参照图可借色彩/构图」许可对文字卡渲染路径 SHALL NOT 适用。渲染器 SHALL 为独立注入依赖，SHALL NOT 实现生图提供方接口、SHALL NOT 进入图源路由表（防被跨源 fallback 路由到）。

#### Scenario: 类型层无原图入口
- **WHEN** 编译期检查渲染器类型契约
- **THEN** 原图信息在类型层面无入口，与原图配色/版式无信息通路

#### Scenario: 原卡配色不进新卡
- **WHEN** 原笔记封面为某配色文字卡、新帖渲染文字卡
- **THEN** 新卡配色/版式由账号哈希与本系统模板表决定，与原图无关

### Requirement: 确定性简洁长文版式

文字卡 renderer SHALL 在旧要点卡之外支持 `article_cover` 和 `article_page`。长文版式 SHALL 使用固定的浅灰纸面、深灰常规字重正文、稳定字号与行高、按完整短句分段和语义词组断行；封面 SHALL 只使用黑色主题区、黄色标题和浅灰正文区，内页 SHALL 只使用标题、细分隔线和正文。长文版式 MUST NOT 渲染英文眉题、页码、网格、圆角信息框、标签胶囊、角部装饰、水印或来源图像元素。

#### Scenario: 文章内页保持简洁
- **WHEN** renderer 收到有效 `article_page` 文案
- **THEN** 输出为 1728×2304 PNG，包含标题、细分隔线和常规字重短句正文
- **AND** 输出不包含英文眉题、页码、网格、卡片框或标签

#### Scenario: 文章封面使用固定分区
- **WHEN** renderer 收到有效 `article_cover` 文案
- **THEN** 输出上部为黑色主题区和黄色标题，下部为浅灰短句正文，不加入其它装饰

#### Scenario: 旧要点卡逐字保持原路径
- **WHEN** renderer 收到不带长文 `layoutKind` 的历史 `title + bullets + tags` 文案
- **THEN** 继续调用现有要点卡布局、主题与缩减逻辑，不因新增长文能力改变结果

### Requirement: 长文断行、占用与溢出可证

长文布局 SHALL 使用仓内 font-manifest 字宽进行标题和正文断行，正文每个输入段落 SHALL 先按完整句边界规范为短句块。renderer SHALL 计算标题行数、正文行数、段落数量、内容底边和页面占用率并写入审计元数据。`article_page` 占用率低于下限或高于上限、任一正文块超过行数上限、或存在无法覆盖的字形时 SHALL 显式返回失败；不得拉伸行高、静默截断或删除段落。

#### Scenario: 短句按字体度量换行
- **WHEN** 长文段落含中文、Latin 和全角标点混排
- **THEN** 断行由 font-manifest 纯函数确定，标点不孤立到下一行，渲染像素不越出左右边界

#### Scenario: 页面占用不足显式失败
- **WHEN** `article_page` 的计算占用率低于 0.80
- **THEN** renderer 返回 `invalid_copy` 并说明内容过疏，不输出大面积空白卡

#### Scenario: 页面溢出显式失败
- **WHEN** `article_page` 的计算占用率高于 0.96 或内容底边超过安全区域
- **THEN** renderer 返回 `invalid_copy`，不得截掉末尾段落后伪装成功

#### Scenario: 同输入仍字节级一致
- **WHEN** 同一长文文案和 seed 渲染两次
- **THEN** 两次 PNG 字节全等，布局审计元数据也完全相同

### Requirement: 长文审核失败不做无效确定性重渲染

由于长文模板不消费来源装饰令牌，长文卡第一次视觉审核失败后系统 SHALL NOT 通过改变装饰令牌或帖子种子再次渲染同一文案；失败 SHALL 按现有审核失败语义如实结算。旧要点卡的现有一次样式收敛行为保持不变。

#### Scenario: 长文视觉失败只审核一次
- **WHEN** 已渲染的 `article_page` 第一次视觉审核返回 failed
- **THEN** 系统不再次调用 renderer 生成等价长文 PNG，并按失败结果结算该槽

#### Scenario: 要点卡保持现有收敛
- **WHEN** 历史要点卡第一次视觉审核失败且存在来源样式令牌
- **THEN** 系统仍可按现有一次严格样式重渲染逻辑处理

