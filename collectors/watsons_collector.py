from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
import csv
import winsound  # For Windows sound
import os

# Setup ChromeDriver
# put the location of the Chrome Driver
service = Service(r" ")
options = Options()
options.headless = True

driver = webdriver.Chrome(service=service, options=options)

def play_completion_sound():
    """Play a sound to indicate scraping is complete"""
    try:
        # Play custom sound file
        # the location of the custom sound
        sound_file = r" "
        if os.path.exists(sound_file):
            winsound.PlaySound(sound_file, winsound.SND_FILENAME)
            print("✓ Custom completion sound played!")
        else:
            # Fallback to system sound if custom file not found
            winsound.PlaySound("SystemExclamation", winsound.SND_ALIAS)
            print("✓ Fallback system sound played (custom file not found)")
    except Exception as e:
        # Fallback for non-Windows systems or if sound fails
        print("\a" * 3)  # Multiple system bells
        print(f"Scraping complete! ✓ (Sound error: {e})")

def get_all_product_links(category_url):
    driver.get(category_url)
    time.sleep(2)

    all_links = set()
    page_count = 0  # Start from 0
    
    # Extract base URL without existing query parameters
    base_url = category_url.split('?')[0]
    
    while True:
        print(f"Scraping page {page_count + 1}...")
        
        # Scroll to load all products
        last_height = driver.execute_script("return document.body.scrollHeight")
        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

        # Collect product links from current page
        elements = driver.find_elements(By.CSS_SELECTOR, "a[href*='/p/']")
        current_page_links = 0
        for el in elements:
            href = el.get_attribute("href")
            if href and href not in all_links:
                all_links.add(href)
                current_page_links += 1
        
        print(f"Found {current_page_links} new products on page {page_count + 1}")
        print(f"Total unique products so far: {len(all_links)}")

        # Stop if no products found on current page
        if current_page_links == 0:
            print("No products found on this page. Stopping pagination.")
            break

        # Try to go to next page by constructing the URL directly
        next_page_count = page_count + 1
        next_page_url = f"{base_url}?pageSize=64&currentPage={next_page_count}"
        
        # Check if next page exists by trying to load it
        driver.get(next_page_url)
        time.sleep(2)
        
        # Check if we're still on the same page (no next page) by comparing URLs
        current_url = driver.current_url
        if f"currentPage={next_page_count}" not in current_url:
            print("No more pages found. Finished scraping.")
            break
            
        page_count = next_page_count
            
        # Safety limit to prevent infinite loops
        if page_count > 50:
            print("Reached maximum page limit (50 pages)")
            break

    print(f"Total unique products found: {len(all_links)}")
    return list(all_links)

def is_single_product(product_name):
    """Check if the product is a single item (not a bundle/combo)"""
    # Indicators of multiple products in one listing
    multi_product_indicators = [
        ' combo', ' bundle', ' pack', ' set',
        ' twin', ' duo', ' pair', ' kit', ' collection'
    ]
    
    # Check for size combinations that indicate multiple products
    # Pattern: number+unit number+unit (e.g., "473ml 454g", "100ml 200ml")
    import re
    size_pattern = r'\d+\s*(ml|g|oz|l)\s+\d+\s*(ml|g|oz|l)'
    
    product_lower = product_name.lower()
    
    # Check for multi-product indicators
    for indicator in multi_product_indicators:
        if indicator in product_lower:
            return False
    
    # Check for multiple size patterns
    if re.search(size_pattern, product_lower):
        return False
    
    return True

