const state = { csrfToken: null, user: null, users: [], vehicles: [] };
const $ = (selector) => document.querySelector(selector);

async function apiRequest(url, options = {}) {
  const headers = new Headers(options.headers || {});
  if (options.method === "POST") {
    headers.set("Content-Type", "application/json");
    if (state.csrfToken) headers.set("X-CSRF-Token", state.csrfToken);
  }
  const response = await fetch(url, { ...options, headers, credentials: "same-origin" });
  const result = await response.json();
  if (response.status === 401 || response.status === 403) {
    window.location.replace("/");
    throw new Error(result.error || "Admin access is required.");
  }
  if (!response.ok) throw new Error(result.error || `Request failed (${response.status}).`);
  return result;
}

function showNotice(message, isError = false) {
  const notice = $("#notice");
  notice.textContent = message;
  notice.classList.toggle("error", isError);
  notice.hidden = !message;
}

function setActiveSection(section) {
  document.querySelectorAll(".tab-button").forEach((button) => {
    const active = button.dataset.section === section;
    button.classList.toggle("active", active);
    if (active) button.setAttribute("aria-current", "page");
    else button.removeAttribute("aria-current");
  });
  document.querySelectorAll(".dashboard-section").forEach((panel) => {
    const active = panel.id === `section-${section}`;
    panel.hidden = !active;
    panel.classList.toggle("active", active);
  });
  history.replaceState(null, "", `#${section}`);
}

function makeCell(text) {
  const cell = document.createElement("td");
  cell.textContent = text || "—";
  return cell;
}

function makeStatus(status) {
  const badge = document.createElement("span");
  badge.className = `status-chip ${status}`;
  badge.textContent = status;
  return badge;
}

function accountAction(user) {
  if (user.role === "admin") return null;
  if (user.status === "pending") {
    return [
      { label: "Approve", status: "active", className: "button button-approve" },
      { label: "Reject", status: "rejected", className: "button button-reject" }
    ];
  }
  if (user.role === "operator" || user.role === "authority") {
    if (user.status === "active") return [{ label: "Suspend", status: "suspended", className: "button button-reject" }];
    if (user.status === "suspended" || user.status === "rejected") {
      return [{ label: "Reactivate", status: "active", className: "button button-approve" }];
    }
  }
  return null;
}

async function setAccountStatus(user, status) {
  const action = status === "active" ? "approve/reactivate" : status;
  if (!window.confirm(`${action[0].toUpperCase()}${action.slice(1)} ${user.name} (${user.email})?`)) return;
  try {
    await apiRequest(`/api/admin/users/${user.id}/status`, {
      method: "POST",
      body: JSON.stringify({ status })
    });
    showNotice(`${user.name}'s account is now ${status}.`);
    await loadDashboard();
  } catch (error) {
    showNotice(error.message, true);
  }
}

function createActionButtons(user, parent) {
  const actions = accountAction(user);
  if (!actions) {
    parent.textContent = "—";
    return;
  }
  actions.forEach((action) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = action.className;
    button.textContent = action.label;
    button.addEventListener("click", () => setAccountStatus(user, action.status));
    parent.append(button);
  });
}

function renderApprovalList() {
  const pending = state.users.filter((user) =>
    user.status === "pending" && ["operator", "authority"].includes(user.role)
  );
  $("#approval-count").textContent = String(pending.length);
  const list = $("#approval-list");
  list.replaceChildren();
  if (!pending.length) {
    const empty = document.createElement("p");
    empty.className = "empty-state";
    empty.textContent = "You’re all caught up. No stakeholder accounts are waiting for approval.";
    list.append(empty);
    return;
  }
  pending.forEach((user) => {
    const card = document.createElement("article");
    card.className = "approval-card";
    const main = document.createElement("div");
    main.className = "approval-main";
    const icon = document.createElement("span");
    icon.className = "approval-icon";
    icon.textContent = user.role === "operator" ? "▣" : "⌖";
    const details = document.createElement("div");
    details.className = "approval-details";
    const name = document.createElement("strong");
    name.textContent = user.name;
    const email = document.createElement("span");
    email.textContent = user.email;
    const meta = document.createElement("div");
    meta.className = "approval-meta";
    const role = document.createElement("span");
    role.className = "role-chip";
    role.textContent = user.role === "operator" ? "Bus operator" : "Transport authority";
    const organization = document.createElement("span");
    organization.className = "role-chip";
    organization.textContent = user.organization || "Organization not provided";
    meta.append(role, organization);
    details.append(name, email, meta);
    main.append(icon, details);
    const actions = document.createElement("div");
    actions.className = "approval-actions";
    createActionButtons(user, actions);
    card.append(main, actions);
    list.append(card);
  });
}

