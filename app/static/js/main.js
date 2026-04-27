let selectedCustomerId = null;
let selectedCustomer = null;
let selectedProductId = null;
let selectedProduct = null;
let selectedProductLabel = "";
let lastTrendSummary = "";
let products = [];
let productPagination = { page: 1, pageSize: 4, totalCount: 0, totalPages: 0 };
let isLoadingProducts = false;
let currentSessionAuthenticated = false;
let preparedAdCopyPromptContextKey = "";
const productPageSize = 4;
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
  currentSessionAuthenticated = authenticated;
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
  updateProductPaginationControls();
  updateSessionStatusBadge(authenticated);
  const loginBtn = document.getElementById("loginBtn");
  if (loginBtn) {
    loginBtn.textContent = authenticated ? "change-user" : "Sign in with Entra ID";
  }
}

function setUserUpn(user) {
  const upnDisplay = document.getElementById("userUpnDisplay");
  if (!upnDisplay) return;
  if (!user) {
    upnDisplay.textContent = "";
    return;
  }
  const upn = user.user_principal_name || user.email || user.user_id;
  upnDisplay.textContent = upn ? `UPN: ${upn}` : "";
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

  const productMetric = products.length
    ? `${products.length} shown / ${productPagination.totalCount} total`
    : "Catalog pending";
  setMetric("productsMetric", productMetric, products.length ? "ok" : "muted");
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

function updateProductPaginationControls() {
  const prevButton = document.getElementById("prevProductsPageBtn");
  const nextButton = document.getElementById("nextProductsPageBtn");
  const pageInfo = document.getElementById("productsPageInfo");
  const totalPages = productPagination.totalPages || 0;
  const page = totalPages ? Math.min(productPagination.page, totalPages) : 0;

  if (pageInfo) {
    pageInfo.textContent = totalPages
      ? `Page ${page} of ${totalPages} · ${productPagination.totalCount} products · ${productPagination.pageSize} per page`
      : "No products";
  }
  if (prevButton) {
    prevButton.disabled = !currentSessionAuthenticated || isLoadingProducts || page <= 1;
  }
  if (nextButton) {
    nextButton.disabled =
      !currentSessionAuthenticated || isLoadingProducts || totalPages === 0 || page >= totalPages;
  }
}

function waitForRender() {
  return new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve)));
}

function setAdCopyPrompt(value) {
  const prompt = document.getElementById("adCopyPrompt");
  if (prompt) prompt.value = value || "";
}

function getAdCopyPrompt() {
  return document.getElementById("adCopyPrompt")?.value.trim() || "";
}

function buildAdCopyPromptContextKey(customerDescription) {
  return JSON.stringify({
    customerDescription,
    selectedCustomerId,
    selectedProductId,
    lastTrendSummary,
  });
}

function clearAdCopyDraft() {
  preparedAdCopyPromptContextKey = "";
  setAdCopyPrompt("");
  document.getElementById("adCopyText").textContent = "";
  setMetric("copyMetric", "Awaiting inputs", "muted");
}

function renderCustomerOrderRows(rows) {
  const tbody = document.getElementById("customerOrderRows");
  const empty = document.getElementById("customerOrderRowsEmpty");
  tbody.innerHTML = "";
  const lineItems = Array.isArray(rows) ? rows : [];
  empty.classList.toggle("d-none", lineItems.length > 0);

  lineItems.forEach((row) => {
    const tr = document.createElement("tr");
    [
      row.order_qty,
      row.unit_price,
      row.unit_price_discount,
      row.order_date,
      row.sub_total,
      row.product_name,
    ].forEach((value) => {
      const td = document.createElement("td");
      td.textContent = value ?? "";
      tr.appendChild(td);
    });
    tbody.appendChild(tr);
  });
}

function renderNewsItems(newsItems) {
  const list = document.getElementById("newsList");
  list.innerHTML = "";
  newsItems.forEach((n) => {
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
    selectedHint.textContent = "No products available. Click Load Product to continue.";
    setMetric("productsMetric", "No products", "warn");
    setMetric(
      "trendMetric",
      selectedProductId ? "Product selected" : "Select product",
      selectedProductId ? "info" : "muted",
    );
    updateProductPaginationControls();
    return;
  }
  setMetric("productsMetric", `${products.length} shown / ${productPagination.totalCount} total`, "ok");
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
      selectedProduct = p;
      selectedProductLabel = `${p.product_name} (ID: ${p.product_id})`;
      lastTrendSummary = "";
      Array.from(list.children).forEach((node) => node.classList.remove("active"));
      li.classList.add("active");
      selectedHint.textContent = `Selected product: ${selectedProductLabel}`;
      setMetric("trendMetric", "Product selected", "info");
      document.getElementById("trendSearchQuery").textContent = "";
      document.getElementById("newsList").innerHTML = "";
      document.getElementById("trendPrompt").textContent = "";
      document.getElementById("trendSummary").textContent = "";
      clearAdCopyDraft();
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
    const productOnPage = products.find((p) => p.product_id === selectedProductId);
    if (productOnPage) {
      selectedProduct = productOnPage;
      selectedProductLabel = `${productOnPage.product_name} (ID: ${productOnPage.product_id})`;
      selectedHint.textContent = `Selected product: ${selectedProductLabel}`;
      setMetric("trendMetric", "Product selected", "info");
      updateProductPaginationControls();
      return;
    }
    selectedHint.textContent = selectedProductLabel
      ? `Selected product: ${selectedProductLabel}`
      : "Selected product is on another page.";
    setMetric("trendMetric", "Product selected", "info");
    updateProductPaginationControls();
    return;
  }
  setMetric("trendMetric", "Select product", "muted");
  selectedHint.textContent = "Select 1 product above to enable Product Trend Search.";
  updateProductPaginationControls();
}

