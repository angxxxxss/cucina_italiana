"""Helper per la connessione al DB e operazioni CRUD.

Nota: NON creare tabelle o fare migration: il DB esiste già.
Aggiorna i nomi delle tabelle/colonne se il tuo schema differisce.
"""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
import os
from typing import Any, Dict, List, Optional

import bcrypt
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

load_dotenv()

_ENGINE: Optional[Engine] = None
_Session = None


def _load_config_module():
    try:
        import config  # type: ignore

        return config
    except ModuleNotFoundError:
        return None


def get_db_config() -> Dict[str, Any]:
    config_module = _load_config_module()

    def get_value(env_key: str, fallback_attr: str, default: Any = None) -> Any:
        value = os.getenv(env_key)
        if value is not None and value != "":
            return value
        if config_module and hasattr(config_module, fallback_attr):
            return getattr(config_module, fallback_attr)
        return default

    return {
        "host": get_value("DB_HOST", "DB_HOST", "localhost"),
        "port": int(get_value("DB_PORT", "DB_PORT", 3306)),
        "name": get_value("DB_NAME", "DB_NAME", ""),
        "user": get_value("DB_USER", "DB_USER", ""),
        "password": get_value("DB_PASSWORD", "DB_PASSWORD", ""),
        "secret_key": get_value("SECRET_KEY", "SECRET_KEY", "dev-secret"),
    }


def get_engine() -> Engine:
    global _ENGINE, _Session
    if _ENGINE is None:
        cfg = get_db_config()
        db_url = (
            f"mysql+pymysql://{cfg['user']}:{cfg['password']}@"
            f"{cfg['host']}:{cfg['port']}/{cfg['name']}"
        )
        _ENGINE = create_engine(db_url, pool_pre_ping=True)
        _Session = sessionmaker(bind=_ENGINE)
    return _ENGINE


def fetch_all(query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text(query), params or {})
        return [dict(row) for row in result.mappings().all()]


def fetch_one(query: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text(query), params or {})
        row = result.mappings().first()
        return dict(row) if row else None


def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    return fetch_one(
        """
        SELECT id, username, password, fullname
        FROM users
        WHERE username = :username
        """,
        {"username": username},
    )


def verify_password(plain_password: str, stored_password: str) -> bool:
    """Verifica password.

    TODO: in produzione usa hashing (bcrypt) e salva solo hash.
    """
    if stored_password.startswith("$2"):
        return bcrypt.checkpw(plain_password.encode(), stored_password.encode())
    return plain_password == stored_password


def list_recipes(genre: Optional[str] = None) -> List[Dict[str, Any]]:
    query = """
        SELECT id, name, genre, image_url, servings_default
        FROM recipes
    """
    params: Dict[str, Any] = {}
    if genre:
        query += " WHERE genre = :genre"
        params["genre"] = genre
    return fetch_all(query, params)


def get_recipe(recipe_id: int) -> Optional[Dict[str, Any]]:
    return fetch_one(
        """
        SELECT id, name, description, genre, image_url, servings_default
        FROM recipes
        WHERE id = :recipe_id
        """,
        {"recipe_id": recipe_id},
    )


def get_recipe_ingredients(recipe_id: int) -> List[Dict[str, Any]]:
    return fetch_all(
        """
        SELECT i.name, ri.quantity, ri.unit
        FROM recipe_ingredients ri
        JOIN ingredients i ON i.id = ri.ingredient_id
        WHERE ri.recipe_id = :recipe_id
        """,
        {"recipe_id": recipe_id},
    )


def get_recipe_wines(recipe_id: int) -> List[Dict[str, Any]]:
    """Recupera vini consigliati, se la tabella esiste."""
    try:
        return fetch_all(
            """
            SELECT w.id, w.name, w.price
            FROM recipe_wines rw
            JOIN wines w ON w.id = rw.wine_id
            WHERE rw.recipe_id = :recipe_id
            """,
            {"recipe_id": recipe_id},
        )
    except SQLAlchemyError:
        return []


def calculate_recipe_cost(recipe_id: int, people: int) -> Decimal:
    """Calcola il costo totale per un numero di persone.

    Formula:
    - costo_parziale = (quantity / servings_default) * people * price_per_unit
    - costo_ricetta_per_people = somma dei costi parziali
    """
    recipe = fetch_one(
        """
        SELECT servings_default
        FROM recipes
        WHERE id = :recipe_id
        """,
        {"recipe_id": recipe_id},
    )
    if not recipe:
        return Decimal("0.00")

    servings_default = Decimal(str(recipe["servings_default"]))
    if servings_default == 0:
        return Decimal("0.00")

    rows = fetch_all(
        """
        SELECT ri.quantity, i.price_per_unit
        FROM recipe_ingredients ri
        JOIN ingredients i ON i.id = ri.ingredient_id
        WHERE ri.recipe_id = :recipe_id
        """,
        {"recipe_id": recipe_id},
    )

    total = Decimal("0")
    for row in rows:
        quantity = Decimal(str(row["quantity"]))
        price_per_unit = Decimal(str(row["price_per_unit"]))
        partial = (quantity / servings_default) * Decimal(people) * price_per_unit
        total += partial

    return total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def add_cart_item(user_id: int, recipe_id: int, people: int, wine_id: Optional[int]) -> None:
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO cart_items (user_id, recipe_id, people, wine_id)
                VALUES (:user_id, :recipe_id, :people, :wine_id)
                """
            ),
            {
                "user_id": user_id,
                "recipe_id": recipe_id,
                "people": people,
                "wine_id": wine_id,
            },
        )


def list_cart_items(user_id: int) -> List[Dict[str, Any]]:
    return fetch_all(
        """
        SELECT ci.id, ci.recipe_id, ci.people, ci.wine_id,
               r.name AS recipe_name, r.image_url
        FROM cart_items ci
        JOIN recipes r ON r.id = ci.recipe_id
        WHERE ci.user_id = :user_id
        """,
        {"user_id": user_id},
    )


def remove_cart_item(user_id: int, item_id: int) -> None:
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                DELETE FROM cart_items
                WHERE id = :item_id AND user_id = :user_id
                """
            ),
            {"item_id": item_id, "user_id": user_id},
        )


def clear_cart(user_id: int) -> None:
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(
            text("DELETE FROM cart_items WHERE user_id = :user_id"),
            {"user_id": user_id},
        )


def create_order(user_id: int, items: List[Dict[str, Any]], total: Decimal) -> int:
    """Crea ordine e righe d'ordine.

    TODO: usare transazioni robuste e gestione errori.
    """
    engine = get_engine()
    with engine.begin() as conn:
        result = conn.execute(
            text(
                """
                INSERT INTO orders (user_id, total)
                VALUES (:user_id, :total)
                """
            ),
            {"user_id": user_id, "total": float(total)},
        )
        order_id = result.lastrowid

        for item in items:
            conn.execute(
                text(
                    """
                    INSERT INTO order_items (order_id, recipe_id, people, wine_id, item_total)
                    VALUES (:order_id, :recipe_id, :people, :wine_id, :item_total)
                    """
                ),
                {
                    "order_id": order_id,
                    "recipe_id": item["recipe_id"],
                    "people": item["people"],
                    "wine_id": item.get("wine_id"),
                    "item_total": float(item["item_total"]),
                },
            )

    return int(order_id)
