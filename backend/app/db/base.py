from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


# Import all models here so Alembic autogenerate can detect them.
# These imports must stay even if the symbols look unused.
from app.models import user_models  # noqa: F401, E402
from app.models import audit_models  # noqa: F401, E402
from app.models import domain_models  # noqa: F401, E402
