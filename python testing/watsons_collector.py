from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import csv
import winsound  # For Windows sound
import os
import re

# Setup ChromeDriver
service = Service(r"C:\Users\User\Desktop\python testing\chromedriver-win64\chromedriver.exe")
options = Options()
options.headless = True

# Disable ONLY images for faster loading (CSS is now ENABLED)
prefs = {
    'profile.managed_default_content_settings.images': 2,
    'profile.default_content_setting_values.javascript': 1,
}
options.add_experimental_option("prefs", prefs)
options.add_argument('--blink-settings=imagesEnabled=false')

driver = webdriver.Chrome(service=service, options=options)

def extract_category_from_url(url):
    """Extract category name from URL"""
    try:
        pattern = r'skincare/([^/]+)/c/'
        match = re.search(pattern, url)
        
        if match:
            category = match.group(1)
            category = category.replace('-', ' ').title()
            return category
        
        pattern2 = r'/([^/]+)/c/\d+'
        match2 = re.search(pattern2, url)
        
        if match2:
            category = match2.group(1)
            category = category.replace('-', ' ').title()
            return category
        
        return "Uncategorized"
    except:
        return "Uncategorized"

def is_combo_url(url):
    """Check if URL contains combo/bundle keywords to filter out early"""
    # Keywords that indicate combos/bundles in URLs
    combo_keywords = [
        'combo', 'bundle', 'pack', 'set',
        'trio', 'calendar', 'kit', 'collection',
        'duo', 'pair', 'twin', 'multi'
    ]
    
    url_lower = url.lower()
    
    # Check for combo keywords in the URL path
    for keyword in combo_keywords:
        if keyword in url_lower:
            # Make sure it's not part of another word
            pattern = r'[^a-z]' + keyword + r'[^a-z]|^' + keyword + r'[^a-z]|[^a-z]' + keyword + r'$'
            if re.search(pattern, url_lower):
                return True
    
    # Check for patterns like "2-in-1", "3-in-1", etc.
    if re.search(r'\d+\s*-\s*in\s*-\s*\d+', url_lower):
        return True
    
    # Check for patterns like "2x", "3x", etc.
    if re.search(r'/\d+\s*x\s*\d+/', url_lower):
        return True
    
    return False

def is_single_product(product_name):
    """Check if the product is a single item (not a bundle/combo)"""
    # This is a secondary check for product names (after URL filtering)
    exclude_keywords = [
        'combo', 'bundle', 'pack', 'set',
        'trio', 'calendar', 'sponge', 'refill',
        'twin', 'duo', 'pair', 'kit', 'collection'
    ]
    
    product_lower = product_name.lower()
    
    for keyword in exclude_keywords:
        pattern = r'\b' + re.escape(keyword) + r'\b'
        if re.search(pattern, product_lower):
            return False
    
    size_pattern = r'\d+\s*(ml|g|oz|l)\s+\d+\s*(ml|g|oz|l)'
    if re.search(size_pattern, product_lower):
        return False
    
    quantity_pattern = r'\d+\s*x\s*\d+'
    if re.search(quantity_pattern, product_lower):
        return False
    
    if re.search(r'\band\b|\&', product_lower):
        if not re.search(r'wash\s+and\s+care|clean\s+and\s+clear', product_lower):
            return False
    
    return True

def play_completion_sound():
    """Play a sound to indicate scraping is complete"""
    try:
        sound_file = r"C:\Users\User\Desktop\python testing\pop.wav"
        if os.path.exists(sound_file):
            winsound.PlaySound(sound_file, winsound.SND_FILENAME)
            print("✓ Custom completion sound played!")
        else:
            winsound.PlaySound("SystemExclamation", winsound.SND_ALIAS)
            print("✓ Fallback system sound played (custom file not found)")
    except Exception as e:
        print("\a" * 3)
        print(f"Scraping complete! ✓ (Sound error: {e})")

