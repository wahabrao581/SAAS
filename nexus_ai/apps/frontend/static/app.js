const $ = (selector) => document.querySelector(selector);

const ui = {
  authPanel: $("#auth-panel"),
  loginForm: $("#login-form"),
  authNotice: $("#auth-notice"),
  studio: $("#studio"),
  email: $("#email-input"),
  password: $("#password-input"),
  connection: $("#connection-indicator"),
  connectionLabel: $("#connection-label"),
  roleIndicator: $("#role-indicator"),
  primaryNav: $("#primary-nav"),
  sidebarToggle: $("#sidebar-toggle"),
  profileToggle: $("#profile-toggle"),
  profileSidebar: $("#profile-sidebar"),
  profileClose: $("#profile-close"),
  profileContent: $("#profile-content"),
  profileName: $("#profile-name"),
  profileAvatar: $("#profile-avatar"),
  profileBalance: $("#profile-credit-balance"),
  themeToggle: $("#theme-toggle"),
  sidebar: $("#studio-sidebar"),
  connectButton: $("#connect-button"),
  signoutButton: $("#signout-button"),
  adminPanel: $("#admin-panel"),
  adminNotice: $("#admin-notice"),
  refreshAdmin: $("#refresh-admin-button"),
  adminUsers: $("#admin-users"),
  adminProviders: $("#admin-providers"),
  adminModels: $("#admin-models"),
  adminPlans: $("#admin-plans"),
  adminUserCount: $("#admin-user-count"),
  adminProviderCount: $("#admin-provider-count"),
  adminModelCount: $("#admin-model-count"),
  adminPlanCount: $("#admin-plan-count"),
  adminUserDetail: $("#admin-user-detail"),
  adminDetailTitle: $("#admin-detail-title"),
  adminDetailContent: $("#admin-detail-content"),
  adminDetailClose: $("#admin-detail-close"),
  adminEditor: $("#admin-editor"),
  adminEditorForm: $("#admin-editor-form"),
  adminEditorTitle: $("#admin-editor-title"),
  adminEditorFields: $("#admin-editor-fields"),
  adminEditorError: $("#admin-editor-error"),
  adminEditorClose: $("#admin-editor-close"),
  adminEditorCancel: $("#admin-editor-cancel"),
  notice: $("#notice"),
  projects: $("#project-select"),
  projectName: $("#project-name-input"),
  createProject: $("#create-project-button"),
  refreshProjects: $("#refresh-projects-button"),
  masterPrompt: $("#master-prompt"),
  separator: $("#separator-mode"),
  splitButton: $("#split-button"),
  model: $("#model-input"),
  resolution: $("#resolution-input"),
  duration: $("#duration-input"),
  quality: $("#quality-input"),
  creditEstimate: $("#credit-estimate"),
  creditEstimateValue: $("#credit-estimate-value"),
  creditEstimateNote: $("#credit-estimate-note"),
  subscriptionPrompt: $("#subscription-prompt"),
  subscriptionPromptTitle: $("#subscription-prompt-title"),
  subscriptionPromptCopy: $("#subscription-prompt-copy"),
  subscriptionPlanPreview: $("#subscription-plan-preview"),
  generateButton: $("#generate-button"),
  assetTarget: $("#asset-target-select"),
  assetLibrary: $("#asset-library"),
  assetCount: $("#asset-count"),
  canvasTitle: $("#canvas-title"),
  canvasSubtitle: $("#canvas-subtitle"),
  timeline: $("#timeline"),
  jobStatus: $("#job-status"),
  assembleButton: $("#assemble-button"),
};

const assetRoles = [
  "first_frame",
  "last_frame",
  "character",
  "background",
  "reference",
  "style",
  "other",
];
const supportedImageTypes = new Set(["image/png", "image/jpeg", "image/webp", "image/gif"]);
const terminalJobStates = new Set(["completed", "partial", "failed", "canceled"]);
const maxImageBytes = 2 * 1024 * 1024;
const state = {
  token: null,
  role: "user",
  socket: null,
  pendingRequest: null,
  requestQueue: Promise.resolve(),
  projectId: new URLSearchParams(window.location.search).get("project") || sessionStorage.getItem("framecraft.project"),
  segments: [],
  assetLibrary: [],
  lockedAssetIds: new Set(),
  adminData: { users: [], providers: [], models: [], plans: [] },
  activeAdminEditor: null,
  activeAdminUserId: null,
  accountOverview: null,
  projects: [],
  estimateTimer: null,
  expiringSession: false,
  tokenExpiryTimer: null,
  activeJobId: sessionStorage.getItem("framecraft.active_job"),
  pollTimer: null,
};

class RealtimeError extends Error {}

function showNotice(message, kind = "error") {
  ui.notice.textContent = message;
  ui.notice.classList.remove("hidden", "is-success");
  if (kind === "success") ui.notice.classList.add("is-success");
}

function clearNotice() {
  ui.notice.textContent = "";
  ui.notice.classList.add("hidden");
  ui.notice.classList.remove("is-success");
}

function setConnection(status, label) {
  ui.connection.classList.remove("is-online", "is-connecting", "is-error", "is-offline");
  ui.connection.classList.add(`is-${status}`);
  ui.connectionLabel.textContent = label;
  ui.connectButton.textContent = status === "online" ? "Connected" : status === "connecting" ? "Connecting…" : "Connect";
  ui.connectButton.disabled = status === "online" || status === "connecting";
}

function showStudio() {
  ui.authPanel.classList.add("hidden");
  ui.studio.classList.remove("hidden");
  ui.adminPanel.classList.add("hidden");
  ui.sidebarToggle.classList.remove("hidden");
  ui.profileToggle.classList.remove("hidden");
  ui.primaryNav.classList.remove("hidden");
  ui.connectButton.classList.remove("hidden");
  ui.connection.classList.remove("hidden");
  ui.roleIndicator.classList.add("hidden");
  ui.signoutButton.classList.remove("hidden");
}

function showAdminPanel() {
  ui.authPanel.classList.add("hidden");
  ui.studio.classList.add("hidden");
  ui.adminPanel.classList.remove("hidden");
  ui.sidebarToggle.classList.add("hidden");
  ui.profileToggle.classList.add("hidden");
  ui.primaryNav.classList.add("hidden");
  ui.profileSidebar.classList.add("hidden");
  ui.connectButton.classList.add("hidden");
  ui.connection.classList.add("hidden");
  ui.roleIndicator.textContent = state.role === "superuser" ? "Superuser" : "Admin";
  ui.roleIndicator.classList.remove("hidden");
  ui.signoutButton.classList.remove("hidden");
  loadAdminData();
}

function showAuthenticatedView() {
  if (state.role === "admin" || state.role === "superuser") showAdminPanel();
  else {
    showStudio();
    connectSocket();
  }
}

function applyTheme(theme) {
  const selected = theme === "light" ? "light" : "dark";
  document.body.dataset.theme = selected;
  ui.themeToggle.textContent = selected === "dark" ? "Light theme" : "Dark theme";
  ui.themeToggle.setAttribute("aria-label", `Switch to ${selected === "dark" ? "light" : "dark"} theme`);
  localStorage.setItem("framecraft.theme", selected);
}

function toggleSidebar() {
  const collapsed = ui.studio.classList.toggle("sidebar-collapsed");
  ui.sidebarToggle.textContent = collapsed ? "Show controls" : "Hide controls";
  ui.sidebarToggle.setAttribute("aria-expanded", String(!collapsed));
}

const adminResources = {
  users: {
    path: "/user/",
    itemPath: (item) => `/user/${encodeURIComponent(item.id)}`,
    dataKey: "users",
    body: ui.adminUsers,
    count: ui.adminUserCount,
    columns: 5,
    identity: (item) => item.id,
    cells: (item) => [item.email, item.username, item.role, item.is_active ? "Active" : "Inactive"],
    createPath: "/user/signup",
    fields: [
      { key: "email", label: "Email", type: "email", required: true },
      { key: "username", label: "Username", type: "text" },
      { key: "password", label: "Temporary password", type: "password", required: true, help: "Provide this to the user securely; they should change it after signing in." },
    ],
  },
  providers: {
    path: "/providers/",
    itemPath: (item) => `/providers/${encodeURIComponent(item.name)}`,
    dataKey: "providers",
    body: ui.adminProviders,
    count: ui.adminProviderCount,
    columns: 6,
    identity: (item) => item.name,
    cells: (item) => [item.display_name || item.name, item.provider_type, item.base_url, item.api_key_env, item.is_active ? "Active" : "Inactive"],
    fields: [
      { key: "name", label: "Provider key", type: "text", required: true, maxLength: 100 },
      { key: "display_name", label: "Display name", type: "text", required: true, maxLength: 150 },
      { key: "provider_type", label: "Type", type: "select", required: true, defaultValue: "video_generation", options: ["video_generation", "payment", "storage", "other"] },
      { key: "base_url", label: "Base URL", type: "url", help: "The public API endpoint for your hosted inference service." },
      { key: "api_key_env", label: "API key environment variable", type: "text", maxLength: 100, help: "Enter the server environment variable name, never the secret value." },
      { key: "settings", label: "Settings (JSON)", type: "json", defaultValue: "{}" },
      { key: "is_active", label: "Enabled", type: "checkbox", defaultValue: true },
    ],
  },
  models: {
    path: "/providers/models",
    itemPath: (item) => `/providers/models/${encodeURIComponent(item.id)}`,
    dataKey: "models",
    body: ui.adminModels,
    count: ui.adminModelCount,
    columns: 5,
    identity: (item) => item.id,
    cells: (item) => [item.display_name || item.name, item.provider_id, item.description, item.is_active ? "Active" : "Inactive"],
    fields: [
      { key: "provider_id", label: "Provider", type: "provider", required: true },
      { key: "name", label: "Model key", type: "text", required: true, maxLength: 100 },
      { key: "display_name", label: "Display name", type: "text", required: true, maxLength: 150 },
      { key: "description", label: "Description", type: "textarea" },
      { key: "capabilities", label: "Capabilities (JSON)", type: "json", defaultValue: "{}", help: 'Optional pricing: {"credit_rates":{"standard":"0.25","high":"0.4","ultra":"0.6"}} credits per generated second.' },
      { key: "is_active", label: "Enabled", type: "checkbox", defaultValue: true },
    ],
  },
  plans: {
    path: "/subscriptions/plans",
    itemPath: (item) => `/subscriptions/plans/${encodeURIComponent(item.slug)}`,
    dataKey: "plans",
    body: ui.adminPlans,
    count: ui.adminPlanCount,
    columns: 5,
    identity: (item) => item.slug,
    cells: (item) => [item.name, `${item.price} ${item.currency}`, item.credits_per_period, item.is_active ? "Active" : "Inactive"],
    fields: [
      { key: "name", label: "Plan name", type: "text", required: true },
      { key: "slug", label: "Plan slug", type: "text", required: true },
      { key: "description", label: "Description", type: "textarea" },
      { key: "price", label: "Price", type: "number", valueType: "number", min: 0, step: "0.01", required: true },
      { key: "currency", label: "Currency", type: "text", defaultValue: "USD", required: true },
      { key: "billing_interval", label: "Billing interval", type: "select", defaultValue: "monthly", options: ["one_time", "monthly", "yearly"] },
      { key: "credits_per_period", label: "Credits per period", type: "number", valueType: "number", min: 0, step: "0.0001", required: true },
      { key: "max_concurrent_jobs", label: "Concurrent jobs", type: "number", valueType: "number", min: 1, step: 1, defaultValue: 1 },
      { key: "max_resolution", label: "Maximum resolution", type: "text", defaultValue: "720p" },
      { key: "features", label: "Features (JSON)", type: "json", defaultValue: "{}" },
      { key: "is_active", label: "Enabled", type: "checkbox", defaultValue: true },
      { key: "is_public", label: "Public", type: "checkbox", defaultValue: true },
    ],
  },
};