def check_for_eczema(driver):
    """Check if the product description mentions eczema in a positive context"""
    try:
        # Get all text content from the page
        page_text = driver.find_element(By.TAG_NAME, "body").text.lower()
        
        # Comprehensive eczema-related keywords
        eczema_keywords = [
            # Medical terms
            'eczema', 'atopic dermatitis', 'dermatitis', 'contact dermatitis', 
            'seborrheic dermatitis', 'nummular eczema', 'dyshidrotic eczema',
            'neurodermatitis', 'stasis dermatitis', 'xerotic eczema',
            
            # Symptoms (more specific combinations)
            'itchy skin', 'skin itch', 'pruritus', 'skin inflammation',
            'skin rash', 'red patches', 'dry skin condition', 'flaky skin',
            'scaly skin', 'skin flaking', 'skin scaling', 'rough skin',
            'cracked skin', 'skin fissures', 'skin weeping', 'oozing skin',
            'skin crusting', 'skin blisters', 'skin bumps', 'skin irritation',
            'extremely dry skin', 'severely dry skin', 'chronically dry skin',
            'dry itchy skin',
        ]
        
        # Negative indicators (mentions that mean NOT for eczema)
        negative_indicators = [
            'do not use', 'avoid', 'not for', 'not recommended', 'warning',
            'if you have', 'consult your doctor', 'see a doctor', 'discontinue use'
        ]
        
        # Positive indicators (mentions that mean FOR eczema)
        positive_indicators = [
            'for eczema', 'treats eczema', 'eczema relief', 'eczema care',
            'eczema treatment', 'soothe eczema', 'calm eczema', 'relieve eczema',
            'manage eczema', 'eczema-prone', 'suitable for eczema', 'eczema-friendly'
        ]
        
        # Check if any eczema-related keyword appears in the text
        for keyword in eczema_keywords:
            if keyword in page_text:
                # Check context around the keyword to determine if it's positive or negative
                keyword_index = page_text.find(keyword)
                if keyword_index >= 0:
                    # Get broader context around the keyword
                    start = max(0, keyword_index - 150)
                    end = min(len(page_text), keyword_index + len(keyword) + 150)
                    context = page_text[start:end]
                    
                    # Check for explicit positive context first
                    if any(positive in context for positive in positive_indicators):
                        return "Yes"  # Explicit positive mention
                    
                    # Check for negative context
                    if any(negative in context for negative in negative_indicators):
                        return "No"  # Negative mention (warning/avoid)
                    
                    # For general mentions without clear context, check if it's in a list of conditions
                    # If it's just listed among other conditions without positive context, assume No
                    condition_indicators = ['condition', 'disease', 'disorder', 'problem', 'issue']
                    if any(indicator in context for indicator in condition_indicators):
                        return "No"  # Likely just listing conditions, not treating them
                    
                    # If no clear context but mentions symptoms, check if product description suggests treatment
                    symptom_keywords = ['itchy', 'rash', 'redness', 'dryness', 'flaky', 'scaly']
                    if any(symptom in keyword for symptom in symptom_keywords):
                        # Check if product description suggests it helps with these symptoms
                        treatment_indicators = ['relieve', 'soothe', 'calm', 'reduce', 'help with', 'improve']
                        if any(treatment in context for treatment in treatment_indicators):
                            return "Yes"
                        else:
                            return "No"  # Just mentioning symptoms without treatment context
                    
                    # Default to No for ambiguous mentions
                    return "No"
        
        return "No"
        
    except Exception as e:
        print(f"Error checking for eczema: {e}")
        return "No"

def check_for_baby(driver):
    """Check if the product description mentions it's for babies"""
    try:
        # Get all text content from the page
        page_text = driver.find_element(By.TAG_NAME, "body").text.lower()
        
        # More specific baby keywords to avoid false positives
        baby_keywords = [
            'for baby', 'for babies', 'for infant', 'for newborns',
            'baby care', 'baby skin', 'baby formula', 
            'baby shampoo', 'baby lotion', 'baby cream', 'baby oil',
            'infant care', 'newborn care', 'toddler care'
        ]
        
        # Check if any baby-related keyword appears in the text
        for keyword in baby_keywords:
            if keyword in page_text:
                return "Yes"
        
        return "No"
        
    except Exception as e:
        print(f"Error checking for baby: {e}")
        return "No"

