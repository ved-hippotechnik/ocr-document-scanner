"""Add ApiKey WebhookConfig WebhookDelivery ApiUsageLog tables

Revision ID: 69b50c735da4
Revises: ee980f9ccd4f
Create Date: 2026-02-23 11:50:52.305548

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '69b50c735da4'
down_revision = 'ee980f9ccd4f'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('api_keys',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('key_prefix', sa.String(length=16), nullable=False),
        sa.Column('key_hash', sa.String(length=64), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('scopes', sa.Text(), nullable=True),
        sa.Column('rate_limit', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_api_keys_user_id'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key_hash', name='uq_api_keys_key_hash'),
    )
    op.create_index('ix_api_keys_user_id', 'api_keys', ['user_id'])

    op.create_table('webhook_configs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('url', sa.String(length=2048), nullable=False),
        sa.Column('secret', sa.String(length=64), nullable=False),
        sa.Column('events', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_webhook_configs_user_id'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_webhook_configs_user_id', 'webhook_configs', ['user_id'])

    op.create_table('webhook_deliveries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('webhook_config_id', sa.Integer(), nullable=False),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('payload', sa.Text(), nullable=False),
        sa.Column('response_status', sa.Integer(), nullable=True),
        sa.Column('response_body', sa.Text(), nullable=True),
        sa.Column('attempts', sa.Integer(), nullable=True),
        sa.Column('max_attempts', sa.Integer(), nullable=True),
        sa.Column('next_retry_at', sa.DateTime(), nullable=True),
        sa.Column('delivered_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['webhook_config_id'], ['webhook_configs.id'],
                                name='fk_webhook_deliveries_config_id'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_webhook_deliveries_config_id', 'webhook_deliveries', ['webhook_config_id'])
    op.create_index('ix_webhook_delivery_config_created', 'webhook_deliveries',
                    ['webhook_config_id', 'created_at'])

    op.create_table('api_usage_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('api_key_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('endpoint', sa.String(length=200), nullable=False),
        sa.Column('request_count', sa.Integer(), nullable=True),
        sa.Column('error_count', sa.Integer(), nullable=True),
        sa.Column('total_latency_ms', sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(['api_key_id'], ['api_keys.id'], name='fk_api_usage_logs_key_id'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('api_key_id', 'date', 'endpoint', name='uq_usage_key_date_endpoint'),
    )
    op.create_index('ix_api_usage_key_date', 'api_usage_logs', ['api_key_id', 'date'])


def downgrade():
    op.drop_table('api_usage_logs')
    op.drop_table('webhook_deliveries')
    op.drop_table('webhook_configs')
    op.drop_table('api_keys')