function listFromResponse(body) {
  if (Array.isArray(body)) return body;
  for (const key of ["results", "items", "data"]) {
    if (Array.isArray(body?.[key])) return body[key];
  }
  throw new Error("The server returned an unexpected list response.");
}

async function adminRequest(path, options = {}) {
  const headers = { Authorization: `Bearer ${state.token}` };
  if (options.body !== undefined) headers["Content-Type"] = "application/json";
  const response = await fetch(path, {
    method: options.method || "GET",
    headers,
    body: options.body === undefined ? undefined : JSON.stringify(options.body),
  });
  const text = await response.text();
  let body = null;
  if (text) {
    try {
      body = JSON.parse(text);
    } catch {
      if (response.ok) throw new Error(`The server returned an unreadable response (HTTP ${response.status}).`);
    }
  }
  if (response.status === 401 && state.token) {
    handleSessionExpired(parseErrorBody(body, "Your session expired. Please sign in again."));
  }
  if (!response.ok) throw new Error(parseErrorBody(body, `Request failed (HTTP ${response.status}).`));
  return body;
}

function showAuthNotice(message) {
  ui.authNotice.textContent = message;
  ui.authNotice.classList.remove("hidden", "is-success");
}

function handleSessionExpired(message) {
  if (state.expiringSession) return;
  state.expiringSession = true;
  signOut(message || "Your session expired. Please sign in again.");
}

function scheduleSessionExpiry() {
  if (state.tokenExpiryTimer) clearTimeout(state.tokenExpiryTimer);
  state.tokenExpiryTimer = null;
  try {
    const segment = state.token?.split(".")[1];
    if (!segment) {
      handleSessionExpired("Your session token could not be read. Please sign in again.");
      return;
    }
    const normalized = segment.replace(/-/g, "+").replace(/_/g, "/");
    const encoded = normalized.padEnd(normalized.length + ((4 - (normalized.length % 4)) % 4), "=");
    const payload = JSON.parse(atob(encoded));
    if (!Number.isFinite(payload.exp)) {
      handleSessionExpired("Your session token does not have a valid expiry. Please sign in again.");
      return;
    }
    const delay = payload.exp * 1000 - Date.now();
    if (delay <= 0) {
      handleSessionExpired("Your session expired. Please sign in again.");
      return;
    }
    state.tokenExpiryTimer = setTimeout(
      () => handleSessionExpired("Your session expired. Please sign in again."),
      Math.min(delay, 2_147_483_647),
    );
  } catch {
    handleSessionExpired("Your session token could not be read. Please sign in again.");
  }
}
function addText(parent, tag, text, className = "") {
  const element = document.createElement(tag);
  element.textContent = text == null ? "" : String(text);
  if (className) element.className = className;
  parent.append(element);
  return element;
}

function formatCredits(value) {
  const amount = Number(value);
  return Number.isFinite(amount) ? amount.toFixed(4).replace(/\.?0+$/, "") : "0";
}

async function loadAccountOverview() {
  const data = await adminRequest("/subscriptions/me");
  state.accountOverview = data;
  const previousModel = ui.model.value;
  ui.model.replaceChildren();
  if (!data.models?.length) {
    ui.model.add(new Option("No active models configured", ""));
    ui.model.disabled = true;
  } else {
    data.models.forEach((model) => {
      ui.model.add(new Option(
        `${model.display_name || model.name} (${model.name})`,
        model.name,
      ));
    });
    ui.model.disabled = false;
    ui.model.value = data.models.some((model) => model.name === previousModel)
      ? previousModel
      : data.models[0].name;
  }
  renderAccountOverview();
  updateCreditEstimate();
}

function renderAccountOverview() {
  const overview = state.accountOverview;
  ui.profileContent.replaceChildren();
  if (!overview) {
    addText(ui.profileContent, "p", "Account details are not available.", "empty-note");
    return;
  }
  const profile = overview.profile || {};
  const credits = overview.credits || {};
  const displayName = profile.full_name || profile.username || profile.email || "Your account";
  ui.profileName.textContent = displayName;
  ui.profileAvatar.textContent = displayName.split(/\s+/).slice(0, 2).map((part) => part[0]).join("").toUpperCase();
  ui.profileBalance.textContent = `${formatCredits(credits.balance)} credits`;
  const currentPlan = overview.subscription;
  ui.subscriptionPrompt.classList.toggle("hidden", Boolean(currentPlan));
  ui.subscriptionPlanPreview.replaceChildren();
  if (!currentPlan) {
    const availablePlans = overview.plans || [];
    ui.subscriptionPromptTitle.textContent = availablePlans.length ? "No active subscription" : "Choose a subscription";
    ui.subscriptionPromptCopy.textContent = availablePlans.length
      ? "Compare the available plans and credit allowances:"
      : "No plans are published yet. Check back or contact your administrator.";
    availablePlans.slice(0, 3).forEach((plan) => {
      const price = new Intl.NumberFormat(undefined, {
        style: "currency",
        currency: plan.currency || "USD",
        maximumFractionDigits: 2,
      }).format(Number(plan.price) || 0);
      addText(
        ui.subscriptionPlanPreview,
        "span",
        `${plan.name} · ${price} · ${formatCredits(plan.credits_per_period)} credits`,
      );
    });
  }
  const identity = document.createElement("section");
  identity.className = "profile-card";
  addText(identity, "h3", profile.full_name || profile.username || profile.email || "Account");
  addText(identity, "p", profile.email || "", "muted");
  addText(identity, "p", `Role: ${profile.role || "user"}`, "profile-meta");
  ui.profileContent.append(identity);

  const balance = document.createElement("section");
  balance.className = "profile-card profile-balance-card";
  addText(balance, "span", "AVAILABLE CREDITS", "eyebrow");
  addText(balance, "strong", formatCredits(credits.balance), "profile-balance");
  addText(balance, "p", `Earned ${formatCredits(credits.lifetime_earned)} · Used ${formatCredits(credits.lifetime_spent)}`, "profile-meta");
  ui.profileContent.append(balance);

  const subscription = document.createElement("section");
  subscription.className = "profile-card";
  addText(subscription, "h3", "Subscription");
  const plan = overview.subscription;
  addText(subscription, "p", plan ? `${plan.plan.name} · ${plan.status}` : "No active plan", "profile-meta");
  if (plan?.current_period_end) addText(subscription, "p", `Renews / ends ${new Date(plan.current_period_end).toLocaleDateString()}`, "profile-meta");
  ui.profileContent.append(subscription);

  const models = document.createElement("section");
  models.className = "profile-card";
  addText(models, "h3", "Available models");
  addText(models, "p", overview.profile?.allowed_models === null
    ? "Your account can use all active models."
    : ((overview.profile?.allowed_models || []).join(", ") || "No models currently assigned."), "profile-meta");
  (overview.models || []).forEach((model) => addText(models, "span", model.display_name || model.name, "model-chip"));
  ui.profileContent.append(models);

  const history = document.createElement("section");
  history.className = "profile-card";
  addText(history, "h3", "Recent credit activity");
  if (!overview.transactions?.length) addText(history, "p", "No credit transactions yet.", "profile-meta");
  (overview.transactions || []).forEach((transaction) => {
    const row = document.createElement("div");
    row.className = "profile-transaction";
    addText(row, "span", transaction.description || transaction.transaction_type);
    addText(row, "strong", `${Number(transaction.amount) > 0 ? "+" : ""}${formatCredits(transaction.amount)}`);
    history.append(row);
  });
  ui.profileContent.append(history);
}

