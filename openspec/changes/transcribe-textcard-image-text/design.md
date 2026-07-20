## Context

现有链路已经有三个可复用部件：

1. `cover-form-sensor` 可逐图判断 `text_card/photo/illustration/other`，但明确禁止输出 OCR 文字；
2. `OpenAiCompatVisionClient` 是云端统一多模态出口；
3. `CoverCardWriter` 在全卡片来源时生成有序 `cardSet`，下游按数组顺序确定性渲染。

缺口是来源文字不可见、不可追溯，也没有“来源卡 i → 生成卡 i”的语义映射。

## Goals / Non-Goals

**Goals**

- 识别并转写高置信文字卡，按参考图原始数组顺序记录。
- 让空 DOM 文字卡依真实转写内容参与精选评估与保真改写。
- 生成轮播文字卡时保持逐槽语义对应，同时继续防止逐字搬运。
- 用一个结构化字段和现有视觉/渲染链完成，保持实现简洁。

**Non-Goals**

- 不做边缘 OCR，不改协议，不把原图直接发布。
- 不从照片、插画、截图中泛化抽字。
- 不做历史全量回填；旧行在重新观测后自然获得记录。
- 不新建一套图片生成或卡片渲染系统。

## Decisions

### D1. 准入预筛后做“判形 + 一次批量转写”

共鸣预筛先执行，未通过者零视觉成本。通过后对有序图片逐张复用形态识别，只选择高置信 `text_card`；所有入选图片在一次多模态请求里转写。形态识别和转写保持两次独立调用，避免让原本禁止 OCR 的判形提示承担第二职责。

### D2. 一个 JSONB 是唯一事实源

`curated_content.text_card_transcription` 保存：

```json
{
  "version": 1,
  "status": "complete",
  "anchor": "sha256:...",
  "provider": "dashscope",
  "model": "qwen-vl-plus",
  "transcribedAt": 0,
  "cards": [
    {
      "sourceArrayIndex": 0,
      "sourceIndex": 1,
      "capturedAt": 0,
      "status": "transcribed",
      "text": "..."
    }
  ]
}
```

`cards` 必须按 `sourceArrayIndex` 升序。缺字或单卡失败用 `empty/failed` 记录，不造文字。聚合正文在消费时从成功卡片派生，不再另存 `image_text`、模型、时间等重复列。

### D3. 缓存锚基于有序图片身份

边缘现有图片协议没有抓取时间，不能假装拥有 `capturedAt`。转写锚由有序 `{sourceArrayIndex, sourceIndex, usableUrl}` 计算 SHA-256；顺序或 URL 改变即失效。同一进程再加 single-flight，避免两个同源事件并发重复付费。`capturedAt` 记录云端收到本次快照的时刻，仅供审计，不冒充边缘抓取时间。

### D4. 正文增补与来源记录分开

启用态把成功卡片文字按顺序合并到 DOM 正文，供精选评估和现有保真链消费；结构化 JSONB 保留逐卡来源。每次观测都从新的 DOM 正文重新构造有效正文，避免重复追加旧 OCR。失败时原 DOM 正文原样保留；有效正文仍空则不建精选壳行。

### D5. 第 i 张参考卡对应第 i 张生成卡

当文字卡轮播使用的每个来源槽都有成功转写时，`CoverCardWriter` 把有序槽信息传入一次 `cardSet` 文案调用：

- 输出数组顺序和来源槽顺序相同；
- 每张生成卡保留对应来源卡的信息职责和叙事位置；
- 只能使用改写终稿支持的事实，冲突时终稿优先；
- 必须换表达，原转写只用于对应和产后重叠检查。

若任一槽缺少有效转写，整套回落现有“按改写终稿拆 N 张卡”的逻辑，不猜测缺失卡内容。计划记录 `ordered_transcription` 或 `body_fallback`，便于审计。

### D6. 独立开关，默认复用现有视觉配置

`AIDCP_TEXTCARD_OCR=true` 才产生判形、转写和写入。`AIDCP_TEXTCARD_OCR_PROVIDER/MODEL` 可覆盖；缺省分别复用 `AIDCP_COVER_FORM_PROVIDER/MODEL` 的解析结果。视觉客户端仍在所选厂商缺密钥时请求前报错，转写服务捕获并记录失败，不跨厂商兜底，也不阻断浏览或发布。

## Risks / Trade-offs

- VL 可能漏字：逐卡状态与原文都保留，解析不完整就标 partial；不把缺失内容猜完整。
- 多图上下文较大：仅一次批量请求，输出上限 8192，卡片文字和生成提示均有长度上限。
- 判形逐图有额外成本：共鸣预筛前置、最大图片数沿精选上限、缓存与 single-flight 控制重复调用。
- 转写原文存在搬运风险：生成 prompt 同时收到改写终稿并明确“终稿事实优先、必须重写”，产后连续字符重叠闸继续执行。

## Migration Plan

1. 部署新增 JSONB 列与代码，旗标保持关闭。
2. 在 dev 开启，使用真实文字卡验证顺序、识别质量、缓存和逐槽生成。
3. 通过后保留 dev 开启；异常时关闭旗标即可停止新调用和新写入，旧 JSONB 对旧路径无副作用。
