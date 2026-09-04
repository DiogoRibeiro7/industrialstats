# Releases

`industrialstats` uses one long-lived branch, `main`, and one release workflow: `.github/workflows/release.yml`.

## Normal development

All normal work targets `main` through pull requests.

When preparing a release, update the version consistently in the normal development/release-preparation PR:

- `pyproject.toml`
- `src/industrialstats/__init__.py`
- `CITATION.cff`
- `CHANGELOG.md`

That PR goes through the normal repository CI. No separate release PR is required.

## Release flow

After the release-preparation changes are on `main`:

1. create a GitHub Release with tag `vX.Y.Z` from `main`;
2. publishing the GitHub Release triggers `.github/workflows/release.yml`;
3. the workflow checks out that exact tag;
4. it verifies that the tag matches the version in `pyproject.toml`;
5. it builds wheel and sdist and runs `twine check`;
6. it attaches the distributions to the GitHub Release;
7. it publishes to PyPI through OIDC Trusted Publishing.

There is no PyPI API token and no personal GitHub token.

## PyPI

The Trusted Publisher configuration is:

- project: `industrialstats`
- owner: `DiogoRibeiro7`
- repository: `industrialstats`
- workflow: `release.yml`
- environment: `pypi`

The `pypi` GitHub environment must exist and match the Trusted Publisher configuration.

## Release invariants

- Never reuse a version already published to PyPI.
- Never move a published release tag.
- Never publish from an unreviewed commit.
- `main` is the only long-lived branch.
- `CHANGELOG.md` is updated as part of the normal release-preparation PR.
