from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy 
from flask_marshmallow import Marshmallow 
import os
#import pymysql

# Init app
app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
# Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'db.sqlite')
#app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://username:password@localhost/db_name'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Init db
db = SQLAlchemy(app)
# Init ma
ma = Marshmallow(app)

# Package Class/Model
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

#
@app.route('/rmapi')
def hello():
  return 'api root'
# Create a Package
@app.route('/rmapi/package', methods=['POST'])
def new_package():
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
def get_packages():
  all_packages = Package.query.all()
  result = packages_schema.dump(all_packages)
  return jsonify(result)

# Get Single Package
@app.route('/rmapi/package/<id>', methods=['GET'])
def get_package(id):
  package = Package.query.get(id)
  return package_schema.jsonify(package)

# Update a Package
@app.route('/rmapi/package/<id>', methods=['PUT'])
def update_package(id):
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
def delete_package(id):
  package = Package.query.get(id)
  db.session.delete(package)
  db.session.commit()

  return package_schema.jsonify(package)
# Run Server
if __name__ == '__main__':
  app.run(debug=False)