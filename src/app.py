"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User, Favorite, Planet, Character
#from models import Person

app = Flask(__name__)
app.url_map.strict_slashes = False

db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace("postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

# Handle/serialize errors like a JSON object
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# generate sitemap with all your endpoints
@app.route('/')
def sitemap():
    return generate_sitemap(app)

@app.route('/user', methods=['GET'])
def handle_hello():

    response_body = {
        "msg": "Hello, this is your GET /user response "
    }

    return jsonify(response_body), 200

@app.route('/people', methods=['GET'])
@app.route('/people/<int:character_id>', methods=['GET'])
def get_characters(character_id=None):
    if character_id is not None:
        character = Character.query.get(character_id)
        if character is None:
            return jsonify({"msg": "Character not found"}), 404
        return jsonify(character.serialize()), 200
    characters = Character.query.all()
    characters = list(map(lambda character: character.serialize(), characters))
    return jsonify(characters), 200


@app.route('/planets', methods=['GET'])
@app.route('/planets/<int:planet_id>', methods=['GET'])
def get_planets(planet_id=None):
    if planet_id is not None:
        planet = Planet.query.get(planet_id)
        if planet is None:
            return jsonify({"msg": "Planet not found"}), 404
        return jsonify(planet.serialize()), 200
    planets = Planet.query.all()
    planets = list(map(lambda planet: planet.serialize(), planets))
    return jsonify(planets), 200

@app.route('/favorite/planet/<int:planet_id>', methods=['POST'])
def add_favorite_planet(planet_id=None):
    body = request.get_json()
    if 'user_id' not in body:
        return jsonify({"msg": "Missing user_id field"}), 400
    user_id = body['user_id']
    user = User.query.get(user_id)
    if user is None:
        return jsonify({"msg": "User not found"}), 404
    if planet_id is not None:
        planet = Planet.query.get(planet_id)
        if planet is None:
            return jsonify({"msg": "Planet not found"}), 404
    else:
        if 'planet_id' not in body:
            return jsonify({"msg": "Missing planet_id field"}), 400
        planet_id = body['planet_id']
        planet = Planet.query.get(planet_id)
        if planet is None:
            return jsonify({"msg": "Planet not found"}), 404
    new_favorite = Favorite(user=user, planet=planet)
    db.session.add(new_favorite)
    db.session.commit()
    return jsonify(new_favorite.serialize()), 201


@app.route('/favorite/people/<int:people_id>', methods=['POST'])
def add_favorite_people(people_id=None):
    body = request.get_json()
    if 'user_id' not in body or 'character_id' not in body:
        return jsonify({"msg": "Missing required fields"}), 400
    user = User.query.get(body['user_id'])
    character = Character.query.get(body['character_id'])
    if user is None:
        return jsonify({"msg": "User not found"}), 404
    if character is None:
        return jsonify({"msg": "Character not found"}), 404
    new_favorite = Favorite(user=user, character=character)
    db.session.add(new_favorite)
    db.session.commit()
    return jsonify(new_favorite.serialize()), 201


@app.route('/user/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    user = User.query.get(user_id)
    if user is None:
        return jsonify({"msg": "User not found"}), 404
    db.session.delete(user)
    db.session.commit()
    return jsonify({"msg": "User deleted"}), 200

@app.route('/planet/<int:id>', methods=['DELETE'])
def delete_planet(id):
    planet = Planet.query.get(id)
    if planet is None:
        return jsonify({'error': 'Planet not found'}), 404
    db.session.delete(planet)
    db.session.commit()
    return jsonify({'message': 'Planet deleted successfully'}), 200

@app.route('/people/<int:id>', methods=['DELETE'])
def delete_character(id):
    character = Character.query.get(id)
    if character is None:
        return jsonify({'error': 'Character not found'}), 404
    db.session.delete(character)
    db.session.commit()
    return jsonify({'message': 'Character deleted successfully'}), 200

@app.route('/favorite/people/<int:character_id>', methods=['DELETE'])
def delete_favorite_character(character_id):
    character = Character.query.get(character_id)
    if character:
        db.session.delete(character)
        db.session.commit()
        return jsonify({"success": True}), 200
    else:
        return jsonify({"error": "Character not found"}), 404


@app.route('/favorite/planet/<int:planet_id>', methods=['DELETE'])
def ddelete_favorite_(planet_id):
    planet = Planet.query.get(planet_id)
    if planet is None:
        return jsonify({"msg": "Planet not found"}), 404
    db.session.delete(planet)
    db.session.commit()
    return jsonify({"msg": "Planet deleted"}), 200

# this only runs if `$ python src/app.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
