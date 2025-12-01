from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import csv
import winsound
import os

# Setup ChromeDriver
service = Service(r"C:\Users\User\Desktop\python testing\chromedriver-win64\chromedriver.exe")
options = Options()
options.headless = True

driver = webdriver.Chrome(service=service, options=options)

def wait_for_page_load(timeout=10):
    """Wait for page to load by checking for specific elements"""
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".product-heading h1, [class*='product'], [data-at='product_name']"))
        )
    except:
        pass

def play_completion_sound():
    """Play a sound to indicate scraping is complete"""
    try:
        sound_file = r"C:\Users\User\Desktop\python testing\pop.wav"
        if os.path.exists(sound_file):
            winsound.PlaySound(sound_file, winsound.SND_FILENAME)
            print("✓ Custom completion sound played!")
        else:
            winsound.PlaySound("SystemExclamation", winsound.SND_ALIAS)
            print("✓ Fallback system sound played")
    except Exception as e:
        print("\a" * 3)
        print(f"Scraping complete! ✓ (Sound error: {e})")

def is_combo_product(product_name):
    """Check if the product is a combo/set/bundle"""
    combo_keywords = [
        ' combo', ' bundle', ' pack', ' set',
        ' trio', ' calendar', ' sponge', ' refill',
        ' twin', ' duo', ' pair', ' kit', ' collection'
    ]
    
    if product_name == "N/A" or not product_name:
        return False
    
    product_lower = product_name.lower()
    
    for keyword in combo_keywords:
        if keyword in product_lower:
            return True
    
    return False

def get_all_product_links(category_url):
    """Get all product links from category page, filter combo products immediately"""
    driver.get(category_url)
    wait_for_page_load()
    
    all_links = set()
    page = 1
    total_combo_skipped = 0
    
    while True:
        print(f"\nScraping page {page}...")
        
        # Scroll to load all products
        last_height = driver.execute_script("return document.body.scrollHeight")
        scrolls = 0
        while scrolls < 2:  # Reduced scrolls
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(0.5)  # Reduced sleep
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
            scrolls += 1

        # Find ONLY product links, not all containers
        all_a_tags = driver.find_elements(By.TAG_NAME, "a")
        current_page_links = 0
        page_combo_count = 0
        
        print(f"Found {len(all_a_tags)} links on page {page}")
        
        # First pass: collect all product links
        product_links = []
        for tag in all_a_tags:
            try:
                href = tag.get_attribute("href")
                if href and '/products/' in href:
                    if href.startswith('/'):
                        full_url = f"https://www.sephora.my{href}"
                    elif 'sephora.my' in href:
                        full_url = href
                    else:
                        continue
                    
                    if full_url not in all_links:
                        product_links.append(full_url)
            except:
                continue
        
        print(f"Found {len(product_links)} potential product URLs")
        
        # Second pass: check if they're combo products
        for url in product_links:
            try:
                # Extract product name from the link text
                link_element = driver.find_element(By.XPATH, f"//a[@href='{url}' or @href='{url.replace('https://www.sephora.my', '')}']")
                product_name = link_element.text.strip()
                
                # Check if it's a combo product
                if product_name and is_combo_product(product_name):
                    page_combo_count += 1
                    continue  # Skip combo product
                
                # Add to our collection
                all_links.add(url)
                current_page_links += 1
                
                # Show progress
                if current_page_links <= 5:  # Show first 5 found
                    print(f"  Found: {product_name}")
                    
            except Exception as e:
                # If we can't get the name, still add the URL (will check later)
                all_links.add(url)
                current_page_links += 1
        
        total_combo_skipped += page_combo_count
        
        print(f"Page {page} Results:")
        print(f"  • New products found: {current_page_links}")
        print(f"  • Combo products skipped: {page_combo_count}")
        print(f"  • Total unique products: {len(all_links)}")
        
        # Stop if no products found on this page
        if current_page_links == 0 and page > 1:
            print("No products found on this page. Stopping pagination.")
            break
            
        # Try to go to next page
        page += 1
        next_page_url = ""
        
        if '?page=' in category_url:
            base_url = category_url.split('?page=')[0]
            next_page_url = f"{base_url}?page={page}"
        elif '?' in category_url:
            next_page_url = f"{category_url}&page={page}"
        else:
            next_page_url = f"{category_url}?page={page}"
        
        # Try loading next page
        try:
            driver.get(next_page_url)
            wait_for_page_load(5)  # Shorter timeout
            
            # Check if we're on a different page
            current_url = driver.current_url
            if f"page={page}" not in current_url and page > 2:
                print("No more pages found.")
                break
                
        except Exception as e:
            print(f"Cannot navigate to next page: {e}")
            break
            
        # Safety limit
        if page > 20:  # Reduced limit
            print("Reached page limit (20 pages)")
            break
        if len(all_links) > 200:  # Product limit
            print("Reached product limit (200 products)")
            break
    
    print(f"\nFinal Results:")
    print(f"• Total unique products found: {len(all_links)}")
    print(f"• Total combo products skipped: {total_combo_skipped}")
    
    return list(all_links)