function clearFlowState(clearProducts = false) {
  selectedCustomerId = null;
  selectedCustomer = null;
  selectedProductId = null;
  selectedProduct = null;
  selectedProductLabel = "";
  lastTrendSummary = "";
  document.getElementById("customerDescription").value = "";
  document.getElementById("generatedSql").textContent = "";
  document.getElementById("customersList").innerHTML = "";
  document.getElementById("selectedCustomerHint").textContent = "";
  document.getElementById("selectedProductHint").textContent = "";
  renderCustomerOrderRows([]);
  document.getElementById("customerAnalysisPrompt").textContent = "";
  document.getElementById("customerAnalysis").textContent = "";
  document.getElementById("newsList").innerHTML = "";
  document.getElementById("trendSearchQuery").textContent = "";
  document.getElementById("trendPrompt").textContent = "";
  document.getElementById("trendSummary").textContent = "";
  setAdCopyPrompt("");
  document.getElementById("adCopyText").textContent = "";
  preparedAdCopyPromptContextKey = "";
  setMetric("customersMetric", "Awaiting query", "muted");
  setMetric("analysisMetric", "Awaiting selection", "muted");
  setMetric("trendMetric", "Select product", "muted");
  setMetric("copyMetric", "Awaiting inputs", "muted");
  if (clearProducts) {
    products = [];
    productPagination = { page: 1, pageSize: productPageSize, totalCount: 0, totalPages: 0 };
    document.getElementById("productsList").innerHTML = "";
    setMetric("productsMetric", "Catalog pending", "muted");
  }
  updateProductPaginationControls();
}

