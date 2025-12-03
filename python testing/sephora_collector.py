from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

import time
import csv
import winsound
import os

# Setup ChromeDriver
#service = Service(r"C:\Users\User\Desktop\python testing\chromedriver-win64\chromedriver.exe")
#options = Options()
options.headless = False

# ADDED: Disable images for faster loading
prefs = {
    'profile.default_content_setting_values': {
        'images': 2,  # 2 = Block images
        'javascript': 1,  # Keep JavaScript enabled
    }
}
options.add_experimental_option('prefs', prefs)

options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])

driver = webdriver.Chrome(service=service, options=options)

def wait_for_page_load(timeout=8):  # Increased from 5 to 8
    """Wait for page to load by checking for specific elements"""
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".product-heading h1, a[href*='/products/']"))
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

def is_combo_product(product_name, url=""):
    """Check if the product is a combo/set/bundle using name AND URL"""
    combo_keywords = [
        'combo', 'bundle', 'pack', 'set',
        'trio', 'calendar', 'sponge', 'refill',
        'twin', 'duo', 'pair', 'kit', 'collection'
    ]
    
    # Check product name (convert to lowercase and remove special chars)
    if product_name and product_name != "N/A":
        product_lower = product_name.lower()
        # Replace special characters with spaces for better matching
        product_clean = product_lower.replace('-', ' ').replace('+', ' ').replace('&', ' ')
        
        for keyword in combo_keywords:
            if keyword in product_clean:
                return True
    
    # Check URL
    if url:
        url_lower = url.lower()
        # URLs use hyphens, so we need to check with hyphens
        for keyword in combo_keywords:
            # Check both with space and with hyphen
            if f' {keyword}' in url_lower or f'-{keyword}' in url_lower or f'/{keyword}' in url_lower:
                return True
    
    return False

def parse_product(url):
    """Extract brand and product name from product page"""
    driver.get(url)
    time.sleep(2)
    
    try:
        # Try multiple selectors for product name
        product_name = ""
        name_selectors = [
            ".product-heading h1",
            "h1[data-at='product_name']",
            "h1.product-name",
            "h1"
        ]
        
        for selector in name_selectors:
            try:
                product_name = driver.find_element(By.CSS_SELECTOR, selector).text
                if product_name:
                    break
            except:
                continue
        
        if not product_name:
            product_name = "N/A"
            
    except:
        product_name = "N/A"
    
    # Check if combo product using updated function
    if is_combo_product(product_name, url):
        print(f"Skipping combo: {product_name}")
        return None

    try:
        # Try multiple selectors for brand
        brand_name = ""
        brand_selectors = [
            ".product-brand a",
            ".product-brand",
            "[data-at='brand_name']",
            ".brand-name"
        ]
        
        for selector in brand_selectors:
            try:
                brand_element = driver.find_element(By.CSS_SELECTOR, selector)
                brand_name = brand_element.text.strip()
                if brand_name:
                    break
            except:
                continue
        
        if not brand_name:
            brand_name = "N/A"
            
    except:
        brand_name = "N/A"

    return {
        "brandName": brand_name,
        "productName": product_name,
        "productURL": url
    }

