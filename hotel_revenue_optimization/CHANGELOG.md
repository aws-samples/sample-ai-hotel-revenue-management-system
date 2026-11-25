# Changelog

All notable changes to the Hotel Revenue Optimization System will be documented in this file.

## [2.1.1] - 2026-11-25

Security and maintenance release for the agent and the web UI. If you ran `build.sh` or `deploy.sh` from an
earlier version, recreate your virtual environment (see "Install AgentCore CLI" in the README).

### Security
- **Install only AWS packages**: `build.sh` and `deploy.sh` install `bedrock-agentcore` and
  `bedrock-agentcore-starter-toolkit` at the versions in `requirements.txt` and stop if that fails. Earlier
  versions fell back to `bedrock-agentcore-sdk`, `amazon-bedrock-agentcore` and `agentcore`, which are not AWS
  packages. The README no longer tells you to download the CLI from a placeholder URL.
- **Patched dependencies**: `bedrock-agentcore-starter-toolkit` 0.1.0 to 0.1.13 (CVE-2026-4269); the beta
  `aws_opentelemetry_distro_genai_beta` replaced by `aws-opentelemetry-distro` 0.24.0 or later, which brings
  OpenTelemetry 1.45.2 (CVE-2026-114603, CVE-2026-126360, CVE-2026-116694). Web UI: Flask 3.1.3, Werkzeug 3.1.9,
  PyJWT 2.15.1, cryptography 50.0.2, Markdown 3.10.3, Requests 2.34.2, python-dotenv 1.2.4, Flask-WTF 1.2.2.
- **Version floors**: unquoted `>=` in `pip install` lines was read by the shell as a redirect, so the floor was
  dropped; the specifiers are quoted now.
- **Containers**: the agent image runs as a non-root user in `/app`, and a `.dockerignore` keeps `.env`, virtual
  environments and old reports out of the image.
- **Reports**: each run writes its own report file and returns it only when the crew finished, so a failed run
  can no longer return an earlier run's report.
- **Account-specific files removed**: `create_correct_target.sh` and `authorizer_config.json`, and the AWS account
  ID, runtime ARN and monitoring workspace ID of the original deployment.
- **Web UI**: Cognito ID tokens are verified (signature against the user pool keys, issuer, audience, token use,
  expiry) before a session is created, and `/auth/process-token` takes the identity only from a verified token;
  production refuses to start without a strong `SECRET_KEY`, which the stack now generates in AWS Secrets
  Manager along with passing the Cognito client secret as a secret; sign-in uses `state` and PKCE; `next`
  redirects stay on the site; rendered reports are sanitized; email reports go only to the signed-in user's
  verified address; secrets and tokens are no longer logged; the task role is scoped to the calls the app makes;
  the image builds from the public Python 3.12 base image and runs as a non-root user. Tests:
  `hotel_revenue_optimization_ui/tests/test_security.py`.

### Changed
- **Current Bedrock models**: the Claude 3.x, Claude 3.7 Sonnet, Claude Sonnet 4, Nova Premier and Titan Text
  Express models the sample used have reached end of life. The tiers now use Amazon Nova 2 Lite, Amazon Nova Micro,
  Claude Sonnet 5.5 and Claude Haiku 5.5, through cross-region inference profiles. All model IDs are in
  `utils/model_config.py`, with `MODEL_TIER1` to `MODEL_TIER4`, `BEDROCK_INFERENCE_PROFILE_PREFIX` and
  `BEDROCK_CLAUDE_EFFORT` to override them.
- **Claude 5 requests**: Claude 5 models reject `temperature` and `top_p`, and reason before they answer by
  default; requests to Claude send only `maxTokens` and an effort level (default `low`).
- `MODEL_PROVIDER` is read on every lookup instead of once at import.

### Fixed
- A failed model call was returned as report text ("Error invoking model ..."); it now raises, and the call is
  retried once on the provider's basic-tier model.
- With CrewAI 0.203 (what `crewai>=0.148.0,<1.0.0` installs today) the crew could not be created: the embedder
  setting used a removed format. Memory is off, so the embedder is no longer set.
- CrewAI's planning step forced a tool call, which Claude 5 rejects; the crew now uses CrewAI's text path, and
  reruns without planning if the planner's output cannot be parsed.