def get_all_product_links(category_url):
    """Get all product links from a category page - FILTER COMBO URLs EARLY"""
    print(f"Loading category page: {category_url}")
    driver.get(category_url)
    
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )
    time.sleep(1)

    all_links = set()
    combo_links_filtered = 0
    page_count = 0
    
    base_url = category_url.split('?')[0]
    
    while True:
        print(f"Scraping page {page_count + 1}...")
        time.sleep(2)
        
        elements = driver.find_elements(By.CSS_SELECTOR, "a[href*='/p/']")
        current_page_links = 0
        current_page_filtered = 0
        
        for el in elements:
            href = el.get_attribute("href")
            if not href:
                continue
                
            # EARLY FILTERING: Check if URL contains combo keywords
            if is_combo_url(href):
                combo_links_filtered += 1
                current_page_filtered += 1
                continue
                
            if href not in all_links:
                all_links.add(href)
                current_page_links += 1
        
        print(f"Found {current_page_links} new single products on page {page_count + 1}")
        print(f"Filtered out {current_page_filtered} combo/bundle URLs on this page")
        print(f"Total unique single products so far: {len(all_links)}")

        if current_page_links == 0 and current_page_filtered == 0:
            print("No products found on this page. Stopping pagination.")
            break

        next_page_count = page_count + 1
        next_page_url = f"{base_url}?pageSize=64&currentPage={next_page_count}"
        
        driver.get(next_page_url)
        time.sleep(2)
        
        current_url = driver.current_url
        if f"currentPage={next_page_count}" not in current_url:
            print("No more pages found. Finished scraping.")
            break
            
        page_count = next_page_count
            
        if page_count > 50:
            print("Reached maximum page limit (50 pages)")
            break

    print(f"\nURL Filtering Summary:")
    print(f"  Total unique single products found: {len(all_links)}")
    print(f"  Combo/bundle URLs filtered out: {combo_links_filtered}")
    print(f"  Total URLs processed: {len(all_links) + combo_links_filtered}")
    
    return list(all_links)

def extract_product_info_fast(url, category_url=None):
    """FAST VERSION: Extract product info with minimal checks (URL already filtered)"""
    try:
        print(f"Loading product page: {url}")
        driver.get(url)
        
        # Shorter wait times since we already filtered combo URLs
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        time.sleep(2)  # Reduced from 2 seconds
        
        product_info = {
            'brand_name': 'N/A',
            'product_name': 'N/A',
            'url': url,
            'category': extract_category_from_url(category_url) if category_url else extract_category_from_url(url),
        }
        
        # Try to get product name quickly - try fewer selectors
        product_selectors = [
            ".product-name",
            ".product-title",
            "h1.title",
            "[itemprop='name']",
            "h1"
        ]
        
        for selector in product_selectors:
            try:
                element = driver.find_element(By.CSS_SELECTOR, selector)
                text = element.text.strip()
                if text and len(text) < 200:
                    product_info['product_name'] = text
                    break
            except:
                continue
        
        # Fallback to title tag
        if product_info['product_name'] == 'N/A':
            try:
                title = driver.title
                if title and len(title) < 200:
                    product_info['product_name'] = title
            except:
                pass
        
        # Quick brand extraction - fewer selectors
        brand_selectors = [
            ".product-brand a",
            ".brand-name",
            "[itemprop='brand']",
            ".product-info__brand"
        ]
        
        for selector in brand_selectors:
            try:
                element = driver.find_element(By.CSS_SELECTOR, selector)
                text = element.text.strip()
                if text and len(text) < 50:
                    product_info['brand_name'] = text
                    break
            except:
                continue
        
        print(f"  ✓ {product_info['brand_name']} - {product_info['product_name']}")
        return product_info
        
    except Exception as e:
        print(f"Error extracting product info from {url}: {e}")
        return {
            'brand_name': 'N/A',
            'product_name': 'N/A',
            'url': url,
            'category': extract_category_from_url(category_url) if category_url else extract_category_from_url(url),
        }

def read_existing_data(output_file):
    """Read existing data from CSV file and return as sorted list"""
    existing_data = []
    try:
        with open(output_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing_data.append({
                    'brand_name': row.get('brand_name', 'N/A'),
                    'product_name': row.get('product_name', 'N/A'),
                    'url': row.get('url', ''),
                    'category': row.get('category', 'Uncategorized')
                })
        print(f"Read {len(existing_data)} existing products from CSV")
    except FileNotFoundError:
        print("No existing CSV file found.")
    except Exception as e:
        print(f"Error reading CSV: {e}")
    
    return existing_data

def write_sorted_data(data, output_file):
    """Write data to CSV file sorted alphabetically by brand name then product name"""
    sorted_data = sorted(data, key=lambda x: (
        x['brand_name'].lower() if x['brand_name'] != 'N/A' else 'zzzzzzzz',
        x['product_name'].lower() if x['product_name'] != 'N/A' else 'zzzzzzzz'
    ))
    
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["brand_name", "product_name", "url", "category"])
        writer.writeheader()
        writer.writerows(sorted_data)
    
    print(f"Saved {len(sorted_data)} products to {output_file} (sorted alphabetically)")

