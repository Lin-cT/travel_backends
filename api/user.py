import json, jwt
from flask import Blueprint, request, jsonify, current_app, Response, make_response
from flask_restful import Api, Resource
from auth_middleware import token_required
from model.users import User

user_api = Blueprint('user_api', __name__, url_prefix='/api/users')
api = Api(user_api)

class UserAPI:
    class _Itinerary(Resource):
        #retrieving data for all users in database
        def get(self):
            itinerary = User.query.with_entities(User._itinerary).all()
            jsonData = [row[0] for row in itinerary]
            print(jsonData)
            return jsonify(jsonData)
                
        #Itinerary api code
        def put(self):
            body = request.get_json()
            token = request.cookies.get("jwt")
            data = jwt.decode(token, 
                            current_app.config["SECRET_KEY"], 
                            algorithms=["HS256"])
            itinerary = body.get('itinerary')
            users = User.query.all()
            for user in users:
                if user.uid == data["_uid"]:    
                    print(data["_uid"])
                    user.update("", "", "", itinerary, "")
                    print(user._itinerary)

        #Posting itinerary data
        def post(self):
            token = request.cookies.get("jwt")
            data = jwt.decode(token, 
                            current_app.config["SECRET_KEY"], 
                            algorithms=["HS256"])
            users = User.query.all()
            for user in users:
                if user.uid == data["_uid"]:    
                    return user.itinerary
    class _CRUD(Resource):
        def post(self):
            ''' Read data from the json body '''
            body = request.get_json()
            print(body)
            ''' Avoid garbage in, error checking '''
            # validate name
            name = body.get('name')
            if name is None or len(name) < 2:
                return {'message': f'Name is missing, or is less than 2 characters'}, 400
            # validate uid
            uid = body.get('uid')
            if uid is None or len(uid) < 2:
                return {'message': f'User ID is missing, or is less than 2 characters'}, 400
            # look for password and dob
            password = body.get('password')

            ''' #1: Key code block, setup USER OBJECT '''
            uo = User(name=name, uid=uid)
            
            ''' Additional garbage error checking '''
            # set password if provided
            if password is not None:
                uo.set_password(password)
            # convert to date type
            # create user in the database
            user = uo.create()
            # success returns json of user
            if user:
                print(user.read())
                return ((user.read()), 200)
            # failure returns error
            return {'message': f'Processed {name}, either a format error or User ID {uid} is duplicate'}, 400

        @token_required
        def get(self, current_user):
            users = User.query.all()
            json_ready = [user.read() for user in users]
            return jsonify(json_ready)

        @token_required
        def delete(self, current_user):
            body = request.get_json()
            uid = body.get('uid')
            users = User.query.all()
            for user in users:
                if user.uid == uid:
                    user.delete()
            return jsonify(user.read())

        @token_required
        def put(self, current_user):
            body = request.get_json()
            uid = body.get('uid')
            name = body.get('name')
            image = body.get('image')
            users = User.query.all()
            for user in users:
                if user.uid == uid:
                    user.update(name, '', '', image)
            return f"{user.read()} Updated"

    class _Security(Resource):
        def post(self):
            try:
                body = request.get_json()
                print(body)
                if not body:
                    return {
                        "message": "Please provide user details",
                        "data": None,
                        "error": "Bad request"
                    }, 400
                ''' Get Data '''
                uid = body.get('uid')
                if uid is None:
                    print("error at uid")
                    return {'message': f'User ID is missing'}, 400
                password = body.get('password')
                
                ''' Find user '''
                user = User.query.filter_by(_uid=uid).first()
                if user is None or not user.is_password(password):
                    print("error at password")
                    return {'message': f"Invalid user id or password"}, 401
                if user:
                    try:
                        token = jwt.encode(
                            {"_uid": user._uid},
                            current_app.config["SECRET_KEY"],
                            algorithm="HS256"
                        )
                        resp = Response("Authentication for %s successful" % (user._uid))
                        resp.set_cookie(key="jwt", value=token, max_age=3600, secure=True, samesite='None', path='/', httponly=False, domain="davidl0914.github.io/frontcasts")
                        print(resp.headers)
                        return resp
                    except Exception as e:
                        return {
                            "error": "Something went wrong",
                            "message": str(e)
                        }, 500
                return {
                    "message": "Error fetching auth token!",
                    "data": None,
                    "error": "Unauthorized"
                }, 404

            except Exception as e:
                return {
                        "message": "Something went wrong!",
                        "error": str(e),
                        "data": None
                }, 500

    # Register API resources
    api.add_resource(_CRUD, '/')
    api.add_resource(_Security, '/authenticate')
    api.add_resource(_Itinerary, '/itinerary')