function updateCreditEstimate() {
  if (state.estimateTimer) clearTimeout(state.estimateTimer);
  state.estimateTimer = setTimeout(async () => {
    const modelName = ui.model.value.trim();
    const duration = Number(ui.duration.value);
    const sceneCount = state.segments.length;
    if (!state.projectId || !sceneCount || !modelName || !Number.isFinite(duration) || duration <= 0) {
      ui.creditEstimateValue.textContent = "Choose a project and model";
      ui.creditEstimateNote.textContent = "Split the project into scenes to calculate a total.";
      return;
    }
    ui.creditEstimateValue.textContent = "Calculating…";
    try {
      const estimate = await adminRequest("/subscriptions/estimate", {
        method: "POST",
        body: {
          model_name: modelName,
          quality: ui.quality.value,
          duration_seconds: duration,
          scene_count: sceneCount,
        },
      });
      ui.creditEstimateValue.textContent = `${formatCredits(estimate.total)} credits`;
      ui.creditEstimateNote.textContent = `${formatCredits(estimate.per_scene)} per scene · ${formatCredits(estimate.credit_balance)} available · ${estimate.quality}`;
    } catch (error) {
      ui.creditEstimateValue.textContent = "Estimate unavailable";
      ui.creditEstimateNote.textContent = error.message;
    }
  }, 250);
}

function renderAdminRows(resource, items) {
  resource.body.replaceChildren();
  if (!items.length) {
    const row = document.createElement("tr");
    const cell = document.createElement("td");
    cell.colSpan = resource.columns;
    cell.className = "admin-empty";
    cell.textContent = "No records found.";
    row.append(cell);
    resource.body.append(row);
    return;
  }
  items.forEach((item) => {
    const row = document.createElement("tr");
    resource.cells(item).forEach((value) => {
      const cell = document.createElement("td");
      cell.textContent = value == null || value === "" ? "—" : String(value);
      row.append(cell);
    });
    const actions = document.createElement("td");
    if (resource.dataKey === "users") {
      actions.append(makeAdminAction("Details", () => openAdminUserDetails(item.id)));
    } else if (resource.fields) {
      actions.append(makeAdminAction("Edit", () => openAdminEditor(resource.dataKey, item)));
    }
    actions.append(makeAdminAction("Delete", () => deleteAdminItem(resource.dataKey, item)));
    row.append(actions);
    resource.body.append(row);
  });
}

function makeAdminAction(label, handler) {
  const button = document.createElement("button");
  button.className = "text-button";
  button.type = "button";
  button.textContent = label;
  button.addEventListener("click", handler);
  return button;
}

async function loadAdminData() {
  ui.adminNotice.textContent = "";
  ui.adminNotice.classList.add("hidden");
  ui.refreshAdmin.disabled = true;
  const errors = [];
  await Promise.all(Object.entries(adminResources).map(async ([key, resource]) => {
    try {
      const result = await adminRequest(`${resource.path}?page_size=100`);
      const items = listFromResponse(result);
      state.adminData[resource.dataKey] = items;
      renderAdminRows(resource, items);
      resource.count.textContent = `${items.length} RECORD${items.length === 1 ? "" : "S"}`;
    } catch (error) {
      resource.body.replaceChildren();
      const row = document.createElement("tr");
      const cell = document.createElement("td");
      cell.colSpan = resource.columns;
      cell.className = "admin-empty";
      cell.textContent = error.message;
      row.append(cell);
      resource.body.append(row);
      resource.count.textContent = "UNAVAILABLE";
      errors.push(`${resource.path}: ${error.message}`);
    }
  }));
  if (errors.length) {
    ui.adminNotice.textContent = `Some admin data could not be loaded:\n${errors.join("\n")}`;
    ui.adminNotice.classList.remove("hidden");
  }
  ui.refreshAdmin.disabled = false;
}

function addDetailSection(parent, title) {
  const section = document.createElement("section");
  section.className = "admin-detail-section";
  addText(section, "h3", title);
  parent.append(section);
  return section;
}

function openAdminUserDetails(userId) {
  state.activeAdminUserId = userId;
  ui.adminDetailTitle.textContent = "User details";
  ui.adminDetailContent.replaceChildren();
  addText(ui.adminDetailContent, "p", "Loading user details…", "empty-note");
  ui.adminUserDetail.showModal();
  loadAdminUserDetails(userId).catch((error) => {
    ui.adminDetailContent.replaceChildren();
    addText(ui.adminDetailContent, "p", error.message, "admin-editor-error");
  });
}

async function loadAdminUserDetails(userId) {
  const detail = await adminRequest(`/subscriptions/admin/users/${encodeURIComponent(userId)}`);
  if (state.activeAdminUserId !== userId) return;
  const user = detail.user;
  ui.adminDetailTitle.textContent = user.full_name || user.username || user.email;
  ui.adminDetailContent.replaceChildren();

  const summary = addDetailSection(ui.adminDetailContent, "Account");
  addText(summary, "p", `${user.email} · ${user.role} · ${user.is_active ? "Active" : "Inactive"}`);
  addText(summary, "p", `Credits: ${formatCredits(detail.credits.balance)} available · ${formatCredits(detail.credits.lifetime_spent)} spent`);
  addText(summary, "p", `Verified: ${user.is_verified ? "Yes" : "No"} · Joined ${new Date(user.created_at).toLocaleDateString()}`, "profile-meta");

  renderAdminCreditForm(user.id);
  renderAdminModelAccessForm(user);
  renderAdminSubscriptionForm(user.id);

  const projects = addDetailSection(ui.adminDetailContent, `Projects (${detail.projects.length})`);
  if (!detail.projects.length) addText(projects, "p", "No projects.", "profile-meta");
  detail.projects.forEach((project) => {
    const row = document.createElement("div");
    row.className = "admin-detail-row";
    addText(row, "span", `${project.name} · ${project.status} · ${project.total_scenes} scenes`);
    row.append(makeAdminAction("View prompts & assets", () => loadAdminProjectDetails(project.id)));
    projects.append(row);
  });

  const payments = addDetailSection(ui.adminDetailContent, `Payments (${detail.payments.length})`);
  if (!detail.payments.length) addText(payments, "p", "No payments.", "profile-meta");
  detail.payments.forEach((payment) => {
    const row = document.createElement("div");
    row.className = "admin-detail-row";
    addText(row, "span", `${payment.payment_type} · ${payment.status} · ${payment.amount} ${payment.currency} · ${formatCredits(payment.credits_purchased)} credits`);
    if (payment.status !== "completed" && payment.payment_type === "credit_purchase") {
      row.append(makeAdminAction("Confirm manually", () => confirmAdminPayment(payment.id)));
    }
    payments.append(row);
  });

  const subscriptions = addDetailSection(ui.adminDetailContent, `Subscription history (${detail.subscriptions.length})`);
  if (!detail.subscriptions.length) addText(subscriptions, "p", "No assigned subscriptions.", "profile-meta");
  detail.subscriptions.forEach((subscription) => {
    addText(subscriptions, "p", `${subscription.plan.name} · ${subscription.status} · ${new Date(subscription.started_at).toLocaleDateString()}`);
  });

  const history = addDetailSection(ui.adminDetailContent, `Credit ledger (${detail.transactions.length})`);
  if (!detail.transactions.length) addText(history, "p", "No credit transactions.", "profile-meta");
  detail.transactions.forEach((transaction) => {
    addText(history, "p", `${new Date(transaction.created_at).toLocaleString()} · ${transaction.transaction_type} · ${formatCredits(transaction.amount)} · ${transaction.description || "—"}`, "profile-meta");
  });
}

function renderAdminCreditForm(userId) {
  const section = addDetailSection(ui.adminDetailContent, "Adjust credits");
  const form = document.createElement("form");
  form.className = "admin-action-form";
  const amount = document.createElement("input");
  amount.type = "number";
  amount.step = "0.0001";
  amount.required = true;
  amount.placeholder = "Positive grant or negative deduction";
  const description = document.createElement("input");
  description.required = true;
  description.minLength = 5;
  description.maxLength = 500;
  description.placeholder = "Reason for this adjustment";
  const submit = document.createElement("button");
  submit.className = "button button-small-text";
  submit.type = "submit";
  submit.textContent = "Apply adjustment";
  form.append(amount, description, submit);
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    submit.disabled = true;
    try {
      await adminRequest(`/subscriptions/admin/users/${encodeURIComponent(userId)}/credits`, {
        method: "POST",
        body: {
          amount: Number(amount.value),
          description: description.value.trim(),
          idempotency_key: `admin-adjust:${crypto.randomUUID()}`,
        },
      });
      await loadAdminUserDetails(userId);
      await loadAdminData();
    } catch (error) {
      addText(section, "p", error.message, "admin-editor-error");
    } finally {
      submit.disabled = false;
    }
  });
  section.append(form);
}

function renderAdminModelAccessForm(user) {
  const section = addDetailSection(ui.adminDetailContent, "Model access");
  const unrestricted = user.allowed_models === null;
  const allModels = new Set([
    ...state.adminData.models.map((model) => model.name),
    ...(user.allowed_models || []),
  ]);
  const allowAllLabel = document.createElement("label");
  const allowAll = document.createElement("input");
  allowAll.type = "checkbox";
  allowAll.checked = unrestricted;
  allowAllLabel.append(allowAll, document.createTextNode(" Allow all models"));
  section.append(allowAllLabel);
  const choices = document.createElement("div");
  choices.className = "admin-model-choices";
  const checkboxes = [];
  Array.from(allModels).sort().forEach((name) => {
    const label = document.createElement("label");
    const input = document.createElement("input");
    input.type = "checkbox";
    input.value = name;
    input.checked = (user.allowed_models || []).includes(name);
    input.disabled = unrestricted;
    label.append(input, document.createTextNode(` ${name}`));
    choices.append(label);
    checkboxes.push(input);
  });
  allowAll.addEventListener("change", () => checkboxes.forEach((checkbox) => { checkbox.disabled = allowAll.checked; }));
  section.append(choices);
  const save = document.createElement("button");
  save.className = "button button-small-text";
  save.type = "button";
  save.textContent = "Save model access";
  save.addEventListener("click", async () => {
    save.disabled = true;
    try {
      await adminRequest(`/subscriptions/admin/users/${encodeURIComponent(user.id)}/models`, {
        method: "PUT",
        body: { allowed_models: allowAll.checked ? null : checkboxes.filter((item) => item.checked).map((item) => item.value) },
      });
      await loadAdminUserDetails(user.id);
    } catch (error) {
      addText(section, "p", error.message, "admin-editor-error");
    } finally {
      save.disabled = false;
    }
  });
  section.append(save);
}

