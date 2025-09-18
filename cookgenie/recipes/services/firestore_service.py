from google.cloud import firestore

db = firestore.Client()

def get_all_recipes():
    recipes_ref = db.collection("cookgenie")
    docs = recipes_ref.stream()
    return [{**doc.to_dict(), "id": doc.id} for doc in docs]

def get_recipe_by_id(recipe_id):
    doc = db.collection("cookgenie").document(recipe_id).get()
    return doc.to_dict() if doc.exists else None