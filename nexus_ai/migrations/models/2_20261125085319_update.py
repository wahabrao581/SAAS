from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "providers" (
    "id" CHAR(36) NOT NULL PRIMARY KEY,
    "name" VARCHAR(100) NOT NULL UNIQUE,
    "display_name" VARCHAR(150) NOT NULL,
    "provider_type" VARCHAR(30) NOT NULL,
    "base_url" TEXT,
    "api_key_env" VARCHAR(100),
    "is_active" INT NOT NULL,
    "settings" JSON NOT NULL,
    "created_at" TIMESTAMP NOT NULL,
    "updated_at" TIMESTAMP NOT NULL
) /* External service configuration shared by the application. */;
CREATE INDEX IF NOT EXISTS "idx_providers_provide_a5e94b" ON "providers" ("provider_type", "is_active");
        CREATE TABLE IF NOT EXISTS "provider_models" (
    "id" CHAR(36) NOT NULL PRIMARY KEY,
    "name" VARCHAR(100) NOT NULL,
    "display_name" VARCHAR(150) NOT NULL,
    "description" TEXT,
    "capabilities" JSON NOT NULL,
    "is_active" INT NOT NULL,
    "created_at" TIMESTAMP NOT NULL,
    "updated_at" TIMESTAMP NOT NULL,
    "provider_id" CHAR(36) NOT NULL REFERENCES "providers" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_provider_mo_provide_6926da" UNIQUE ("provider_id", "name")
) /* A model exposed by a video-generation provider. */;
CREATE INDEX IF NOT EXISTS "idx_provider_mo_provide_3344bc" ON "provider_models" ("provider_id", "is_active");"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "provider_models";
        DROP TABLE IF EXISTS "providers";"""


MODELS_STATE = (
    "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"
    "WX7/P587u+o="
)
