# Automated releases

`industrialstats` uses one long-lived branch, `main`, and one release workflow: `.github/workflows/release.yml`.

Zenodo archives each published GitHub Release through the Zenodo GitHub integration.

## Normal development

All normal work targets `main` through pull requests. Commit and PR titles should follow Conventional Commits because Release Please derives semantic versions from them:

- `fix:` -> patch release
- `feat:` -> minor release
- `feat!:` / `fix!:` / `BREAKING CHANGE:` -> major release

Release Please maintains `CHANGELOG.md` and synchronizes version metadata automatically.

## Release flow

There is no manual version editing, tag creation, GitHub Release creation, PyPI API token, or personal GitHub token.

After conventional commits land on `main`, `.github/workflows/release.yml` runs Release Please and creates or updates a release pull request. That PR contains the generated changelog and synchronized version metadata, including the Python package version and `CITATION.cff` version.

When a release is desired:

1. review the Release Please pull request;
2. merge it into `main`;
3. Release Please creates the version tag and published GitHub Release;
4. the same `release.yml` run checks out that exact tag;
5. it builds wheel and sdist and runs `twine check`;
6. it attaches both distributions to the GitHub Release;
7. it publishes to PyPI through OIDC Trusted Publishing;
8. Zenodo archives that GitHub Release and mints the DOI.

The only human release action is merging the Release Please pull request.

Because Release Please uses GitHub's built-in `GITHUB_TOKEN`, its generated release PR does not start a separate pull-request CI workflow. Publication safety therefore remains inside `release.yml`: the release artifacts are built and validated from the created tag before PyPI publication.

## PyPI

PyPI publishing is tokenless. The Trusted Publisher configuration is:

- project: `industrialstats`
- owner: `DiogoRibeiro7`
- repository: `industrialstats`
- workflow: `release.yml`
- environment: `pypi`

The `pypi` GitHub environment must exist and match the Trusted Publisher configuration.

## Zenodo

Connect GitHub to Zenodo and enable `DiogoRibeiro7/industrialstats`. Zenodo archives each published GitHub Release automatically.

`CITATION.cff` is the repository metadata source. Release Please maintains its version. The optional `date-released` field is intentionally omitted so it cannot become stale; the GitHub/Zenodo publication timestamp is the authoritative release date. The DOI must not be fabricated or pre-filled before Zenodo mints it.

## Release invariants

- Never reuse a version already published to PyPI.
- Never move a published release tag.
- Never publish from an unreviewed branch.
- `main` is the only long-lived branch.
- A published GitHub Release is the canonical release event for both PyPI and Zenodo.