def scrape_single_product(product_url, output_file="watsons_products_simple.csv", category_url=None):
    """Scrape a single product URL with early filtering"""
    print(f"\nScraping single product: {product_url}")
    
    # EARLY FILTERING: Check if URL contains combo keywords
    if is_combo_url(product_url):
        print(f"✗ Skipping combo/bundle URL: {product_url}")
        return False, 0
    
    existing_data = read_existing_data(output_file)
    existing_urls = {item['url'] for item in existing_data}
    
    if product_url in existing_urls:
        print("Product already exists in CSV. Skipping.")
        return False, 0
    
    try:
        data = extract_product_info_fast(product_url, category_url)
        
        # Secondary check on product name (just in case)
        if not is_single_product(data['product_name']):
            print(f"✗ Skipping bundle/combo: {data['product_name']}")
            return False, 0
            
        existing_data.append(data)
        write_sorted_data(existing_data, output_file)
        
        print(f"✓ Added and sorted: {data['brand_name']} - {data['product_name']}")
        return True, 1
    except Exception as e:
        print(f"Failed to scrape {product_url}: {e}")
        return False, 0

def scrape_category(category_url, output_file="watsons_products_simple.csv"):
    """Scrape all products from a category page - OPTIMIZED VERSION"""
    print(f"\nScraping category: {category_url}")
    
    category_name = extract_category_from_url(category_url)
    print(f"Category detected: {category_name}")
    
    # Get product links with early filtering
    product_urls = get_all_product_links(category_url)
    print(f"Found {len(product_urls)} single products after URL filtering.")
    
    if not product_urls:
        print("No single products to scrape after filtering.")
        return 0, 0
    
    existing_data = read_existing_data(output_file)
    existing_urls = {item['url'] for item in existing_data}
    
    # Filter out products that already exist in CSV
    new_product_urls = [url for url in product_urls if url not in existing_urls]
    print(f"Found {len(new_product_urls)} new products to scrape")
    
    if not new_product_urls:
        print("No new products to add. Exiting.")
        return 0, 0
    
    # Scrape new products with optimized function
    new_products = []
    failed_urls = []
    
    print(f"\nStarting fast scraping of {len(new_product_urls)} products...")
    start_time = time.time()
    
    for i, url in enumerate(new_product_urls, 1):
        try:
            data = extract_product_info_fast(url, category_url)
            
            # Quick secondary check
            if is_single_product(data['product_name']):
                new_products.append(data)
                print(f"[{i}/{len(new_product_urls)}] ✓ {data['brand_name']} - {data['product_name'][:50]}...")
            else:
                print(f"[{i}/{len(new_product_urls)}] ✗ Secondary filter: {data['product_name'][:50]}...")
                
        except Exception as e:
            print(f"[{i}/{len(new_product_urls)}] ✗ Failed: {e}")
            failed_urls.append(url)
        
        # Progress indicator
        if i % 10 == 0:
            elapsed = time.time() - start_time
            avg_time = elapsed / i
            remaining = avg_time * (len(new_product_urls) - i)
            print(f"  Progress: {i}/{len(new_product_urls)} | Avg: {avg_time:.1f}s/product | Est. remaining: {remaining:.0f}s")
    
    # Combine and sort data
    if new_products:
        all_data = existing_data + new_products
        write_sorted_data(all_data, output_file)
    
    elapsed_total = time.time() - start_time
    print(f"\nScraping completed in {elapsed_total:.1f} seconds")
    print(f"Successfully scraped: {len(new_products)} products")
    print(f"Failed: {len(failed_urls)} URLs")
    if failed_urls:
        print("Failed URLs saved to: failed_urls.txt")
        with open("failed_urls.txt", "w") as f:
            for url in failed_urls:
                f.write(url + "\n")
    
    return len(new_products), len(failed_urls)

def process_urls(url_list, output_file="watsons_products_simple.csv"):
    """Process a list of URLs with optimized filtering"""
    if not url_list:
        print("No URLs provided to process.")
        return
    
    print(f"\nProcessing {len(url_list)} URL(s) with OPTIMIZED filtering...")
    print("✓ Early URL filtering for combo/bundle products")
    print("✓ Faster page loading with reduced wait times")
    print("✓ Progress tracking with time estimates")
    
    total_processed = 0
    total_saved = 0
    total_failed = 0
    
    for i, url in enumerate(url_list, 1):
        print(f"\n{'='*60}")
        print(f"Processing URL {i}/{len(url_list)}: {url}")
        print(f"{'='*60}")
        
        if '/p/' in url:
            category_context = None
            for prev_url in url_list[:i-1]:
                if not '/p/' in prev_url:
                    category_context = prev_url
                    break
            
            saved, count = scrape_single_product(url, output_file, category_context)
            total_processed += 1
            if saved:
                total_saved += count
        else:
            saved_count, failed_count = scrape_category(url, output_file)
            total_saved += saved_count
            total_failed += failed_count
            total_processed += saved_count + failed_count
    
    return total_processed, total_saved, total_failed

