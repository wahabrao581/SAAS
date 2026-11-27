from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "auth_users" (
    "id" UUID NOT NULL PRIMARY KEY,
    "email" VARCHAR(255) NOT NULL UNIQUE,
    "username" VARCHAR(150) UNIQUE,
    "full_name" VARCHAR(255),
    "avatar_url" TEXT,
    "hashed_password" VARCHAR(255) NOT NULL,
    "is_active" BOOL NOT NULL,
    "is_verified" BOOL NOT NULL,
    "role" VARCHAR(50) NOT NULL,
    "allowed_models" JSONB,
    "last_login_at" TIMESTAMPTZ,
    "password_changed_at" TIMESTAMPTZ,
    "failed_login_attempts" INT NOT NULL,
    "locked_until" TIMESTAMPTZ,
    "deactivated_at" TIMESTAMPTZ,
    "deleted_at" TIMESTAMPTZ,
    "onboarding_completed" BOOL NOT NULL,
    "created_at" TIMESTAMPTZ NOT NULL,
    "updated_at" TIMESTAMPTZ NOT NULL
);
COMMENT ON TABLE "auth_users" IS 'Main SaaS user model.';
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSONB NOT NULL
);
CREATE TABLE IF NOT EXISTS "providers" (
    "id" UUID NOT NULL PRIMARY KEY,
    "name" VARCHAR(100) NOT NULL UNIQUE,
    "display_name" VARCHAR(150) NOT NULL,
    "provider_type" VARCHAR(30) NOT NULL,
    "base_url" TEXT,
    "api_key_env" VARCHAR(100),
    "is_active" BOOL NOT NULL,
    "settings" JSONB NOT NULL,
    "created_at" TIMESTAMPTZ NOT NULL,
    "updated_at" TIMESTAMPTZ NOT NULL
);
CREATE INDEX IF NOT EXISTS "idx_providers_provide_a5e94b" ON "providers" ("provider_type", "is_active");
COMMENT ON TABLE "providers" IS 'External service configuration shared by the application.';
CREATE TABLE IF NOT EXISTS "provider_models" (
    "id" UUID NOT NULL PRIMARY KEY,
    "name" VARCHAR(100) NOT NULL,
    "display_name" VARCHAR(150) NOT NULL,
    "description" TEXT,
    "capabilities" JSONB NOT NULL,
    "is_active" BOOL NOT NULL,
    "created_at" TIMESTAMPTZ NOT NULL,
    "updated_at" TIMESTAMPTZ NOT NULL,
    "provider_id" UUID NOT NULL REFERENCES "providers" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_provider_mo_provide_6926da" UNIQUE ("provider_id", "name")
);
CREATE INDEX IF NOT EXISTS "idx_provider_mo_provide_3344bc" ON "provider_models" ("provider_id", "is_active");
COMMENT ON TABLE "provider_models" IS 'A model exposed by a video-generation provider.';
CREATE TABLE IF NOT EXISTS "credit_accounts" (
    "id" UUID NOT NULL PRIMARY KEY,
    "balance" DECIMAL(18,4) NOT NULL,
    "lifetime_earned" DECIMAL(18,4) NOT NULL,
    "lifetime_spent" DECIMAL(18,4) NOT NULL,
    "created_at" TIMESTAMPTZ NOT NULL,
    "updated_at" TIMESTAMPTZ NOT NULL,
    "user_id" UUID NOT NULL REFERENCES "auth_users" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "credit_reservations" (
    "id" UUID NOT NULL PRIMARY KEY,
    "amount" DECIMAL(18,4) NOT NULL,
    "status" VARCHAR(30) NOT NULL,
    "reference_id" VARCHAR(255) NOT NULL,
    "idempotency_key" VARCHAR(255) NOT NULL,
    "expires_at" TIMESTAMPTZ,
    "consumed_at" TIMESTAMPTZ,
    "released_at" TIMESTAMPTZ,
    "metadata" JSONB NOT NULL,
    "created_at" TIMESTAMPTZ NOT NULL,
    "user_id" UUID NOT NULL REFERENCES "auth_users" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_credit_rese_user_id_b7327a" UNIQUE ("user_id", "idempotency_key")
);
CREATE INDEX IF NOT EXISTS "idx_credit_rese_status_a353d2" ON "credit_reservations" ("status", "expires_at");
CREATE INDEX IF NOT EXISTS "idx_credit_rese_user_id_2662b7" ON "credit_reservations" ("user_id", "created_at");
CREATE TABLE IF NOT EXISTS "credit_transactions" (
    "id" UUID NOT NULL PRIMARY KEY,
    "transaction_type" VARCHAR(30) NOT NULL,
    "amount" DECIMAL(18,4) NOT NULL,
    "balance_before" DECIMAL(18,4) NOT NULL,
    "balance_after" DECIMAL(18,4) NOT NULL,
    "description" TEXT,
    "reference_id" VARCHAR(255),
    "idempotency_key" VARCHAR(255) UNIQUE,
    "metadata" JSONB NOT NULL,
    "created_at" TIMESTAMPTZ NOT NULL,
    "user_id" UUID NOT NULL REFERENCES "auth_users" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_credit_tran_user_id_a2e1e5" ON "credit_transactions" ("user_id", "created_at");
CREATE INDEX IF NOT EXISTS "idx_credit_tran_transac_dfaa64" ON "credit_transactions" ("transaction_type", "created_at");
CREATE TABLE IF NOT EXISTS "subscription_plans" (
    "id" UUID NOT NULL PRIMARY KEY,
    "name" VARCHAR(100) NOT NULL UNIQUE,
    "slug" VARCHAR(100) NOT NULL UNIQUE,
    "description" TEXT,
    "price" DECIMAL(12,2) NOT NULL,
    "currency" VARCHAR(10) NOT NULL,
    "billing_interval" VARCHAR(30) NOT NULL,
    "credits_per_period" DECIMAL(18,4) NOT NULL,
    "is_active" BOOL NOT NULL,
    "is_public" BOOL NOT NULL,
    "features" JSONB NOT NULL,
    "max_concurrent_jobs" INT NOT NULL,
    "max_resolution" VARCHAR(30) NOT NULL,
    "created_at" TIMESTAMPTZ NOT NULL,
    "updated_at" TIMESTAMPTZ NOT NULL
);
CREATE TABLE IF NOT EXISTS "user_subscriptions" (
    "id" UUID NOT NULL PRIMARY KEY,
    "status" VARCHAR(30) NOT NULL,
    "started_at" TIMESTAMPTZ NOT NULL,
    "current_period_start" TIMESTAMPTZ NOT NULL,
    "current_period_end" TIMESTAMPTZ,
    "cancel_at_period_end" BOOL NOT NULL,
    "canceled_at" TIMESTAMPTZ,
    "provider" VARCHAR(50),
    "provider_subscription_id" VARCHAR(255),
    "metadata" JSONB NOT NULL,
    "created_at" TIMESTAMPTZ NOT NULL,
    "updated_at" TIMESTAMPTZ NOT NULL,
    "plan_id" UUID NOT NULL REFERENCES "subscription_plans" ("id") ON DELETE RESTRICT,
    "user_id" UUID NOT NULL REFERENCES "auth_users" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_user_subscr_status_487e70" ON "user_subscriptions" ("status", "current_period_end");
CREATE TABLE IF NOT EXISTS "payments" (
    "id" UUID NOT NULL PRIMARY KEY,
    "payment_type" VARCHAR(30) NOT NULL,
    "status" VARCHAR(30) NOT NULL,
    "amount" DECIMAL(12,2) NOT NULL,
    "currency" VARCHAR(10) NOT NULL,
    "credits_purchased" DECIMAL(18,4) NOT NULL,
    "provider" VARCHAR(50) NOT NULL,
    "provider_payment_id" VARCHAR(255),
    "idempotency_key" VARCHAR(255) NOT NULL UNIQUE,
    "paid_at" TIMESTAMPTZ,
    "metadata" JSONB NOT NULL,
    "created_at" TIMESTAMPTZ NOT NULL,
    "updated_at" TIMESTAMPTZ NOT NULL,
    "subscription_id" UUID REFERENCES "user_subscriptions" ("id") ON DELETE SET NULL,
    "user_id" UUID NOT NULL REFERENCES "auth_users" ("id") ON DELETE RESTRICT
);
CREATE INDEX IF NOT EXISTS "idx_payments_user_id_d6dc35" ON "payments" ("user_id", "created_at");
CREATE INDEX IF NOT EXISTS "idx_payments_status_33acf4" ON "payments" ("status", "created_at");
CREATE TABLE IF NOT EXISTS "video_projects" (
    "id" UUID NOT NULL PRIMARY KEY,
    "name" VARCHAR(255) NOT NULL,
    "description" TEXT,
    "original_prompt" TEXT,
    "status" VARCHAR(30) NOT NULL,
    "default_model" VARCHAR(100),
    "default_settings" JSONB NOT NULL,
    "final_video_url" TEXT,
    "final_video_storage_key" TEXT,
    "total_scenes" INT NOT NULL,
    "total_generated_clips" INT NOT NULL,
    "created_at" TIMESTAMPTZ NOT NULL,
    "updated_at" TIMESTAMPTZ NOT NULL,
    "user_id" UUID NOT NULL REFERENCES "auth_users" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_video_proje_user_id_f93e06" ON "video_projects" ("user_id", "created_at");
CREATE INDEX IF NOT EXISTS "idx_video_proje_user_id_88a881" ON "video_projects" ("user_id", "status");
CREATE TABLE IF NOT EXISTS "video_assets" (
    "id" UUID NOT NULL PRIMARY KEY,
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
    "duration" DOUBLE PRECISION,
    "metadata" JSONB NOT NULL,
    "is_deleted" BOOL NOT NULL,
    "created_at" TIMESTAMPTZ NOT NULL,
    "project_id" UUID REFERENCES "video_projects" ("id") ON DELETE SET NULL,
    "user_id" UUID NOT NULL REFERENCES "auth_users" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_video_asset_user_id_db18eb" ON "video_assets" ("user_id", "created_at");
CREATE INDEX IF NOT EXISTS "idx_video_asset_project_1bfdfc" ON "video_assets" ("project_id", "created_at");
CREATE TABLE IF NOT EXISTS "generation_jobs" (
    "id" UUID NOT NULL PRIMARY KEY,
    "status" VARCHAR(30) NOT NULL,
    "model_name" VARCHAR(100) NOT NULL,
    "total_clips" INT NOT NULL,
    "completed_clips" INT NOT NULL,
    "failed_clips" INT NOT NULL,
    "estimated_credits" DECIMAL(18,4) NOT NULL,
    "actual_credits" DECIMAL(18,4) NOT NULL,
    "credit_reservation_id" UUID,
    "idempotency_key" VARCHAR(255) NOT NULL,
    "settings" JSONB NOT NULL,
    "error_message" TEXT,
    "started_at" TIMESTAMPTZ,
    "completed_at" TIMESTAMPTZ,
    "created_at" TIMESTAMPTZ NOT NULL,
    "updated_at" TIMESTAMPTZ NOT NULL,
    "project_id" UUID NOT NULL REFERENCES "video_projects" ("id") ON DELETE CASCADE,
    "user_id" UUID NOT NULL REFERENCES "auth_users" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_generation__user_id_a17575" UNIQUE ("user_id", "idempotency_key")
);
CREATE INDEX IF NOT EXISTS "idx_generation__user_id_3292fa" ON "generation_jobs" ("user_id", "status");
CREATE INDEX IF NOT EXISTS "idx_generation__project_40871a" ON "generation_jobs" ("project_id", "created_at");
CREATE INDEX IF NOT EXISTS "idx_generation__status_616232" ON "generation_jobs" ("status", "created_at");
CREATE TABLE IF NOT EXISTS "prompt_segments" (
    "id" UUID NOT NULL PRIMARY KEY,
    "sequence" INT NOT NULL,
    "prompt" TEXT NOT NULL,
    "title" VARCHAR(255),
    "is_approved" BOOL NOT NULL,
    "metadata" JSONB NOT NULL,
    "created_at" TIMESTAMPTZ NOT NULL,
    "updated_at" TIMESTAMPTZ NOT NULL,
    "project_id" UUID NOT NULL REFERENCES "video_projects" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_prompt_segm_project_786de3" UNIQUE ("project_id", "sequence")
);
CREATE TABLE IF NOT EXISTS "video_clips" (
    "id" UUID NOT NULL PRIMARY KEY,
    "sequence" INT NOT NULL,
    "prompt" TEXT NOT NULL,
    "model_name" VARCHAR(100) NOT NULL,
    "status" VARCHAR(30) NOT NULL,
    "settings" JSONB NOT NULL,
    "estimated_credits" DECIMAL(18,4) NOT NULL,
    "actual_credits" DECIMAL(18,4) NOT NULL,
    "provider_name" VARCHAR(100),
    "provider_job_id" VARCHAR(255),
    "output_url" TEXT,
    "output_storage_key" TEXT,
    "output_duration" DOUBLE PRECISION,
    "output_width" INT,
    "output_height" INT,
    "progress" INT NOT NULL,
    "error_message" TEXT,
    "retry_count" INT NOT NULL,
    "started_at" TIMESTAMPTZ,
    "completed_at" TIMESTAMPTZ,
    "created_at" TIMESTAMPTZ NOT NULL,
    "updated_at" TIMESTAMPTZ NOT NULL,
    "job_id" UUID NOT NULL REFERENCES "generation_jobs" ("id") ON DELETE CASCADE,
    "project_id" UUID NOT NULL REFERENCES "video_projects" ("id") ON DELETE CASCADE,
    "segment_id" UUID REFERENCES "prompt_segments" ("id") ON DELETE SET NULL,
    CONSTRAINT "uid_video_clips_job_id_321afd" UNIQUE ("job_id", "sequence")
);
CREATE INDEX IF NOT EXISTS "idx_video_clips_job_id_47f1c2" ON "video_clips" ("job_id", "status");
CREATE INDEX IF NOT EXISTS "idx_video_clips_project_919c66" ON "video_clips" ("project_id", "sequence");
CREATE TABLE IF NOT EXISTS "clip_assets" (
    "id" UUID NOT NULL PRIMARY KEY,
    "role" VARCHAR(30) NOT NULL,
    "sequence" INT NOT NULL,
    "created_at" TIMESTAMPTZ NOT NULL,
    "asset_id" UUID NOT NULL REFERENCES "video_assets" ("id") ON DELETE CASCADE,
    "clip_id" UUID NOT NULL REFERENCES "video_clips" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_clip_assets_clip_id_e0e2b3" UNIQUE ("clip_id", "asset_id", "role")
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """


MODELS_STATE = (
    "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"
)
