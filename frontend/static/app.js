const loginForm = document.getElementById('login-form');
const userInfo = document.getElementById('user-info');
const userName = document.getElementById('user-name');
const logoutButton = document.getElementById('logout-button');

async function apiFetch(path, options = {}) {
  const response = await fetch(path, {
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
    },
    ...options,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.error || 'Errore durante la richiesta');
  }

  return response.json();
}

async function loadUser() {
  const data = await apiFetch('/api/me');
  if (data.user) {
    userInfo.style.display = 'flex';
    userName.textContent = `${data.user.fullname || data.user.username}`;
    if (loginForm) {
      loginForm.style.display = 'none';
    }
  } else {
    userInfo.style.display = 'none';
    if (loginForm) {
      loginForm.style.display = 'flex';
    }
  }
}

async function handleLogin(event) {
  event.preventDefault();
  const formData = new FormData(loginForm);
  const payload = {
    username: formData.get('username'),
    password: formData.get('password'),
  };

  await apiFetch('/api/login', {
    method: 'POST',
    body: JSON.stringify(payload),
  });

  loginForm.reset();
  await loadUser();
  refreshPageData();
}

async function handleLogout() {
  await apiFetch('/api/logout', { method: 'POST' });
  await loadUser();
  refreshPageData();
}

function refreshPageData() {
  const path = window.location.pathname;
  if (path.endsWith('/recipe.html')) {
    loadRecipeDetail();
  } else if (path.endsWith('/cart.html')) {
    loadCart();
  } else {
    loadRecipes();
  }
}

async function loadRecipes() {
  const genreFilter = document.getElementById('genre-filter');
  const selectedGenre = genreFilter ? genreFilter.value : '';
  const query = selectedGenre ? `?genre=${encodeURIComponent(selectedGenre)}` : '';
  const recipes = await apiFetch(`/api/recipes${query}`);

  const container = document.getElementById('recipes');
  if (!container) return;
  container.innerHTML = '';

  const genres = new Set(recipes.map((recipe) => recipe.genre).filter(Boolean));
  if (genreFilter) {
    const current = genreFilter.value;
    genreFilter.innerHTML = '<option value="">Tutti</option>';
    genres.forEach((genre) => {
      const option = document.createElement('option');
      option.value = genre;
      option.textContent = genre;
      genreFilter.appendChild(option);
    });
    genreFilter.value = current;
  }

  recipes.forEach((recipe) => {
    const card = document.createElement('article');
    card.className = 'recipe-card';
    card.innerHTML = `
      <img src="${recipe.image_url || 'https://placehold.co/400x250'}" alt="${recipe.name}">
      <div class="recipe-card-body">
        <h3>${recipe.name}</h3>
        <p class="muted">${recipe.genre || 'Genere non specificato'}</p>
        <p class="price">€ ${recipe.cost_per_person.toFixed(2)} / persona</p>
        <a class="primary" href="/recipe.html?id=${recipe.id}">Dettaglio</a>
      </div>
    `;
    container.appendChild(card);
  });
}

async function loadRecipeDetail() {
  const detailContainer = document.getElementById('recipe-detail');
  if (!detailContainer) return;

  const params = new URLSearchParams(window.location.search);
  const id = params.get('id');
  if (!id) {
    detailContainer.innerHTML = '<p>ID ricetta mancante.</p>';
    return;
  }

  const recipe = await apiFetch(`/api/recipes/${id}`);
  const me = await apiFetch('/api/me');

  const ingredientList = recipe.ingredients
    .map((item) => `<li>${item.name} - ${item.quantity} ${item.unit}</li>`)
    .join('');

  detailContainer.innerHTML = `
    <div class="recipe-detail-card">
      <img src="${recipe.image_url || 'https://placehold.co/600x350'}" alt="${recipe.name}">
      <div class="recipe-detail-content">
        <h2>${recipe.name}</h2>
        <p>${recipe.description || 'Nessuna descrizione disponibile.'}</p>
        <p class="muted">Genere: ${recipe.genre || 'N/D'}</p>
        <p class="price">€ ${recipe.cost_per_person.toFixed(2)} / persona</p>
        <h3>Ingredienti</h3>
        <ul>${ingredientList}</ul>
        <div class="add-to-cart">
          <label>Numero persone</label>
          <input type="number" min="1" value="${recipe.servings_default || 1}" id="people-input" />
          <button id="add-to-cart" class="primary">Aggiungi al carrello</button>
          <p id="cart-message" class="muted"></p>
        </div>
      </div>
    </div>
  `;

  const addButton = document.getElementById('add-to-cart');
  const message = document.getElementById('cart-message');

  if (!me.user) {
    addButton.disabled = true;
    message.textContent = 'Effettua il login per aggiungere al carrello.';
  } else {
    addButton.addEventListener('click', async () => {
      const people = Number(document.getElementById('people-input').value || 1);
      try {
        await apiFetch('/api/cart', {
          method: 'POST',
          body: JSON.stringify({ recipe_id: Number(id), people }),
        });
        message.textContent = 'Aggiunto al carrello!';
      } catch (error) {
        message.textContent = error.message;
      }
    });
  }
}

async function loadCart() {
  const cartContainer = document.getElementById('cart-items');
  if (!cartContainer) return;

  let data;
  try {
    data = await apiFetch('/api/cart');
  } catch (error) {
    cartContainer.innerHTML = `<p>${error.message}</p>`;
    return;
  }

  cartContainer.innerHTML = '';

  data.items.forEach((item) => {
    const row = document.createElement('div');
    row.className = 'cart-item';
    row.innerHTML = `
      <img src="${item.image_url || 'https://placehold.co/120x80'}" alt="${item.recipe_name}">
      <div>
        <h4>${item.recipe_name}</h4>
        <p class="muted">Persone: ${item.people}</p>
      </div>
      <div class="cart-actions">
        <span class="price">€ ${item.item_total.toFixed(2)}</span>
        <button data-id="${item.id}" class="secondary">Rimuovi</button>
      </div>
    `;
    row.querySelector('button').addEventListener('click', async () => {
      await apiFetch(`/api/cart/${item.id}`, { method: 'DELETE' });
      await loadCart();
    });
    cartContainer.appendChild(row);
  });

  document.getElementById('cart-total').textContent = `€ ${data.total.toFixed(2)}`;
}

async function handleCheckout() {
  try {
    const data = await apiFetch('/api/checkout', { method: 'POST' });
    alert(`Ordine #${data.order_id} completato! Totale: € ${data.total.toFixed(2)}`);
    await loadCart();
  } catch (error) {
    alert(error.message);
  }
}

if (loginForm) {
  loginForm.addEventListener('submit', handleLogin);
}

if (logoutButton) {
  logoutButton.addEventListener('click', handleLogout);
}

const genreFilter = document.getElementById('genre-filter');
if (genreFilter) {
  genreFilter.addEventListener('change', loadRecipes);
}

const checkoutButton = document.getElementById('checkout-button');
if (checkoutButton) {
  checkoutButton.addEventListener('click', handleCheckout);
}

loadUser().then(refreshPageData).catch((error) => {
  console.error(error);
});
