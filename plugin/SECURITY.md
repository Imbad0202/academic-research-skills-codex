# Security Policy

## Supported versions

Only the latest release on the `main` branch receives security fixes.

| Version | Supported |
|---------|-----------|
| Latest (`main`) | Yes |
| Older releases | No |

## Reporting a vulnerability

If you find a security issue in the Codex distribution, **do not open a public
issue**.

Instead, use GitHub's **private vulnerability reporting**:

1. Go to the [Security Advisories](https://github.com/Imbad0202/academic-research-skills-codex/security/advisories) page.
2. Click **"Report a vulnerability"**.
3. Include what you found, how to reproduce it, affected versions or commits,
   and the potential impact.

You will receive a response within 7 days. If the report is accepted, a fix will
be issued and credited in the release notes. If declined, you will receive an
explanation.

## Scope

The following are in scope for security reports:

- **Prompt injection or router bypass** - inputs that cause the Codex adapter to
  bypass ARS integrity gates, Socratic scoping, ethics protocols, or other
  blocking constraints.
- **Credential leakage** - configurations, scripts, or prompts that expose API
  keys or tokens, including optional `ANTHROPIC_API_KEY` and cross-model
  reviewer configuration.
- **Data exfiltration** - adapter behavior that sends manuscripts, research
  data, citations, or user-provided files to unintended external services.
- **Vendoring or sync integrity failures** - issues that make this package
  silently use unverified upstream content, wrong source commits, or Claude-only
  runtime files as active Codex instructions.
- **Security-check bypasses** - defects in release-readiness checks that hide
  high-impact issues such as real secrets, unsafe shell execution, or known
  vulnerable dependencies.

The following are out of scope:

- AI output quality issues such as weak arguments, hallucinations, or incomplete
  literature coverage, unless they are caused by a security-relevant bypass.
- General installation problems, feature requests, or non-security bugs - use
  [Issues](https://github.com/Imbad0202/academic-research-skills-codex/issues)
  instead.
- Upstream ARS behavior that is not specific to the Codex distribution; report
  those in the upstream [academic-research-skills](https://github.com/Imbad0202/academic-research-skills)
  repository.
