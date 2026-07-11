# panel-curated-content Specification (delta)

## ADDED Requirements

### Requirement: 精选页展示图片快照并控制洗稿是否带图参考

后台精选内容页 SHALL 在笔记行展示可用的原笔记图片参考快照。列表 SHOULD 展示首张可用缩略图，详情视图 SHALL 展示有序图集、图片来源状态和可打开的原图/OSS 链接。缺少图片时 MUST 呈现为空状态，MUST NOT 渲染死链或占位假图。

当运营从精选笔记触发参照洗稿时，若该行存在可用图片，界面 SHALL 让运营明确知道本次会带图参考，并允许选择“仅文本参照”。前端请求体 SHALL 携带 `useReferenceImages?: boolean`；服务端 MUST 只在该行属于请求账号且图片可用时把图片放入 `referenceNote.images`。评论行、空正文壳行和无图片行保持既有拒绝/文本-only 行为。

#### Scenario: 列表展示首张缩略图

- **WHEN** 一条精选笔记有至少一张可用 `ossUrl` 或 `sourceUrl`
- **THEN** 列表展示首张图缩略图，详情视图展示按顺序排列的图集

#### Scenario: 图片缺失不渲染死链

- **WHEN** 一条精选笔记没有可用图片
- **THEN** 页面显示无图片状态，不渲染打不开的链接或占位假图

#### Scenario: 洗稿触发可选择带图或仅文本

- **WHEN** 运营对有图精选笔记点击洗稿
- **THEN** 界面默认带图参考，并允许改为仅文本参照；请求体中的 `useReferenceImages` 与选择一致

#### Scenario: 服务端仍按账号和行类型防越权

- **WHEN** 洗稿触发请求携带 `accountId` 与 `useReferenceImages`
- **THEN** 服务端仍通过 `getOneForAccount` 读取行，仍只允许本账号 `note` 行且正文非空，MUST NOT 因图片字段泄露其它账号行

#### Scenario: 红线反例 - 前端默认宣称用了图片但服务端未带图

- **WHEN** 服务端发现图片不可用、provider 不支持或运营选择仅文本
- **THEN** UI/回执/审计 MUST 可区分“未使用图片参考”，MUST NOT 用成功提示暗示图片已参与生成
