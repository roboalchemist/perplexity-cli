# Contributing

## Release Process

Releases use a GitHub Actions workflow that auto-bumps the Homebrew formula.

### Required Secret

- `HOMEBREW_TAP_TOKEN` — GitHub PAT with `repo` scope for the `roboalchemist/homebrew-tap` repository

To create: GitHub → Settings → Developer settings → Personal access tokens → Generate new token (classic) → check `repo`

### How It Works

1. Create a GitHub release with a version tag (e.g., `v1.1.0`)
2. The `bump-tap.yml` workflow fires
3. It downloads the release tarball, computes SHA256, and updates the Homebrew formula
