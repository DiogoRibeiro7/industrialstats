# Automated releases

`industrialstats` uses a single release branch, `main`, and two GitHub Actions workflows:

1. `.github/workflows/release-please.yml` maintains the release pull request and creates the GitHub tag/release.
2. `.github/workflows/release.yml` builds and publishes the resulting release to PyPI through OIDC Trusted Publishing.

Zenodo archives the same GitHub Release through the Zenodo GitHub integration.

## Normal development

All normal work targets `main` through pull requests. Commit and PR titles should follow Conventional Commits because Release Please derives semantic versions from them:

- `fix:` -> patch release
- `feat:` -> minor release
- `feat!:` / `fix!:` / `BREAKING CHANGE:` -> major release

For pre-1.0 versions, semantic versioning still applies according to the Release Please configuration.

## Release flow

There is no manual version editing, tag creation, or GitHub Release creation.

After conventional commits land on `main`, Release Please creates or updates a release PR. That PR contains the generated changelog and synchronized version metadata, including the Python package metadata and `CITATION.cff` version.

The release process is:

1. normal PRs merge into `main`;
2. Release Please updates its release PR;
3. CI runs on the release PR;
4. merge the release PR when ready;
5. Release Please creates the version tag and published GitHub Release;
6. `.github/workflows/release.yml` builds wheel and sdist, runs `twine check`, attaches both distributions to the GitHub Release, and publishes to PyPI through OIDC;
7. Zenodo archives that GitHub Release and mints the DOI.

The only human release action is merging the green Release Please PR.

## One-time GitHub setup

Create a fine-grained GitHub personal access token stored as the repository Actions secret:

`RELEASE_PLEASE_TOKEN`

The token is used only for GitHub release orchestration. It should be scoped to this repository with the minimum permissions needed for:

- Contents: read and write
- Pull requests: read and write
- Issues: read and write

Using this token rather than the built-in `GITHUB_TOKEN` ensures Release Please pull requests trigger the normal CI checks.

## PyPI

PyPI publishing remains tokenless. Configure the Trusted Publisher for:

- project: `industrialstats`
- owner: `DiogoRibeiro7`
- repository: `industrialstats`
- workflow: `release.yml`
- environment: `pypi`

The `pypi` GitHub environment must exist and match the Trusted Publisher configuration.

## Zenodo

Connect GitHub to Zenodo and enable `DiogoRibeiro7/industrialstats`. Zenodo will archive each published GitHub Release automatically.

`CITATION.cff` is the repository metadata source. The version is maintained by Release Please. The DOI should not be fabricated or pre-filled before Zenodo mints it.

## Release invariants

- Never reuse a version already published to PyPI.
- Never move a published release tag.
- Never publish from an unreviewed branch.
- `main` is the only long-lived branch.
- A published GitHub Release is the canonical release event for both PyPI and Zenodo.
