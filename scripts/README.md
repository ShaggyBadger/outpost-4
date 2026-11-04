# Scripts

Repository-level setup and data-transfer commands live here. Run them from the
repository root:

- `./scripts/init.sh` creates local environment configuration, enforces
  restrictive `.env` permissions, prompts for a site name, generates a secret
  when needed, applies the checked-in migrations, and starts the development
  services. It does not generate migrations.
- `./scripts/export_initial_database.sh` creates and uploads a one-time local
  database backup for an approved initial content transfer.
- `./scripts/db-dump.sh [label]` writes a custom-format dump to `db/dumps/`.
  It refuses to leave an empty file behind when the dump fails.
- `./scripts/db-restore.sh <dump>` restores a dump into the local database,
  dropping existing objects first.
- `configure_local_site.py` is invoked inside the Docker Python environment by
  the initializer; it updates the README title and Wagtail site name and
  preserves an existing secret unless explicitly rotated.
