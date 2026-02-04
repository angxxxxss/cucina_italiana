# La Cucina Italiana - Web App Demo

Applicazione demo per consultare ricette e acquistare ingredienti tramite un DB MySQL/MariaDB **già esistente**.

> ⚠️ **Importante:** questa app **non** crea tabelle e **non** inserisce dati. Lo schema e i dati devono essere già presenti nel database.

## Requisiti

- Python 3.10+
- MySQL/MariaDB con schema e dati già importati

## Configurazione credenziali

Puoi usare **uno** dei due metodi:

### 1) File `backend/config.py`

Copia `backend/config_example.py` in `backend/config.py` e inserisci i tuoi valori:

```bash
cp backend/config_example.py backend/config.py
```

Esempio (modifica i valori):

```python
DB_HOST = "localhost"
DB_PORT = 3306
DB_NAME = "cucina_italiana"
DB_USER = "tuo_utente"
DB_PASSWORD = "tua_password"
SECRET_KEY = "sostituisci_con_valore_forte"
```

### 2) File `.env`

Copia `backend/.env.example` in `backend/.env` e aggiorna le variabili:

```bash
cp backend/.env.example backend/.env
```

Contenuto esempio:

```dotenv
DB_HOST=localhost
DB_PORT=3306
DB_NAME=cucina_italiana
DB_USER=tuo_utente
DB_PASSWORD=tua_password
SECRET_KEY=sostituisci_con_valore_forte
```

> **Nota sicurezza:** non committare mai `backend/config.py` o `.env` con credenziali reali.

## Installazione dipendenze

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

## Avvio

```bash
python3 backend/app.py
```

Apri il browser su: http://localhost:5000

## API principali

- `POST /api/login` `{username, password}`
- `POST /api/logout`
- `GET /api/me`
- `GET /api/recipes?genre=`
- `GET /api/recipes/<id>`
- `POST /api/cart` `{recipe_id, people, wine_id?}`
- `GET /api/cart`
- `DELETE /api/cart/<item_id>`
- `POST /api/checkout`

## Note sul database

Lo schema atteso (da adattare se necessario) include:

- `users` (id, username, password, fullname)
- `recipes` (id, name, description, genre, image_url, servings_default)
- `ingredients` (id, name, price_per_unit)
- `recipe_ingredients` (recipe_id, ingredient_id, quantity, unit)
- `cart_items` (id, user_id, recipe_id, people, wine_id)
- `orders` (id, user_id, total)
- `order_items` (id, order_id, recipe_id, people, wine_id, item_total)
- opzionale: `wines`, `recipe_wines`

Se il tuo schema usa nomi diversi, aggiorna le query in `backend/models.py`.

## TODO suggeriti (già commentati nel codice)

- Validazione server-side di input (es. people > 0, recipe_id esistente).
- Hashing password (bcrypt) in produzione.
- Transazioni robuste al checkout (BEGIN/COMMIT con gestione errori).

