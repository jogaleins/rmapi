from flask_marshmallow import Marshmallow 
# flask imports
from flask import Flask, request, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
import uuid # for public id
from  werkzeug.security import generate_password_hash, check_password_hash
# imports for PyJWT authentication
import jwt
from datetime import datetime, timedelta
from functools import wraps
import os

#import pymysql

# Init app
app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
# Database
#app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'db.sqlite')
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://k3s:k3s_123@192.168.1.200/rm'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['SECRET_KEY'] = 'your secret key'

# Init db
db = SQLAlchemy(app)
# Init ma
ma = Marshmallow(app)

# Package Class/Model
class Users(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    public_id = db.Column(db.String(50), unique = True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(70), unique = True)
    password = db.Column(db.String(80))

class Package(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  package = db.Column(db.String(100), unique=True)
  system = db.Column(db.String(100))
  baseline = db.Column(db.String(100))
  state = db.Column(db.String(100))
  dimstream = db.Column(db.String(100))

  def __init__(self, package, system, baseline, state, dimstream):
    self.self = self
    self.package = package
    self.system = system
    self.baseline = baseline
    self.state = state
    self.dimstream = dimstream

# Package Schema
class PackageSchema(ma.Schema):
  class Meta:
    fields = ('id', 'package', 'system', 'baseline', 'state','dimstream')


# Init schema
package_schema = PackageSchema()
packages_schema = PackageSchema(many=True)

# decorator for verifying the JWT
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        # jwt is passed in the request header
        for i in request.headers:
            print(i)
        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']
        # return 401 if token is not passed
        if not token:
            return jsonify({'message' : 'Token is missing !!'}), 401
  
        try:
            # decoding the payload to fetch the stored details
            data = jwt.decode(token, app.config['SECRET_KEY'])
            current_user = Users.query\
                .filter_by(public_id = data['public_id'])\
                .first()
        except:
            return jsonify({
                'message' : 'Token is invalid !!'
            }), 401
        # returns the current logged in users contex to the routes
        return  f(current_user, *args, **kwargs)
  
    return decorated

#Routes
@app.route('/rmapi')
def hello():
  return 'api root'

# route for logging user in
@app.route('/rmapi/login', methods =['POST'])
def login():
    # creates dictionary of form data
    auth = request.json
  
    if not auth or not auth.get('email') or not auth.get('password'):
        # returns 401 if any email or / and password is missing
        return make_response(
            'Could not verify',
            401,
            {'WWW-Authenticate' : 'Basic realm ="Login required !!"'}
        )
  
    user = Users.query\
        .filter_by(email = auth.get('email'))\
        .first()
  
    if not user:
        # returns 401 if user does not exist
        return make_response(
            'Could not verify',
            401,
            {'WWW-Authenticate' : 'Basic realm ="User does not exist !!"'}
        )
  
    if check_password_hash(user.password, auth.get('password')):
        # generates the JWT Token
        token = jwt.encode({
            'public_id': user.public_id,
            'exp' : datetime.utcnow() + timedelta(minutes = 30)
        }, app.config['SECRET_KEY'])
  
        return make_response(jsonify({'token' : token.decode('UTF-8')}), 201)
    # returns 403 if password is wrong
    return make_response(
        'Could not verify',
        403,
        {'WWW-Authenticate' : 'Basic realm ="Wrong Password !!"'}
    )
  
# signup route
@app.route('/rmapi/signup', methods =['POST'])
def signup():
    # creates a dictionary of the form data
    data = request.json
  
    # gets name, email and password
    name, email = data.get('name'), data.get('email')
    password = data.get('password')
  
    # checking for existing user
    user = Users.query\
        .filter_by(email = email)\
        .first()
    if not user:
        # database ORM object
        user = Users(
            public_id = str(uuid.uuid4()),
            name = name,
            email = email,
            password = generate_password_hash(password)
        )
        # insert user
        db.session.add(user)
        db.session.commit()
  
        return make_response('Successfully registered.', 201)
    else:
        # returns 202 if user already exists
        return make_response('User already exists. Please Log in.', 202)

#Get All users
@app.route('/rmapi/users', methods=['GET'])
@token_required
def get_all_users(current_user):
    # querying the database
    # for all the entries in it
    users = Users.query.all()
    # converting the query objects
    # to list of jsons
    output = []
    for user in users:
        # appending the user data json
        # to the response list
        output.append({
            'public_id': user.public_id,
            'name' : user.name,
            'email' : user.email
        })
  
    return jsonify({'users': output})

# Create a Package
@app.route('/rmapi/package', methods=['POST'])
@token_required
def new_package(current_user):
  package = request.json['package']
  system = request.json['system']
  baseline = request.json['baseline']
  state = request.json['state']
  dimstream = request.json['dimstream']

  new_package = Package(package, system, baseline, state, dimstream)

  db.session.add(new_package)
  db.session.commit()

  return package_schema.jsonify(new_package)

# Get All Packages
@app.route('/rmapi/package', methods=['GET'])
@token_required
def get_packages(current_user):
  all_packages = Package.query.all()
  result = packages_schema.dump(all_packages)
  return jsonify(result)

# Get Single Package
@app.route('/rmapi/package/<id>', methods=['GET'])
@token_required
def get_package(current_user,id):
  package = Package.query.get(id)
  return package_schema.jsonify(package)

# Update a Package
@app.route('/rmapi/package/<id>', methods=['PUT'])
@token_required
def update_package(current_user,id):
  package_to_update = Package.query.get(id)

  package = request.json['package']
  system = request.json['system']
  baseline = request.json['baseline']
  state = request.json['state']
  dimstream = request.json['dimstream']

  package_to_update.package = package
  package_to_update.system = system
  package_to_update.baseline = baseline
  package_to_update.state = state
  package_to_update.dimstream = dimstream


  db.session.commit()

  return package_schema.jsonify(package_to_update)

# Delete Package
@app.route('/rmapi/package/<id>', methods=['DELETE'])
@token_required
def delete_package(current_user,id):
  package = Package.query.get(id)
  db.session.delete(package)
  db.session.commit()

  return package_schema.jsonify(package)
# Run Server
if __name__ == '__main__':
  app.run(debug=True)