def get_user_urls():
    """Get URLs from user input"""
    print("\n" + "="*60)
    print("WATSONS WEB SCRAPER - OPTIMIZED VERSION")
    print("="*60)
    print("FASTER SCRAPING WITH:")
    print("✓ Early filtering of combo/bundle URLs")
    print("✓ Reduced page load times")
    print("✓ Alphabetical sorting by brand & product")
    print("✓ Progress tracking with time estimates")
    print("="*60)
    
    print("\nHow would you like to input URLs?")
    print("1. Enter URLs one by line (press Enter twice when done)")
    print("2. Enter URLs separated by commas")
    print("3. Load URLs from a text file")
    choice = input("\nEnter choice (1, 2, or 3): ").strip()
    
    url_list = []
    
    if choice == "1":
        print("\nEnter URLs (one per line). Press Enter twice when done:")
        print("Example:")
        print("https://www.watsons.com.my/skincare/face-wash-cleanser/c/120101")
        print()
        
        while True:
            url = input().strip()
            if not url:
                if url_list:
                    break
                else:
                    continue
            if url.startswith(('http://', 'https://')):
                url_list.append(url)
            else:
                print(f"Skipping invalid URL: {url}")
    
    elif choice == "2":
        print("\nEnter URLs separated by commas:")
        urls_input = input("URLs: ").strip()
        if urls_input:
            url_list = [url.strip() for url in urls_input.split(',') if url.strip()]
            url_list = [url for url in url_list if url.startswith(('http://', 'https://'))]
    
    elif choice == "3":
        print("\nEnter the path to your text file (one URL per line):")
        file_path = input("File path: ").strip()
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                url_list = [line.strip() for line in f if line.strip()]
                url_list = [url for url in url_list if url.startswith(('http://', 'https://'))]
                print(f"Loaded {len(url_list)} URLs from file.")
        except FileNotFoundError:
            print(f"Error: File not found: {file_path}")
            return []
        except Exception as e:
            print(f"Error reading file: {e}")
            return []
    
    else:
        print("Invalid choice.")
        return []
    
    url_list = list(dict.fromkeys(url_list))
    
    if url_list:
        print(f"\nWill process {len(url_list)} unique URL(s):")
        for i, url in enumerate(url_list, 1):
            url_type = "Product" if '/p/' in url else "Category"
            category_name = extract_category_from_url(url)
            print(f"{i}. [{url_type}] [{category_name}] {url}")
        print()
        return url_list
    else:
        print("No valid URLs provided.")
        return []

# ------------------------------
# MAIN
# ------------------------------
if __name__ == "__main__":
    url_list = get_user_urls()
    
    if not url_list:
        print("No URLs to process. Exiting.")
        exit()
    
    output_file = input("Enter output CSV filename (default: watsons_products_simple.csv): ").strip()
    if not output_file:
        output_file = "watsons_products_simple.csv"
    elif not output_file.endswith('.csv'):
        output_file += '.csv'
    
    print(f"\n{'='*60}")
    print("OPTIMIZED SCRAPING STARTING")
    print("="*60)
    print(f"Processing {len(url_list)} URL(s)")
    print(f"Output: {output_file}")
    print("="*60)
    
    start_time = time.time()
    total_processed, total_saved, total_failed = process_urls(url_list, output_file)
    total_time = time.time() - start_time
    
    driver.quit()
    
    print("\n" + "="*60)
    print("FINAL SUMMARY")
    print("="*60)
    print(f"Total processing time: {total_time:.1f} seconds")
    print(f"Total URLs processed: {len(url_list)}")
    print(f"Total products saved: {total_saved}")
    print(f"Total failed/excluded: {total_failed}")
    print(f"Average time per product: {total_time/max(total_saved, 1):.2f} seconds")
    print(f"Output file: {output_file}")
    
    if total_saved > 0:
        print(f"\nPerformance: {total_saved/total_time:.1f} products/second")
    
    print("="*60)
    
    play_completion_sound()
    print("\nDone! Products are sorted alphabetically in the CSV.")