def detect_country(driver):
    """Detect the country of origin from the product page"""
    try:
        # Method 1: Look for "Origin" heading and get the next paragraph
        headings = driver.find_elements(By.XPATH, "//h4[contains(translate(text(), 'ORIGIN', 'origin'), 'origin')]")
        
        for heading in headings:
            try:
                # Try to find the next sibling paragraph
                next_element = heading.find_element(By.XPATH, "./following-sibling::p[1]")
                country = next_element.text.strip()
                if country and len(country) < 50:  # Reasonable length for country name
                    return country
            except:
                continue
        
        # Method 2: Look for other country indicators in the page text
        page_text = driver.find_element(By.TAG_NAME, "body").text.lower()
        
        country_indicators = [
            'made in', 'product of', 'origin:', 'from', 'formulated in',
            'manufactured in', 'produced in'
        ]
        
        common_countries = [
            'usa', 'united states', 'japan', 'korea', 'south korea', 'france',
            'germany', 'united kingdom', 'uk', 'china', 'taiwan', 'malaysia',
            'thailand', 'australia', 'canada', 'italy', 'spain', 'switzerland'
        ]
        
        for indicator in country_indicators:
            if indicator in page_text:
                # Find the context around the indicator
                indicator_index = page_text.find(indicator)
                if indicator_index >= 0:
                    start = max(0, indicator_index)
                    end = min(len(page_text), indicator_index + len(indicator) + 30)
                    context = page_text[start:end]
                    
                    # Look for country names in the context
                    for country in common_countries:
                        if country in context:
                            return country.title()
        
        return ""  # Return empty string if no country found
        
    except Exception as e:
        print(f"Error detecting country: {e}")
        return ""

def detect_body_parts(driver):
    """Detect which body parts the product is used for"""
    try:
        # Get text from specific sections only (not entire page)
        page_text = ""
        
        # Try to get product description specifically (avoid footer, navigation, etc.)
        try:
            # Focus on main product content areas
            content_selectors = [
                ".product-description", 
                ".description", 
                "[class*='description']", 
                "[class*='detail']",
                ".product-details",
                ".specifications"
            ]
            
            for selector in content_selectors:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    if "footer" not in element.get_attribute("class").lower() and "nav" not in element.get_attribute("class").lower():
                        page_text += " " + element.text.lower()
        except:
            pass
        
        # Also check product usage section specifically
        try:
            usage_headings = driver.find_elements(By.XPATH, "//h4[contains(translate(text(), 'USAGE', 'usage'), 'usage') or contains(translate(text(), 'HOW TO USE', 'how to use'), 'how to use') or contains(translate(text(), 'PRODUCT USAGE', 'product usage'), 'product usage')]")
            for heading in usage_headings:
                try:
                    next_element = heading.find_element(By.XPATH, "./following-sibling::p[1]")
                    page_text += " " + next_element.text.lower()
                except:
                    pass
        except:
            pass
        
        # If no specific content found, fall back to entire page but be more careful
        if not page_text.strip():
            page_text = driver.find_element(By.TAG_NAME, "body").text.lower()
        
        # Body part keywords (skin removed)
        body_part_keywords = {
            'face': ['face', 'facial', 'forehead', 'cheek', 'chin', 'nose'],
            'body': ['body', 'bodily', 'full body', 'whole body', 'shower'],
            'hair': ['hair', 'shampoo', 'conditioner', 'scalp'],
            'neck': ['neck', 'neckline', 'decollete'],
            'arms': ['arm', 'arms', 'underarm', 'armpit'],
            'legs': ['leg', 'legs', 'thigh', 'calf'],
            'feet': ['foot', 'toes', 'sole', 'heel'],
            'lips': ['lip', 'lips', 'lip care'],
            'eye': ['eye', 'eyes', 'eyelid', 'under eye', 'eye area']
        }
        
        detected_parts = []
        
        # First priority: Check product name (most reliable)
        try:
            product_name = driver.find_element(By.CLASS_NAME, "product-name").text.lower()
            for part, keywords in body_part_keywords.items():
                for keyword in keywords:
                    if keyword in product_name:
                        if part not in detected_parts:
                            detected_parts.append(part)
                        break
        except:
            pass
        
        # For cleansing products, assume face if not specified otherwise
        if not detected_parts:
            cleansing_indicators = ['cleansing', 'cleanser', 'cleanse', 'face wash', 'facial wash', 'makeup remover', 'makeup removal']
            product_name_lower = product_name.lower() if 'product_name' in locals() else ""
            
            if any(indicator in product_name_lower for indicator in cleansing_indicators):
                if 'face' not in detected_parts:
                    detected_parts.append('face')
        
        # Second priority: Check description with context
        for part, keywords in body_part_keywords.items():
            for keyword in keywords:
                if keyword in page_text:
                    # Context checking - look for usage context but be less strict
                    keyword_index = page_text.find(keyword)
                    if keyword_index >= 0:
                        # Get context around the keyword
                        start = max(0, keyword_index - 50)
                        end = min(len(page_text), keyword_index + len(keyword) + 50)
                        context = page_text[start:end]
                        
                        # Check if it's likely to be about product usage
                        usage_indicators = ['for', 'use', 'cleanse', 'wash', 'care', 'treatment', 'apply', 'on', 'clean', 'gentle', 'remove', 'massage', 'makeup']
                        negative_indicators = ['ingredient', 'extract', 'oil', 'acid', 'chemical', 'footer', 'copyright', 'nav', 'menu']  # Avoid non-usage mentions
                        
                        # For face-related terms in cleansing context, be more lenient
                        if part == 'face' and any(indicator in context for indicator in ['cleansing', 'cleanse', 'makeup']):
                            if part not in detected_parts:
                                detected_parts.append(part)
                            break
                        # For other parts, require usage indicators AND no negative indicators
                        elif (any(indicator in context for indicator in usage_indicators) and 
                              not any(negative in context for negative in negative_indicators)):
                            if part not in detected_parts:
                                detected_parts.append(part)
                            break
        
        return ", ".join(detected_parts) if detected_parts else "Not specified"
        
    except Exception as e:
        print(f"Error detecting body parts: {e}")
        return "Not specified"