function renderAdminSubscriptionForm(userId) {
  const section = addDetailSection(ui.adminDetailContent, "Assign subscription plan");
  const form = document.createElement("form");
  form.className = "admin-action-form";
  const select = document.createElement("select");
  select.required = true;
  select.add(new Option("Choose a plan…", ""));
  state.adminData.plans.filter((plan) => plan.is_active).forEach((plan) => {
    select.add(new Option(`${plan.name} · ${plan.billing_interval} · ${plan.credits_per_period} credits`, plan.id));
  });
  const note = document.createElement("input");
  note.required = true;
  note.minLength = 5;
  note.maxLength = 500;
  note.value = "Manual admin assignment";
  const submit = document.createElement("button");
  submit.className = "button button-small-text";
  submit.type = "submit";
  submit.textContent = "Assign plan";
  form.append(select, note, submit);
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    submit.disabled = true;
    try {
      await adminRequest(`/subscriptions/admin/users/${encodeURIComponent(userId)}/subscription`, {
        method: "POST",
        body: { plan_id: select.value, note: note.value.trim() },
      });
      await loadAdminUserDetails(userId);
    } catch (error) {
      addText(section, "p", error.message, "admin-editor-error");
    } finally {
      submit.disabled = false;
    }
  });
  section.append(form);
}

async function confirmAdminPayment(paymentId) {
  if (!window.confirm("Confirm that payment was manually verified and complete this credit purchase?")) return;
  const providerPaymentId = window.prompt("Optional provider payment reference:");
  if (providerPaymentId === null) return;
  try {
    await adminRequest(`/subscriptions/admin/payments/${encodeURIComponent(paymentId)}/confirm`, {
      method: "POST",
      body: { provider_payment_id: providerPaymentId.trim() || null },
    });
    await loadAdminUserDetails(state.activeAdminUserId);
  } catch (error) {
    ui.adminDetailContent.prepend(Object.assign(document.createElement("p"), {
      className: "admin-editor-error",
      textContent: error.message,
    }));
  }
}

async function loadAdminProjectDetails(projectId) {
  const userId = state.activeAdminUserId;
  ui.adminDetailTitle.textContent = "Project details";
  ui.adminDetailContent.replaceChildren();
  addText(ui.adminDetailContent, "p", "Loading project details…", "empty-note");
  try {
    const data = await adminRequest(`/subscriptions/admin/projects/${encodeURIComponent(projectId)}`);
    ui.adminDetailContent.replaceChildren();
    const back = document.createElement("button");
    back.className = "button button-small-text";
    back.type = "button";
    back.textContent = "← Back to user";
    back.addEventListener("click", () => loadAdminUserDetails(userId));
    ui.adminDetailContent.append(back);
    const project = data.project;
    ui.adminDetailTitle.textContent = project.name;
    const details = addDetailSection(ui.adminDetailContent, "Project");
    addText(details, "p", `${project.user.email} · ${project.status} · ${project.total_scenes} scenes`);
    addText(details, "p", project.description || "No description.", "profile-meta");
    addText(details, "p", project.original_prompt || "No original prompt.", "admin-project-prompt");
    const prompts = addDetailSection(ui.adminDetailContent, `Scene prompts (${data.prompts.length})`);
    data.prompts.forEach((prompt) => {
      const block = document.createElement("article");
      block.className = "admin-project-prompt";
      addText(block, "h4", `Scene ${prompt.sequence}${prompt.title ? ` · ${prompt.title}` : ""}`);
      addText(block, "p", prompt.prompt);
      prompts.append(block);
    });
    const assets = addDetailSection(ui.adminDetailContent, `Assets (${data.assets.length})`);
    if (!data.assets.length) addText(assets, "p", "No assets.", "profile-meta");
    data.assets.forEach((asset) => {
      const row = document.createElement("div");
      row.className = "admin-detail-row";
      addText(row, "span", `${asset.name} · ${asset.mime_type} · ${formatBytes(asset.file_size)}`);
      appendSafeLink(row, asset.url, "Open asset");
      assets.append(row);
    });
    const clips = addDetailSection(ui.adminDetailContent, `Generated clips (${data.clips.length})`);
    data.clips.forEach((clip) => {
      const block = document.createElement("article");
      block.className = "admin-project-prompt";
      addText(block, "h4", `Scene ${clip.sequence} · ${clip.model_name} · ${clip.status}`);
      addText(block, "p", clip.prompt);
      appendSafeLink(block, clip.output_url, "Open generated clip");
      (clip.assets || []).forEach((asset) => {
        const row = document.createElement("div");
        row.className = "admin-detail-row";
        addText(row, "span", `${asset.name} · ${asset.role}`);
        appendSafeLink(row, asset.url, "Open asset");
        block.append(row);
      });
      clips.append(block);
    });
  } catch (error) {
    ui.adminDetailContent.replaceChildren();
    addText(ui.adminDetailContent, "p", error.message, "admin-editor-error");
  }
}

function appendSafeLink(parent, rawUrl, label) {
  if (!rawUrl) return;
  let url;
  try {
    url = new URL(rawUrl, window.location.href);
  } catch {
    return;
  }
  if (!["http:", "https:"].includes(url.protocol)) return;
  const link = document.createElement("a");
  link.href = url.href;
  link.target = "_blank";
  link.rel = "noopener noreferrer";
  link.className = "text-button";
  link.textContent = label;
  parent.append(link);
}

function openAdminEditor(resourceKey, item = null) {
  const resource = adminResources[resourceKey];
  if (!resource?.fields || (item && resource.dataKey === "users")) return;
  state.activeAdminEditor = { resourceKey, item };
  ui.adminEditorTitle.textContent = `${item ? "Edit" : "Add"} ${resourceKey === "models" ? "provider model" : resourceKey === "plans" ? "subscription plan" : resourceKey.slice(0, -1)}`;
  ui.adminEditorError.textContent = "";
  ui.adminEditorError.classList.add("hidden");
  ui.adminEditorFields.replaceChildren();

  resource.fields.forEach((field) => {
    const fieldContainer = document.createElement("div");
    fieldContainer.className = "admin-field";
    const label = document.createElement("label");
    label.textContent = field.label;
    const control = makeAdminField(field, item);
    control.name = field.key;
    if (field.required && !item) control.required = true;
    if (field.maxLength) control.maxLength = field.maxLength;
    label.htmlFor = `admin-field-${field.key}`;
    control.id = label.htmlFor;
    fieldContainer.append(label, control);
    if (field.help) {
      const help = document.createElement("p");
      help.className = "form-note";
      help.textContent = field.help;
      fieldContainer.append(help);
    }
    ui.adminEditorFields.append(fieldContainer);
  });
  ui.adminEditor.showModal();
}

function makeAdminField(field, item) {
  const value = item?.[field.key] ?? field.defaultValue ?? "";
  if (field.type === "textarea" || field.type === "json") {
    const textarea = document.createElement("textarea");
    textarea.rows = field.type === "json" ? 5 : 3;
    textarea.value = field.type === "json" && typeof value !== "string" ? JSON.stringify(value, null, 2) : value;
    return textarea;
  }
  if (field.type === "select" || field.type === "provider") {
    const select = document.createElement("select");
    select.className = "select-control";
    const choices = field.type === "provider"
      ? state.adminData.providers.map((provider) => [provider.id, `${provider.display_name} (${provider.name})`])
      : field.options.map((option) => [option, option]);
    select.add(new Option("Choose…", ""));
    choices.forEach(([optionValue, label]) => select.add(new Option(label, optionValue)));
    select.value = value;
    return select;
  }
  if (field.type === "checkbox") {
    const input = document.createElement("input");
    input.type = "checkbox";
    input.checked = Boolean(value);
    return input;
  }
  const input = document.createElement("input");
  input.type = field.type;
  input.value = value;
  if (field.min !== undefined) input.min = field.min;
  if (field.step !== undefined) input.step = field.step;
  return input;
}

function readAdminForm() {
  const resource = adminResources[state.activeAdminEditor.resourceKey];
  const data = {};
  resource.fields.forEach((field) => {
    const control = ui.adminEditorForm.elements.namedItem(field.key);
    if (field.type === "checkbox") {
      data[field.key] = control.checked;
    } else if (field.type === "json") {
      try {
        data[field.key] = JSON.parse(control.value || "{}");
      } catch {
        throw new Error(`${field.label} must contain valid JSON.`);
      }
    } else {
      const value = control.value.trim();
      if (field.key === "username" && !value) data[field.key] = null;
      else if (field.valueType === "number" && value) data[field.key] = Number(value);
      else if (field.type !== "password" && !value && !field.required && field.type !== "select" && field.type !== "provider") data[field.key] = null;
      else data[field.key] = value;
    }
  });
  return data;
}

