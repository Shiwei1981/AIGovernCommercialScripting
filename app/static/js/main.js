let selectedCustomerId = null;
let selectedProductId = null;
let lastTrendSummary = "";
let products = [];
let isLoadingProducts = false;
const actionButtonIds = [
  "loadProductsBtn",
  "queryCustomersBtn",
  "analyzeCustomerBtn",
  "trendSearchBtn",
  "adCopyBtn",
  "resetBtn",
];

function showError(message) {
  console.error(message);
  const box = document.getElementById("errorBox");
  box.textContent = message;
  box.classList.remove("d-none");
}

function clearError() {
  const box = document.getElementById("errorBox");
  box.classList.add("d-none");
  box.textContent = "";
}

function setBusinessEnabled(authenticated) {
  const flow = document.getElementById("businessFlow");
  const preLoginHint = document.getElementById("preLoginHint");
  if (authenticated) {
    flow.classList.remove("d-none");
    preLoginHint.classList.add("d-none");
  } else {
    flow.classList.add("d-none");
    preLoginHint.classList.remove("d-none");
    clearFlowState(true);
  }
  actionButtonIds.forEach((id) => {
    const button = document.getElementById(id);
    button.disabled = !authenticated;
  });
  initializeWorkflowMetrics(authenticated);
  updateSessionStatusBadge(authenticated);
  const loginBtn = document.getElementById("loginBtn");
  if (loginBtn) {
    loginBtn.textContent = authenticated ? "Re-authenticate" : "Sign in with Entra ID";
  }
}

function updateSessionStatusBadge(authenticated) {
  const badge = document.getElementById("sessionStatusBadge");
  const text = document.getElementById("sessionStatusText");
  if (!badge || !text) return;
  badge.classList.remove("status-pill--ok", "status-pill--warn", "status-pill--muted");
  if (authenticated) {
    badge.classList.add("status-pill--ok");
    text.textContent = "Signed in";
  } else {
    badge.classList.add("status-pill--warn");
    text.textContent = "Not signed in";
  }
}

function setMetric(metricId, text, variant = "muted") {
  const el = document.getElementById(metricId);
  if (!el) return;
  el.textContent = text;
  el.classList.remove(
    "metric-pill--muted",
    "metric-pill--ok",
    "metric-pill--info",
    "metric-pill--warn",
  );
  el.classList.add("metric-pill", `metric-pill--${variant}`);
}

function initializeWorkflowMetrics(authenticated) {
  if (!authenticated) {
    setMetric("productsMetric", "Sign-in required", "warn");
    setMetric("customersMetric", "Sign-in required", "warn");
    setMetric("analysisMetric", "Sign-in required", "warn");
    setMetric("trendMetric", "Sign-in required", "warn");
    setMetric("copyMetric", "Sign-in required", "warn");
    return;
  }

  setMetric("productsMetric", products.length ? `${products.length} loaded` : "Catalog pending", products.length ? "ok" : "muted");
  setMetric("customersMetric", "Awaiting query", "muted");
  setMetric("analysisMetric", "Awaiting selection", "muted");
  setMetric("trendMetric", selectedProductId ? "Product selected" : "Select product", selectedProductId ? "info" : "muted");
  setMetric("copyMetric", "Awaiting inputs", "muted");
}

function initializeTooltips() {
  if (!window.bootstrap?.Tooltip) return;
  document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach((node) => {
    new window.bootstrap.Tooltip(node);
  });
}

function appendSelectableItemContent(item, title, meta) {
  const titleNode = document.createElement("div");
  titleNode.className = "selectable-item__title";
  titleNode.textContent = title;
  item.appendChild(titleNode);

  if (!meta) return;
  const metaNode = document.createElement("div");
  metaNode.className = "selectable-item__meta";
  metaNode.textContent = meta;
  item.appendChild(metaNode);
}

