# CI/CD Implementation Guide

## 1. Purpose and Scope

This document defines how to implement and harden CI/CD for the Education Weather Agent repository using:

- GitHub Actions as the automation platform
- GitHub Container Registry (GHCR) for Docker images

The guide is aligned with the current repository structure, tests, Docker setup, and existing workflows.

---

## 2. Current State (Already in Repository)

The project already includes:

- A CI workflow that runs:
  - Ruff lint and format checks
  - Bandit code security scan
  - pip-audit dependency vulnerability scan
  - All 6 test groups: UnitMock, UnitLLM, IntegrationMock, IntegrationLLM, SystemMock, SystemLLM
- A release workflow that builds Docker image and pushes to GHCR on git tags `v*`
- Multi-stage Docker build with non-root runtime user
- `docker-compose.yml` for container runtime
- Test markers and layer separation suitable for staged CI execution

This is a strong baseline. The remaining work is to structure a full delivery and deployment process with clear environment gates, secrets strategy, and deployment automation.

---

## 3. Required Tools, Accounts, and Access

This section lists what is required to implement CI/CD for this repository based on the current codebase, workflows, and runtime configuration.

### 3.1 Mandatory Tools and Services

- GitHub repository
  - Why required: Source control, PR flow, branch protection, Actions workflows.
  - Required access: Maintainer/Admin rights for branch protection and secrets.
- GitHub Actions (hosted runners)
  - Why required: Runs `.github/workflows/ci.yml` and `.github/workflows/release.yml`.
  - Required access: Actions enabled in repository or org, permission to use `ubuntu-latest`.
- Python 3.12 runtime in CI
  - Why required: Used by current workflows and tests.
  - Required access: Provided by `actions/setup-python`.
- Docker and Buildx
  - Why required: Builds release container image from `Dockerfile`.
  - Required access: Available on GitHub-hosted runners.
- GHCR (GitHub Container Registry)
  - Why required: Stores built release images.
  - Required access: `packages: write` permission in release workflow; package visibility configured.
- OpenAI API
  - Why required: IntegrationLLM and SystemLLM tests, plus application runtime.
  - Required access: Valid OpenAI account and API key with billing enabled.
- Telegram Bot API
  - Why required: Production bot runtime (`TELEGRAM_BOT_TOKEN`).
  - Required access: Telegram bot created via BotFather.
- Deployment host (VM/server)
  - Why required: Runs container in staging and production for CD.
  - Required access: SSH access, Docker installed, outbound network access.

### 3.2 Required Accounts

1. GitHub account with repository Maintainer/Admin rights.
2. OpenAI account with API key creation permission and active billing.
3. Telegram account to create/manage bot token in BotFather.
4. Hosting account for deployment target:
   - VPS provider account, or
   - Cloud account (AWS/Azure/GCP) if cloud deployment is chosen.

Note: AWS is not required by the current codebase itself. It is required only if AWS is selected as the deployment platform.

### 3.3 Required Secrets and Variables

- `OPENAI_API_KEY`
  - Used in CI: Yes (IntegrationLLM and SystemLLM jobs).
  - Used in runtime/CD: Yes.
  - Scope recommendation: GitHub Environment secrets (`staging`, `production`) and optionally a repo secret for CI.
- `TELEGRAM_BOT_TOKEN`
  - Used in CI: No (current CI tests do not require it).
  - Used in runtime/CD: Yes.
  - Scope recommendation: GitHub Environment secrets only.
- `DEFAULT_MODEL`
  - Used in CI: No.
  - Used in runtime/CD: Optional runtime override.
  - Scope recommendation: Environment variable on deployment host or GitHub environment variable.
- `PROMPT_VERSION`
  - Used in CI: No.
  - Used in runtime/CD: Optional runtime override.
  - Scope recommendation: Environment variable on deployment host or GitHub environment variable.

### 3.4 Registry and Runner Requirements