def parse_product(url):
    """Extract brand and product name from product page"""
    driver.get(url)
    wait_for_page_load()

    try:
        product_name = driver.find_element(By.CSS_SELECTOR, ".product-heading h1").text
    except:
        product_name = "N/A"
    
    # Double-check for combo products (in case listing page detection missed some)
    if is_combo_product(product_name):
        print(f"Skipping combo product: {product_name}")
        return None

    try:
        brand_element = driver.find_element(By.CSS_SELECTOR, ".product-brand a")
        brand_name = brand_element.text.strip()
    except:
        try:
            brand_name = driver.find_element(By.CSS_SELECTOR, ".product-brand").text.strip()
        except:
            brand_name = "N/A"

    return {
        "brandName": brand_name,
        "productName": product_name,
        "productURL": url
    }

def scrape_single_product(product_url, output_file="sephora_products.csv"):
    """Scrape a single product URL"""
    print(f"Scraping single product: {product_url}")
    
    existing_urls = set()
    file_exists = False
    
    try:
        with open(output_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing_urls.add(row["productURL"])
            file_exists = True
            print(f"Found {len(existing_urls)} existing products in CSV")
    except FileNotFoundError:
        print("Creating new CSV file.")
    
    if product_url in existing_urls:
        print("Product already exists. Skipping.")
        return
    
    try:
        data = parse_product(product_url)
        if data is not None:
            mode = "a" if file_exists else "w"
            with open(output_file, mode, newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=["brandName", "productName", "productURL"])
                
                if not file_exists:
                    writer.writeheader()
                
                writer.writerow(data)
                print(f"✓ Scraped: {data['brandName']} - {data['productName']}")
        else:
            print("Skipped combo product")
    except Exception as e:
        print(f"✗ Failed to scrape {product_url}: {e}")

def scrape_category(category_url, output_file="sephora_products.csv"):
    """Scrape all products from a category"""
    print("Getting product links from category...")
    product_urls = get_all_product_links(category_url)
    print(f"\nFound {len(product_urls)} individual products (combo products already filtered out).")

    existing_urls = set()
    file_exists = False
    
    try:
        with open(output_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing_urls.add(row["productURL"])
            file_exists = True
            print(f"Found {len(existing_urls)} existing products in CSV")
    except FileNotFoundError:
        print("Creating new CSV file.")
    
    new_product_urls = [url for url in product_urls if url not in existing_urls]
    print(f"Found {len(new_product_urls)} new products to scrape")
    
    if not new_product_urls:
        print("No new products to add.")
        return

    mode = "a" if file_exists else "w"
    with open(output_file, mode, newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["brandName", "productName", "productURL"])
        
        if not file_exists:
            writer.writeheader()
        
        for i, url in enumerate(new_product_urls, 1):
            try:
                data = parse_product(url)
                if data is not None:
                    writer.writerow(data)
                    print(f"[{i}/{len(new_product_urls)}] ✓ {data['brandName']} - {data['productName']}")
                else:
                    print(f"[{i}/{len(new_product_urls)}] Skipped combo product")
            except Exception as e:
                print(f"[{i}/{len(new_product_urls)}] ✗ Failed: {url} - Error: {e}")
            
            time.sleep(0.3)

if __name__ == "__main__":
    print("=" * 50)
    print("SEPHORA MALAYSIA PRODUCT SCRAPER")
    print("=" * 50)
    print("\nEnter URL to scrape:")
    print("1. Category URL (e.g., https://www.sephora.my/categories/skincare/cleanser)")
    print("2. Single Product URL (e.g., https://www.sephora.my/products/fresh-soy-face-cleanser/v/150ml)")
    print()
    
    user_url = input("URL: ").strip()
    
    if not user_url:
        print("Error: No URL provided!")
        exit()
    
    if not user_url.startswith(('http://', 'https://')):
        print("Error: Invalid URL format!")
        exit()
    
    print(f"\nStarting to scrape: {user_url}")
    print("Please wait...\n")
    
    if '/products/' in user_url:
        scrape_single_product(user_url)
    else:
        scrape_category(user_url)
    
    driver.quit()
    
    print("\n" + "=" * 50)
    print("SCRAPING COMPLETED!")
    print("=" * 50)
    play_completion_sound()
    print("\nResults saved to: sephora_products.csv")


