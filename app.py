from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Float
import os
from flask_marshmallow import Marshmallow
from flask_jwt_extended import JWTManager, create_access_token, jwt_required
from flask_mail import Mail, Message

# app config
app = Flask(__name__)
baseDir = os.path.abspath(os.path.dirname(__file__))  # get current dir
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(baseDir, 'planets.db')
app.config['JWT_SECRET_KEY'] = 'super-secret'  # change it
app.config['MAIL_SERVER'] = 'smtp.mailtrap.io'
app.config['MAIL_PORT'] = 2525
app.config['MAIL_USERNAME'] = '4d59d8ed30eaed'
app.config['MAIL_PASSWORD'] = '87c6e3c2eb9b32'
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False

db = SQLAlchemy(app)
ma = Marshmallow(app)
jwt = JWTManager(app)
mail = Mail(app)


@app.cli.command('db_create')
def db_create():
    db.create_all()
    print("Database Created!")


@app.cli.command('db_drop')
def db_drop():
    db.drop_all()
    print("Database Dropped!")


@app.cli.command('db_seed')
def seed_db():
    mercury = Planet(planet_name='Mercury',
                     planet_type='Class D',
                     home_star='Sol',
                     mass=3.258e3,
                     radius=1516,
                     distance=35.98e6)

    venus = Planet(planet_name='Venus',
                   planet_type='Class K',
                   home_star='Sol',
                   mass=4.867e24,
                   radius=3760,
                   distance=67.24e6)

    earth = Planet(planet_name='Earth',
                   planet_type='Class M',
                   home_star='Sol',
                   mass=5.98767e24,
                   radius=3935,
                   distance=92.24e6)

    db.session.add(mercury)
    db.session.add(venus)
    db.session.add(earth)

    test_user = User(first_name='Si',
                     last_name='Thu',
                     email='test@test.com',
                     password='123456')

    db.session.add(test_user)
    db.session.commit()


# routes
@app.route("/")
def hello_world():
    return 'Hello World!'


@app.route("/super_simple")
def super_simple():
    return jsonify(message='Hello from the planetary api')


@app.route('/parameters')
def parameters():
    name = request.args.get("name")
    age = int(request.args.get("age"))

    if age < 18:
        return jsonify(message="Sorry, " + name + " You are not old enough gg"), 401
    if age > 18:
        return jsonify(message="Welcome, " + name + " You are old enough")


@app.route('/url_variables/<string:name>/<int:age>')
def url_variables(name: str, age: int):
    if age < 18:
        return jsonify(message="Sorry, " + name + " You are not old enough gg"), 401
    if age > 18:
        return jsonify(message="Welcome, " + name + " You are old enough")


@app.route('/planets', methods=['GET'])
def planets():
    planet_list = Planet.query.all()
    result = planets_schema.dump(planet_list)
    return jsonify(result)


@app.route('/register', methods=['POST'])
def register():
    email = request.form["email"]
    check_email = User.query.filter_by(email=email).first()

    if check_email:
        return jsonify(message="User is already exit!"), 409
    else:
        first_name = request.form["first_name"]
        last_name = request.form["last_name"]
        password = request.form["password"]

        user = User(first_name=first_name, last_name=last_name, password=password, email=email)
        db.session.add(user)
        db.session.commit()

        return jsonify(message="User is created"), 201


@app.route('/login', methods=['POST'])
def login():
    if request.is_json:
        email = request.json["email"]
        password = request.json["password"]
    else:
        email = request.form["email"]
        password = request.form["password"]

    check_user = User.query.filter_by(email=email, password=password).first()

    if check_user:
        access_token = create_access_token(identity=email)
        return jsonify(message="login successfully", access_token=access_token)
    else:
        return jsonify(message="Invalid user"), 401


@app.route("/retrieve_password/<string:email>", methods=['GET'])
def retrieve_password(email: str):
    user = User.query.filter_by(email=email).first()
    if user:
        msg = Message("Your planetary api password is " + user.password,
                      sender="admin@planteryapi.com",
                      recipients=[email])
        mail.send(msg)
        return jsonify(message="Password send to " + email)
    else:
        return jsonify(message="That email doesn't exit"), 401


@app.route("/planet_detail/<int:planet_id>", methods=['GET'])
def planet_detail(planet_id: int):
    planet = Planet.query.filter_by(planet_id=planet_id).first()
    if planet:
        result = planet_schema.dump(planet)
        return jsonify(result)
    else:
        return jsonify(message="The planet doesn't exit"), 404


@app.route("/add_planet", methods=['POST'])
@jwt_required()
def add_planet():
    planet_name = request.form['planet_name'].strip()
    check_planet = Planet.query.filter_by(planet_name=planet_name).first()
    if check_planet:
        return jsonify(message='The planet is already exit'), 409
    else:
        planet_type = request.form['planet_type']
        home_star = request.form['home_star']
        mass = float(request.form['mass'])
        radius = float(request.form['radius'])
        distance = float(request.form['distance'])

        new_planet = Planet(planet_name=planet_name, planet_type=planet_type,
                            home_star=home_star, mass=mass, radius=radius,
                            distance=distance)

        db.session.add(new_planet)
        db.session.commit()

        return jsonify(message="The new planet has been added"), 201


@app.route("/update_planet", methods=['PUT'])
@jwt_required()
def update_planet():
    planet_id = int(request.form['planet_id'])
    planet = Planet.query.filter_by(planet_id=planet_id).first()
    if planet:
        planet.planet_type = request.form['planet_type'].strip()
        planet.planet_name = request.form['planet_name'].strip()
        planet.home_star = request.form['home_star'].strip()
        planet.distance = float(request.form['distance'].strip())
        planet.mass = float(request.form['mass'].strip())
        planet.radius = float(request.form['radius'].strip())

        db.session.commit()
        return jsonify(message="The update is success"), 202
    else:
        return jsonify(message="The planet doesn't exit"), 404


@app.route('/remove_planet/<int:planet_id>', methods=['DELETE'])
@jwt_required()
def remove_planet(planet_id: int):
    planet = Planet.query.filter_by(planet_id=planet_id).first()
    if planet:
        db.session.delete(planet)
        db.session.commit()

        return jsonify(message='Your planet is deleted'), 202
    else:
        return jsonify(message="Your planet doesn't exist"), 404


# database model
class User(db.Model):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String, unique=True)
    password = Column(String)


class Planet(db.Model):
    __tablename__ = "planets"
    planet_id = Column(Integer, primary_key=True)
    planet_name = Column(String)
    planet_type = Column(String)
    home_star = Column(String)
    mass = Column(Float)
    radius = Column(String)
    distance = Column(String)


class UserSchema(ma.Schema):
    class Meta:
        fields = ('id', 'first_name', 'last_name', 'email', 'password')


user_schema = UserSchema()
users_schema = UserSchema(many=True)


class PlanetSchema(ma.Schema):
    class Meta:
        fields = ('planet_id', 'planet_name', 'planet_type', 'home_star', 'mass', 'radius', 'distance')


planet_schema = PlanetSchema()
planets_schema = PlanetSchema(many=True)

if __name__ == '__main__':
    app.run()
