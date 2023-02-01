from .models.model import Role
from flaskr.db import get_db
from flask import Blueprint, current_app, g, jsonify, make_response

def add_roles():
    with current_app.app_context():
        db = get_db()
        roles_collection = db.roles
        exisiting_roles = roles_collection.find()
        exisiting_roles = [Role(**doc).to_json() for doc in exisiting_roles]

        roles = []
        roles.append(Role(name = 'admin'))
        roles.append(Role(name = 'user'))

        for role in exisiting_roles:
            for index, new_role in enumerate(roles):
                if (role['name'] == new_role.name):
                    roles.pop(index)

        for role in roles:
            roles_collection.insert_one(role.to_bson())
