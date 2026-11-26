from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "subscription_plans" (
    "id" CHAR(36) NOT NULL PRIMARY KEY,
    "name" VARCHAR(100) NOT NULL UNIQUE,
    "slug" VARCHAR(100) NOT NULL UNIQUE,
    "description" TEXT,
    "price" VARCHAR(40) NOT NULL,
    "currency" VARCHAR(10) NOT NULL,
    "billing_interval" VARCHAR(30) NOT NULL,
    "credits_per_period" VARCHAR(40) NOT NULL,
    "is_active" INT NOT NULL,
    "is_public" INT NOT NULL,
    "features" JSON NOT NULL,
    "max_concurrent_jobs" INT NOT NULL,
    "max_resolution" VARCHAR(30) NOT NULL,
    "created_at" TIMESTAMP NOT NULL,
    "updated_at" TIMESTAMP NOT NULL
);
        CREATE TABLE IF NOT EXISTS "credit_accounts" (
    "id" CHAR(36) NOT NULL PRIMARY KEY,
    "balance" VARCHAR(40) NOT NULL,
    "lifetime_earned" VARCHAR(40) NOT NULL,
    "lifetime_spent" VARCHAR(40) NOT NULL,
    "created_at" TIMESTAMP NOT NULL,
    "updated_at" TIMESTAMP NOT NULL,
    "user_id" CHAR(36) NOT NULL REFERENCES "auth_users" ("id") ON DELETE CASCADE
);
        CREATE TABLE IF NOT EXISTS "credit_reservations" (
    "id" CHAR(36) NOT NULL PRIMARY KEY,
    "amount" VARCHAR(40) NOT NULL,
    "status" VARCHAR(30) NOT NULL,
    "reference_id" VARCHAR(255) NOT NULL,
    "idempotency_key" VARCHAR(255) NOT NULL,
    "expires_at" TIMESTAMP,
    "consumed_at" TIMESTAMP,
    "released_at" TIMESTAMP,
    "metadata" JSON NOT NULL,
    "created_at" TIMESTAMP NOT NULL,
    "user_id" CHAR(36) NOT NULL REFERENCES "auth_users" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_credit_rese_user_id_b7327a" UNIQUE ("user_id", "idempotency_key")
);
CREATE INDEX IF NOT EXISTS "idx_credit_rese_status_a353d2" ON "credit_reservations" ("status", "expires_at");
CREATE INDEX IF NOT EXISTS "idx_credit_rese_user_id_2662b7" ON "credit_reservations" ("user_id", "created_at");
        CREATE TABLE IF NOT EXISTS "credit_transactions" (
    "id" CHAR(36) NOT NULL PRIMARY KEY,
    "transaction_type" VARCHAR(30) NOT NULL,
    "amount" VARCHAR(40) NOT NULL,
    "balance_before" VARCHAR(40) NOT NULL,
    "balance_after" VARCHAR(40) NOT NULL,
    "description" TEXT,
    "reference_id" VARCHAR(255),
    "idempotency_key" VARCHAR(255) UNIQUE,
    "metadata" JSON NOT NULL,
    "created_at" TIMESTAMP NOT NULL,
    "user_id" CHAR(36) NOT NULL REFERENCES "auth_users" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_credit_tran_user_id_a2e1e5" ON "credit_transactions" ("user_id", "created_at");
CREATE INDEX IF NOT EXISTS "idx_credit_tran_transac_dfaa64" ON "credit_transactions" ("transaction_type", "created_at");
        CREATE TABLE IF NOT EXISTS "user_subscriptions" (
    "id" CHAR(36) NOT NULL PRIMARY KEY,
    "status" VARCHAR(30) NOT NULL,
    "started_at" TIMESTAMP NOT NULL,
    "current_period_start" TIMESTAMP NOT NULL,
    "current_period_end" TIMESTAMP,
    "cancel_at_period_end" INT NOT NULL,
    "canceled_at" TIMESTAMP,
    "provider" VARCHAR(50),
    "provider_subscription_id" VARCHAR(255),
    "created_at" TIMESTAMP NOT NULL,
    "updated_at" TIMESTAMP NOT NULL,
    "plan_id" CHAR(36) NOT NULL REFERENCES "subscription_plans" ("id") ON DELETE RESTRICT,
    "user_id" CHAR(36) NOT NULL REFERENCES "auth_users" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_user_subscr_status_487e70" ON "user_subscriptions" ("status", "current_period_end");
        CREATE TABLE IF NOT EXISTS "payments" (
    "id" CHAR(36) NOT NULL PRIMARY KEY,
    "payment_type" VARCHAR(30) NOT NULL,
    "status" VARCHAR(30) NOT NULL,
    "amount" VARCHAR(40) NOT NULL,
    "currency" VARCHAR(10) NOT NULL,
    "credits_purchased" VARCHAR(40) NOT NULL,
    "provider" VARCHAR(50) NOT NULL,
    "provider_payment_id" VARCHAR(255),
    "idempotency_key" VARCHAR(255) NOT NULL UNIQUE,
    "paid_at" TIMESTAMP,
    "metadata" JSON NOT NULL,
    "created_at" TIMESTAMP NOT NULL,
    "updated_at" TIMESTAMP NOT NULL,
    "subscription_id" CHAR(36) REFERENCES "user_subscriptions" ("id") ON DELETE SET NULL,
    "user_id" CHAR(36) NOT NULL REFERENCES "auth_users" ("id") ON DELETE RESTRICT
);
CREATE INDEX IF NOT EXISTS "idx_payments_user_id_d6dc35" ON "payments" ("user_id", "created_at");
CREATE INDEX IF NOT EXISTS "idx_payments_status_33acf4" ON "payments" ("status", "created_at");
        CREATE TABLE IF NOT EXISTS "video_projects" (
    "id" CHAR(36) NOT NULL PRIMARY KEY,
    "name" VARCHAR(255) NOT NULL,
    "description" TEXT,
    "original_prompt" TEXT,
    "status" VARCHAR(30) NOT NULL,
    "default_model" VARCHAR(100),
    "default_settings" JSON NOT NULL,
    "final_video_url" TEXT,
    "final_video_storage_key" TEXT,
    "total_scenes" INT NOT NULL,
    "total_generated_clips" INT NOT NULL,
    "created_at" TIMESTAMP NOT NULL,
    "updated_at" TIMESTAMP NOT NULL,
    "user_id" CHAR(36) NOT NULL REFERENCES "auth_users" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_video_proje_user_id_f93e06" ON "video_projects" ("user_id", "created_at");
CREATE INDEX IF NOT EXISTS "idx_video_proje_user_id_88a881" ON "video_projects" ("user_id", "status");
        CREATE TABLE IF NOT EXISTS "video_assets" (
    "id" CHAR(36) NOT NULL PRIMARY KEY,
    "name" VARCHAR(255) NOT NULL,
    "asset_type" VARCHAR(30) NOT NULL,
    "mime_type" VARCHAR(100) NOT NULL,
    "file_size" BIGINT NOT NULL,
    "storage_provider" VARCHAR(30) NOT NULL,
    "storage_key" TEXT NOT NULL,
    "url" TEXT,
    "checksum" VARCHAR(128),
    "width" INT,
    "height" INT,
    "duration" REAL,
    "metadata" JSON NOT NULL,
    "is_deleted" INT NOT NULL,
    "created_at" TIMESTAMP NOT NULL,
    "project_id" CHAR(36) REFERENCES "video_projects" ("id") ON DELETE SET NULL,
    "user_id" CHAR(36) NOT NULL REFERENCES "auth_users" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_video_asset_user_id_db18eb" ON "video_assets" ("user_id", "created_at");
CREATE INDEX IF NOT EXISTS "idx_video_asset_project_1bfdfc" ON "video_assets" ("project_id", "created_at");
        CREATE TABLE IF NOT EXISTS "generation_jobs" (
    "id" CHAR(36) NOT NULL PRIMARY KEY,
    "status" VARCHAR(30) NOT NULL,
    "model_name" VARCHAR(100) NOT NULL,
    "total_clips" INT NOT NULL,
    "completed_clips" INT NOT NULL,
    "failed_clips" INT NOT NULL,
    "estimated_credits" VARCHAR(40) NOT NULL,
    "actual_credits" VARCHAR(40) NOT NULL,
    "credit_reservation_id" CHAR(36),
    "idempotency_key" VARCHAR(255) NOT NULL,
    "settings" JSON NOT NULL,
    "error_message" TEXT,
    "started_at" TIMESTAMP,
    "completed_at" TIMESTAMP,
    "created_at" TIMESTAMP NOT NULL,
    "updated_at" TIMESTAMP NOT NULL,
    "project_id" CHAR(36) NOT NULL REFERENCES "video_projects" ("id") ON DELETE CASCADE,
    "user_id" CHAR(36) NOT NULL REFERENCES "auth_users" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_generation__user_id_a17575" UNIQUE ("user_id", "idempotency_key")
);
CREATE INDEX IF NOT EXISTS "idx_generation__user_id_3292fa" ON "generation_jobs" ("user_id", "status");
CREATE INDEX IF NOT EXISTS "idx_generation__project_40871a" ON "generation_jobs" ("project_id", "created_at");
CREATE INDEX IF NOT EXISTS "idx_generation__status_616232" ON "generation_jobs" ("status", "created_at");
        CREATE TABLE IF NOT EXISTS "prompt_segments" (
    "id" CHAR(36) NOT NULL PRIMARY KEY,
    "sequence" INT NOT NULL,
    "prompt" TEXT NOT NULL,
    "title" VARCHAR(255),
    "is_approved" INT NOT NULL,
    "metadata" JSON NOT NULL,
    "created_at" TIMESTAMP NOT NULL,
    "updated_at" TIMESTAMP NOT NULL,
    "project_id" CHAR(36) NOT NULL REFERENCES "video_projects" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_prompt_segm_project_786de3" UNIQUE ("project_id", "sequence")
);
        CREATE TABLE IF NOT EXISTS "video_clips" (
    "id" CHAR(36) NOT NULL PRIMARY KEY,
    "sequence" INT NOT NULL,
    "prompt" TEXT NOT NULL,
    "model_name" VARCHAR(100) NOT NULL,
    "status" VARCHAR(30) NOT NULL,
    "settings" JSON NOT NULL,
    "estimated_credits" VARCHAR(40) NOT NULL,
    "actual_credits" VARCHAR(40) NOT NULL,
    "provider_name" VARCHAR(100),
    "provider_job_id" VARCHAR(255),
    "output_url" TEXT,
    "output_storage_key" TEXT,
    "output_duration" REAL,
    "output_width" INT,
    "output_height" INT,
    "progress" INT NOT NULL,
    "error_message" TEXT,
    "retry_count" INT NOT NULL,
    "started_at" TIMESTAMP,
    "completed_at" TIMESTAMP,
    "created_at" TIMESTAMP NOT NULL,
    "updated_at" TIMESTAMP NOT NULL,
    "job_id" CHAR(36) NOT NULL REFERENCES "generation_jobs" ("id") ON DELETE CASCADE,
    "project_id" CHAR(36) NOT NULL REFERENCES "video_projects" ("id") ON DELETE CASCADE,
    "segment_id" CHAR(36) REFERENCES "prompt_segments" ("id") ON DELETE SET NULL,
    CONSTRAINT "uid_video_clips_job_id_321afd" UNIQUE ("job_id", "sequence")
);
CREATE INDEX IF NOT EXISTS "idx_video_clips_job_id_47f1c2" ON "video_clips" ("job_id", "status");
CREATE INDEX IF NOT EXISTS "idx_video_clips_project_919c66" ON "video_clips" ("project_id", "sequence");
        CREATE TABLE IF NOT EXISTS "clip_assets" (
    "id" CHAR(36) NOT NULL PRIMARY KEY,
    "role" VARCHAR(30) NOT NULL,
    "sequence" INT NOT NULL,
    "created_at" TIMESTAMP NOT NULL,
    "asset_id" CHAR(36) NOT NULL REFERENCES "video_assets" ("id") ON DELETE CASCADE,
    "clip_id" CHAR(36) NOT NULL REFERENCES "video_clips" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_clip_assets_clip_id_e0e2b3" UNIQUE ("clip_id", "asset_id", "role")
);
        ALTER TABLE "auth_users" ADD "deleted_at" TIMESTAMP;
        ALTER TABLE "auth_users" ADD "locked_until" TIMESTAMP;
        ALTER TABLE "auth_users" ADD "failed_login_attempts" INT NOT NULL DEFAULT 0;
        ALTER TABLE "auth_users" ADD "onboarding_completed" INT NOT NULL DEFAULT 0;
        ALTER TABLE "auth_users" ADD "full_name" VARCHAR(255);
        ALTER TABLE "auth_users" ADD "deactivated_at" TIMESTAMP;
        ALTER TABLE "auth_users" ADD "avatar_url" TEXT;
        ALTER TABLE "auth_users" ADD "last_login_at" TIMESTAMP;
        ALTER TABLE "auth_users" ADD "password_changed_at" TIMESTAMP;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "auth_users" DROP COLUMN "deleted_at";
        ALTER TABLE "auth_users" DROP COLUMN "locked_until";
        ALTER TABLE "auth_users" DROP COLUMN "failed_login_attempts";
        ALTER TABLE "auth_users" DROP COLUMN "onboarding_completed";
        ALTER TABLE "auth_users" DROP COLUMN "full_name";
        ALTER TABLE "auth_users" DROP COLUMN "deactivated_at";
        ALTER TABLE "auth_users" DROP COLUMN "avatar_url";
        ALTER TABLE "auth_users" DROP COLUMN "last_login_at";
        ALTER TABLE "auth_users" DROP COLUMN "password_changed_at";
        DROP TABLE IF EXISTS "payments";
        DROP TABLE IF EXISTS "generation_jobs";
        DROP TABLE IF EXISTS "video_clips";
        DROP TABLE IF EXISTS "credit_transactions";
        DROP TABLE IF EXISTS "clip_assets";
        DROP TABLE IF EXISTS "video_projects";
        DROP TABLE IF EXISTS "video_assets";
        DROP TABLE IF EXISTS "prompt_segments";
        DROP TABLE IF EXISTS "user_subscriptions";
        DROP TABLE IF EXISTS "subscription_plans";
        DROP TABLE IF EXISTS "credit_reservations";
        DROP TABLE IF EXISTS "credit_accounts";"""


MODELS_STATE = (
    "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"
    "5/Rn9D3g=="
)