async function loadProducts(page = 1) {
  if (isLoadingProducts) return;
  isLoadingProducts = true;
  productPagination.page = Math.max(1, Number(page) || 1);
  updateProductPaginationControls();
  setMetric("productsMetric", "Loading...", "info");
  try {
    const query = new URLSearchParams({
      page: String(productPagination.page),
      page_size: String(productPageSize),
    });
    const data = await api(`/api/products?${query.toString()}`);
    products = Array.isArray(data.items) ? data.items : [];
    productPagination = {
      page: data.page || productPagination.page,
      pageSize: data.page_size || productPageSize,
      totalCount: data.total_count || 0,
      totalPages: data.total_pages || 0,
    };
    renderProducts();
  } catch (e) {
    setMetric("productsMetric", "Load failed", "warn");
    showError(`Product load failed: ${e.message}`);
  } finally {
    isLoadingProducts = false;
    updateProductPaginationControls();
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
  window.location.href = currentSessionAuthenticated ? "/auth/login?prompt=select_account" : "/auth/login";
};

document.getElementById("loadProductsBtn").onclick = withLoading("loadProductsBtn", async () => {
  clearError();
  await loadProducts(1);
});

document.getElementById("prevProductsPageBtn").onclick = async () => {
  clearError();
  await loadProducts(productPagination.page - 1);
};

document.getElementById("nextProductsPageBtn").onclick = async () => {
  clearError();
  await loadProducts(productPagination.page + 1);
};

document.getElementById("queryCustomersBtn").onclick = withLoading("queryCustomersBtn", async () => {
  clearError();
  setMetric("customersMetric", "Searching...", "info");
  document.getElementById("generatedSql").textContent = "";
  try {
    const customer_description = document.getElementById("customerDescription").value.trim();
    if (!customer_description) throw new Error("Please enter customer description first.");
    const data = await api("/api/customers/query", {
      method: "POST",
      body: JSON.stringify({ customer_description }),
    });
    selectedCustomerId = null;
    selectedCustomer = null;
    const list = document.getElementById("customersList");
    const selectedHint = document.getElementById("selectedCustomerHint");
    list.innerHTML = "";
    selectedHint.textContent = "";
    document.getElementById("generatedSql").textContent = data.generated_sql || "";
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
      const address = c.address_display || c.location || "N/A";
      appendSelectableItemContent(
        li,
        `CompanyName: ${companyName}`,
        `姓名：${customerName} | 地址：${address}`,
      );
      const selectCustomer = () => {
        selectedCustomerId = c.customer_id;
        selectedCustomer = c;
        Array.from(list.children).forEach((node) => node.classList.remove("active"));
        li.classList.add("active");
        selectedHint.textContent = `已选择客户：CompanyName: ${companyName} | 姓名：${customerName} | 地址：${address} (ID: ${c.customer_id})`;
        setMetric("customersMetric", "Customer selected", "ok");
        setMetric("analysisMetric", "Ready to run", "info");
        clearAdCopyDraft();
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
    if (!selectedProductId || !selectedProduct) throw new Error("Please select a product first.");
    renderCustomerOrderRows([]);
    document.getElementById("customerAnalysisPrompt").textContent = "";
    document.getElementById("customerAnalysis").textContent = "";
    setMetric("analysisMetric", "Loading orders", "info");
    const preview = await api(`/api/customers/${selectedCustomerId}/analysis/preview`, {
      method: "POST",
      body: JSON.stringify({
        selected_customer: selectedCustomer || { customer_id: selectedCustomerId },
        selected_product: selectedProduct,
      }),
    });
    renderCustomerOrderRows(preview.order_line_items);
    document.getElementById("customerAnalysisPrompt").textContent = preview.generated_prompt || "";
    await waitForRender();
    setMetric("analysisMetric", "Running analysis", "info");
    const data = await api(`/api/customers/${selectedCustomerId}/analysis/execute`, {
      method: "POST",
      body: JSON.stringify({ generated_prompt: preview.generated_prompt }),
    });
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
    if (!selectedProductId || !selectedProduct) throw new Error("Please select a product first.");
    lastTrendSummary = "";
    document.getElementById("trendSearchQuery").textContent = "";
    document.getElementById("newsList").innerHTML = "";
    document.getElementById("trendPrompt").textContent = "";
    document.getElementById("trendSummary").textContent = "";
    clearAdCopyDraft();
    setMetric("trendMetric", "Searching news", "info");
    const preview = await api("/api/trends/search/preview", {
      method: "POST",
      body: JSON.stringify({
        product_id: selectedProductId,
        selected_product: selectedProduct,
      }),
    });
    const queryBox = document.getElementById("trendSearchQuery");
    queryBox.textContent = preview.search_query || "";
    renderNewsItems(preview.news_items || []);
    document.getElementById("trendPrompt").textContent = preview.generated_prompt || "";
    await waitForRender();
    setMetric("trendMetric", "Summarizing trend", "info");
    const data = await api("/api/trends/search/execute", {
      method: "POST",
      body: JSON.stringify({
        search_query: preview.search_query,
        news_items: preview.news_items,
        generated_prompt: preview.generated_prompt || "",
        valid_ratio: preview.valid_ratio,
        fetch_errors: preview.fetch_errors || [],
      }),
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
    if (!selectedCustomer) throw new Error("Please select a customer first.");
    if (!selectedProductId || !selectedProduct) throw new Error("Please select a product first.");
    if (!lastTrendSummary) throw new Error("Please run Product Trend Search first.");
    const customer_description = document.getElementById("customerDescription").value.trim();
    const currentContextKey = buildAdCopyPromptContextKey(customer_description);
    const editedPrompt = getAdCopyPrompt();

    if (preparedAdCopyPromptContextKey === currentContextKey && editedPrompt) {
      document.getElementById("adCopyText").textContent = "";
      setMetric("copyMetric", "Generating draft", "info");
      const data = await api("/api/ad-copy/execute", {
        method: "POST",
        body: JSON.stringify({ generated_prompt: editedPrompt }),
      });
      document.getElementById("adCopyText").textContent = data.ad_copy_text;
      setMetric("copyMetric", "Draft ready", "ok");
      return;
    }

    setAdCopyPrompt("");
    document.getElementById("adCopyText").textContent = "";
    setMetric("copyMetric", "Preparing prompt", "info");
    const preview = await api("/api/ad-copy/preview", {
      method: "POST",
      body: JSON.stringify({
        customer_description,
        customer_id: selectedCustomerId,
        product_id: selectedProductId,
        trend_summary: lastTrendSummary,
        selected_customer: selectedCustomer,
        selected_product: selectedProduct,
      }),
    });
    setAdCopyPrompt(preview.generated_prompt || "");
    preparedAdCopyPromptContextKey = currentContextKey;
    await waitForRender();
    setMetric("copyMetric", "Prompt ready to edit", "info");
  } catch (e) {
    setMetric("copyMetric", "Generation blocked", "warn");
    showError(`Advertising script generation failed: ${e.message}`);
  }
});

document.getElementById("resetBtn").onclick = withLoading("resetBtn", async () => {
  clearError();
  try {
    await api("/api/reset", { method: "POST" });
    clearFlowState(true);
  } catch (e) {
    showError(`Reset failed: ${e.message}`);
  }
});

async function refreshSession() {
  const session = await api("/api/session").catch(() => ({ authenticated: false }));
  const el = document.getElementById("sessionInfo");
  if (!session.authenticated) {
    el.textContent = "Not signed in. Sign in to unlock the guided workflow.";
    setUserUpn(null);
    setBusinessEnabled(false);
    return;
  }
  setBusinessEnabled(true);
  setUserUpn(session.user);
  const upn = session.user.user_principal_name || session.user.email || session.user.user_id;
  el.textContent = `Signed in: ${session.user.display_name || upn}`;
}

initializeTooltips();
refreshSession();
