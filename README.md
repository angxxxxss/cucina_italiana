# La Cucina Italiana - Demo Web App

Applicazione demo per consultare ricette e acquistare il set completo di ingredienti.

## Requisiti
- Python 3.10+
- PostgreSQL

## Setup database
1. Crea un database PostgreSQL:
   ```bash
   createdb cucina_italiana
   ```
2. Importa lo schema e i dati demo:
   ```bash
   psql cucina_italiana < db/schema.sql
   ```

## Backend
1. Installa le dipendenze:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r backend/requirements.txt
   ```
2. Configura la variabile di ambiente (opzionale):
   ```bash
   export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/cucina_italiana"
   ```
3. Avvia il server:
   ```bash
   python3 backend/app.py
   ```

## Frontend
Apri il browser su:
```
http://localhost:5000
```

## Utenti demo
- `mario` / `password123`
- `giulia` / `ricette2024`

## Note
- In produzione usare hashing per le password (bcrypt).
- Aggiungere validazione server-side per input e transazioni robuste in checkout.