function withLoading(buttonId, handler) {
  return async (...args) => {
    const button = document.getElementById(buttonId);
    let originalLabel;
    if (button) {
      originalLabel = button.textContent.trim();
      const loadingLabel = button.dataset.loadingText?.trim();
      button.classList.add("is-loading");
      button.disabled = true;
      button.setAttribute("aria-busy", "true");
      if (loadingLabel) {
        button.textContent = loadingLabel;
      }
    }
    try {
      return await handler(...args);
    } finally {
      if (button) {
        button.classList.remove("is-loading");
        button.disabled = false;
        button.removeAttribute("aria-busy");
        if (originalLabel !== undefined) button.textContent = originalLabel;
      }
    }
  };
}

function renderProducts() {
  const list = document.getElementById("productsList");
  const selectedHint = document.getElementById("selectedProductHint");
  list.innerHTML = "";
  selectedHint.textContent = "";
  if (!Array.isArray(products) || products.length === 0) {
    selectedProductId = null;
    selectedHint.textContent = "No products available. Reload the catalog to continue.";
    setMetric("productsMetric", "No products", "warn");
    setMetric("trendMetric", "Select product", "muted");
    return;
  }
  setMetric("productsMetric", `${products.length} loaded`, "ok");
  if (!products.some((p) => p.product_id === selectedProductId)) {
    selectedProductId = null;
  }
  products.forEach((p) => {
    const li = document.createElement("li");
    li.className = "selectable-item";
    li.setAttribute("role", "button");
    li.tabIndex = 0;
    appendSelectableItemContent(
      li,
      p.product_name,
      `Category: ${p.category_name} | Product ID: ${p.product_id}`,
    );
    const selectProduct = () => {
      selectedProductId = p.product_id;
      Array.from(list.children).forEach((node) => node.classList.remove("active"));
      li.classList.add("active");
      selectedHint.textContent = `Selected product: ${p.product_name} (ID: ${p.product_id})`;
      setMetric("trendMetric", "Product selected", "info");
    };
    li.onclick = selectProduct;
    li.onkeydown = (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        selectProduct();
      }
    };
    if (p.product_id === selectedProductId) {
      li.classList.add("active");
    }
    list.appendChild(li);
  });
  if (selectedProductId) {
    const selectedProduct = products.find((p) => p.product_id === selectedProductId);
    if (selectedProduct) {
      selectedHint.textContent = `Selected product: ${selectedProduct.product_name} (ID: ${selectedProduct.product_id})`;
      setMetric("trendMetric", "Product selected", "info");
      return;
    }
  }
  setMetric("trendMetric", "Select product", "muted");
  selectedHint.textContent = "Select 1 product above to enable Product Trend Search.";
}

function clearFlowState(clearProducts = false) {
  selectedCustomerId = null;
  selectedProductId = null;
  lastTrendSummary = "";
  document.getElementById("customerDescription").value = "";
  document.getElementById("customersList").innerHTML = "";
  document.getElementById("selectedCustomerHint").textContent = "";
  document.getElementById("selectedProductHint").textContent = "";
  document.getElementById("customerAnalysis").textContent = "";
  document.getElementById("newsList").innerHTML = "";
  document.getElementById("trendSearchQuery").textContent = "";
  document.getElementById("trendSummary").textContent = "";
  document.getElementById("adCopyText").textContent = "";
  setMetric("customersMetric", "Awaiting query", "muted");
  setMetric("analysisMetric", "Awaiting selection", "muted");
  setMetric("trendMetric", "Select product", "muted");
  setMetric("copyMetric", "Awaiting inputs", "muted");
  if (clearProducts) {
    products = [];
    document.getElementById("productsList").innerHTML = "";
    setMetric("productsMetric", "Catalog pending", "muted");
  }
}

