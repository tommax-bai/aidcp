## Context

The settings page currently presents itself as "model config" and exposes only model/provider choices plus model API keys. The encrypted credential store is already generic (`provider_credentials(provider, field)`), and cloud already reads several non-model credentials from that store or env, including OSS (`oss/access_key_id`) and billing refresh (`aliyun/billing_access_key_*`, `volcengine/billing_access_key_*`).

The operator problem is naming and reachability: billing price refresh reports missing credentials even when model API keys exist, because those are different platform-level AccessKey pairs. Operators should manage those platform credentials from the console without pasting secrets into docs or commits.

## Goals / Non-Goals

**Goals:**

- Reposition `/settings` as "平台配置", with model/provider settings as one section.
- Use one platform credential definition list to drive backend whitelist and frontend display.
- Add console-managed platform AccessKey pairs for Alibaba Cloud and Volcengine billing.
- Keep existing model API key behavior, encrypted storage, masking, and restart-required semantics.
- Make billing refresh consume platform-configured AccessKey pairs and avoid confusing "dashscope credential" wording for Alibaba billing.

**Non-Goals:**

- Do not change the `provider_credentials` schema.
- Do not introduce cron/scheduled billing sync.
- Do not log, document, or commit any plaintext key.
- Do not automatically grant or verify cloud-account IAM permissions; API failure remains an honest billing API error.
- Do not collapse every Alibaba use case into one forced credential if a more specific credential already exists.

## Decisions

### D1: Add a platform credential registry, not another table

Keep `provider_credentials(provider, field)` unchanged and define allowed credentials in code:

- Model API credentials:
  - `dashscope/dashscope_api_key`
  - `volcengine/volcengine_api_key`
- Platform AccessKey credentials:
  - `aliyun/access_key_id`
  - `aliyun/access_key_secret`
  - `volcengine/access_key_id`
  - `volcengine/access_key_secret`

The registry will include label, group, input kind, env fallback names, and whether restart is required. This keeps the existing encryption path and avoids schema migration risk.

Alternative considered: separate `platform_credentials` table. Rejected because the existing table is already generic and safely encrypted.

### D2: Prefer specific runtime fields, then generic platform fields, then env

Runtime lookups should preserve existing keys while adding generic platform fallbacks:

- Billing refresh for Alibaba:
  - `aliyun/billing_access_key_id` and `aliyun/billing_access_key_secret`
  - then `aliyun/access_key_id` and `aliyun/access_key_secret`
  - then existing env aliases
- Billing refresh for Volcengine:
  - `volcengine/billing_access_key_id` and `volcengine/billing_access_key_secret`
  - then `volcengine/access_key_id` and `volcengine/access_key_secret`
  - then existing env aliases
- OSS can continue to read `oss/access_key_*`; adding `aliyun/access_key_*` as fallback is useful but not required for billing.

This allows one Alibaba platform AK to be reused where appropriate without breaking deployments that intentionally split credentials by purpose.

### D3: Keep one write endpoint with stronger whitelist

`PUT /api/config/credential` remains the write API. The only change is replacing the text-provider-only whitelist with the platform credential registry. Unknown `(provider, field)` pairs still return 400 and write nothing.

### D4: Frontend groups credentials by platform purpose

The settings page becomes:

- "模型与厂商": global text/image provider and model names.
- "平台凭据": grouped credential rows:
  - Model API keys.
  - Platform AccessKeys for billing/querying cloud account charges.

Inputs remain password fields; plaintext never round-trips. Successful saves clear only that field input.

### D5: Operator-facing missing-credential labels use platform names

Manual price refresh may still key diagnostics by provider internally, but the console should render clear labels such as "阿里云账单凭据" and "火山账单凭据" instead of implying that the DashScope model API key is missing.

## Risks / Trade-offs

- [Risk] A platform AK may lack billing API permission even though it is configured. → Treat provider API rejection as `billing_api_error` and keep the refresh result honest.
- [Risk] One user-visible page now contains several credential types. → Use sections and concise labels instead of adding another settings route.
- [Risk] Existing stored `oss/access_key_*` or `billing_access_key_*` values may exist. → Runtime lookup keeps specific credentials first, so existing deployments keep working.
- [Risk] Saved credentials require restart before runtime users see them. → Preserve existing warning and success copy: encrypted save succeeds, runtime effect after cloud restart.
