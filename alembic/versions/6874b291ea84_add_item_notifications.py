"""add_item_notifications

Revision ID: 6874b291ea84
Revises: 1681835979ba
Create Date: 2025-08-16 15:58:13.915084

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6874b291ea84'
down_revision: Union[str, Sequence[str], None] = '1681835979ba'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create the notification function
    op.execute("""
        CREATE OR REPLACE FUNCTION item_notify() RETURNS trigger
            LANGUAGE plpgsql
        AS $$
        BEGIN
            PERFORM pg_notify('update_items', to_json(NEW)::text);
            RETURN NEW;
        END;
        $$;
    """)
    
    # Grant permissions
    op.execute("ALTER FUNCTION item_notify() OWNER TO postgres;")
    
    # Create the trigger
    op.execute("""
        CREATE OR REPLACE TRIGGER item_update
            AFTER INSERT OR UPDATE ON items
            FOR EACH ROW
        EXECUTE PROCEDURE item_notify();
    """)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop the trigger
    op.execute("DROP TRIGGER IF EXISTS item_update ON items;")
    
    # Drop the function
    op.execute("DROP FUNCTION IF EXISTS item_notify();")
