from sqlalchemy.exc import IntegrityError


def get_violated_constraint(error: IntegrityError) -> str | None:
    driver_error = error.orig.__cause__ if error.orig is not None else None
    return getattr(driver_error, "constraint_name", None)
