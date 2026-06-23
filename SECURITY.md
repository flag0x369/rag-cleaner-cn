# Security Policy

`rag-cleaner-cn` is designed as a local-first document cleaning tool. By default it does not upload source files, call external LLM services, or write to vector databases.

## Reporting a Vulnerability

If you find a security issue, please avoid posting private data, source documents, tokens, cookies, API keys, or exploitable details in a public issue.

For a public GitHub repository, use GitHub's private vulnerability reporting or open a minimal public issue that only says a private security report is needed. Include enough non-sensitive context for maintainers to reproduce the problem privately.

## Sensitive Data

- Do not commit real customer documents, private URLs, credentials, cookies, tokens, or API keys.
- Redact sample text before attaching bug reports.
- Keep generated cleaning output out of commits unless it is synthetic fixture data.

## Dependency Policy

New dependencies must not upload user documents by default. Any future LLM or remote service integration must be opt-in and must keep original text separate from generated content.
