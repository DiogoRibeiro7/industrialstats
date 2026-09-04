# Security Policy

## Supported versions

`industrialstats` is pre-1.0. Only the most recent release on PyPI receives
security fixes; there are no maintained backport branches.

| Version | Supported |
| --- | --- |
| Latest release | Yes |
| Anything older | No |

## Reporting a vulnerability

Please do **not** open a public issue for a security problem.

Report privately through
[GitHub Security Advisories](https://github.com/DiogoRibeiro7/industrialstats/security/advisories/new),
or by email to [dfr@esmad.ipp.pt](mailto:dfr@esmad.ipp.pt).

Please include:

- a description of the issue and why you believe it is a security problem;
- the version of `industrialstats` and of Python you are using;
- a minimal reproduction, ideally a short script;
- any known workaround.

You can expect an acknowledgement within 7 days and an assessment within 30
days. If a fix is warranted, it ships in a new release and the advisory is
published once users have had a reasonable chance to upgrade.

## Scope

This library performs statistical computation on data you supply. Reports are
in scope when they describe, for example:

- code execution or file writes outside a path the caller explicitly provided;
- unsafe deserialization of untrusted input;
- a vulnerable dependency that `industrialstats` actually exposes.

The following are **not** security vulnerabilities, though they are welcome as
ordinary bug reports:

- an incorrect statistical result or a numerically unstable computation;
- resource exhaustion from a deliberately large design or candidate set;
- an exception raised on malformed input.

Statistical correctness issues are treated as high-priority bugs. Please open a
normal issue for them, with the design specification and expected result.
