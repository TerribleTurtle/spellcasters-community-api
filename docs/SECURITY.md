# Security Policy

## Supported Versions

This project is currently in **Early Access**.
*Please note: This data is community-gathered and updated. As such, it may contain inaccuracies or mistakes.*

| Version | Supported              |
| ------- | ---------------------- |
| v2.x    | :white_check_mark:     |
| v1.x    | :warning: (Deprecated) |
| < 1.0   | :x:                    |

## Reporting a Vulnerability

We take the security of this API seriously. If you find a vulnerability, please follow these steps:

1.  **Do NOT open a public issue.**
2.  Email the maintainers at `terribleturtlesdev@gmail.com`.
    _Since this is a community project without a dedicated security team, please allow up to 72 hours for a response._
3.  Include a proof of concept or description of the vulnerability.

### What to report?

- **XSS Vectors:** Ways to inject scripts via data fields.
- **Build Process Exploits:** Malicious assets that crash the build.
- **Data Leaks:** Accidental exposure of private keys (though none should exist).

## Scope

This project is a static API. The scope is limited to:

- The JSON data integrity.
- The build scripts in `scripts/`.
- The GitHub Actions workflows.

## Known Vulnerabilities / Exceptions

The following are known security alerts that are accepted as exceptions:

- **`elliptic` (Low Severity)**: Located in the development dependencies (`browserify` -> `crypto-browserify` -> `create-ecdh` -> `elliptic`). The package is on its latest version (`6.6.1`) and there is currently no patch available. Since this is restricted to the local development and build environment and not exposed in the final static API, this warning is currently ignored.