def detect_product_function(driver):
    """Detect what the product does (its function)"""
    try:
        # Get all text content from the page
        page_text = driver.find_element(By.TAG_NAME, "body").text.lower()
        
        # Product function keywords
        function_keywords = {
            'cleansing': ['cleanse', 'cleansing', 'purify', 'purifying', 'remove dirt', 'deep clean'],
            'moisturizing': ['moisturize', 'moisturizing', 'hydrate', 'hydrating', 'hydration'],
            'exfoliating': ['exfoliate', 'exfoliating', 'scrub', 'scrubbing', 'remove dead skin'],
            'rejuvenating': ['rejuvenate', 'rejuvenating', 'revitalize', 'revitalizing', 'renew'],
            'nourishing': ['nourish', 'nourishing', 'nutrient', 'nutritious', 'feed skin'],
            'brightening': ['brighten', 'brightening', 'glow', 'radiance', 'luminous'],
            'anti-aging': ['anti-aging', 'anti aging', 'wrinkle', 'fine lines', 'age spot'],
            'acne treatment': ['acne', 'pimple', 'breakout', 'blemish', 'clear skin'],
            'soothing': ['soothe', 'soothing', 'calm', 'calming', 'relieve irritation'],
            'protecting': ['protect', 'protecting', 'shield', 'defend', 'barrier'],
            'repairing': ['repair', 'repairing', 'restore', 'restoring', 'heal'],
            'firming': ['firm', 'firming', 'tighten', 'tightening', 'lift'],
            'whitening': ['whiten', 'whitening', 'lighten', 'lightening', 'even tone']
        }
        
        detected_functions = []
        for function, keywords in function_keywords.items():
            for keyword in keywords:
                if keyword in page_text:
                    if function not in detected_functions:
                        detected_functions.append(function)
                    break
        
        return ", ".join(detected_functions) if detected_functions else "Not specified"
        
    except Exception as e:
        print(f"Error detecting product function: {e}")
        return "Not specified"

def detect_category_type(product_name, driver):
    """Detect the product type/category based on name and description"""
    try:
        # Get all text content from the page
        page_text = driver.find_element(By.TAG_NAME, "body").text.lower()
        combined_text = (product_name + " " + page_text).lower()
        
        # Product type keywords and patterns
        category_types = {
            'cleanser': ['cleanser', 'cleansing', 'face wash', 'facial wash'],
            'moisturizer': ['moisturizer', 'moisturising', 'moisturizing', 'cream', 'lotion'],
            'serum': ['serum', 'essence', 'concentrate', 'ampoule'],
            'toner': ['toner', 'toning', 'freshener', 'astringent'],
            'mask': ['mask', 'masque', 'sheet mask', 'pack', 'eye mask'],
            'sunscreen': ['sunscreen', 'sunblock', 'spf', 'uv protection'],
            'treatment': ['treatment', 'treatment cream', 'spot treatment'],
            'scrub': ['scrub', 'exfoliator', 'polishing', 'gommage'],
            'oil': ['oil', 'facial oil', 'body oil', 'hair oil'],
            'gel': ['gel', 'gel cleanser', 'gel moisturizer'],
            'foam': ['foam', 'foaming', 'cleansing foam'],
            'balm': ['balm', 'ointment', 'salve'],
            'spray': ['spray', 'mist', 'aerosol'],
            'powder': ['powder', 'talc', 'dusting powder'],
            'stick': ['stick', 'roll-on', 'applicator stick'],
            'body wash': ['body wash', 'shower gel', 'body shower'],
            'shampoo': ['shampoo', 'hair wash', 'dry shampoo'],
            'conditioner': ['conditioner', 'hair conditioner'],
            'soap': ['soap', 'bar soap', 'bath soap'],
            'tonic': ['tonic', 'hair tonic', 'skin tonic']
        }
        
        # Check for matches in the combined text
        for category, keywords in category_types.items():
            for keyword in keywords:
                if keyword in combined_text:
                    return category
        
        return "Not specified"
        
    except Exception as e:
        print(f"Error detecting category type: {e}")
        return "Not specified"

