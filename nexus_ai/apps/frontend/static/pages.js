const pageMessage = document.querySelector("#page-message");
const token = sessionStorage.getItem("framecraft.access_token");
let account = null;
let plans = [];
let selectedPlan = null;

function showPageMessage(message, kind = "error") {
  pageMessage.textContent = message;
  pageMessage.classList.remove("hidden", "is-success");
  if (kind === "success") pageMessage.classList.add("is-success");
}

function applyPageTheme(theme) {
  const selected = theme === "light" ? "light" : "dark";
  document.body.dataset.theme = selected;
  const button = document.querySelector("#pages-theme-toggle");
  button.textContent = selected === "dark" ? "Light theme" : "Dark theme";
  button.setAttribute("aria-label", `Switch to ${selected === "dark" ? "light" : "dark"} theme`);
  localStorage.setItem("framecraft.theme", selected);
}

function clearSavedSession() {
  sessionStorage.removeItem("framecraft.access_token");
  sessionStorage.removeItem("framecraft.role");
  sessionStorage.removeItem("framecraft.project");
  sessionStorage.removeItem("framecraft.active_job");
}

async function apiRequest(path) {
  const response = await fetch(path, {
    headers: { Authorization: `Bearer ${token}` },
  });
  let body = null;
  try {
    body = await response.json();
  } catch {
    if (response.ok) throw new Error("The server returned an unreadable response.");
  }
  if (response.status === 401) {
    clearSavedSession();
    throw new Error("Your session expired. Please sign in again.");
  }
  if (!response.ok) {
    throw new Error(typeof body?.detail === "string" ? body.detail : `Request failed (HTTP ${response.status}).`);
  }
  return body;
}

function setProfile(profile, credits) {
  const name = profile.full_name || profile.username || profile.email || "Account";
  document.querySelector("#pages-profile-name").textContent = name;
  document.querySelector("#pages-credit-balance").textContent = `${Number(credits.balance || 0).toLocaleString()} credits`;
  document.querySelector("#pages-avatar").textContent = name.split(/\s+/).slice(0, 2).map((part) => part[0]).join("").toUpperCase();
}

function addText(parent, tag, text, className = "") {
  const element = document.createElement(tag);
  element.textContent = text == null ? "" : String(text);
  if (className) element.className = className;
  parent.append(element);
  return element;
}

function setupSamplePreviews() {
  document.querySelectorAll(".sample-preview").forEach((preview) => {
    preview.addEventListener("click", () => {
      const { videoId, videoTitle } = preview.dataset;
      if (!videoId || !videoTitle) {
        showPageMessage("A sample video is missing its YouTube details.");
        return;
      }

      const iframe = document.createElement("iframe");
      iframe.src = `https://www.youtube-nocookie.com/embed/${encodeURIComponent(videoId)}?autoplay=1&playsinline=1`;
      iframe.title = videoTitle;
      iframe.allow = "accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share";
      iframe.allowFullscreen = true;
      iframe.referrerPolicy = "strict-origin-when-cross-origin";
      preview.replaceWith(iframe);
    });
  });
}

function formatPrice(plan) {
  const amount = Number(plan.price);
  const price = new Intl.NumberFormat(undefined, {
    style: "currency",
    currency: plan.currency || "USD",
    maximumFractionDigits: 2,
  }).format(Number.isFinite(amount) ? amount : 0);
  return `${price}${plan.billing_interval === "one_time" ? " one time" : ` / ${plan.billing_interval.replace("ly", "")}`}`;
}

function renderPlanSummary() {
  if (!selectedPlan) {
    document.querySelector("#payment-plan-name").textContent = "Select a plan";
    document.querySelector("#payment-plan-price").textContent = "—";
    document.querySelector("#payment-plan-interval").textContent = "";
    document.querySelector("#payment-plan-credits").textContent = "—";
    return;
  }
  document.querySelector("#payment-plan-name").textContent = selectedPlan.name;
  document.querySelector("#payment-plan-price").textContent = new Intl.NumberFormat(undefined, {
    style: "currency",
    currency: selectedPlan.currency || "USD",
    maximumFractionDigits: 2,
  }).format(Number(selectedPlan.price) || 0);
  document.querySelector("#payment-plan-interval").textContent = selectedPlan.billing_interval === "one_time"
    ? "one-time payment"
    : `per ${selectedPlan.billing_interval.replace("ly", "")}`;
  document.querySelector("#payment-plan-credits").textContent = `${Number(selectedPlan.credits_per_period || 0).toLocaleString()} credits`;
}