1. CI runner: GitHub-hosted `ubuntu-latest` is sufficient for this project.
2. Docker registry: GHCR is already integrated in `release.yml`.
3. Registry auth: workflow uses `GITHUB_TOKEN`; repository settings must allow package publishing.
4. Image naming: `ghcr.io/<owner>/<repo>:vX.Y.Z` and `ghcr.io/<owner>/<repo>:sha-<shortsha>`.

---

## 4. Target CI/CD Model

### CI (Continuous Integration)

Run on every PR and push to main branch:

1. Code quality and security checks.
2. Fast deterministic test suites first.
3. LLM-dependent test suites conditionally.
4. Build validation for Docker image.
5. Test result and coverage artifacts.

### CD (Continuous Delivery / Deployment)

Run on release tags (`v*`) and manual promotion:

1. Build immutable Docker image.
2. Push image to GHCR with versioned tags.
3. Promote image to environment (`staging`, then `production`).
4. Deploy container with environment-specific secrets.
5. Verify health and rollback if needed.

---

## 5. Branching and Release Strategy

Recommended Git flow:

- Feature branches -> Pull Request -> `main`
- Protected `main` branch:
  - Require PR review
  - Require CI checks to pass
  - Require branch up to date before merge
- Releases via semantic tags:
  - `v0.1.0`, `v0.2.0`, `v1.0.0`

Release source of truth is git tag.

---

## 6. CI Pipeline Design (GitHub Actions)

### 6.1 Trigger Matrix

- `pull_request` to `main`
- `push` to `main`
- `workflow_dispatch` for manual full regression run

### 6.2 Job Order and Cost Control

Use staged execution to reduce CI cost and runtime:

1. Static checks stage:
   - Ruff
   - Bandit
   - pip-audit
2. Deterministic tests stage (always required):
   - UnitMock
   - UnitLLM
   - IntegrationMock
   - SystemMock
3. LLM tests stage (conditional):
   - IntegrationLLM
   - SystemLLM
   - Run only when `OPENAI_API_KEY` exists
   - Run only on `main` and nightly schedule to control spend
4. Build stage:
   - Docker build test (without push) for PRs

### 6.3 Recommended CI Enhancements

- Add `concurrency` to cancel stale runs on the same branch
- Add timeout per job (for example 10-20 minutes)
- Publish JUnit/pytest artifacts for failed runs
- Add coverage report for deterministic suites
- Keep LLM jobs separate and visibly conditional based on policy

---

## 7. CD Pipeline Design (GitHub Actions)

### 7.1 Release Build

Keep current tag-based release build and extend metadata:

- Push images to GHCR with tags:
  - `:vX.Y.Z`
  - `:sha-<shortsha>`
  - `:latest` only for production-approved release
- Generate SBOM and provenance
- Run image vulnerability scan before deployment gate

### 7.2 Environment Promotion

Use GitHub Environments:

- `staging`
- `production`

Configure environment protections:

- Required reviewers for `production`
- Environment-scoped secrets
- Deployment history and audit trail

Promotion pattern:

1. Auto deploy to `staging` after release image push.
2. Run smoke test in `staging`.
3. Manual approval.
4. Deploy same immutable image digest to `production`.

---

## 8. Secrets and Configuration Strategy

### 8.1 Repository and Environment Secrets

Use the minimum required scope:

- Repo secret:
  - `OPENAI_API_KEY` (if LLM tests are enabled in CI)
- Environment secrets (`staging`/`production`):
  - `TELEGRAM_BOT_TOKEN`
  - `OPENAI_API_KEY`
  - Deployment credentials (SSH key, cloud credentials)

Never store secrets in:

- Repository files
- Docker image layers
- Workflow logs

### 8.2 Runtime Variables

Expected by application:

- `TELEGRAM_BOT_TOKEN`
- `OPENAI_API_KEY`
- `DEFAULT_MODEL` (if overridden from default)
- `PROMPT_VERSION` (if overridden from default)

Set these per environment during deployment, not during image build.

---

## 9. Recommended Workflow Set

