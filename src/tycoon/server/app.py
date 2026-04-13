from fastapi import FastAPI
from tycoon import __version__


def create_app() -> FastAPI:
    """Factory function for the FastAPI application."""
    application = FastAPI()

    @application.get("/")
    def root():
        return {"message": "Welcome to Tycoon", "version": __version__}

    @application.get("/health")
    def health():
        return {"status": "ok"}

    @application.get("/check-updates")
    def check_updates():
        """Check for updates to the database-tycoon package."""
        import httpx
        from packaging.version import parse as parse_version

        try:
            response = httpx.get("https://pypi.org/pypi/database-tycoon/json", timeout=10)
            response.raise_for_status()
            latest_version = parse_version(response.json()["info"]["version"])
            current_version = parse_version(__version__)

            return {
                "update_available": latest_version > current_version,
                "current_version": str(current_version),
                "latest_version": str(latest_version),
            }
        except httpx.HTTPError as e:
            return {"error": f"Failed to check for updates: {e}"}
        except KeyError as e:
            return {"error": f"Unexpected response format: missing key {e}"}

    return application


app = create_app()