async function loadProducts(forceReload = false) {
  if (isLoadingProducts) return;
  if (!forceReload && products.length > 0) {
    renderProducts();
    return;
  }
  isLoadingProducts = true;
  setMetric("productsMetric", "Loading...", "info");
  try {
    products = await api("/api/products/bootstrap");
    renderProducts();
  } catch (e) {
    setMetric("productsMetric", "Load failed", "warn");
    showError(`Product bootstrap failed: ${e.message}`);
  } finally {
    isLoadingProducts = false;
  }
}

async function api(url, opts = {}) {
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    ...opts,
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({ error: "Unknown error" }));
    throw new Error(err.error || "Request failed");
  }
  return response.json();
}

document.getElementById("loginBtn").onclick = () => {
  window.location.href = "/auth/login";
};

document.getElementById("loadProductsBtn").onclick = withLoading("loadProductsBtn", async () => {
  clearError();
  await loadProducts(true);
});

document.getElementById("queryCustomersBtn").onclick = withLoading("queryCustomersBtn", async () => {
  clearError();
  setMetric("customersMetric", "Searching...", "info");
  try {
    const customer_description = document.getElementById("customerDescription").value.trim();
    if (!customer_description) throw new Error("Please enter customer description first.");
    const data = await api("/api/customers/query", {
      method: "POST",
      body: JSON.stringify({ customer_description }),
    });
    selectedCustomerId = null;
    const list = document.getElementById("customersList");
    const selectedHint = document.getElementById("selectedCustomerHint");
    list.innerHTML = "";
    selectedHint.textContent = "";
    if (!Array.isArray(data.results) || data.results.length === 0) {
      selectedHint.textContent = "No matched customers. Try refining the description.";
      setMetric("customersMetric", "0 matches", "warn");
      setMetric("analysisMetric", "Awaiting selection", "muted");
      return;
    }
    setMetric("customersMetric", `${data.results.length} matches`, "ok");
    setMetric("analysisMetric", "Awaiting selection", "muted");
    data.results.forEach((c) => {
      const li = document.createElement("li");
      li.className = "selectable-item";
      li.setAttribute("role", "button");
      li.tabIndex = 0;
      const companyName = c.company_name || "N/A";
      const customerName = c.customer_name || "N/A";
      const address = c.location || "N/A";
      appendSelectableItemContent(
        li,
        `CompanyName: ${companyName}`,
        `姓名：${customerName} | 地址：${address}`,
      );
      const selectCustomer = () => {
        selectedCustomerId = c.customer_id;
        Array.from(list.children).forEach((node) => node.classList.remove("active"));
        li.classList.add("active");
        selectedHint.textContent = `已选择客户：CompanyName: ${companyName} | 姓名：${customerName} | 地址：${address} (ID: ${c.customer_id})`;
        setMetric("customersMetric", "Customer selected", "ok");
        setMetric("analysisMetric", "Ready to run", "info");
      };
      li.onclick = selectCustomer;
      li.onkeydown = (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          selectCustomer();
        }
      };
      list.appendChild(li);
    });
    selectedHint.textContent = "Select 1 customer above to enable Customer Analysis.";
  } catch (e) {
    setMetric("customersMetric", "Query failed", "warn");
    showError(`Customer query failed: ${e.message}`);
  }
});

document.getElementById("analyzeCustomerBtn").onclick = withLoading("analyzeCustomerBtn", async () => {
  clearError();
  try {
    if (!selectedCustomerId) throw new Error("Please select a customer first.");
    setMetric("analysisMetric", "Running analysis", "info");
    const data = await api(`/api/customers/${selectedCustomerId}/analysis`, { method: "POST" });
    document.getElementById("customerAnalysis").textContent = data.analysis_text;
    setMetric("analysisMetric", "Analysis ready", "ok");
  } catch (e) {
    setMetric("analysisMetric", selectedCustomerId ? "Analysis failed" : "Select customer", selectedCustomerId ? "warn" : "muted");
    showError(`Customer analysis failed: ${e.message}`);
  }
});

