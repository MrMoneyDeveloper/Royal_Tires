# Data layer

SQLAlchemy persistence infrastructure is split by responsibility:

- `base.py`: declarative Base and UTC timestamp type/helpers.
- `db_context.py`: engine creation and database-specific connection setup.
- `session.py`: session factory and FastAPI-scoped database dependency.

This package is the project's DbContext-equivalent boundary. Application code imports it directly; there is no root database compatibility facade.
