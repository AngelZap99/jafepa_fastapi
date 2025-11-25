import re

from pydantic import BaseModel, SecretStr, field_validator


PASSWORD_RE = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[A-Za-z\d@$!%*?&]{8,}$")


class PasswordValidationMixin(BaseModel):
    password: SecretStr

    @field_validator("password")
    @classmethod
    def validate_strong_password(cls, value: SecretStr) -> SecretStr:
        # Get the real value of the password
        s = value.get_secret_value()

        if not PASSWORD_RE.fullmatch(s):
            # Raise a validation error that FastAPI will handle as a 422
            raise ValueError(
                "The password must be at least 8 characters long and contain at least one uppercase letter, one lowercase letter, and one number"
            )

        return value


__all__ = ["PasswordValidationMixin"]
