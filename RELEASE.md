# Release checklist

This repository publishes one GitHub Release to two destinations:

1. PyPI receives the built wheel and source distribution through GitHub Actions and PyPI Trusted Publishing.
2. Zenodo archives the GitHub Release and mints the software DOI through the Zenodo GitHub integration.

## One-time PyPI setup

Before the first release, configure a pending GitHub Trusted Publisher in PyPI for:

- PyPI project name: `industrialstats`
- GitHub owner: `DiogoRibeiro7`
- GitHub repository: `industrialstats`
- workflow file: `release.yml`
- environment: `pypi`

The workflow intentionally does not use a long-lived PyPI API token. The `pypi` GitHub environment and the Trusted Publisher configuration must match.

## One-time Zenodo setup

Before the first release:

1. Connect the GitHub account to Zenodo.
2. Synchronize the repository list in Zenodo.
3. Enable `DiogoRibeiro7/industrialstats` in the Zenodo GitHub integration.

The repository uses `CITATION.cff` as the software metadata source. Do not add a DOI to `CITATION.cff` before Zenodo has minted the real DOI.

## Release preparation

For each release:

1. Set the same version in:
   - `pyproject.toml`
   - `src/industrialstats/__init__.py`
   - `CITATION.cff`
2. Set `date-released` in `CITATION.cff` to the intended release date.
3. Run the full PR CI and ensure quality plus Python 3.11, 3.12, 3.13, and 3.14 are green.
4. Build locally if desired:

   ```bash
   python -m pip install --upgrade build twine
   python -m build
   python -m twine check dist/*
   ```

5. Merge the release-preparation PR into `develop`.
6. Create a Git tag matching the package version exactly, for example `v0.1.0`.
7. Create and publish a GitHub Release from that tag.

## Automated release behaviour

Publishing the GitHub Release triggers `.github/workflows/release.yml`.

The workflow:

- checks that the GitHub Release tag equals `v<pyproject version>`;
- builds the wheel and source distribution;
- validates the distributions with `twine check`;
- attaches both distributions to the GitHub Release;
- publishes them to PyPI through OIDC Trusted Publishing.

If the repository has been enabled in Zenodo, the same GitHub Release is automatically ingested and archived there.

## After the first Zenodo release

After Zenodo creates the first record:

1. verify the title, author, version, licence, release date, keywords, and repository URL;
2. verify that Software Heritage archival is scheduled or complete;
3. record the Zenodo DOI in the release notes and README if desired;
4. only add a DOI to `CITATION.cff` if you deliberately want to pin citation metadata to a specific Zenodo DOI rather than let Zenodo manage release metadata from the CFF.

## Release invariants

- Never reuse or overwrite a published version on PyPI.
- Never move an existing public release tag to different source code.
- Never publish from a dirty or unreviewed branch.
- A GitHub Release is the canonical release event for both PyPI and Zenodo.
