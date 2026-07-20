## ADDED Requirements

### Requirement: 万相参考图生成默认使用 1K 输出规格

当当前图片 provider 为 DashScope/Wanxiang 且生成请求包含至少一张可用参考图时，系统 SHALL 默认向 Wanxiang 提交 `size = "1K"`，以降低参考洗稿配图的像素与传输负担。系统 MUST 保留显式运行时尺寸覆盖能力；该默认值变更 MUST NOT 改变无参考图 Wanxiang 请求、Seedream 请求或确定性文字卡的既有尺寸语义。

#### Scenario: 带参考图且未配置覆盖时使用 1K

- **WHEN** Wanxiang 生成请求包含可用参考图，且未提供构造参数或 `AIDCP_WANXIANG_REFERENCE_IMAGE_SIZE` 环境覆盖
- **THEN** 提交给 Wanxiang 的请求参数包含 `size = "1K"`

#### Scenario: 显式参考图尺寸覆盖优先于 1K 默认值

- **WHEN** Wanxiang 生成请求包含可用参考图，且运行时显式配置 `AIDCP_WANXIANG_REFERENCE_IMAGE_SIZE = "2K"`
- **THEN** 提交请求使用 `size = "2K"`，系统 MUST NOT 将其改写为 `1K`

#### Scenario: 无参考图请求保持既有默认

- **WHEN** Wanxiang 生成请求不包含可用参考图，且未配置普通图片尺寸覆盖
- **THEN** 提交请求继续使用既有 `size = "1024*1024"`，不受参考图默认值变更影响

#### Scenario: 其它图片路线尺寸不变

- **WHEN** 发布配图走 Seedream provider 或确定性文字卡渲染路线
- **THEN** 该路线继续使用其既有尺寸配置与输出尺寸，不读取 Wanxiang 参考图尺寸默认值
