"""Applicazione Flask per La Cucina Italiana.

Espone API REST e serve le pagine frontend.
"""

from __future__ import annotations

from decimal import Decimal
import os
from typing import Any, Dict, Optional

from dotenv import load_dotenv # type: ignore
from flask import Flask, jsonify, request, session, send_from_directory # type: ignore

import models

load_dotenv()

app = Flask(__name__, static_folder="../frontend/static", static_url_path="/static")

config = models.get_db_config()
app.secret_key = config["secret_key"]


@app.route("/")
def index() -> Any:
    return send_from_directory("../frontend", "index.html")


@app.route("/recipe.html")
def recipe_page() -> Any:
    return send_from_directory("../frontend", "recipe.html")


@app.route("/cart.html")
def cart_page() -> Any:
    return send_from_directory("../frontend", "cart.html")


@app.route("/api/me")
def me() -> Any:
    user = session.get("user")
    if not user:
        return jsonify({"user": None})
    return jsonify({"user": user})


@app.route("/api/login", methods=["POST"])
def login() -> Any:
    payload = request.get_json(silent=True) or {}
    username = payload.get("username", "").strip()
    password = payload.get("password", "")

    if not username or not password:
        return jsonify({"error": "Credenziali mancanti."}), 400

    user = models.get_user_by_username(username)
    if not user:
        return jsonify({"error": "Utente non trovato."}), 401

    if not models.verify_password(password, user["password"]):
        return jsonify({"error": "Password errata."}), 401

    session["user"] = {
        "id": user["id"],
        "username": user["username"],
        "fullname": user.get("fullname"),
    }
    return jsonify({"user": session["user"]})


@app.route("/api/logout", methods=["POST"])
def logout() -> Any:
    session.pop("user", None)
    return jsonify({"status": "ok"})


def _require_login() -> Optional[Dict[str, Any]]:
    user = session.get("user")
    return user


@app.route("/api/recipes")
def recipes() -> Any:
    genre = request.args.get("genre")
    rows = models.list_recipes(genre)

    recipes_out = []
    for row in rows:
        cost = models.calculate_recipe_cost(row["id"], 1)
        recipes_out.append(
            {
                "id": row["id"],
                "name": row["name"],
                "genre": row["genre"],
                "image_url": row.get("image_url"),
                "cost_per_person": float(cost),
            }
        )

    return jsonify(recipes_out)


@app.route("/api/recipes/<int:recipe_id>")
def recipe_detail(recipe_id: int) -> Any:
    recipe = models.get_recipe(recipe_id)
    if not recipe:
        return jsonify({"error": "Ricetta non trovata."}), 404

    ingredients = models.get_recipe_ingredients(recipe_id)
    wines = models.get_recipe_wines(recipe_id)
    cost = models.calculate_recipe_cost(recipe_id, 1)

    return jsonify(
        {
            "id": recipe["id"],
            "name": recipe["name"],
            "description": recipe.get("description"),
            "genre": recipe.get("genre"),
            "image_url": recipe.get("image_url"),
            "servings_default": recipe.get("servings_default"),
            "ingredients": ingredients,
            "wines": wines,
            "cost_per_person": float(cost),
        }
    )


@app.route("/api/cart", methods=["GET"])
def cart_list() -> Any:
    user = _require_login()
    if not user:
        return jsonify({"error": "Autenticazione richiesta."}), 401

    items = models.list_cart_items(user["id"])
    output_items = []
    total = Decimal("0.00")

    for item in items:
        item_total = models.calculate_recipe_cost(item["recipe_id"], item["people"])
        total += item_total
        output_items.append(
            {
                "id": item["id"],
                "recipe_id": item["recipe_id"],
                "people": item["people"],
                "wine_id": item.get("wine_id"),
                "recipe_name": item.get("recipe_name"),
                "image_url": item.get("image_url"),
                "item_total": float(item_total),
            }
        )

    return jsonify({"items": output_items, "total": float(total)})


@app.route("/api/cart", methods=["POST"])
def cart_add() -> Any:
    user = _require_login()
    if not user:
        return jsonify({"error": "Autenticazione richiesta."}), 401

    payload = request.get_json(silent=True) or {}
    recipe_id = payload.get("recipe_id")
    people = payload.get("people")
    wine_id = payload.get("wine_id")

    # TODO: validare che recipe_id esista e people > 0.
    if not recipe_id or not people:
        return jsonify({"error": "Dati mancanti."}), 400

    models.add_cart_item(user["id"], int(recipe_id), int(people), wine_id)
    return jsonify({"status": "ok"})


@app.route("/api/cart/<int:item_id>", methods=["DELETE"])
def cart_remove(item_id: int) -> Any:
    user = _require_login()
    if not user:
        return jsonify({"error": "Autenticazione richiesta."}), 401

    models.remove_cart_item(user["id"], item_id)
    return jsonify({"status": "ok"})


@app.route("/api/checkout", methods=["POST"])
def checkout() -> Any:
    user = _require_login()
    if not user:
        return jsonify({"error": "Autenticazione richiesta."}), 401

    items = models.list_cart_items(user["id"])
    if not items:
        return jsonify({"error": "Carrello vuoto."}), 400

    items_with_total = []
    total = Decimal("0.00")
    for item in items:
        item_total = models.calculate_recipe_cost(item["recipe_id"], item["people"])
        total += item_total
        items_with_total.append(
            {
                "recipe_id": item["recipe_id"],
                "people": item["people"],
                "wine_id": item.get("wine_id"),
                "item_total": item_total,
            }
        )

    # TODO: usare transazioni (BEGIN/COMMIT) e gestione errori robusta.
    order_id = models.create_order(user["id"], items_with_total, total)
    models.clear_cart(user["id"])

    return jsonify({"status": "ok", "order_id": order_id, "total": float(total)})


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=True)
