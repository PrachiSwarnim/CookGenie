import asyncio
import requests
from google.cloud import storage
from io import BytesIO
import json
from datetime import timedelta
from bs4 import BeautifulSoup

BUCKET_NAME = "cookgenie"
GCS_KEY_PATH = "robust-cycle-462516-v7-0c8f8cd91eb6.json"
SCRAPE_DO_TOKEN = "e92a9e41897546749a1d45f0e422682659e79de258a"

# Initialize GCS client
storage_client = storage.Client.from_service_account_json(GCS_KEY_PATH)
bucket = storage_client.bucket(BUCKET_NAME)

SIGNED_URL_EXPIRATION_DAYS = 7

# --- GCS Upload Functions ---
def upload_image_to_gcs(image_url, filename):
    try:
        response = requests.get(image_url)
        if response.status_code == 200:
            blob = bucket.blob(f"recipes/{filename}")
            blob.upload_from_file(BytesIO(response.content), content_type="image/jpeg")
            signed_url = blob.generate_signed_url(expiration=timedelta(days=SIGNED_URL_EXPIRATION_DAYS))
            return signed_url
    except Exception as e:
        print(f"⚠️ Failed to upload image {filename}: {e}")
    return None

def upload_json_to_gcs(data, filename):
    try:
        blob = bucket.blob(f"recipes/{filename}")
        blob.upload_from_string(json.dumps(data, indent=2), content_type="application/json")
        signed_url = blob.generate_signed_url(expiration=timedelta(days=SIGNED_URL_EXPIRATION_DAYS))
        return signed_url
    except Exception as e:
        print(f"⚠️ Failed to upload JSON {filename}: {e}")
    return None

# --- Fetch HTML via Scrape.do ---
def fetch_html(url):
    api_url = f"http://api.scrape.do/?url={url}&token={SCRAPE_DO_TOKEN}"
    try:
        resp = requests.get(api_url, timeout=60)
        if resp.status_code == 200:
            return resp.text
    except Exception as e:
        print(f"⚠️ Failed to fetch {url}: {e}")
    return None

# --- Parse a single recipe ---
def parse_recipe(html, url, category_name):
    try:
        soup = BeautifulSoup(html, "html.parser")

        title_tag = soup.select_one("h1.entry-title")
        title = title_tag.get_text(strip=True) if title_tag else "Untitled Recipe"

        ingredients = [li.get_text(strip=True) for li in soup.select("div.wprm-recipe-ingredients-container li")]
        instructions = [li.get_text(strip=True) for li in soup.select("div.wprm-recipe-instructions-container li")]

        image_tag = soup.select_one("div.wprm-recipe-image img")
        image_url = image_tag['src'] if image_tag else None
        cloud_image_url = upload_image_to_gcs(image_url, f"{category_name}/{title}.jpg") if image_url else None

        recipe = {
            "url": url,
            "title": title,
            "ingredients": ingredients,
            "instructions": instructions,
            "image": cloud_image_url,
            "category": category_name
        }

        upload_json_to_gcs(recipe, f"{category_name}/{title}.json")
        print(f"✅ Scraped and uploaded: {category_name}/{title}")
        return recipe
    except Exception as e:
        print(f"⚠️ Failed to parse recipe at {url}: {e}")
        return None

# --- Scrape category ---
def scrape_category(category_url, category_name, max_pages=5):
    recipes = []
    for page_num in range(1, max_pages + 1):
        url = f"{category_url}page/{page_num}/" if page_num > 1 else category_url
        print(f"\n[INFO] Scraping list page: {url}")
        html = fetch_html(url)
        if not html:
            break

        soup = BeautifulSoup(html, "html.parser")
        recipe_links = [a['href'] for a in soup.select("h2.entry-title > a")]

        if not recipe_links:
            break

        for link in recipe_links:
            recipe_html = fetch_html(link)
            if recipe_html:
                recipe = parse_recipe(recipe_html, link, category_name)
                if recipe:
                    recipes.append(recipe)
    return recipes

# --- Run scraping ---
if __name__ == "__main__":
    categories = {
        # "asian": "https://www.recipetineats.com/category/cuisines/asian-recipes/",
        # "indian": "https://www.recipetineats.com/category/cuisines/indian-recipes/",
        # "italian": "https://www.recipetineats.com/category/cuisines/italian-recipes/",
        # "mediterranean": "https://www.recipetineats.com/category/cuisines/mediterranean-recipes/",
        # "south-american": "https://www.recipetineats.com/category/cuisines/south-american-recipes/",
        "greek": "https://www.recipetineats.com/category/cuisines/greek-recipes/",
        "french": "https://www.recipetineats.com/category/cuisines/french-recipes/",
    }

    all_results = {}
    for category_name, url in categories.items():
        print(f"\n[INFO] Starting category: {category_name}")
        recipes = scrape_category(url, category_name)
        all_results[category_name] = recipes

    # Upload a master index file
    upload_json_to_gcs(all_results, "index.json")

    print("\n=== SUMMARY ===")
    for category, recipes in all_results.items():
        print(f"{category}: {len(recipes)} recipes scraped and uploaded")