async function submitAdminEditor(event) {
  event.preventDefault();
  if (!state.activeAdminEditor) return;
  const { resourceKey, item } = state.activeAdminEditor;
  const resource = adminResources[resourceKey];
  const submit = ui.adminEditorForm.querySelector('button[type="submit"]');
  submit.disabled = true;
  try {
    const body = readAdminForm();
    const method = item ? "PUT" : "POST";
    const path = item
      ? resource.itemPath(item)
      : (resource.createPath || resource.path);
    await adminRequest(path, { method, body });
    ui.adminEditor.close();
    state.activeAdminEditor = null;
    await loadAdminData();
  } catch (error) {
    ui.adminEditorError.textContent = error.message;
    ui.adminEditorError.classList.remove("hidden");
  } finally {
    submit.disabled = false;
  }
}

async function deleteAdminItem(resourceKey, item) {
  const resource = adminResources[resourceKey];
  const identity = resource.identity(item);
  const display = item.display_name || item.name || item.email || item.slug || identity;
  if (!window.confirm(`Delete "${display}"? This cannot be undone.`)) return;
  try {
    await adminRequest(resource.itemPath(item), { method: "DELETE" });
    await loadAdminData();
  } catch (error) {
    ui.adminNotice.textContent = error.message;
    ui.adminNotice.classList.remove("hidden");
  }
}

function parseErrorBody(body, fallback) {
  if (typeof body?.detail === "string") return body.detail;
  if (Array.isArray(body?.detail)) {
    return body.detail.map((item) => {
      const location = Array.isArray(item.loc) ? item.loc.join(".") : "input";
      return `${location}: ${item.msg || "Invalid value"}`;
    }).join("\n");
  }
  if (typeof body?.message === "string") return body.message;
  return fallback;
}

function describeValidationErrors(errors) {
  if (!Array.isArray(errors)) return "The server rejected this action.";
  return errors.map((item) => {
    const location = Array.isArray(item.loc) ? item.loc.join(".") : "input";
    return `${location}: ${item.msg || item.type || "Invalid value"}`;
  }).join("\n");
}

