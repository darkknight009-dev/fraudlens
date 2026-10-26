"""Validate environment configuration without printing secret values."""

import sys

sys.path.insert(0, "backend")

from app.core.config import get_settings


def main() -> None:
    settings = get_settings()
    print(
        f"Configuration valid for app_env={settings.app_env}; "
        f"database configured={bool(settings.database_url)}"
    )


if __name__ == "__main__":
    main()