Implement or evolve toward this workflow set:

1. `ci.yml`
   - quality + security + deterministic tests + conditional LLM tests + docker build check
2. `release.yml`
   - tag-based image build/push to GHCR
3. `deploy-staging.yml`
   - auto deploy released image to staging
4. `deploy-production.yml`
   - manual approval deploy of the same image digest

---

## 10. Deployment Pattern

Use a direct deployment pattern suitable for this repository size and current infrastructure maturity:

- Host prepared manually once
- CD workflow deploys by SSH:
  - Pull image from GHCR
  - Restart container with env file or injected env vars
  - Run smoke check

This pattern is suitable for educational and small-scale setups.

---

## 11. Step-by-Step Implementation Plan

Use this exact sequence to implement end-to-end CI/CD:

1. Configure repository governance in GitHub.
   - Enable branch protection for `main`.
   - Require CI checks from `ci.yml`.
   - Require at least one PR review.
2. Configure package publishing.
   - Ensure Actions can publish to GHCR.
   - Confirm `release.yml` has `packages: write` permission.
3. Create GitHub Environments.
   - Create `staging` and `production` environments.
   - Add required reviewers for `production`.
4. Add secrets.
   - Add `OPENAI_API_KEY` for CI LLM tests and runtime.
   - Add `TELEGRAM_BOT_TOKEN` in `staging` and `production`.
   - Add deployment credentials (for example `SSH_PRIVATE_KEY`, `SSH_HOST`, `SSH_USER`).
5. Validate CI execution.
   - Open PR and verify lint, security, and deterministic tests pass.
   - Verify LLM jobs behavior with/without `OPENAI_API_KEY`.
6. Validate release build.
   - Create test tag like `v0.1.0-rc1` (or project policy equivalent).
   - Confirm image appears in GHCR with expected tags.
7. Implement deployment workflows.
   - Add `deploy-staging.yml` triggered after successful release build.
   - Add smoke test step after deployment.
   - Add `deploy-production.yml` with manual approval.
8. Enforce immutable promotion.
   - Deploy by image digest (`@sha256:...`), not mutable tags.
   - Promote same digest from staging to production.
9. Add operational safeguards.
   - Add workflow `concurrency` and job timeouts.
   - Add artifact upload for pytest results and logs.
   - Add rollback step (redeploy previous known-good digest).

### Phase 1 

- Keep existing `ci.yml` and `release.yml`
- Add branch protection rules
- Add GitHub Environments (`staging`, `production`)
- Move runtime secrets to environment scope
- Add CI concurrency cancellation and job timeouts

### Phase 2

- Add `deploy-staging.yml`
- Add smoke tests after deployment
- Add `deploy-production.yml` with approval gate
- Pin deployment by image digest (not mutable tag)

---

## 12. Quality Gates and Exit Criteria

A release is deployable when:

- CI required checks are green
- No critical vulnerabilities in dependency/security scans
- Deterministic test suites pass
- LLM suites pass according to defined policy (or are explicitly skipped by policy)
- Docker image is built and published
- Staging smoke tests pass
- Production deployment approved

---

## 13. Risk Register and Mitigations

- Risk: LLM test flakiness/cost spikes
  - Mitigation: Run LLM jobs conditionally, separate from required deterministic gate
- Risk: Secret leakage in logs
  - Mitigation: Use GitHub Secrets + environment scope + avoid echoing sensitive vars
- Risk: Drift between staging and production
  - Mitigation: Promote identical image digest between environments
- Risk: Deployment drift due to manual host changes
  - Mitigation: Keep deployment scripted in GitHub Actions and document host baseline

---

## 14. Minimal Acceptance Checklist

- [ ] Required checks enforced for PR merge
- [ ] Release tags produce GHCR image
- [ ] Required tools/accounts/access from Section 3 are provisioned
- [ ] Staging deployment automated from release artifact
- [ ] Production deployment protected by approval
- [ ] Runtime secrets stored in GitHub Environments