async function login(email, password) {
  const response = await fetch("/user/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  let body;
  try {
    body = await response.json();
  } catch {
    throw new Error(`Sign-in failed (HTTP ${response.status}). The server returned an unreadable response.`);
  }
  if (!response.ok) throw new Error(parseErrorBody(body, `Sign-in failed (HTTP ${response.status}).`));
  if (!body.access_token) throw new Error("Sign-in response did not contain an access token.");
  ui.authNotice.textContent = "";
  ui.authNotice.classList.add("hidden");
  state.token = body.access_token;
  state.role = ["admin", "superuser"].includes(body.role) ? body.role : "user";
  scheduleSessionExpiry();
  sessionStorage.setItem("framecraft.access_token", state.token);
  sessionStorage.setItem("framecraft.role", state.role);
  ui.password.value = "";
}

function connectSocket() {
  if (!state.token) {
    showNotice("Sign in before connecting to realtime.");
    return;
  }
  if (state.socket && [WebSocket.CONNECTING, WebSocket.OPEN].includes(state.socket.readyState)) return;

  clearNotice();
  setConnection("connecting", "Connecting");
  const url = new URL("/realtime/", window.location.href);
  url.protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  url.searchParams.set("token", state.token);
  const socket = new WebSocket(url);
  state.socket = socket;

  socket.addEventListener("open", async () => {
    if (state.socket !== socket) return;
    setConnection("online", "Realtime connected");
    showStudio();
    try {
      await loadAccountOverview();
      const savedProjectId = state.projectId;
      const savedJobId = state.activeJobId;
      await loadProjects();
      const savedProjectExists = savedProjectId
        && state.projects.some((project) => project.id === savedProjectId);
      if (savedProjectExists) {
        await loadProject(savedProjectId);
      }
      state.activeJobId = savedProjectExists ? savedJobId : null;
      if (state.activeJobId) {
        sessionStorage.setItem("framecraft.active_job", state.activeJobId);
        scheduleJobPoll(0);
      } else {
        sessionStorage.removeItem("framecraft.active_job");
      }
      updateCreditEstimate();
    } catch (error) {
      showNotice(error.message);
    }
  });

  socket.addEventListener("message", (event) => {
    let message;
    try {
      message = JSON.parse(event.data);
    } catch {
      showNotice("Received an invalid JSON message from the realtime server.");
      return;
    }
    const pending = state.pendingRequest;
    if (!pending || message.action !== pending.action) {
      if (message.status === "error") {
        showNotice(message.message || describeValidationErrors(message.errors));
      }
      return;
    }
    clearTimeout(pending.timeout);
    state.pendingRequest = null;
    if (message.status === "error") {
      const errorText = message.errors
        ? describeValidationErrors(message.errors)
        : (message.message || "The realtime action failed.");
      pending.reject(new RealtimeError(errorText));
      return;
    }
    pending.resolve(message.data ?? {});
  });

  socket.addEventListener("error", () => {
    if (state.socket === socket) showNotice("WebSocket connection error. Check the server and try connecting again.");
  });

  socket.addEventListener("close", (event) => {
    if (state.socket !== socket) return;
    state.socket = null;
    setConnection(event.code === 1000 ? "offline" : "error", event.code === 1000 ? "Disconnected" : "Connection closed");
    if (state.pendingRequest) {
      clearTimeout(state.pendingRequest.timeout);
      state.pendingRequest.reject(new Error("Realtime connection closed before the action completed."));
      state.pendingRequest = null;
    }
    if (event.code !== 1000) {
      showNotice(event.reason || "The realtime connection closed. Reconnect and retry the action.");
      adminRequest("/subscriptions/me").catch(() => undefined);
    }
  });
}

function sendActionNow(action, payload) {
  if (!state.socket || state.socket.readyState !== WebSocket.OPEN) {
    return Promise.reject(new Error("Realtime is disconnected. Connect before sending an action."));
  }
  if (state.pendingRequest) {
    return Promise.reject(new Error("Another realtime action is still waiting for a response."));
  }

  return new Promise((resolve, reject) => {
    const timeout = setTimeout(() => {
      if (state.pendingRequest?.action !== action) return;
      state.pendingRequest = null;
      reject(new Error(`Timed out waiting for "${action}". Check the connection and try again.`));
      if (state.socket?.readyState === WebSocket.OPEN) {
        state.socket.close(4000, "Action response timeout");
      }
    }, 45000);
    state.pendingRequest = { action, resolve, reject, timeout };
    try {
      state.socket.send(JSON.stringify({ action, payload }));
    } catch (error) {
      clearTimeout(timeout);
      state.pendingRequest = null;
      reject(new Error(`Could not send "${action}": ${error.message}`));
    }
  });
}

function sendAction(action, payload = {}) {
  const request = state.requestQueue.then(() => sendActionNow(action, payload));
  state.requestQueue = request.catch(() => undefined);
  return request;
}

function appendProjectOption(project) {
  const option = document.createElement("option");
  option.value = project.id;
  option.textContent = `${project.name} · ${project.status}`;
  ui.projects.append(option);
}

async function loadProjects() {
  const result = await sendAction("list_projects", { limit: 100, offset: 0 });
  ui.projects.replaceChildren(new Option("Choose a project…", ""));
  state.projects = Array.isArray(result.projects) ? result.projects : [];
  state.projects.forEach(appendProjectOption);
  if (state.projectId && state.projects.some((project) => project.id === state.projectId)) {
    ui.projects.value = state.projectId;
  } else if (state.projectId) {
    state.projectId = null;
    sessionStorage.removeItem("framecraft.project");
  }
}

function makeScene(segment) {
  return {
    id: segment.id,
    sequence: segment.sequence,
    title: segment.title || `Scene ${segment.sequence}`,
    prompt: segment.prompt,
    savedPrompt: segment.prompt,
    dirty: false,
    isApproved: Boolean(segment.is_approved),
    assets: [],
    clip: null,
  };
}

async function loadProject(projectId) {
  const nextProjectId = projectId || null;
  if (state.projectId !== nextProjectId) state.lockedAssetIds.clear();
  state.projectId = nextProjectId;
  state.activeJobId = null;
  sessionStorage.removeItem("framecraft.active_job");
  if (state.projectId) sessionStorage.setItem("framecraft.project", state.projectId);
  else sessionStorage.removeItem("framecraft.project");
  if (state.pollTimer) clearTimeout(state.pollTimer);
  state.pollTimer = null;
  if (!projectId) {
    state.segments = [];
    state.assetLibrary = [];
    ui.masterPrompt.value = "";
    ui.canvasTitle.textContent = "Your scenes, in sequence";
    ui.canvasSubtitle.textContent = "Split a prompt to begin building your timeline.";
    ui.jobStatus.classList.add("hidden");
    ui.assembleButton.classList.add("hidden");
    renderTimeline();
    renderAssetLibrary();
    updateCreditEstimate();
    return;
  }

  clearNotice();
  const [project, segmentResult, assetResult] = await Promise.all([
    sendAction("get_project", { project_id: projectId }),
    sendAction("get_prompt_segments", { project_id: projectId }),
    sendAction("list_assets", { project_id: projectId }),
  ]);
  ui.canvasTitle.textContent = project.name || "Project storyboard";
  ui.canvasSubtitle.textContent = `${project.status || "draft"} · ${project.total_scenes || 0} scenes`;
  ui.masterPrompt.value = project.original_prompt || "";
  state.segments = (segmentResult.segments || []).map(makeScene);
  state.assetLibrary = (assetResult.assets || []).map((asset) => ({
    id: asset.id,
    assetId: asset.id,
    name: asset.name,
    url: asset.url,
    mimeType: asset.mime_type,
    fileSize: asset.file_size,
    role: "reference",
  }));
  state.segments.forEach(applyLockedAssets);
  renderTimeline();
  renderAssetLibrary();
  updateCreditEstimate();
}

function setProjectSelection(projectId) {
  state.projectId = projectId;
  ui.projects.value = projectId || "";
  ui.assetTarget.replaceChildren(new Option("Choose a scene…", ""));
  state.segments.forEach((scene) => {
    const option = new Option(`Scene ${scene.sequence}`, scene.id);
    ui.assetTarget.append(option);
  });
}

function renderTimeline() {
  ui.timeline.replaceChildren();
  ui.generateButton.disabled = !state.projectId || state.segments.length === 0 || !ui.model.value;
  ui.canvasSubtitle.textContent = state.segments.length
    ? `${state.segments.length} ${state.segments.length === 1 ? "scene" : "scenes"} · Drag image references onto a scene`
    : (state.projectId ? "This project has no scenes yet. Add a prompt and split it." : "Split a prompt to begin building your timeline.");

  if (state.segments.length === 0) {
    const empty = document.createElement("div");
    empty.className = "timeline-empty";
    empty.innerHTML = '<div class="empty-illustration" aria-hidden="true"><span class="film-frame frame-one"></span><span class="film-frame frame-two"></span><span class="film-frame frame-three"></span></div><h2>Your storyboard starts here</h2><p>Add a script on the left and split it into scenes.<br>Then drag reference images onto any scene.</p>';
    ui.timeline.append(empty);
    setProjectSelection(state.projectId);
    return;
  }

  state.segments.forEach((scene) => ui.timeline.append(renderScene(scene)));
  setProjectSelection(state.projectId);
}

function renderScene(scene) {
  const card = document.createElement("article");
  card.className = "scene-card";
  card.dataset.sceneId = scene.id;
  card.addEventListener("dragover", (event) => {
    const types = Array.from(event.dataTransfer.types);
    if (types.includes("Files") || types.includes("application/x-framecraft-asset-id")) {
      event.preventDefault();
      card.classList.add("is-dragging");
    }
  });
  card.addEventListener("dragleave", (event) => {
    if (!card.contains(event.relatedTarget)) card.classList.remove("is-dragging");
  });
  card.addEventListener("drop", (event) => {
    event.preventDefault();
    card.classList.remove("is-dragging");
    if (event.dataTransfer.files.length) {
      addImagesToScene(scene, event.dataTransfer.files);
      return;
    }
    const assetId = event.dataTransfer.getData("application/x-framecraft-asset-id");
    const asset = state.assetLibrary.find((item) => item.assetId === assetId);
    if (asset) attachAssetToScene(scene, asset);
  });

  const header = document.createElement("div");
  header.className = "scene-header";
  const number = document.createElement("span");
  number.className = "scene-number";
  number.textContent = `SCENE ${String(scene.sequence).padStart(2, "0")}`;
  const actions = document.createElement("div");
  actions.className = "scene-actions";
  const approval = document.createElement("span");
  approval.className = `scene-state${scene.isApproved ? " approved" : ""}`;
  approval.textContent = scene.isApproved ? "Approved" : "Draft";
  const saveButton = document.createElement("button");
  saveButton.className = "text-button";
  saveButton.type = "button";
  saveButton.textContent = "Save";
  saveButton.addEventListener("click", () => saveScene(scene));
  const approveButton = document.createElement("button");
  approveButton.className = "text-button";
  approveButton.type = "button";
  approveButton.textContent = scene.isApproved ? "Approved ✓" : "Approve";
  approveButton.disabled = scene.isApproved;
  approveButton.addEventListener("click", () => approveScene(scene));
  actions.append(approval, saveButton, approveButton);
  header.append(number, actions);

  const body = document.createElement("div");
  body.className = "scene-body";
  body.append(renderClip(scene));
  const prompt = document.createElement("textarea");
  prompt.className = "scene-prompt";
  prompt.rows = 3;
  prompt.maxLength = 20000;
  prompt.setAttribute("aria-label", `Prompt for scene ${scene.sequence}`);
  prompt.value = scene.prompt;
  prompt.addEventListener("input", () => {
    scene.prompt = prompt.value;
    scene.dirty = scene.prompt !== scene.savedPrompt;
    if (scene.isApproved) {
      scene.isApproved = false;
      approval.classList.remove("approved");
      approval.textContent = "Draft";
      approveButton.textContent = "Approve";
      approveButton.disabled = false;
    }
  });
  body.append(prompt);

  const footer = document.createElement("div");
  footer.className = "scene-footer";
  const hint = document.createElement("span");
  hint.className = "scene-hint";
  hint.textContent = "Changes apply to this scene only · 20,000 characters max";
  footer.append(hint);
  body.append(footer);

  const assets = document.createElement("div");
  assets.className = "scene-assets";
  scene.assets.forEach((asset) => assets.append(renderSceneAsset(scene, asset)));
  assets.append(renderDropZone(scene));
  body.append(assets);
  const dropHint = document.createElement("p");
  dropHint.className = "scene-drop-hint";
  dropHint.textContent = "Drop images here or choose files. Images are sent as JSON data (2 MB max each).";
  body.append(dropHint);
  card.append(header, body);
  return card;
}

function renderClip(scene) {
  const preview = document.createElement("div");
  preview.className = "clip-preview";
  const clip = scene.clip;
  if (clip?.output_url) {
    const video = document.createElement("video");
    video.className = "clip-video";
    video.controls = true;
    video.preload = "metadata";
    video.src = clip.output_url;
    preview.append(video);
    const status = document.createElement("div");
    status.className = "clip-progress-row";
    status.textContent = `${clip.status || "completed"} · ${clip.progress ?? 100}%`;
    preview.append(status);
    return preview;
  }

  const placeholder = document.createElement("div");
  placeholder.className = "clip-placeholder";
  const icon = document.createElement("span");
  icon.className = "clip-placeholder-icon";
  icon.textContent = clip ? "◌" : "▶";
  const text = document.createElement("span");
  text.textContent = clip
    ? (clip.error_message || `${clip.status || "queued"} · ${clip.progress || 0}%`)
    : "Generated clip will appear here";
  placeholder.append(icon, text);
  preview.append(placeholder);

  if (clip && !clip.error_message) {
    const track = document.createElement("div");
    track.className = "progress-track";
    const fill = document.createElement("div");
    fill.className = "progress-fill";
    fill.style.width = `${Math.max(0, Math.min(100, Number(clip.progress) || 0))}%`;
    track.append(fill);
    preview.append(track);
  }
  return preview;
}

function renderSceneAsset(scene, asset) {
  const card = document.createElement("div");
  card.className = "scene-asset";
  const image = document.createElement("img");
  image.alt = asset.name;
  const imageSource = asset.dataUrl || asset.url;
  if (imageSource) image.src = imageSource;
  else image.hidden = true;
  const info = document.createElement("div");
  info.className = "scene-asset-info";
  const name = document.createElement("span");
  name.className = "scene-asset-name";
  name.textContent = asset.name;
  const role = document.createElement("select");
  role.className = "select-control scene-asset-role";
  role.setAttribute("aria-label", `Asset role for ${asset.name}`);
  assetRoles.forEach((value) => role.add(new Option(value.replaceAll("_", " "), value)));
  role.value = asset.role || "reference";
  role.addEventListener("change", () => { asset.role = role.value; });
  info.append(name, role);
  const remove = document.createElement("button");
  remove.className = "remove-asset";
  remove.type = "button";
  remove.textContent = "×";
  remove.setAttribute("aria-label", `Remove ${asset.name} from scene`);
  remove.addEventListener("click", () => {
    if (state.lockedAssetIds.has(asset.assetId)) {
      toggleAssetLock(asset);
      return;
    }
    scene.assets = scene.assets.filter((item) => item.assetId !== asset.assetId);
    renderTimeline();
  });
  if (state.lockedAssetIds.has(asset.assetId)) {
    remove.textContent = "⌑";
    remove.setAttribute("aria-label", `Unpin ${asset.name} from all scenes`);
    remove.title = "Unpin from all scenes";
  }
  card.append(image, info, remove);
  return card;
}

function renderDropZone(scene) {
  const label = document.createElement("label");
  label.className = "drop-zone";
  const fileInput = document.createElement("input");
  fileInput.type = "file";
  fileInput.accept = Array.from(supportedImageTypes).join(",");
  fileInput.multiple = true;
  fileInput.hidden = true;
  fileInput.addEventListener("change", () => {
    addImagesToScene(scene, fileInput.files);
    fileInput.value = "";
  });
  const icon = document.createElement("span");
  icon.className = "drop-icon";
  icon.textContent = "+";
  const text = document.createElement("span");
  text.textContent = "Add image";
  label.append(fileInput, icon, text);
  return label;
}

function renderAssetLibrary() {
  ui.assetLibrary.replaceChildren();
  ui.assetCount.textContent = `${state.assetLibrary.length} FILE${state.assetLibrary.length === 1 ? "" : "S"}`;
  if (state.assetLibrary.length === 0) {
    const empty = document.createElement("p");
    empty.className = "empty-note";
    empty.textContent = "Uploaded references will appear here.";
    ui.assetLibrary.append(empty);
    return;
  }

  state.assetLibrary.forEach((asset) => {
    const row = document.createElement("div");
    row.className = "library-asset";
    row.draggable = true;
    row.addEventListener("dragstart", (event) => {
      event.dataTransfer.setData("application/x-framecraft-asset-id", asset.assetId);
      event.dataTransfer.effectAllowed = "copy";
    });
    const thumb = document.createElement("span");
    thumb.className = "library-thumb";
    if (asset.dataUrl || asset.url) {
      const image = document.createElement("img");
      image.alt = "";
      image.src = asset.dataUrl || asset.url;
      thumb.append(image);
    } else {
      thumb.textContent = "▧";
    }
    const detail = document.createElement("div");
    const name = document.createElement("div");
    name.className = "library-asset-name";
    name.textContent = asset.name;
    const meta = document.createElement("div");
    meta.className = "library-asset-meta";
    meta.textContent = asset.fileSize ? `${formatBytes(asset.fileSize)} · image` : "registered asset";
    detail.append(name, meta);
    const attach = document.createElement("button");
    attach.className = "attach-button";
    attach.type = "button";
    attach.textContent = "Attach";
    attach.disabled = !ui.assetTarget.value || state.segments.length === 0;
    attach.addEventListener("click", () => attachLibraryAsset(asset));
    const pin = document.createElement("button");
    pin.className = "attach-button asset-pin-button";
    pin.type = "button";
    const locked = state.lockedAssetIds.has(asset.assetId);
    pin.textContent = locked ? "Pinned" : "Pin";
    pin.setAttribute("aria-pressed", String(locked));
    pin.setAttribute("aria-label", `${locked ? "Unpin" : "Pin"} ${asset.name} ${locked ? "from" : "to"} all scenes`);
    pin.addEventListener("click", () => toggleAssetLock(asset));
    row.append(thumb, detail, attach, pin);
    ui.assetLibrary.append(row);
  });
}

function attachAssetToScene(scene, asset) {
  if (scene.assets.some((item) => item.assetId === asset.assetId)) {
    showNotice(`${asset.name} is already attached to this scene.`);
    return false;
  }
  if (scene.assets.length >= 30) {
    showNotice(`Scene ${scene.sequence} already has the maximum of 30 image references.`);
    return false;
  }
  scene.assets.push({ ...asset, role: asset.role || "reference" });
  return true;
}

function applyLockedAssets(scene) {
  state.assetLibrary
    .filter((asset) => state.lockedAssetIds.has(asset.assetId))
    .forEach((asset) => attachAssetToScene(scene, asset));
}

function toggleAssetLock(asset) {
  if (state.lockedAssetIds.has(asset.assetId)) {
    state.lockedAssetIds.delete(asset.assetId);
    state.segments.forEach((scene) => {
      scene.assets = scene.assets.filter((item) => item.assetId !== asset.assetId);
    });
  } else {
    const wouldExceedSceneLimit = state.segments.some((scene) => (
      scene.assets.length >= 30 && !scene.assets.some((item) => item.assetId === asset.assetId)
    ));
    if (wouldExceedSceneLimit) {
      showNotice("This asset cannot be pinned because at least one scene already has 30 references.");
      return;
    }
    state.lockedAssetIds.add(asset.assetId);
    state.segments.forEach((scene) => {
      if (!scene.assets.some((item) => item.assetId === asset.assetId)) {
        attachAssetToScene(scene, asset);
      }
    });
  }
  renderTimeline();
  renderAssetLibrary();
}

function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  return `${(bytes / 1024).toFixed(bytes < 1024 * 1024 ? 0 : 1)} KB`;
}

