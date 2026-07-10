## ADDED Requirements

### Requirement: Image Generation Usage Is Recorded Honestly

The system SHALL record publish image generation attempts in the usage store so operators can see image-model activity by account, role, provider, and model.

- Cloud SHALL record each image provider attempt with `role='publish:ImageGenerator'`, the current publish account id, the active image provider id, and the active image model name.
- Image usage rows SHALL increment `calls` for each provider attempt and `ok_calls` only when a real image URL is produced by the provider.
- Because image providers do not return token usage, image usage rows SHALL store prompt, completion, and total token counts as 0. The system MUST NOT synthesize token counts from image count, prompt length, pixels, duration, cost, or any provider-specific estimate.
- Usage recording MUST NOT block or alter the image generation result. Recorder failures SHALL be swallowed like text LLM usage failures.
- Token billing price refresh targets SHALL ignore zero-token image usage rows and MUST NOT request token price snapshots for image-generation rows.
- The console SHALL label `publish:ImageGenerator` as an image-generation role and SHALL avoid presenting image usage rows as token consumption beyond their honest zero-token counts and call counts.

#### Scenario: Successful image generation appears in usage

- **GIVEN** a publish run generates two images through provider `volcengine` and image model `doubao-seedream-4-5-251128`
- **WHEN** the image provider returns two real image URLs
- **THEN** the usage store records two calls for `role='publish:ImageGenerator'`, provider `volcengine`, and that model
- **AND** `ok_calls` is 2 while prompt, completion, and total tokens are all 0.

#### Scenario: Failed image generation records a failed call without fake tokens

- **WHEN** an image provider attempt returns no URL
- **THEN** the usage store records the call with `ok_calls` unchanged
- **AND** token counts remain 0.

#### Scenario: Image rows do not become token price refresh targets

- **GIVEN** local usage contains only image-generation rows with total tokens equal to 0
- **WHEN** an operator triggers provider model pricing refresh
- **THEN** cloud does not include those image rows as token billing price targets
- **AND** it MUST NOT write or request token price snapshots for the image model.
