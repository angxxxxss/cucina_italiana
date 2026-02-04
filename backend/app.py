"""API Flask per La Cucina Italiana."""
import os
import secrets
from flask import Flask, jsonify, request, send_from_directory, make_response
import models

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")


def get_session_id():
    return request.cookies.get("session_id")


def get_current_user():
    session_id = get_session_id()
    if not session_id:
        return None
    return models.get_user_by_session(session_id)


@app.route("/")
def home():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.route("/recipe.html")
def recipe_page():
    return send_from_directory(FRONTEND_DIR, "recipe.html")


@app.route("/cart.html")
def cart_page():
    return send_from_directory(FRONTEND_DIR, "cart.html")


@app.route("/static/<path:filename>")
def static_files(filename):
    return send_from_directory(os.path.join(FRONTEND_DIR, "static"), filename)


@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    username = data.get("username")
    password = data.get("password")
    if not username or not password:
        return jsonify({"error": "Credenziali mancanti"}), 400

    user = models.get_user_by_credentials(username, password)
    if not user:
        return jsonify({"error": "Credenziali non valide"}), 401

    session_id = secrets.token_hex(16)
    models.create_session(session_id, user["id"])
    response = make_response(
        jsonify({"user": {"id": user["id"], "username": user["username"], "fullname": user["full_name"]}})
    )
    response.set_cookie("session_id", session_id, httponly=True, samesite="Lax")
    return response


@app.route("/api/logout", methods=["POST"])
def logout():
    session_id = get_session_id()
    if session_id:
        models.delete_session(session_id)
    response = make_response(jsonify({"ok": True}))
    response.set_cookie("session_id", "", expires=0)
    return response


@app.route("/api/me")
def me():
    user = get_current_user()
    if not user:
        return jsonify({"user": None})
    return jsonify({"user": {"id": user["id"], "username": user["username"], "fullname": user["full_name"]}})


@app.route("/api/recipes")
def recipes():
    genre = request.args.get("genre")
    recipes = models.list_recipes(genre)
    payload = []
    for recipe in recipes:
        cost_per_person = models.calculate_cost_per_person(recipe["id"])
        payload.append(
            {
                "id": recipe["id"],
                "name": recipe["name"],
                "genre": recipe["genre"],
                "image_url": recipe["image_url"],
                "cost_per_person": cost_per_person,
            }
        )
    return jsonify(payload)


@app.route("/api/recipes/<int:recipe_id>")
def recipe_detail(recipe_id):
    recipe = models.get_recipe(recipe_id)
    if not recipe:
        return jsonify({"error": "Ricetta non trovata"}), 404
    ingredients = models.list_recipe_ingredients(recipe_id)
    wines = models.list_recipe_wines(recipe_id)
    cost_per_person = models.calculate_cost_per_person(recipe_id)
    return jsonify(
        {
            "id": recipe["id"],
            "name": recipe["name"],
            "description": recipe["description"],
            "genre": recipe["genre"],
            "image_url": recipe["image_url"],
            "servings_default": recipe["servings_default"],
            "ingredients": [
                {"name": item["name"], "quantity": float(item["quantity"]), "unit": item["unit"]}
                for item in ingredients
            ],
            "wines": [
                {"id": wine["id"], "name": wine["name"], "price": float(wine["price"])}
                for wine in wines
            ],
            "cost_per_person": cost_per_person,
        }
    )


@app.route("/api/cart", methods=["GET", "POST", "DELETE"])
def cart():
    user = get_current_user()
    if not user:
        return jsonify({"error": "Autenticazione richiesta"}), 401

    if request.method == "POST":
        data = request.get_json() or {}
        recipe_id = data.get("recipe_id")
        people = data.get("people")
        wine_id = data.get("wine_id")
        # TODO: validare recipe_id esistente e people > 0.
        models.add_cart_item(user["id"], recipe_id, people, wine_id)
        return jsonify({"ok": True})

    if request.method == "DELETE":
        item_id = request.args.get("item_id")
        if item_id:
            models.remove_cart_item(user["id"], int(item_id))
        return jsonify({"ok": True})

    items = []
    total = 0.0
    for item in models.list_cart_items(user["id"]):
        item_total = models.calculate_recipe_cost(item["recipe_id"], item["people"])
        items.append(
            {
                "id": item["id"],
                "recipe_id": item["recipe_id"],
                "recipe_name": item["name"],
                "image_url": item["image_url"],
                "people": item["people"],
                "wine_id": item["wine_id"],
                "item_total": item_total,
            }
        )
        total += item_total
    return jsonify({"items": items, "total": total})


@app.route("/api/checkout", methods=["POST"])
def checkout():
    user = get_current_user()
    if not user:
        return jsonify({"error": "Autenticazione richiesta"}), 401

    cart_items = models.list_cart_items(user["id"])
    if not cart_items:
        return jsonify({"error": "Carrello vuoto"}), 400

    items_with_total = []
    for item in cart_items:
        item_total = models.calculate_recipe_cost(item["recipe_id"], item["people"])
        items_with_total.append(
            {
                "recipe_id": item["recipe_id"],
                "people": item["people"],
                "wine_id": item["wine_id"],
                "item_total": item_total,
            }
        )

    order_id = models.create_order(user["id"], items_with_total)
    models.clear_cart(user["id"])
    return jsonify({"ok": True, "order_id": order_id})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