def parse_product(url):
    driver.get(url)
    time.sleep(3)

    try:
        product_name = driver.find_element(By.CLASS_NAME, "product-name").text
    except:
        product_name = "N/A"

    # Check if this is a single product (not a bundle/combo)
    if not is_single_product(product_name):
        print(f"Skipping multi-product bundle: {product_name}")
        return None

    try:
        # Extract product brand
        brand_element = driver.find_element(By.CSS_SELECTOR, ".brand-group .product-brand a")
        brand_name = brand_element.text
    except:
        brand_name = "N/A"

    # Check for eczema mention
    eczema_product = check_for_eczema(driver)
    
    # Check for baby mention
    baby_product = check_for_baby(driver)
    
    # Detect country of origin
    country = detect_country(driver)
    
    # Detect body parts
    body_parts = detect_body_parts(driver)
    
    # Detect product function
    product_function = detect_product_function(driver)
    
    # Detect category type
    category_type = detect_category_type(product_name, driver)

    try:
        # IMPROVED: More flexible approach to find ingredients
        product_ingredient = "N/A"
        
        # Method 1: Look for any heading containing "ingredient" (case insensitive)
        headings = driver.find_elements(By.XPATH, "//h4[contains(translate(text(), 'INGREDIENT', 'ingredient'), 'ingredient')]")
        
        if not headings:
            # Method 2: Look for any element containing "ingredient"
            headings = driver.find_elements(By.XPATH, "//*[contains(translate(text(), 'INGREDIENT', 'ingredient'), 'ingredient')]")
        
        for heading in headings:
            try:
                # Try to find the next sibling paragraph or div
                next_element = heading.find_element(By.XPATH, "./following-sibling::p[1]")
                if next_element.text.strip():
                    product_ingredient = next_element.text
                    break
            except:
                try:
                    # Try finding next div or any following element with text
                    next_element = heading.find_element(By.XPATH, "./following-sibling::*[1]")
                    if next_element.text.strip():
                        product_ingredient = next_element.text
                        break
                except:
                    continue
        
        # Method 3: If still not found, try to find any element with ingredient information
        if product_ingredient == "N/A":
            all_elements = driver.find_elements(By.XPATH, "//*[contains(translate(text(), 'INGREDIENT', 'ingredient'), 'ingredient') or contains(translate(text(), 'COMPOSITION', 'composition'), 'composition')]")
            for element in all_elements:
                parent = element.find_element(By.XPATH, "..")
                siblings = parent.find_elements(By.XPATH, "./*")
                for sibling in siblings:
                    if sibling.text.strip() and sibling != element:
                        product_ingredient = sibling.text
                        break
                if product_ingredient != "N/A":
                    break
                    
    except Exception as e:
        print(f"Error extracting ingredients from {url}: {e}")
        product_ingredient = "N/A"

    return {
        "brandName": brand_name,
        "productName": product_name,
        "categoryType": category_type,
        "bodyParts": body_parts,
        "productFunction": product_function,
        "babyProduct": baby_product,
        "eczemaProduct": eczema_product,
        "country": country,
        "productIngredient": product_ingredient,
        "productURL": url
    }