function readDataUrl(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.addEventListener("load", () => resolve(reader.result));
    reader.addEventListener("error", () => reject(new Error(`Could not read ${file.name}.`)));
    reader.readAsDataURL(file);
  });
}

function readImageDimensions(dataUrl) {
  return new Promise((resolve, reject) => {
    const image = new Image();
    image.onload = () => resolve({ width: image.naturalWidth, height: image.naturalHeight });
    image.onerror = () => reject(new Error("This file is not a readable image."));
    image.src = dataUrl;
  });
}

async function addImagesToScene(scene, fileList) {
  const files = Array.from(fileList || []);
  if (files.length === 0) return;
  if (!state.projectId) {
    showNotice("Choose or create a project before adding image references.");
    return;
  }
  if (scene.assets.length + files.length > 30) {
    showNotice("A scene can have at most 30 image references.");
    return;
  }
  for (const file of files) {
    if (!supportedImageTypes.has(file.type)) {
      showNotice(`${file.name}: use a PNG, JPEG, WebP, or GIF image.`);
      continue;
    }
    if (file.size === 0 || file.size > maxImageBytes) {
      showNotice(`${file.name}: image size must be between 1 byte and 2 MB for JSON upload.`);
      continue;
    }
    try {
      const dataUrl = await readDataUrl(file);
      const dimensions = await readImageDimensions(dataUrl);
      const assetRole = "reference";
      const storageKey = `browser/${crypto.randomUUID()}/${file.name.replaceAll("/", "_")}`;
      const registered = await sendAction("register_asset", {
        project_id: state.projectId,
        name: file.name,
        asset_type: "image",
        mime_type: file.type,
        file_size: file.size,
        storage_provider: "custom",
        storage_key: storageKey,
        width: dimensions.width,
        height: dimensions.height,
        metadata: {
          source: "framecraft_browser_upload",
          image_data: dataUrl,
          role: assetRole,
        },
      });
      if (!registered.asset_id) throw new Error("Asset registration response did not include an asset ID.");
      const asset = {
        assetId: registered.asset_id,
        id: registered.asset_id,
        name: registered.name || file.name,
        dataUrl,
        url: registered.url || null,
        fileSize: file.size,
        mimeType: file.type,
        role: assetRole,
      };
      scene.assets.push(asset);
      state.assetLibrary.unshift(asset);
      renderTimeline();
      renderAssetLibrary();
      showNotice(`${file.name} registered and attached to scene ${scene.sequence}.`, "success");
    } catch (error) {
      showNotice(`${file.name}: ${error.message}`);
    }
  }
}

function attachLibraryAsset(asset) {
  const sceneId = ui.assetTarget.value;
  const scene = state.segments.find((item) => item.id === sceneId);
  if (!scene) {
    showNotice("Choose a scene before attaching an asset.");
    return;
  }
  if (!attachAssetToScene(scene, asset)) return;
  renderTimeline();
  renderAssetLibrary();
}

async function saveScene(scene) {
  if (!scene.id) return showNotice("This scene does not have a server ID; split the prompt again.");
  const button = Array.from(document.querySelectorAll(".scene-card")).find((card) => card.dataset.sceneId === scene.id)?.querySelector(".scene-actions .text-button");
  try {
    if (button) button.disabled = true;
    const result = await sendAction("update_prompt_segment", {
      segment_id: scene.id,
      prompt: scene.prompt,
      title: scene.title,
    });
    scene.prompt = result.prompt ?? scene.prompt;
    scene.savedPrompt = scene.prompt;
    scene.dirty = false;
    scene.title = result.title ?? scene.title;
    scene.isApproved = false;
    showNotice(`Scene ${scene.sequence} saved.`, "success");
  } catch (error) {
    showNotice(error.message);
  } finally {
    if (button) button.disabled = false;
  }
}

async function approveScene(scene) {
  try {
    await sendAction("approve_prompt_segments", { segment_ids: [scene.id] });
    scene.isApproved = true;
    renderTimeline();
    showNotice(`Scene ${scene.sequence} approved.`, "success");
  } catch (error) {
    showNotice(error.message);
  }
}

async function splitPrompt() {
  const prompt = ui.masterPrompt.value.trim();
  if (!prompt) {
    showNotice("Write a video prompt before splitting it into scenes.");
    ui.masterPrompt.focus();
    return;
  }
  ui.splitButton.disabled = true;
  clearNotice();
  try {
    const payload = {
      prompt,
      separator_mode: ui.separator.value,
    };
    if (state.projectId) payload.project_id = state.projectId;
    const result = await sendAction("split_prompt", payload);
    if (!result.project_id || !Array.isArray(result.segments)) {
      throw new Error("The server returned an incomplete prompt split response.");
    }
    state.projectId = result.project_id;
    await loadProjects();
    ui.projects.value = state.projectId;
    await loadProject(state.projectId);
    showNotice(`${result.total_segments} scenes created from your prompt.`, "success");
  } catch (error) {
    showNotice(error.message);
  } finally {
    ui.splitButton.disabled = false;
  }
}

async function createProject() {
  const name = ui.projectName.value.trim();
  if (name.length < 2) {
    showNotice("Enter a project name with at least 2 characters.");
    ui.projectName.focus();
    return;
  }
  ui.createProject.disabled = true;
  try {
    const result = await sendAction("create_project", {
      name,
      original_prompt: ui.masterPrompt.value.trim() || null,
    });
    const projectId = result.project?.id;
    if (!projectId) throw new Error("The server did not return a project ID.");
    ui.projectName.value = "";
    await loadProjects();
    ui.projects.value = projectId;
    await loadProject(projectId);
    showNotice(`Project "${name}" created.`, "success");
  } catch (error) {
    showNotice(error.message);
  } finally {
    ui.createProject.disabled = false;
  }
}

async function generateScenes() {
  if (!state.projectId || state.segments.length === 0) {
    showNotice("Choose a project with at least one scene before generating.");
    return;
  }
  const modelName = ui.model.value.trim();
  const duration = Number(ui.duration.value);
  if (!modelName || modelName.length > 100) {
    showNotice("Choose an active model from the model list.");
    return;
  }
  if (!Number.isFinite(duration) || duration <= 0 || duration > 60) {
    showNotice("Clip duration must be greater than 0 and no more than 60 seconds.");
    return;
  }
  if (state.segments.some((scene) => scene.assets.length > 30)) {
    showNotice("A scene can have at most 30 image references.");
    return;
  }
  ui.generateButton.disabled = true;
  clearNotice();
  try {
    for (const scene of state.segments.filter((item) => item.dirty)) {
      const saved = await sendAction("update_prompt_segment", {
        segment_id: scene.id,
        prompt: scene.prompt,
        title: scene.title,
      });
      scene.prompt = saved.prompt ?? scene.prompt;
      scene.savedPrompt = scene.prompt;
      scene.dirty = false;
      scene.isApproved = false;
    }
    const scenesToApprove = state.segments.filter((scene) => !scene.isApproved);
    if (scenesToApprove.length > 0) {
      await sendAction("approve_prompt_segments", {
        segment_ids: scenesToApprove.map((scene) => scene.id),
      });
      scenesToApprove.forEach((scene) => { scene.isApproved = true; });
      renderTimeline();
    }
    const result = await sendAction("submit_video_generation", {
      project_id: state.projectId,
      model_name: modelName,
      idempotency_key: crypto.randomUUID(),
      settings: {},
      clips: state.segments.map((scene) => ({
        sequence: scene.sequence,
        segment_id: scene.id,
        prompt: scene.prompt,
        model_name: modelName,
        settings: {
          resolution: ui.resolution.value,
          duration_seconds: duration,
          fps: 24,
          quality: ui.quality.value,
          aspect_ratio: "16:9",
        },
        assets: scene.assets.map((asset, index) => ({
          asset_id: asset.assetId,
          role: asset.role || "reference",
          sequence: index,
        })),
      })),
    });
    if (!result.job_id) throw new Error("The server did not return a generation job ID.");
    state.activeJobId = result.job_id;
    sessionStorage.setItem("framecraft.active_job", result.job_id);
    state.segments.forEach((scene) => {
      scene.clip = { status: result.status || "queued", progress: 0 };
    });
    ui.jobStatus.textContent = `${result.status || "queued"} · ${result.total_clips} clips`;
    ui.jobStatus.classList.remove("hidden");
    ui.assembleButton.classList.add("hidden");
    renderTimeline();
    showNotice(`Generation job queued (${result.job_id}).`, "success");
    loadAccountOverview().catch((error) => showNotice(`Could not refresh account credits: ${error.message}`));
    scheduleJobPoll(1500);
  } catch (error) {
    showNotice(error.message);
  } finally {
    ui.generateButton.disabled = !state.projectId || state.segments.length === 0 || !ui.model.value;
  }
}

