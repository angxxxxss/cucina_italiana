const state = {
  user: null,
};

async function apiFetch(url, options = {}) {
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    ...options,
  });
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(data.error || "Errore API");
  }
  return response.json();
}

async function loadMe() {
  const data = await apiFetch("/api/me");
  state.user = data.user;
  renderLogin();
}

function renderLogin() {
  const loginForm = document.getElementById("login-form");
  const loginInfo = document.getElementById("login-info");
  if (!loginForm || !loginInfo) return;

  if (state.user) {
    loginForm.classList.add("hidden");
    loginInfo.innerHTML = `Ciao <strong>${state.user.fullname}</strong> <button id="logout-button">Logout</button>`;
    document.getElementById("logout-button").addEventListener("click", logout);
  } else {
    loginForm.classList.remove("hidden");
    loginInfo.textContent = "";
  }
}

async function login() {
  const username = document.getElementById("login-username").value;
  const password = document.getElementById("login-password").value;
  try {
    await apiFetch("/api/login", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    });
    await loadMe();
    refreshPageData();
  } catch (error) {
    alert(error.message);
  }
}

async function logout() {
  await apiFetch("/api/logout", { method: "POST" });
  state.user = null;
  renderLogin();
  refreshPageData();
}

function setupLoginHandlers() {
  const loginButton = document.getElementById("login-button");
  if (loginButton) {
    loginButton.addEventListener("click", login);
  }
}

async function loadRecipes() {
  const genreFilter = document.getElementById("genre-filter");
  const genre = genreFilter ? genreFilter.value : "";
  const url = genre ? `/api/recipes?genre=${encodeURIComponent(genre)}` : "/api/recipes";
  const recipes = await apiFetch(url);
  const container = document.getElementById("recipes");
  if (!container) return;
  container.innerHTML = recipes
    .map(
      (recipe) => `
      <article class="recipe-card">
        <img src="${recipe.image_url}" alt="${recipe.name}" />
        <div class="recipe-card-body">
          <h3>${recipe.name}</h3>
          <p>${recipe.genre}</p>
          <p class="price">€ ${recipe.cost_per_person.toFixed(2)} / persona</p>
          <a class="button" href="/recipe.html?id=${recipe.id}">Dettagli</a>
        </div>
      </article>
    `
    )
    .join("");
}

async function loadRecipeDetail() {
  const container = document.getElementById("recipe-detail");
  if (!container) return;
  const params = new URLSearchParams(window.location.search);
  const recipeId = params.get("id");
  if (!recipeId) {
    container.textContent = "Ricetta non trovata.";
    return;
  }
  const recipe = await apiFetch(`/api/recipes/${recipeId}`);
  container.innerHTML = `
    <div class="recipe-hero">
      <img src="${recipe.image_url}" alt="${recipe.name}" />
      <div>
        <h2>${recipe.name}</h2>
        <p>${recipe.description}</p>
        <p class="price">€ ${recipe.cost_per_person.toFixed(2)} / persona</p>
        <p>Porzioni base: ${recipe.servings_default}</p>
      </div>
    </div>
    <div class="recipe-content">
      <div>
        <h3>Ingredienti</h3>
        <ul>
          ${recipe.ingredients
            .map((item) => `<li>${item.name}: ${item.quantity} ${item.unit}</li>`)
            .join("")}
        </ul>
      </div>
      <div>
        <h3>Vini consigliati</h3>
        <ul>
          ${recipe.wines.map((wine) => `<li>${wine.name} (€ ${wine.price.toFixed(2)})</li>`).join("")}
        </ul>
      </div>
    </div>
    <div class="recipe-actions">
      <label for="people">Numero persone</label>
      <input type="number" id="people" min="1" value="${recipe.servings_default}" />
      <button id="add-to-cart" class="button">Aggiungi al carrello</button>
      <span class="hint">${state.user ? "" : "Effettua il login per aggiungere al carrello."}</span>
    </div>
  `;

  const addButton = document.getElementById("add-to-cart");
  if (addButton) {
    if (!state.user) {
      addButton.disabled = true;
      return;
    }
    addButton.addEventListener("click", async () => {
      const people = parseInt(document.getElementById("people").value, 10);
      try {
        await apiFetch("/api/cart", {
          method: "POST",
          body: JSON.stringify({ recipe_id: parseInt(recipeId, 10), people }),
        });
        window.location.href = "/cart.html";
      } catch (error) {
        alert(error.message);
      }
    });
  }
}

async function loadCart() {
  const container = document.getElementById("cart");
  if (!container) return;
  if (!state.user) {
    container.innerHTML = "<p>Effettua il login per vedere il carrello.</p>";
    return;
  }
  try {
    const data = await apiFetch("/api/cart");
    if (!data.items.length) {
      container.innerHTML = "<p>Il carrello è vuoto.</p>";
      return;
    }
    container.innerHTML = `
      <div class="cart-items">
        ${data.items
          .map(
            (item) => `
          <div class="cart-item">
            <img src="${item.image_url}" alt="${item.recipe_name}" />
            <div>
              <h3>${item.recipe_name}</h3>
              <p>Persone: ${item.people}</p>
              <p>Totale: € ${item.item_total.toFixed(2)}</p>
              <button class="link-button" data-remove="${item.id}">Rimuovi</button>
            </div>
          </div>
        `
          )
          .join("")}
      </div>
      <div class="cart-summary">
        <h3>Totale carrello: € ${data.total.toFixed(2)}</h3>
        <button id="checkout" class="button">Checkout</button>
      </div>
    `;

    container.querySelectorAll("button[data-remove]").forEach((button) => {
      button.addEventListener("click", async () => {
        const itemId = button.getAttribute("data-remove");
        await apiFetch(`/api/cart?item_id=${itemId}`, { method: "DELETE" });
        loadCart();
      });
    });

    const checkoutButton = document.getElementById("checkout");
    checkoutButton.addEventListener("click", async () => {
      try {
        const result = await apiFetch("/api/checkout", { method: "POST" });
        container.innerHTML = `<p>Ordine #${result.order_id} completato con successo!</p>`;
      } catch (error) {
        alert(error.message);
      }
    });
  } catch (error) {
    container.innerHTML = `<p>${error.message}</p>`;
  }
}

function refreshPageData() {
  if (document.getElementById("recipes")) {
    loadRecipes();
  }
  if (document.getElementById("recipe-detail")) {
    loadRecipeDetail();
  }
  if (document.getElementById("cart")) {
    loadCart();
  }
}

function setupFilters() {
  const genreFilter = document.getElementById("genre-filter");
  if (genreFilter) {
    genreFilter.addEventListener("change", loadRecipes);
  }
}

window.addEventListener("DOMContentLoaded", async () => {
  setupLoginHandlers();
  setupFilters();
  await loadMe();
  refreshPageData();
});
