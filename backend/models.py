"""Helper DB e funzioni CRUD per La Cucina Italiana."""
import os
from decimal import Decimal
import psycopg2
from psycopg2.extras import RealDictCursor

DEFAULT_DB_URL = "postgresql://postgres:postgres@localhost:5432/cucina_italiana"


def get_db_url():
    return os.getenv("DATABASE_URL", DEFAULT_DB_URL)


def get_connection():
    return psycopg2.connect(get_db_url())


def fetch_one(query, params=None):
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params or ())
            return cur.fetchone()


def fetch_all(query, params=None):
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params or ())
            return cur.fetchall()


def execute(query, params=None, fetch=False):
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params or ())
            if fetch:
                return cur.fetchone()


def get_user_by_credentials(username, password):
    # TODO: usare hashing (bcrypt) e confronto sicuro in produzione.
    return fetch_one(
        "SELECT id, username, full_name FROM users WHERE username=%s AND password=%s",
        (username, password),
    )


def create_session(session_id, user_id):
    execute("INSERT INTO sessions (id, user_id) VALUES (%s, %s)", (session_id, user_id))


def delete_session(session_id):
    execute("DELETE FROM sessions WHERE id=%s", (session_id,))


def get_user_by_session(session_id):
    return fetch_one(
        """
        SELECT users.id, users.username, users.full_name
        FROM sessions
        JOIN users ON users.id = sessions.user_id
        WHERE sessions.id = %s
        """,
        (session_id,),
    )


def list_recipes(genre=None):
    if genre:
        return fetch_all(
            "SELECT id, name, genre, image_url, servings_default FROM recipes WHERE genre=%s ORDER BY id",
            (genre,),
        )
    return fetch_all("SELECT id, name, genre, image_url, servings_default FROM recipes ORDER BY id")


def get_recipe(recipe_id):
    return fetch_one(
        "SELECT id, name, description, genre, image_url, servings_default FROM recipes WHERE id=%s",
        (recipe_id,),
    )


def list_recipe_ingredients(recipe_id):
    return fetch_all(
        """
        SELECT ingredients.name, recipe_ingredients.quantity, ingredients.unit, ingredients.price_per_unit
        FROM recipe_ingredients
        JOIN ingredients ON ingredients.id = recipe_ingredients.ingredient_id
        WHERE recipe_ingredients.recipe_id = %s
        ORDER BY ingredients.name
        """,
        (recipe_id,),
    )


def list_recipe_wines(recipe_id):
    return fetch_all(
        """
        SELECT wines.id, wines.name, wines.price
        FROM recipe_wines
        JOIN wines ON wines.id = recipe_wines.wine_id
        WHERE recipe_wines.recipe_id = %s
        ORDER BY wines.name
        """,
        (recipe_id,),
    )


def calculate_recipe_cost(recipe_id, people):
    recipe = get_recipe(recipe_id)
    if not recipe:
        return None
    servings_default = recipe["servings_default"]
    ingredients = list_recipe_ingredients(recipe_id)
    total = Decimal("0")
    for item in ingredients:
        quantity = Decimal(str(item["quantity"]))
        price_per_unit = Decimal(str(item["price_per_unit"]))
        cost = (quantity / Decimal(servings_default)) * Decimal(people) * price_per_unit
        total += cost
    return float(total)


def calculate_cost_per_person(recipe_id):
    recipe = get_recipe(recipe_id)
    if not recipe:
        return None
    ingredients = list_recipe_ingredients(recipe_id)
    total = Decimal("0")
    for item in ingredients:
        quantity = Decimal(str(item["quantity"]))
        price_per_unit = Decimal(str(item["price_per_unit"]))
        total += quantity * price_per_unit
    if recipe["servings_default"] == 0:
        return 0.0
    return float(total / Decimal(recipe["servings_default"]))


def get_or_create_cart(user_id):
    cart = fetch_one("SELECT id FROM carts WHERE user_id=%s ORDER BY id DESC LIMIT 1", (user_id,))
    if cart:
        return cart["id"]
    new_cart = execute(
        "INSERT INTO carts (user_id) VALUES (%s) RETURNING id",
        (user_id,),
        fetch=True,
    )
    return new_cart["id"]


def add_cart_item(user_id, recipe_id, people, wine_id=None):
    cart_id = get_or_create_cart(user_id)
    execute(
        "INSERT INTO cart_items (cart_id, recipe_id, people, wine_id) VALUES (%s, %s, %s, %s)",
        (cart_id, recipe_id, people, wine_id),
    )


def list_cart_items(user_id):
    cart = fetch_one("SELECT id FROM carts WHERE user_id=%s ORDER BY id DESC LIMIT 1", (user_id,))
    if not cart:
        return []
    return fetch_all(
        """
        SELECT cart_items.id, cart_items.recipe_id, cart_items.people, cart_items.wine_id,
               recipes.name, recipes.image_url
        FROM cart_items
        JOIN recipes ON recipes.id = cart_items.recipe_id
        WHERE cart_items.cart_id = %s
        ORDER BY cart_items.id
        """,
        (cart["id"],),
    )


def remove_cart_item(user_id, item_id):
    cart = fetch_one("SELECT id FROM carts WHERE user_id=%s ORDER BY id DESC LIMIT 1", (user_id,))
    if not cart:
        return
    execute("DELETE FROM cart_items WHERE id=%s AND cart_id=%s", (item_id, cart["id"]))


def clear_cart(user_id):
    cart = fetch_one("SELECT id FROM carts WHERE user_id=%s ORDER BY id DESC LIMIT 1", (user_id,))
    if not cart:
        return
    execute("DELETE FROM cart_items WHERE cart_id=%s", (cart["id"],))


def create_order(user_id, items_with_total):
    with get_connection() as conn:
        # TODO: usare transazioni esplicite (BEGIN/COMMIT) e gestione errori robusta.
        with conn.cursor() as cur:
            total = sum(Decimal(str(item["item_total"])) for item in items_with_total)
            cur.execute(
                "INSERT INTO orders (user_id, total) VALUES (%s, %s) RETURNING id",
                (user_id, total),
            )
            order_id = cur.fetchone()[0]
            for item in items_with_total:
                cur.execute(
                    """
                    INSERT INTO order_items (order_id, recipe_id, people, wine_id, item_total)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        order_id,
                        item["recipe_id"],
                        item["people"],
                        item.get("wine_id"),
                        item["item_total"],
                    ),
                )
        conn.commit()
    return order_id