function renderPlans() {
  const list = document.querySelector("#plan-list");
  list.replaceChildren();
  if (!plans.length) {
    addText(list, "p", "No public plans are available yet. Contact your administrator.", "empty-note");
    renderPlanSummary();
    return;
  }
  plans.forEach((plan) => {
    const card = document.createElement("article");
    card.className = "plan-card";
    const isCurrent = account.subscription?.plan?.id === plan.id;
    if (selectedPlan?.id === plan.id) card.classList.add("is-selected");
    addText(card, "p", isCurrent ? "CURRENT PLAN" : plan.billing_interval.replace("_", " ").toUpperCase(), "eyebrow");
    addText(card, "h2", plan.name);
    addText(card, "strong", formatPrice(plan), "plan-price");
    addText(card, "p", `${Number(plan.credits_per_period || 0).toLocaleString()} credits included`, "plan-credits");
    if (plan.description) addText(card, "p", plan.description, "muted");
    if (plan.features && Object.keys(plan.features).length) {
      const features = document.createElement("ul");
      features.className = "plan-features";
      Object.entries(plan.features).forEach(([name, value]) => {
        addText(features, "li", `${name.replaceAll("_", " ")}: ${typeof value === "object" ? JSON.stringify(value) : value}`);
      });
      card.append(features);
    }
    const choose = document.createElement("button");
    choose.className = `button ${isCurrent ? "button-quiet" : "button-primary"} button-wide`;
    choose.type = "button";
    choose.textContent = isCurrent ? "Current plan" : "View payment details";
    choose.addEventListener("click", () => {
      selectedPlan = plan;
      renderPlans();
      renderPlanSummary();
      document.querySelector("#payment-plan-name").scrollIntoView({ behavior: "smooth", block: "center" });
    });
    card.append(choose);
    list.append(card);
  });
  renderPlanSummary();
}

function renderHistory(projects) {
  const list = document.querySelector("#history-list");
  list.replaceChildren();
  if (!projects.length) {
    addText(list, "p", "No projects yet. Start a new storyboard in Studio.", "empty-note");
    return;
  }
  projects.forEach((project) => {
    const article = document.createElement("article");
    article.className = "history-project";
    const heading = document.createElement("div");
    heading.className = "history-project-heading";
    const title = document.createElement("div");
    addText(title, "p", project.status.toUpperCase(), "eyebrow");
    addText(title, "h2", project.name);
    addText(title, "p", `${project.total_scenes} scenes · Updated ${new Date(project.updated_at).toLocaleString()}`, "muted");
    const open = document.createElement("a");
    open.className = "button button-quiet";
    open.href = `/frontend/?project=${encodeURIComponent(project.id)}`;
    open.textContent = "Open project";
    heading.append(title, open);
    article.append(heading);
    if (project.original_prompt) {
      const original = document.createElement("details");
      original.className = "history-original-prompt";
      addText(original, "summary", "Original project prompt");
      addText(original, "p", project.original_prompt);
      article.append(original);
    }
    const prompts = document.createElement("ol");
    prompts.className = "history-prompts";
    project.prompts.forEach((prompt) => {
      const item = document.createElement("li");
      addText(item, "span", `Scene ${prompt.sequence}${prompt.title ? ` · ${prompt.title}` : ""}`, "history-prompt-title");
      addText(item, "p", prompt.prompt);
      prompts.append(item);
    });
    if (!project.prompts.length) addText(article, "p", "No saved scene prompts.", "muted");
    else article.append(prompts);
    list.append(article);
  });
}

async function startPage() {
  setupSamplePreviews();
  applyPageTheme(localStorage.getItem("framecraft.theme") || "dark");
  document.querySelector("#pages-theme-toggle").addEventListener("click", () => {
    applyPageTheme(document.body.dataset.theme === "dark" ? "light" : "dark");
  });
  document.querySelector("#pages-signout").addEventListener("click", () => {
    clearSavedSession();
    window.location.assign("/frontend/");
  });
  if (!token) {
    showPageMessage("Please sign in to view your account. Your browser does not keep your password.", "error");
    return;
  }
  try {
    const [overview, pageData] = await Promise.all([
      apiRequest("/subscriptions/me"),
      document.body.dataset.page === "subscription"
        ? apiRequest("/subscriptions/available-plans")
        : document.body.dataset.page === "history"
          ? apiRequest("/subscriptions/history")
          : Promise.resolve(null),
    ]);
    account = overview;
    setProfile(overview.profile || {}, overview.credits || {});
    if (document.body.dataset.page === "subscription") {
      plans = pageData;
      selectedPlan = plans.find((plan) => plan.id === account.subscription?.plan?.id) || plans[0] || null;
      renderPlans();
    } else if (document.body.dataset.page === "history") {
      renderHistory(pageData.projects || []);
    }
  } catch (error) {
    showPageMessage(error.message);
  }
}

startPage();