def get_all_product_links(category_url):
    """Get all product links from category page, filter combo products by URL"""
    driver.get(category_url)
    time.sleep(3)
    
    all_links = set()
    page = 1
    total_combos_filtered = 0
    
    while True:
        print(f"Scraping page {page}...")
        
        # Scroll
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
        time.sleep(0.5)
        
        # Find all product links
        product_elements = driver.find_elements(By.CSS_SELECTOR, "a[href*='/products/']")
        current_page_links = 0
        page_combos_filtered = 0
        
        for element in product_elements:
            try:
                href = element.get_attribute("href")
                if not href:
                    continue
                    
                # Format URL
                if href.startswith('/'):
                    full_url = f"https://www.sephora.my{href}"
                else:
                    full_url = href
                
                # Skip if already collected
                if full_url in all_links:
                    continue
                
                # Check if URL contains combo keywords
                if is_combo_product("", full_url):  # Check URL only
                    page_combos_filtered += 1
                    continue  # Skip this combo URL
                
                # Get product name from link text (optional)
                product_name = element.text.strip()
                
                # Also check product name if available
                if product_name and is_combo_product(product_name, ""):
                    page_combos_filtered += 1
                    continue  # Skip this combo
                
                # Add non-combo product
                all_links.add(full_url)
                current_page_links += 1
                
            except:
                continue
        
        total_combos_filtered += page_combos_filtered
        
        print(f"Page {page} Results:")
        print(f"  • New products found: {current_page_links} (non-combo only)")
        print(f"  • Combo URLs filtered: {page_combos_filtered}")
        print(f"  • Total products: {len(all_links)}")
        
        # Stop if no products found
        if current_page_links == 0 and page > 1:
            print("No new products found. Stopping.")
            break
            
        # Try next page
        page += 1
        next_page_url = f"{category_url.split('?')[0]}?page={page}"
        
        try:
            driver.get(next_page_url)
            time.sleep(2.5)
            
            # Check for content
            page_text = driver.find_element(By.TAG_NAME, "body").text
            if len(page_text) < 100:
                print("Page appears empty. Stopping.")
                break
                
        except Exception as e:
            print(f"Cannot navigate to next page: {e}")
            break
            
        if page > 30:
            print("Reached page limit (30 pages)")
            break
    
    print(f"\nFinal Results:")
    print(f"• Non-combo products: {len(all_links)}")
    print(f"• Combo URLs filtered: {total_combos_filtered}")
    
    return list(all_links)  # Only NON-COMBO URLs

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
    except FileNotFoundError:
        pass
    
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
                print(f"✓ {data['brandName']} - {data['productName']}")
    except Exception as e:
        print(f"✗ Failed: {e}")

def scrape_category(category_url, output_file="sephora_products.csv"):
    """Scrape all products from a category"""
    print("Getting product links from category...")
    product_urls = get_all_product_links(category_url)
    print(f"Found {len(product_urls)} products.")

    existing_urls = set()
    file_exists = False
    
    try:
        with open(output_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing_urls.add(row["productURL"])
            file_exists = True
    except FileNotFoundError:
        pass
    
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
                    print(f"[{i}/{len(new_product_urls)}] ✓ {data['brandName']}")
                else:
                    print(f"[{i}/{len(new_product_urls)}] Skipped combo")
            except Exception as e:
                print(f"[{i}/{len(new_product_urls)}] ✗ Failed: {e}")
            
            # Consistent delay between products
            time.sleep(0.5)  # Increased from 0.3

if __name__ == "__main__":
    print("=" * 50)
    print("SEPHORA MALAYSIA PRODUCT SCRAPER (MULTI-CATEGORY)")
    print("=" * 50)
    print("\nEnter URLs to scrape (separate by comma or new lines):")
    print("1. Category URLs (e.g., https://www.sephora.my/categories/skincare/cleanser)")
    print("2. Single Product URLs (e.g., https://www.sephora.my/products/fresh-soy-face-cleanser/v/150ml)")
    print("\nEnter 'DONE' when finished entering URLs.")
    print()
    
    urls = []
    while True:
        url_input = input("Enter URL (or 'DONE' to finish): ").strip()
        
        if url_input.upper() == 'DONE':
            break
            
        if not url_input:
            continue
            
        if not url_input.startswith(('http://', 'https://')):
            print(f"Error: Invalid URL format: {url_input}")
            continue
            
        urls.append(url_input)
    
    if not urls:
        print("Error: No URLs provided!")
        exit()
    
    print(f"\nStarting to scrape {len(urls)} URLs...")
    print("Please wait...\n")
    
    start_time = time.time()
    
    for i, user_url in enumerate(urls, 1):
        print(f"\n{'='*60}")
        print(f"PROCESSING URL {i}/{len(urls)}: {user_url}")
        print(f"{'='*60}\n")
        
        if '/products/' in user_url:
            scrape_single_product(user_url)
        else:
            scrape_category(user_url)
        
        print(f"\n✓ Completed URL {i}/{len(urls)}")
        if i < len(urls):  # Add a small pause between URLs
            print("Moving to next URL in 2 seconds...")
            time.sleep(2)
    
    driver.quit()
    
    elapsed_time = time.time() - start_time
    print(f"\nTotal time: {elapsed_time:.1f} seconds")
    
    print("\n" + "=" * 50)
    print("ALL SCRAPING COMPLETED!")
    print("=" * 50)
    play_completion_sound()
    print("\nResults saved to: sephora_products.csv")