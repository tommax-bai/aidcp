# console-image-upload-compression Specification

## Purpose
TBD - created by archiving change compress-admin-upload-images. Update Purpose after archive.
## Requirements
### Requirement: 管理后台发帖图片统一转 JPEG 压缩
管理后台 Facebook 发帖图片上传入口 SHALL 在把图片加入待上传队列前执行客户端预处理：所有被接受的图片文件 MUST 先在浏览器端解码、按完整画面等比绘制、转换为 JPEG 并压缩后再加入队列。转换压缩 MUST 保留完整画面内容，MUST NOT 裁剪、拉伸、补边或改变宽高比。透明像素 SHALL 以白底合成。压缩目标 SHOULD 接近或低于 600KB；若无法达到 600KB 但能生成小于源文件的 JPEG，MAY 使用最小的较小 JPEG 候选。

#### Scenario: 小图也转换为 JPEG
- **WHEN** 运营选择一张格式受支持且浏览器可转换的小图
- **THEN** 管理后台 SHALL 将该图片转换为 JPEG 后加入待上传队列
- **AND** 上传请求的 `contentType` SHALL 为 `image/jpeg`

#### Scenario: 大图压缩后入队
- **WHEN** 运营选择一张大于 600KB 的图片，且浏览器可成功解码并生成更小 JPEG
- **THEN** 管理后台 SHALL 将更小的 JPEG 结果文件加入待上传队列
- **AND** 上传请求的 `filename`、`contentType` 与 `dataBase64` SHALL 来自队列中的 JPEG 文件

#### Scenario: 压缩不得裁剪
- **WHEN** 大图压缩处理完成
- **THEN** 处理后图片的画面范围 SHALL 与原图一致，MUST NOT 只保留中间裁剪区域或固定比例裁切

#### Scenario: 转换失败或不能压小时拒绝上传
- **WHEN** 图片无法解码、无法编码为 JPEG、或没有任何 JPEG 候选小于原始文件
- **THEN** 管理后台 MUST 拒绝将该文件加入待上传队列，并向运营显示该图片无法转换压缩的错误

### Requirement: 上传队列展示压缩结果
管理后台 Facebook 发帖图片上传队列 SHALL 展示待上传 JPEG 文件的实际上传大小；队列项 SHALL 同时展示原始大小与压缩后大小，使运营能看到本地转换压缩结果。

#### Scenario: 队列显示压缩前后大小
- **WHEN** 一张 600KB 以上图片被成功压缩后加入队列
- **THEN** 队列标签 SHALL 展示原始大小到压缩后大小的变化

#### Scenario: 队列显示 JPEG 结果文件名
- **WHEN** 一张非 JPEG 源图成功转换后加入队列
- **THEN** 队列 SHALL 使用 JPEG 文件名与 JPEG 上传大小展示该项，不得继续暗示原格式会被上传