function renderAccounts() {
  const query = $("#account-search").value.trim().toLowerCase();
  const users = state.users.filter((user) =>
    `${user.name} ${user.email} ${user.role} ${user.organization || ""} ${user.status}`.toLowerCase().includes(query)
  );
  const tbody = $("#account-rows");
  tbody.replaceChildren();
  $("#account-empty").hidden = users.length > 0;
  users.forEach((user) => {
    const row = document.createElement("tr");
    row.append(makeCell(user.name));
    row.append(makeCell(user.role));
    row.append(makeCell(user.organization || "—"));
    const statusCell = document.createElement("td");
    statusCell.append(makeStatus(user.status));
    row.append(statusCell);
    row.append(makeCell(new Date(user.createdAt).toLocaleDateString()));
    const actions = document.createElement("td");
    createActionButtons(user, actions);
    row.append(actions);
    tbody.append(row);
  });
}

function renderFleet() {
  const tbody = $("#fleet-rows");
  tbody.replaceChildren();
  $("#fleet-empty").hidden = state.vehicles.length > 0;
  state.vehicles.forEach((vehicle) => {
    const row = document.createElement("tr");
    row.append(makeCell(vehicle.vehicleId));
    row.append(makeCell(vehicle.routeId));
    row.append(makeCell(`${vehicle.organization || vehicle.operatorName} (${vehicle.operatorEmail})`));
    const status = document.createElement("td");
    status.append(makeStatus(vehicle.operatorStatus));
    row.append(status);
    row.append(makeCell(vehicle.driverName ? `${vehicle.driverName} (${vehicle.driverEmail})` : "Unassigned"));
    tbody.append(row);
  });
}

async function loadDashboard() {
  document.body.classList.add("loading");
  try {
    const [summaryResult, userResult, fleetResult] = await Promise.all([
      apiRequest("/api/admin/summary"),
      apiRequest("/api/admin/users"),
      apiRequest("/api/admin/fleet")
    ]);
    state.users = userResult.users;
    state.vehicles = fleetResult.vehicles;
    $("#metric-users").textContent = String(summaryResult.summary.users);
    $("#metric-pending").textContent = String(summaryResult.summary.pending);
    $("#metric-vehicles").textContent = String(summaryResult.summary.vehicles);
    $("#metric-live").textContent = String(summaryResult.summary.live);
    renderApprovalList();
    renderAccounts();
    renderFleet();
  } catch (error) {
    showNotice(error.message, true);
  } finally {
    document.body.classList.remove("loading");
  }
}

document.querySelectorAll(".tab-button").forEach((button) => {
  button.addEventListener("click", () => setActiveSection(button.dataset.section));
});
document.querySelectorAll("[data-refresh]").forEach((button) => {
  button.addEventListener("click", loadDashboard);
});
$("#account-search").addEventListener("input", renderAccounts);
$("#admin-email-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const formData = new FormData(form);
  const submitButton = form.querySelector('button[type="submit"]');
  submitButton.disabled = true;
  try {
    const result = await apiRequest("/api/admin/account/email", {
      method: "POST",
      body: JSON.stringify({
        email: formData.get("email"),
        password: formData.get("password")
      })
    });
    $("#current-admin-email").textContent = result.user.email;
    state.user = result.user;
    state.users = state.users.map((user) => user.id === result.user.id ? result.user : user);
    renderAccounts();
    $("#new-admin-email").value = "";
    $("#admin-current-password").value = "";
    showNotice("Admin sign-in email updated. Use the new address next time you sign in.");
  } catch (error) {
    showNotice(error.message, true);
  } finally {
    submitButton.disabled = false;
  }
});
$("#sign-out").addEventListener("click", async () => {
  try {
    await apiRequest("/api/auth/logout", { method: "POST", body: "{}" });
    window.location.replace("/");
  } catch (error) {
    showNotice(error.message, true);
  }
});

async function initialize() {
  try {
    const session = await apiRequest("/api/auth/me");
    if (!session.user || session.user.role !== "admin") {
      window.location.replace("/");
      return;
    }
    state.csrfToken = session.csrfToken;
    state.user = session.user;
    $("#admin-name").textContent = session.user.name;
    $("#current-admin-email").textContent = session.user.email;
    const section = ["approvals", "accounts", "fleet", "account"].includes(location.hash.slice(1))
      ? location.hash.slice(1)
      : "approvals";
    setActiveSection(section);
    await loadDashboard();
  } catch (error) {
    showNotice(error.message, true);
  }
}

initialize();