- CrewAI 0.203 waited 20 seconds for an answer to a first-run trace prompt on every new runtime session.
- The CrewAI instrumentation in `aws-opentelemetry-distro` 0.24 fails every CrewAI 0.x run, so the container
  images set `OTEL_PYTHON_DISABLED_INSTRUMENTATIONS=aws_crewai`; Bedrock calls are still traced.
- Web UI: `app/services/email_report.py` did not parse, so the UI could not start; Flask-WTF 1.1.1 did not import
  with Werkzeug 3; the `ecs.yaml` security groups referenced each other, so the stack could not deploy.

### Added
- `scripts/check_models.py` checks that every configured model answers in your Region.
- README section "Updating models and AWS package versions".

### Known issues
- CrewAI 0.203.2, the latest CrewAI before 1.0, pins `litellm` 1.74.9, `chromadb` 1.1.x and `json-repair`
  0.25.2, which have published advisories. The LiteLLM and Chroma advisories are in their servers, which this
  sample does not run (no model call goes through LiteLLM, and memory is off), and the `json-repair` one is in
  schema repair code that 0.25.2 does not have. Moving to CrewAI 1.x removes them.

## [2.1.0] - 2025-09-23

### Added
- **Provider-Based Model Architecture**: Clean separation of model providers (AMAZON, ANTHROPIC, HYBRID)
- **Amazon Nova Model Support**: Full integration with Nova Premier, Pro, Lite, and Micro models
- **Inference Profile Support**: Proper handling of models requiring inference profiles (Nova and latest Claude models)
- **Enhanced Observability**: Comprehensive task tracking and performance metrics
- **Clean Response Format**: Removed empty results, added DEBUG-level task logging

### Changed
- **Default Provider**: AMAZON (Nova models) for optimal speed/cost balance
- **Model Configuration**: Provider-based tiers instead of mixed model fallbacks
- **Performance Optimization**: 45s execution time with Amazon Nova models
- **Claude 3.7 Sonnet**: Updated to use Claude 3.7 with prompt caching for ANTHROPIC provider

### Performance Benchmarks
- **AMAZON Provider**: 45 seconds (fastest, most cost-effective)
- **HYBRID Provider**: 83 seconds (balanced speed and quality)  
- **ANTHROPIC Provider**: 238 seconds (highest quality, detailed analysis)

### Fixed
- **Task Duration Logic**: Removed artificial task duration calculations
- **Observability Tracking**: Proper task completion and failure tracking
- **Model Wrapper**: Enhanced Nova model wrapper with inference profile mapping

## [2.0.0] - 2025-07-24

### Added
- **Enhanced Input Processing**: Multi-format input support (prompt, message, structured JSON)
- **Natural Language Processing**: Extract hotel information from free-form text
- **Intelligent Error Handling**: Detect irrelevant queries, booking requests, insufficient information
- **Comprehensive Testing**: Validated with multiple test scenarios and edge cases

### Fixed
- **Critical Input Processing Bug**: System now generates hotel-specific reports instead of hardcoded Miami responses
- **Crew Integration**: Corrected crew execution flow for proper input processing
- **Dynamic Hotel Analysis**: Proper integration with CrewAI framework for dynamic analysis

### Changed
- **Production Deployment**: Successfully deployed to AWS Bedrock AgentCore
- **Agent ARN**: `arn:aws:bedrock-agentcore:<region>:<account-id>:runtime/hotel_revenue_optimization-<id>`
- **Status**: Production-ready and fully operational

## [1.0.0] - 2025-06-15

### Added
- **Initial Release**: Hotel Revenue Optimization System with CrewAI and Amazon Bedrock
- **Multi-Agent Architecture**: Market Analyst, Demand Forecaster, Pricing Strategist, Revenue Manager
- **Claude Model Integration**: Support for Claude 3 Opus, Sonnet, and Haiku models
- **Comprehensive Reporting**: Detailed revenue optimization plans with implementation timelines
- **Performance Monitoring**: Basic logging and metrics collection

### Features
- **Revenue Analysis**: Current performance analysis with gap identification
- **Pricing Strategy**: Dynamic pricing recommendations and implementation plans
- **Risk Assessment**: Comprehensive risk factors and mitigation strategies
- **KPI Tracking**: Primary and secondary performance metrics
- **Financial Projections**: Revenue impact analysis with confidence levels
