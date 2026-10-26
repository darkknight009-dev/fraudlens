"""Run the configured local retention deletion job."""

from app.core.config import get_settings
from app.db.session import get_session_factory
from app.services.retention import run_retention


def main() -> None:
    settings = get_settings()
    with get_session_factory(settings.database_url)() as session:
        print(run_retention(session, settings))


if __name__ == "__main__":
    main()
