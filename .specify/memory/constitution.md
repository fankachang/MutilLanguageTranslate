# TAIDE Translation System Constitution

## Core Principles

### I. Offline-First Architecture
All system components must operate in completely isolated internal network environments without external internet connectivity. This includes:
- Model deployment: All AI models must be deployable locally without external API calls
- Dependency management: All dependencies (libraries, frameworks, static assets) must be available offline
- Self-contained: No reliance on external CDNs, cloud services, or remote resources

### II. Performance as a Feature
Translation performance is a core user experience metric, not optional:
- GPU mode: Target 2-3 seconds for 1000-character translations (95th percentile)
- CPU mode: Target 8-10 seconds for 1000-character translations (95th percentile)
- Concurrency: Support 100 concurrent users without service degradation
- All architecture decisions must consider performance impact and be justified

### III. Simplicity and Pragmatism (NON-NEGOTIABLE)
Avoid over-engineering. Choose simpler solutions unless complexity is justified:
- YAGNI principle: "You Aren't Gonna Need It" - implement features when needed, not speculatively
- Prefer Django built-ins over third-party libraries when functionality overlaps
- Avoid heavy frameworks (React/Vue) when lightweight alternatives (HTMX/Alpine.js) suffice
- Question every new dependency: "Can we achieve this with existing tools?"

### IV. Test-Driven Development
Testing is mandatory, not optional:
- Unit tests: All business logic must have unit test coverage
- Integration tests: API contracts must be verified with integration tests
- Performance tests: Load testing required for concurrency claims (100+ users)
- Test structure: tests/unit/, tests/integration/, tests/performance/

### V. Observability and Maintainability
Systems must be debuggable and maintainable in production:
- Structured logging: Three-level logging (ERROR/WARNING/INFO) with 30-day retention
- Monitoring: System status API exposing resource usage, error statistics, concurrency metrics
- Health checks: /api/health endpoint for monitoring tools
- Error context: All errors must include actionable information (request_id, error_code, suggested resolution)

### VI. Configuration Over Code
Configuration must be externalized and environment-specific:
- YAML-based configuration: config/app_config.yaml, config/model_config.yaml, config/languages.yaml
- No hardcoded values: Resource limits, timeouts, paths must be configurable
- Sensible defaults: System must work out-of-box with minimal configuration
- Documentation: All configuration options must be documented in quickstart.md

### VII. API-First Design
Public interfaces (APIs) are contracts and must be stable:
- RESTful principles: Follow REST conventions for HTTP methods, status codes, resource naming
- Schema validation: All request/response formats must be explicitly defined
- Error consistency: Use standardized error codes and formats across all endpoints
- Backward compatibility: Breaking changes require major version bump and migration guide

## Additional Constraints

### Technology Stack Requirements
- **Language**: Python 3.11+ (no Python 2.x, minimum version enforced)
- **Framework**: Django 4.2+ with ASGI support
- **AI Model**: TAIDE-LX-7B-Chat (local deployment only)
- **Frontend**: Server-rendered templates preferred over SPA (Single Page Applications)
- **Database**: Avoid traditional databases (PostgreSQL/MySQL) unless justified; use SQLite for task queues only

### Security Requirements
- **Authentication**: Not required for internal network deployment, but system must be prepared for future authentication integration
- **Input validation**: All user inputs must be validated server-side (never trust client-side validation alone)
- **Rate limiting**: Protect against abuse even in internal networks (IP-based rate limiting)
- **File uploads**: Strict file type and size validation for batch translation uploads

### Deployment Constraints
- **Internal network**: System must deploy and operate without internet access
- **Single server**: Initial design targets single-server deployment (no distributed systems)
- **Resource isolation**: GPU memory must be limited to prevent OOM errors (0.8 fraction max)
- **Graceful degradation**: System must automatically fall back to CPU mode if GPU unavailable

## Development Workflow

### Code Review Requirements
- **Self-review first**: Author must review their own code before requesting peer review
- **Constitution compliance**: Reviewer must verify changes comply with all principles
- **Test coverage**: New features require corresponding tests (no code without tests)
- **Documentation updates**: Changes affecting APIs or configuration must update relevant docs

### Git Commit Standards
- **Language**: All commit messages, code comments, documentation MUST be in Traditional Chinese (zh-TW)
- **Format**: Follow Conventional Commits specification (feat/fix/docs/refactor/test)
- **Scope**: Include feature branch prefix (e.g., "feat(001-taide-translation): 新增即時翻譯 API")
- **Body**: Explain WHY, not just WHAT (link to spec.md or issue when relevant)

### Testing Gates
- **Pre-commit**: Unit tests must pass locally before committing
- **Pre-push**: All tests (unit + integration) must pass before pushing
- **Pre-deploy**: Performance tests must validate concurrency targets before production deployment
- **Regression**: Breaking changes require explicit approval and migration documentation

## Governance

### Constitution Authority
- This constitution supersedes all other development practices and guidelines
- When conflicts arise between convenience and constitution, constitution wins
- Exceptions require explicit documentation and team consensus

### Amendment Process
- Amendments require documentation in constitution.md with rationale
- Breaking changes to principles require migration plan for existing code
- Version and amendment date must be updated with each change

### Complexity Justification
- Any architecture decision that violates "Simplicity and Pragmatism" must be documented in plan.md under "Complexity Tracking"
- Justification must include: (1) Why needed, (2) Why simpler alternatives rejected
- Examples: Adding 4th microservice, using Repository pattern when direct DB access sufficient

### Enforcement
- All code reviews must verify constitution compliance
- CI/CD pipelines should automate constitution checks where possible (linting, test coverage)
- Refer to [AGENTS.md](../../AGENTS.md) for agent-specific development guidance

**Version**: 1.0.0 | **Ratified**: 2026-01-08 | **Last Amended**: 2026-01-08

