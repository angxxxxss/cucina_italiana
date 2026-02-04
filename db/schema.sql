-- Schema PostgreSQL per "La Cucina Italiana"
-- Nota: per demo le password sono in chiaro. In produzione usare hashing (bcrypt).

DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS cart_items;
DROP TABLE IF EXISTS carts;
DROP TABLE IF EXISTS recipe_wines;
DROP TABLE IF EXISTS recipe_ingredients;
DROP TABLE IF EXISTS wines;
DROP TABLE IF EXISTS ingredients;
DROP TABLE IF EXISTS recipes;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS sessions;

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    full_name TEXT NOT NULL
);

CREATE TABLE sessions (
    id TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE recipes (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    genre TEXT NOT NULL,
    image_url TEXT NOT NULL,
    servings_default INTEGER NOT NULL
);

CREATE TABLE ingredients (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    unit TEXT NOT NULL,
    price_per_unit NUMERIC(10,2) NOT NULL
);

CREATE TABLE recipe_ingredients (
    recipe_id INTEGER NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
    ingredient_id INTEGER NOT NULL REFERENCES ingredients(id) ON DELETE CASCADE,
    quantity NUMERIC(10,2) NOT NULL,
    PRIMARY KEY (recipe_id, ingredient_id)
);

CREATE TABLE wines (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    price NUMERIC(10,2) NOT NULL
);

CREATE TABLE recipe_wines (
    recipe_id INTEGER NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
    wine_id INTEGER NOT NULL REFERENCES wines(id) ON DELETE CASCADE,
    PRIMARY KEY (recipe_id, wine_id)
);

CREATE TABLE carts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE cart_items (
    id SERIAL PRIMARY KEY,
    cart_id INTEGER NOT NULL REFERENCES carts(id) ON DELETE CASCADE,
    recipe_id INTEGER NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
    people INTEGER NOT NULL,
    wine_id INTEGER REFERENCES wines(id)
);

CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    total NUMERIC(10,2) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    recipe_id INTEGER NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
    people INTEGER NOT NULL,
    wine_id INTEGER REFERENCES wines(id),
    item_total NUMERIC(10,2) NOT NULL
);

INSERT INTO users (username, password, full_name)
VALUES
    ('mario', 'password123', 'Mario Rossi'),
    ('giulia', 'ricette2024', 'Giulia Bianchi');

INSERT INTO recipes (name, description, genre, image_url, servings_default)
VALUES
    ('Spaghetti alla Carbonara', 'Pasta con guanciale, uova e pecorino.', 'Primi', 'https://images.unsplash.com/photo-1521389508051-d7ffb5dc8c1c', 2),
    ('Risotto ai Funghi', 'Risotto cremoso con funghi porcini.', 'Primi', 'https://images.unsplash.com/photo-1604908177225-2e1a1d6a2f38', 2),
    ('Tiramisù Classico', 'Dolce al cucchiaio con mascarpone e caffè.', 'Dolci', 'https://images.unsplash.com/photo-1505253758473-96b7015fcd40', 4);

INSERT INTO ingredients (name, unit, price_per_unit)
VALUES
    ('Spaghetti', 'g', 0.01),
    ('Guanciale', 'g', 0.03),
    ('Uova', 'pz', 0.40),
    ('Pecorino Romano', 'g', 0.05),
    ('Riso Carnaroli', 'g', 0.02),
    ('Funghi Porcini', 'g', 0.04),
    ('Burro', 'g', 0.02),
    ('Mascarpone', 'g', 0.03),
    ('Savoiardi', 'pz', 0.15),
    ('Caffè', 'ml', 0.01),
    ('Cacao', 'g', 0.08);

INSERT INTO recipe_ingredients (recipe_id, ingredient_id, quantity)
VALUES
    (1, 1, 200),
    (1, 2, 100),
    (1, 3, 2),
    (1, 4, 50),
    (2, 5, 180),
    (2, 6, 120),
    (2, 7, 40),
    (3, 8, 250),
    (3, 9, 18),
    (3, 10, 120),
    (3, 11, 15);

INSERT INTO wines (name, price)
VALUES
    ('Chianti Classico', 12.50),
    ('Vermentino', 10.00),
    ('Moscato d\'Asti', 14.00);

INSERT INTO recipe_wines (recipe_id, wine_id)
VALUES
    (1, 1),
    (2, 2),
    (3, 3);