document.getElementById("trendSearchBtn").onclick = withLoading("trendSearchBtn", async () => {
  clearError();
  try {
    if (!selectedProductId) throw new Error("Please select a product first.");
    lastTrendSummary = "";
    document.getElementById("trendSearchQuery").textContent = "";
    document.getElementById("newsList").innerHTML = "";
    document.getElementById("trendSummary").textContent = "";
    setMetric("trendMetric", "Searching news", "info");
    const data = await api("/api/trends/search", {
      method: "POST",
      body: JSON.stringify({ product_id: selectedProductId }),
    });
    const list = document.getElementById("newsList");
    const queryBox = document.getElementById("trendSearchQuery");
    list.innerHTML = "";
    queryBox.textContent = data.search_query || "";
    data.news_items.forEach((n) => {
      const li = document.createElement("li");
      const title = document.createElement("div");
      title.className = "news-item__title";
      const link = document.createElement("a");
      link.className = "news-item__title-link";
      link.textContent = n.title;
      link.href = n.publisher_url || n.rss_link;
      link.target = "_blank";
      link.rel = "noopener noreferrer";
      title.appendChild(link);
      const meta = document.createElement("div");
      meta.className = "news-item__meta";
      const metaParts = [n.source_name, n.published_at].filter(Boolean);
      meta.textContent = metaParts.length > 0 ? metaParts.join(" | ") : "Google News result";
      li.appendChild(title);
      li.appendChild(meta);
      if (n.summary_snippet) {
        const snippet = document.createElement("div");
        snippet.className = "news-item__snippet";
        snippet.textContent = n.summary_snippet;
        li.appendChild(snippet);
      }
      list.appendChild(li);
    });
    lastTrendSummary = data.summary.summary_text;
    document.getElementById("trendSummary").textContent = data.summary.summary_text || "";
    const trendVariant = data.news_items.length > 0 ? "ok" : "warn";
    setMetric(
      "trendMetric",
      `${data.news_items.length} result${data.news_items.length === 1 ? "" : "s"}`,
      trendVariant,
    );
  } catch (e) {
    setMetric("trendMetric", selectedProductId ? "Search failed" : "Select product", selectedProductId ? "warn" : "muted");
    showError(`Trend search failed: ${e.message}`);
  }
});

document.getElementById("adCopyBtn").onclick = withLoading("adCopyBtn", async () => {
  clearError();
  try {
    if (!selectedCustomerId) throw new Error("Please select a customer first.");
    if (!selectedProductId) throw new Error("Please select a product first.");
    if (!lastTrendSummary) throw new Error("Please run Product Trend Search first.");
    setMetric("copyMetric", "Generating draft", "info");
    const customer_description = document.getElementById("customerDescription").value.trim();
    const data = await api("/api/ad-copy/generate", {
      method: "POST",
      body: JSON.stringify({
        customer_description,
        customer_id: selectedCustomerId,
        product_id: selectedProductId,
        trend_summary: lastTrendSummary,
      }),
    });
    document.getElementById("adCopyText").textContent = data.ad_copy_text;
    setMetric("copyMetric", "Draft ready", "ok");
  } catch (e) {
    setMetric("copyMetric", "Generation blocked", "warn");
    showError(`Ad copy generation failed: ${e.message}`);
  }
});

document.getElementById("resetBtn").onclick = withLoading("resetBtn", async () => {
  clearError();
  try {
    await api("/api/reset", { method: "POST" });
    clearFlowState(true);
    await loadProducts(true);
  } catch (e) {
    showError(`Reset failed: ${e.message}`);
  }
});

async function refreshSession() {
  const session = await api("/api/session").catch(() => ({ authenticated: false }));
  const el = document.getElementById("sessionInfo");
  if (!session.authenticated) {
    el.textContent = "Not signed in. Sign in to unlock the guided workflow.";
    setBusinessEnabled(false);
    return;
  }
  setBusinessEnabled(true);
  el.textContent = `Signed in: ${session.user.display_name || session.user.user_id}`;
  await loadProducts(false);
}

initializeTooltips();
refreshSession();
