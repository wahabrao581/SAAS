# Framecraft Admin Guide

## Access and roles

Sign in with an account whose role is `admin` or `superuser` to open the administration panel. The API still checks permissions for every request; hiding admin UI controls is not an authorization boundary.

The Users panel can create regular accounts and delete existing accounts. New accounts are created through the normal signup endpoint and receive the default `user` role. The current user API does not provide an admin action to edit another user's profile or role.

Select **Details** for a user to review their account, credit ledger, payments, subscriptions, projects, prompts, and safe asset links. Project detail responses omit embedded image data and asset metadata.

### Credits, access, payments, and plans

- **Adjust credits** accepts a positive grant or a negative deduction. Enter a reason; every adjustment is recorded in the ledger with the admin actor and an idempotency key.
- **Model access** can allow all active models or restrict the account to selected model keys. Generation requests are checked server-side as well as in the Studio UI. An empty selection denies all models.
- **Assign subscription plan** activates the selected plan, grants its configured period credits to the user's balance, and replaces any current active/trial subscription. Monthly and yearly end dates default to one month or one year from assignment; one-time plans do not expire automatically.
- **Confirm manually** is available for pending credit purchases only. Verify payment with the payment provider before confirming; the confirmation adds credits exactly once and records which admin confirmed it. Subscription plans are assigned separately.

## Providers and models

1. Select **Add provider** and enter a stable provider key, display name, provider type, and service base URL.
2. For authenticated services, put the **environment variable name** containing the credential in **API key environment variable**. Do not enter the key itself in the panel. Configure the secret on the application server and restart/reload the server if required by its deployment.
3. Use **Add model** to register a model key and associate it with the provider. The model key is the value currently entered in the Studio's Model name field.
4. Use **Edit** to update provider/model metadata, or **Delete** to remove a record. Deleting a provider can also remove related provider models.
5. To price an active model, set its `capabilities.credit_rates` map. Rates are credits per generated second, for example `{"credit_rates":{"standard":"0.25","high":"0.4","ultra":"0.6"}}`. The Studio estimate multiplies the selected rate by seconds per scene and scene count. Existing `PROMPTING_MODEL_CREDIT_RATES` values remain a fallback for models without database pricing; scalar legacy rates apply to all qualities.

The current provider endpoints manage catalog records. They do not provision RunPod/Kaggle compute or, by themselves, connect a new provider to the video-generation worker. A worker adapter must support the provider's API protocol, resolve the configured environment variable, and map the model key before the provider can serve generation requests. See [example.txt](./example.txt) for configuration examples and that distinction.

## Subscription plans

Use **Add plan** or **Edit** to maintain plan details, billing interval, credit allowance, visibility, and generation limits. Slugs must be unique. Deleting plans may be blocked by related subscriptions; use the API's error message to identify those constraints.

## Studio controls

- **Hide controls / Show controls** collapses the Studio sidebar. The sidebar stays fixed near the top while scrolling and can scroll internally when taller than the viewport.
- Drag an asset from the sidebar library onto a scene, or use **Attach** with the scene selector.
- **Pin** adds an asset to every current scene and automatically includes it in subsequently loaded scenes of that project. **Unpin** removes it from all scenes. Pins are held in browser memory and reset when switching projects or signing out.
- Use the theme button in the header to switch between dark and light themes. The selection is saved in this browser.
- The **Profile & credits** button opens account balance, lifetime credits, current plan, permitted models, and recent credit activity.
- The left-side estimate updates from the selected model, quality, duration, and scene count. The backend recalculates the same estimate and enforces model access before reserving credits.

## API failures

Use **Refresh data** to retry loading admin tables. Individual API errors are shown in the affected table and in the notice above the cards. The backend remains authoritative: a missing permission, invalid field, duplicate key, or related-record constraint is reported rather than silently treated as a successful change.
