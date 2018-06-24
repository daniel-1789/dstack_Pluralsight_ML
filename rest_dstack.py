

from flask import Flask, request
from flask_restful import Resource, Api, reqparse
from json import dumps
import jsonify
import sqlite3

conn = sqlite3.connect('dstack.db')
app = Flask(__name__)
api = Api(app)


class User_Id(Resource):
    def get(self, user_id):
        conn = sqlite3.connect('dstack.db')

        c = conn.cursor()
        c.execute("""SELECT dst_usr, distance FROM distance_matrix where src_usr = ? and src_usr != dst_usr ORDER BY distance LIMIT 10""", (user_id,))        
        rows = c.fetchall()
        user_dict =  {k:v for k, v in rows}

        return (user_dict)


# Define parser and request args
parser = reqparse.RequestParser()
parser.add_argument('id', type=int)
parser.add_argument('num', type=int)
        
class User_Idn(Resource):
    def get(self):
        # http://127.0.0.1:5002/usersn?id=9999&num=15
        args = parser.parse_args()
        user_id = args['id']
        cnt = args['num']
        conn = sqlite3.connect('dstack.db')
  
        c = conn.cursor()
        c.execute("""SELECT dst_usr, distance FROM distance_matrix where src_usr = ? and src_usr != dst_usr ORDER BY distance LIMIT ?""", (user_id,cnt,))        
        rows = c.fetchall()
        user_dict =  {k:v for k, v in rows}

        return (user_dict)



api.add_resource(User_Id, '/users/<user_id>') 
api.add_resource(User_Idn, '/usersn') 


if __name__ == '__main__':
     app.run(port='5002')
     

