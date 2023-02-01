from pymongo import MongoClient

from flask import current_app, g

client = MongoClient('mongodb+srv://maipaw:PHmgNPFOAftr9bf5@cluster0.e5pkosj.mongodb.net/?retryWrites=true&w=majority')
# client = MongoClient('mongodb://localhost:27017/')

def get_db():
    if 'db' not in g:
        g.db = client['maipaw']

    return g.db
