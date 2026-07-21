## ADDED Requirements

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
