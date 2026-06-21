# backend/migrate.py
# ─────────────────────────────────────────────────────────────────────────────
# Safe DB migration — adds missing columns to existing tables.
#
# IMPORTANT: This must be called INSIDE an already-active app_context.
# Do NOT call with app.app_context() here — app.py already has one open.
# Using a nested context was causing SQLAlchemy to lose the bcrypt binding,
# which made bcrypt.check_password_hash() fail → "Invalid email or password".
# ─────────────────────────────────────────────────────────────────────────────
from extensions import db
from sqlalchemy import text
import traceback


def run_migrations():
    """
    Add missing columns to existing tables.
    Call this INSIDE an active app_context — do NOT wrap in app.app_context().
    Safe to run on every startup (checks before altering).
    """
    try:
        with db.engine.connect() as conn:
            # ── help_requests: latitude + longitude ───────────────────────────
            _add_column_if_missing(conn, "help_requests", "latitude",  "DECIMAL(10,8) NULL")
            _add_column_if_missing(conn, "help_requests", "longitude", "DECIMAL(11,8) NULL")
            conn.commit()
        print("✅ Migrations complete")

    except Exception as ex:
        print("⚠️  Migration warning (non-fatal):", ex)
        traceback.print_exc()


def _add_column_if_missing(conn, table, column, col_definition):
    """Add a column only if it doesn't already exist. Silent if already present."""
    try:
        result = conn.execute(
            text(
                "SELECT COUNT(*) FROM information_schema.columns "
                "WHERE table_schema = DATABASE() "
                "AND table_name = :tbl AND column_name = :col"
            ),
            {"tbl": table, "col": column}
        )
        count = result.scalar()
        if count == 0:
            conn.execute(
                text("ALTER TABLE `{}` ADD COLUMN `{}` {}".format(table, column, col_definition))
            )
            print("  ✅ Added column {}.{}".format(table, column))
        else:
            print("  ✓  {}.{} already exists".format(table, column))
    except Exception as ex:
        print("  ⚠️  Could not process {}.{}: {}".format(table, column, ex))
        raise