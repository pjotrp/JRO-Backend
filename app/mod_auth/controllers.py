# Import flask dependencies
from flask import Blueprint, request, jsonify, json
from flask_cors import CORS
import requests
import urllib
from docs import conf
# Import the database object from the main app module
from app.app import db
from flask_jwt_extended import (
    JWTManager,
    jwt_required,
    create_access_token,
    get_jwt_identity,
)

# Import module models (i.e. User)
from app.mod_auth.models import User

# Define the blueprint: 'auth', set its url prefix: app.url/auth
mod_auth = Blueprint('auth', __name__)
CORS(mod_auth)

# Set the route and accepted methods
@mod_auth.route('/login/', methods=['GET', 'OPTIONS'])
def signin():
    auth_code = request.args.get('orcid_auth_code')
    params = {'client_id': conf.ORCID_CLIENT_ID,
              'client_secret': conf.ORCID_SECRET,
              'grant_type': 'authorization_code',
              'code': auth_code,
              'redirect_uri': conf.ORCID_REDIRECT_URL
              }
    hdr = { 'Content-Type' : 'application/x-www-form-urlencoded' }
    # data = urllib.parse.urlencode(params).encode()
    # req = urllib.request.Request(conf.ORCID_API_URL+"token", data=data, headers=hdr)
    results = requests.post(conf.ORCID_API_URL+"token",
              params=params,
              headers=hdr)
    user_data = json.loads(results.text)
    access_token = create_access_token(identity=user_data)
    print(access_token)
    print("---------DATA---------",user_data)
    if 'orcid' in user_data:
        if not user_exists(user_data['orcid']):
            create_user(user_data['orcid'], user_data['name'], None, user_data['access_token'])
        else:
            if is_editor(user_data['orcid']):
                user_data['role'] = 'editor'
                access_token = create_access_token(identity=user_data)
                
    return jsonify(access_token=access_token, orcid=user_data['orcid'])



@mod_auth.route("/profile/", methods=["GET", "OPTIONS"])
@jwt_required
def profile():
    current_user = get_jwt_identity()
    return jsonify(current_user), 200


@mod_auth.route('/logineditor/', methods=['GET', 'OPTIONS'])
def signin_editor():
    auth_code = request.args.get('orcid_auth_code')
    params = {'client_id': conf.ORCID_CLIENT_ID,
              'client_secret': conf.ORCID_SECRET,
              'grant_type': 'authorization_code',
              'code': auth_code,
              'redirect_uri': conf.ORCID_REDIRECT_URL
              }
    hdr = { 'Content-Type' : 'application/x-www-form-urlencoded' }
    # data = urllib.parse.urlencode(params).encode()
    # req = urllib.request.Request(conf.ORCID_API_URL+"token", data=data, headers=hdr)
    results = requests.post(conf.ORCID_API_URL+"token",
              params=params,
              headers=hdr)
    user_data = json.loads(results.text)
    access_token = create_access_token(identity=user_data)
    print(access_token)
    print("---------DATA---------",user_data)
    if 'orcid' in user_data and user_exists(user_data['orcid']) and is_editor(user_data['orcid']):
        return jsonify(access_token=access_token)
    else:
        return jsonify({'status':'not editor'}), 500

def is_editor(orcid):
    user = User.query.filter_by(orcid=orcid).first()
    return user.role=="editor"


def user_exists(orcid):
    user = User.query.filter_by(orcid=orcid).first()
    print (user)
    return True if user else False


def create_user(orcid, name, aka, token):
    user = User(orcid=orcid, name=name, aka=aka, token=token)
    db.session.add(user)
    db.session.commit()
