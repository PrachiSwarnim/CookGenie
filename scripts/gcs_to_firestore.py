import json
import re
from google.cloud import storage, firestore
from google.api_core.exceptions import GoogleAPICallError, PermissionDenied

def safe_doc_id(name: str) -> str:
    """Sanitize a string to use as Firestore document ID"""
    return re.sub(r'[\\/*?:"<>|#?]', "_", name.strip())

def gcs_to_firestore(bucket_name="cookgenie", collection_name="cookgenie"):
    try:
        storage_client = storage.Client()
        firestore_client = firestore.Client()
    except PermissionDenied as e:
        print(f"❌ Could not connect to Firestore: {e}")
        return
    except GoogleAPICallError as e:
        print(f"❌ Firestore API error: {e}")
        return

    try:
        blobs = storage_client.list_blobs(bucket_name, prefix="recipes/")
    except GoogleAPICallError as e:
        print(f"❌ Could not list blobs in bucket '{bucket_name}': {e}")
        return

    for blob in blobs:
        if not blob.name.endswith(".json"):
            continue

        path_parts = blob.name.split("/")
        if len(path_parts) > 2:
            recipe_name = path_parts[2].replace(".json", "")
        else:
            recipe_name = path_parts[-1].replace(".json", "")

        doc_id = safe_doc_id(recipe_name)

        try:
            data = json.loads(blob.download_as_text())
            firestore_client.collection(collection_name).document(doc_id).set(data)
            print(f"✅ Uploaded {recipe_name} -> Firestore ({collection_name}/{doc_id})")
        except PermissionDenied as e:
            print(f"❌ Permission denied for {blob.name}: {e}")
        except GoogleAPICallError as e:
            print(f"❌ Firestore API error for {blob.name}: {e}")
        except Exception as e:
            print(f"❌ Failed to upload {blob.name}: {e}")

if __name__ == "__main__":
    gcs_to_firestore()
