# Releases

`industrialstats` uses one long-lived branch, `main`, and one release workflow: `.github/workflows/release.yml`.

## Release cadence

Prefer small, coherent releases over large accumulated batches.

A release should normally follow once a complete, independently useful slice has merged and the normal CI is green. Do not wait for an entire roadmap milestone when the current changes already form a sensible patch or minor release.

Use Semantic Versioning:

- patch releases for fixes, validation hardening, documentation/release tooling, and backward-compatible maintenance that does not materially expand the public statistical surface;
- minor releases for backward-compatible new statistical capabilities or meaningful API expansion;
- major releases only for intentional incompatible public API changes.

## Normal development

All normal work targets `main` through pull requests.

When preparing a release, update the version consistently in the normal development/release-preparation PR:

- `pyproject.toml`
- `src/industrialstats/__init__.py`
- `CITATION.cff`
- `CHANGELOG.md`

That PR goes through the normal repository CI. No separate release branch is required after the preparation PR has merged.

## Preferred release flow

After the release-preparation changes are on `main`, dispatch the release workflow with the version number **without** the leading `v`:

```bash
gh workflow run release.yml --ref main -f version=0.3.1
```

The manual workflow:

1. checks out the current `main` commit;
2. resolves the requested release tag as `vX.Y.Z`;
3. verifies that the workflow is operating on the current `main` commit;
4. verifies that `pyproject.toml`, `src/industrialstats/__init__.py`, and `CITATION.cff` all match the requested version;
5. verifies that `CHANGELOG.md` contains a dated section for that version;
6. builds the wheel and sdist and runs `twine check`;
7. creates the GitHub Release, or safely reuses it only when its tag already points to the same `main` commit;
8. attaches the distributions to the GitHub Release;
9. publishes to PyPI through OIDC Trusted Publishing;
10. lets the Zenodo GitHub integration archive the same GitHub Release independently.

The workflow refuses to move or reuse an existing release/tag that points at another commit.

## GitHub UI release compatibility

Publishing a GitHub Release manually in the GitHub UI remains supported. The `release.published` trigger uses the same build, validation, upload, and PyPI publication path.

For that path, create a release with tag `vX.Y.Z` pointing to a commit already contained in `main`. The workflow verifies the tag version before publishing.

## PyPI

The Trusted Publisher configuration is:

- project: `industrialstats`
- owner: `DiogoRibeiro7`
- repository: `industrialstats`
- workflow: `release.yml`
- environment: `pypi`

The `pypi` GitHub environment must exist and match the Trusted Publisher configuration.

There is no PyPI API token and no personal GitHub token in the release workflow.

## Zenodo

Zenodo remains enabled as an independent archival destination for published GitHub Releases.

`.zenodo.json` controls the metadata used by Zenodo, including the title, description, creator information, license, and keywords. It is intentionally version-independent so normal package releases do not require an extra Zenodo-specific version edit.

`CITATION.cff` remains the repository citation file used by GitHub and other citation-aware tools.

For an already-published Zenodo record, changing `.zenodo.json` does not retroactively alter that existing record; its metadata must be edited in Zenodo itself.

## Release invariants

- Never reuse a version already published to PyPI.
- Never move a published release tag.
- Never publish from an unreviewed commit.
- Manual workflow releases must use the current `main` commit.
- `main` is the only long-lived branch.
- `CHANGELOG.md` is updated as part of the normal release-preparation PR: the accumulated `## [Unreleased]` entries are retitled to the new version and dated, and a fresh empty `## [Unreleased]` section is left at the top.
