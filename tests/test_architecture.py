from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
ALLOWED_JSON_RESPONSE_FILES = {
    SRC_ROOT / "shared" / "exception_handlers.py",
}


def test_jsonresponse_is_only_used_in_global_exception_handlers():
    offenders: list[str] = []

    for path in SRC_ROOT.rglob("*.py"):
        if path in ALLOWED_JSON_RESPONSE_FILES:
            continue

        if "JSONResponse(" in path.read_text(encoding="utf-8"):
            offenders.append(str(path.relative_to(PROJECT_ROOT)))

    assert offenders == []