function scheduleJobPoll(delay = 3500) {
  if (!state.activeJobId) return;
  if (state.pollTimer) clearTimeout(state.pollTimer);
  state.pollTimer = setTimeout(refreshJob, delay);
}

async function refreshJob() {
  if (!state.activeJobId || !state.socket || state.socket.readyState !== WebSocket.OPEN) return;
  const jobId = state.activeJobId;
  try {
    const job = await sendAction("get_generation_job", { job_id: jobId });
    const clipResult = await sendAction("get_job_clips", { job_id: jobId });
    if (state.activeJobId !== jobId) return;
    const clipsBySequence = new Map((clipResult.clips || []).map((clip) => [clip.sequence, clip]));
    state.segments.forEach((scene) => {
      const clip = clipsBySequence.get(scene.sequence);
      if (clip) scene.clip = clip;
    });
    ui.jobStatus.textContent = `${job.status} · ${job.completed_clips || 0}/${job.total_clips || 0} complete`;
    ui.jobStatus.classList.remove("hidden");
    ui.assembleButton.classList.toggle("hidden", !["completed", "partial"].includes(job.status));
    renderTimeline();
    if (terminalJobStates.has(job.status)) {
      showNotice(`Generation finished with status: ${job.status}.`, job.status === "completed" ? "success" : "error");
      return;
    }
    scheduleJobPoll(4000);
  } catch (error) {
    showNotice(`Could not refresh generation status: ${error.message}`);
    scheduleJobPoll(6000);
  }
}

async function assembleVideo() {
  if (!state.projectId || !state.activeJobId) {
    showNotice("There is no generation job to assemble.");
    return;
  }
  ui.assembleButton.disabled = true;
  try {
    const result = await sendAction("assemble_video", {
      project_id: state.projectId,
      job_id: state.activeJobId,
      output_name: "final_video.mp4",
      include_audio: true,
    });
    ui.jobStatus.textContent = `assembly ${result.status}`;
    showNotice(result.message || "Video assembly queued.", "success");
    scheduleJobPoll(2500);
  } catch (error) {
    showNotice(error.message);
  } finally {
    ui.assembleButton.disabled = false;
  }
}

function signOut(reason = "") {
  if (state.tokenExpiryTimer) clearTimeout(state.tokenExpiryTimer);
  state.tokenExpiryTimer = null;
  if (state.pollTimer) clearTimeout(state.pollTimer);
  state.pollTimer = null;
  if (state.pendingRequest) {
    clearTimeout(state.pendingRequest.timeout);
    state.pendingRequest.reject(new Error("Signed out before the realtime action completed."));
    state.pendingRequest = null;
  }
  if (state.socket) {
    const socket = state.socket;
    state.socket = null;
    socket.close(1000, "Signed out");
  }
  state.token = null;
  state.role = "user";
  state.projectId = null;
  state.segments = [];
  state.assetLibrary = [];
  state.lockedAssetIds.clear();
  state.accountOverview = null;
  state.projects = [];
  state.activeJobId = null;
  state.pendingRequest = null;
  sessionStorage.removeItem("framecraft.access_token");
  sessionStorage.removeItem("framecraft.role");
  sessionStorage.removeItem("framecraft.project");
  sessionStorage.removeItem("framecraft.active_job");
  const rememberedEmail = ui.email.value;
  ui.loginForm.reset();
  if (reason) ui.email.value = rememberedEmail;
  ui.authPanel.classList.remove("hidden");
  ui.studio.classList.add("hidden");
  ui.studio.classList.remove("sidebar-collapsed");
  ui.adminPanel.classList.add("hidden");
  ui.sidebarToggle.classList.add("hidden");
  ui.primaryNav.classList.add("hidden");
  ui.profileToggle.classList.add("hidden");
  ui.profileSidebar.classList.add("hidden");
  ui.sidebarToggle.textContent = "Hide controls";
  ui.sidebarToggle.setAttribute("aria-expanded", "true");
  ui.signoutButton.classList.add("hidden");
  ui.roleIndicator.classList.add("hidden");
  ui.connectButton.classList.remove("hidden");
  ui.connection.classList.remove("hidden");
  setConnection("offline", "Disconnected");
  clearNotice();
  ui.profileName.textContent = "Your account";
  ui.profileAvatar.textContent = "FC";
  ui.profileBalance.textContent = "Credits";
  ui.authNotice.textContent = "";
  ui.authNotice.classList.add("hidden");
  state.expiringSession = false;
  if (reason) showAuthNotice(reason);
}

ui.loginForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  clearNotice();
  ui.authNotice.textContent = "";
  ui.authNotice.classList.add("hidden");
  const submit = ui.loginForm.querySelector('button[type="submit"]');
  submit.disabled = true;
  try {
    await login(ui.email.value.trim(), ui.password.value);
    if (!state.token) return;
    showAuthenticatedView();
  } catch (error) {
    showAuthNotice(error.message);
  } finally {
    submit.disabled = false;
  }
});

ui.connectButton.addEventListener("click", connectSocket);
ui.refreshAdmin.addEventListener("click", loadAdminData);
ui.sidebarToggle.addEventListener("click", toggleSidebar);
ui.profileToggle.addEventListener("click", () => {
  const isHidden = ui.profileSidebar.classList.toggle("hidden");
  ui.profileToggle.setAttribute("aria-expanded", String(!isHidden));
  if (!isHidden && !state.accountOverview) {
    loadAccountOverview().catch((error) => showNotice(error.message));
  }
});
ui.profileClose.addEventListener("click", () => {
  ui.profileSidebar.classList.add("hidden");
  ui.profileToggle.setAttribute("aria-expanded", "false");
});
ui.adminDetailClose.addEventListener("click", () => {
  ui.adminUserDetail.close();
  state.activeAdminUserId = null;
});
ui.themeToggle.addEventListener("click", () => {
  applyTheme(document.body.dataset.theme === "dark" ? "light" : "dark");
});
ui.adminEditorForm.addEventListener("submit", submitAdminEditor);
ui.adminEditorClose.addEventListener("click", () => {
  ui.adminEditor.close();
  state.activeAdminEditor = null;
});
ui.adminEditorCancel.addEventListener("click", () => {
  ui.adminEditor.close();
  state.activeAdminEditor = null;
});
document.querySelectorAll("[data-admin-add]").forEach((button) => {
  button.addEventListener("click", () => openAdminEditor(button.dataset.adminAdd));
});
ui.signoutButton.addEventListener("click", signOut);
ui.splitButton.addEventListener("click", splitPrompt);
ui.createProject.addEventListener("click", createProject);
ui.refreshProjects.addEventListener("click", () => loadProjects().catch((error) => showNotice(error.message)));
ui.generateButton.addEventListener("click", generateScenes);
ui.assembleButton.addEventListener("click", assembleVideo);

ui.projects.addEventListener("change", async () => {
  try {
    const projectId = ui.projects.value;
    if (state.projectId !== projectId) state.lockedAssetIds.clear();
    setProjectSelection(projectId);
    await loadProject(projectId);
    clearNotice();
  } catch (error) {
    showNotice(error.message);
  }
});

ui.assetTarget.addEventListener("change", renderAssetLibrary);
ui.model.addEventListener("change", updateCreditEstimate);
ui.duration.addEventListener("input", updateCreditEstimate);
ui.quality.addEventListener("change", updateCreditEstimate);

applyTheme(localStorage.getItem("framecraft.theme") || "dark");

async function restoreSession() {
  const savedToken = sessionStorage.getItem("framecraft.access_token");
  if (!savedToken) {
    setConnection("offline", "Disconnected");
    return;
  }
  state.token = savedToken;
  state.activeJobId = sessionStorage.getItem("framecraft.active_job");
  try {
    const overview = await adminRequest("/subscriptions/me");
    if (!state.token) return;
    state.accountOverview = overview;
    scheduleSessionExpiry();
    if (!state.token) return;
    state.role = ["admin", "superuser"].includes(overview.profile?.role)
      ? overview.profile.role
      : "user";
    sessionStorage.setItem("framecraft.role", state.role);
    showAuthenticatedView();
  } catch (error) {
    if (state.token) {
      showAuthNotice(`Could not verify your saved session. Please sign in again. ${error.message}`);
    }
  }
}

restoreSession().catch((error) => {
  showAuthNotice(`Could not restore your session: ${error.message}`);
  setConnection("offline", "Disconnected");
});
