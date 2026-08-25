from bson import ObjectId
from backend.database.mongodb import db


class ProfileRepository:

    def __init__(self):
        self.collection = db["patient_profiles"]

    def get_by_user_id(self, user_id):
        print("USER ID RECEIVED:", user_id)
        print("DATABASE:", db.name)
        print("COLLECTION:", self.collection.name)

        query = {
            "user_id": ObjectId(user_id)
        }

        print("QUERY:", query)

        profile = self.collection.find_one(query)

        if not profile:
            raise ValueError("Identity profile not found")

        return profile