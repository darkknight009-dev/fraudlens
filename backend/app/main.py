"""M0 application entrypoint.

Milestone 1 will add settings, middleware, database wiring, and health routes.
"""

from fastapi import FastAPI

app = FastAPI(
    title="FraudLens API",
    description="Integration-first fraud intelligence platform.",
    version="0.1.0",
)


@app.get("/", include_in_schema=False)
def root() -> dict[str, str]:
    """Return scaffold metadata while the M0 foundation is being built."""

    return {"service": "fraudlens-api", "status": "scaffold", "version": "0.1.0"}
