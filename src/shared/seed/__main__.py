try:
    import typer  # noqa: F401
except ModuleNotFoundError as e:  # pragma: no cover
    raise SystemExit(
        "Missing dependency: 'typer'.\n\n"
        "Install it in the same environment you're running this command from, e.g.:\n"
        "  python3 -m pip install typer\n"
        "or reinstall the project's requirements:\n"
        "  python3 -m pip install -r requirements.txt\n"
    ) from e

from .cli import app


if __name__ == "__main__":
    app()