def scrape_single_product(product_url, output_file="watsons_products.csv"):
    """Scrape a single product URL"""
    print(f"Scraping single product: {product_url}")
    
    # Check if file exists and read existing products
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
        print("No existing CSV file found. Creating new file.")
    
    # Check if product already exists
    if product_url in existing_urls:
        print("Product already exists in CSV. Skipping.")
        return
    
    # Scrape the single product
    try:
        data = parse_product(product_url)
        if data is not None:  # Only write if it's a single product (not None)
            mode = "a" if file_exists else "w"
            with open(output_file, mode, newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=[
                    "brandName", "productName", "categoryType", "bodyParts", 
                    "productFunction", "babyProduct", "eczemaProduct", 
                    "country", "productIngredient", "productURL"
                ])
                
                # Write header only if new file
                if not file_exists:
                    writer.writeheader()
                
                writer.writerow(data)
                print(f"Scraped: {data['brandName']} - {data['productName']}")
                print(f"     Category: {data['categoryType']}")
                print(f"     Body Parts: {data['bodyParts']}")
                print(f"     Function: {data['productFunction']}")
                print(f"     Baby Product: {data['babyProduct']}")
                print(f"     Eczema Product: {data['eczemaProduct']}")
                print(f"     Country: {data['country']}")
                print(f"     Ingredients: {data['productIngredient'][:50]}...")
        else:
            print("Skipped multi-product bundle")
    except Exception as e:
        print(f"Failed to scrape {product_url}: {e}")

def scrape_category(category_url, output_file="watsons_products.csv"):
    print("Getting product links from category...")
    product_urls = get_all_product_links(category_url)
    print(f"Found {len(product_urls)} products.")

    # Check if file exists and read existing products
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
        print("No existing CSV file found. Creating new file.")
    
    # Filter out products that already exist in CSV
    new_product_urls = [url for url in product_urls if url not in existing_urls]
    print(f"Found {len(new_product_urls)} new products to scrape")
    
    if not new_product_urls:
        print("No new products to add. Exiting.")
        return

    # Open file in append mode if it exists, write mode if new
    mode = "a" if file_exists else "w"
    with open(output_file, mode, newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "brandName", "productName", "categoryType", "bodyParts", 
            "productFunction", "babyProduct", "eczemaProduct", 
            "country", "productIngredient", "productURL"
        ])
        
        # Write header only if new file
        if not file_exists:
            writer.writeheader()
        
        for i, url in enumerate(new_product_urls, 1):
            try:
                data = parse_product(url)
                if data is not None:  # Only write if it's a single product (not None)
                    writer.writerow(data)
                    print(f"[{i}/{len(new_product_urls)}] Scraped: {data['brandName']} - {data['productName']}")
                    print(f"     Category: {data['categoryType']}")
                    print(f"     Body Parts: {data['bodyParts']}")
                    print(f"     Function: {data['productFunction']}")
                    print(f"     Baby Product: {data['babyProduct']}")
                    print(f"     Eczema Product: {data['eczemaProduct']}")
                    print(f"     Country: {data['country']}")
                    print(f"     Ingredients: {data['productIngredient'][:50]}...")
                else:
                    print(f"[{i}/{len(new_product_urls)}] Skipped multi-product bundle")
            except Exception as e:
                print(f"Failed to scrape {url}: {e}")

# ------------------------------
# MAIN
# ------------------------------
if __name__ == "__main__":
    # Ask user for URL
    print("Watsons Web Scraper")
    print("===================")
    print("You can enter either:")
    print("1. A category URL (e.g., https://www.watsons.com.my/face-wash-cleanser/c/120101)")
    print("2. A single product URL (e.g., https://www.watsons.com.my/product-name/p/BP_12345)")
    print()
    
    user_url = input("Please enter the URL to scrape: ").strip()
    
    # Validate URL
    if not user_url:
        print("Error: No URL provided!")
        exit()
    
    if not user_url.startswith(('http://', 'https://')):
        print("Error: Please enter a valid URL starting with http:// or https://")
        exit()
    
    print(f"Starting to scrape: {user_url}")
    print("This may take a few minutes...")
    
    # Determine if it's a category or single product
    if '/p/' in user_url:
        # Single product URL
        scrape_single_product(user_url)
    else:
        # Category URL
        scrape_category(user_url)
    
    driver.quit()
    
    # Play completion sound
    print("\n" + "="*50)
    print("SCRAPING COMPLETED SUCCESSFULLY!")
    print("="*50)
    play_completion_sound()
    print("Done scraping.")