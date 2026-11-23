# Data

- `curated/` holds small tables we compiled ourselves from public sources. Every row names its source. They are shared under the repository's MIT license.
- `raw/` and `cache/` hold data downloaded by scripts, such as OpenStreetMap (© OpenStreetMap contributors, ODbL 1.0). They are not in git. Rebuild them with the scripts; do not commit them.

When coordinates come from a licensed source, they are not stored in `curated/`. The scripts look them up at build time.
