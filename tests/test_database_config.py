import pytest

from src.shared.database.database_config import validate_database_target


def test_development_database_target_rejects_production_like_db_name():
    with pytest.raises(RuntimeError, match="production-like database target"):
        validate_database_target(
            py_env="development",
            db_host="localhost",
            db_name="prod_jafepa_db",
        )


def test_development_database_target_allows_local_target():
    validate_database_target(
        py_env="development",
        db_host="localhost",
        db_name="jafepa_local",
    )


def test_production_database_target_allows_production_markers():
    validate_database_target(
        py_env="production",
        db_host="prod-db.internal",
        db_name="prod_jafepa_db",
    )
