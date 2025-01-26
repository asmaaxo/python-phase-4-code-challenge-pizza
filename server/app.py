#!/usr/bin/env python3
import os
from flask import Flask, request, make_response
from flask_restful import Api, Resource
from flask_migrate import Migrate
from models import db, Restaurant, RestaurantPizza, Pizza

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.environ.get("DB_URI", f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}")

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.json.compact = False

db.init_app(app)
migrate = Migrate(app, db)
api = Api(app)

@app.route("/")
def index():
    return "<h1>Code Challenge</h1>"

class Restaurants(Resource):
    def get(self):
        restaurants = Restaurant.query.all()
        return make_response([
            {"id": r.id, "name": r.name, "address": r.address}
            for r in restaurants
        ], 200)

class RestaurantByID(Resource):
    def get(self, id):
        restaurant = Restaurant.query.get(id)
        if not restaurant:
            return make_response({"error": "Restaurant not found"}, 404)
        data = {
            "id": restaurant.id,
            "name": restaurant.name,
            "address": restaurant.address,
            "restaurant_pizzas": [
                {
                    "id": rp.id,
                    "pizza_id": rp.pizza_id,
                    "restaurant_id": rp.restaurant_id,
                    "price": rp.price,
                    "pizza": {
                        "id": rp.pizza.id,
                        "name": rp.pizza.name,
                        "ingredients": rp.pizza.ingredients
                    }
                } for rp in restaurant.restaurant_pizzas
            ]
        }
        return make_response(data, 200)

    def delete(self, id):
        restaurant = Restaurant.query.get(id)
        if not restaurant:
            return make_response({"error": "Restaurant not found"}, 404)
        db.session.delete(restaurant)
        db.session.commit()
        return make_response('', 204)

class Pizzas(Resource):
    def get(self):
        pizzas = Pizza.query.all()
        return make_response([
            {"id": p.id, "name": p.name, "ingredients": p.ingredients}
            for p in pizzas
        ], 200)

class RestaurantPizzas(Resource):
    def post(self):
        data = request.get_json()
        price = data.get('price')
        restaurant_id = data.get('restaurant_id')
        pizza_id = data.get('pizza_id')
        if not all([price, restaurant_id, pizza_id]):
            return make_response({"errors": ["validation errors"]}, 400)
        restaurant = Restaurant.query.get(restaurant_id)
        pizza = Pizza.query.get(pizza_id)
        if not (restaurant and pizza):
            return make_response({"errors": ["validation errors"]}, 400)
        try:
            rp = RestaurantPizza(price=price, restaurant_id=restaurant_id, pizza_id=pizza_id)
            db.session.add(rp)
            db.session.commit()
        except ValueError:
            db.session.rollback()
            return make_response({"errors": ["validation errors"]}, 400)
        return make_response({
            "id": rp.id,
            "pizza_id": rp.pizza_id,
            "price": rp.price,
            "restaurant_id": rp.restaurant_id,
            "pizza": {
                "id": rp.pizza.id,
                "name": rp.pizza.name,
                "ingredients": rp.pizza.ingredients
            },
            "restaurant": {
                "id": rp.restaurant.id,
                "name": rp.restaurant.name,
                "address": rp.restaurant.address
            }
        }, 201)

api.add_resource(Restaurants, "/restaurants")
api.add_resource(RestaurantByID, "/restaurants/<int:id>")
api.add_resource(Pizzas, "/pizzas")
api.add_resource(RestaurantPizzas, "/restaurant_pizzas")

if __name__ == "__main__":
    app.run(port=5555, debug=True)
