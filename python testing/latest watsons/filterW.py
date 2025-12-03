import pandas as pd
import os

def read_csv_with_encoding(file_path):
    """Try to read a CSV file with multiple encodings"""
    encodings_to_try = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1', 'utf-16', 'utf-16-le']
    
    for encoding in encodings_to_try:
        try:
            df = pd.read_csv(file_path, encoding=encoding, on_bad_lines='warn')
            print(f"✓ Successfully read {os.path.basename(file_path)} with {encoding} encoding")
            return df
        except UnicodeDecodeError:
            continue
        except Exception as e:
            continue
    
    # If all encodings fail, try with error handling
    try:
        df = pd.read_csv(file_path, encoding='utf-8', on_bad_lines='skip', encoding_errors='replace')
        print(f"✓ Read {os.path.basename(file_path)} with error replacement")
        return df
    except Exception as e:
        print(f"✗ Failed to read {os.path.basename(file_path)}: {e}")
        return None

def remove_taken_products():
    """
    Remove products from watsons_products_simple.csv that are already in brandlist.csv
    """
    
    print("=" * 70)
    print("WATSONS PRODUCT FILTER")
    print("=" * 70)
    
    # Check current directory
    print(f"\nCurrent directory: {os.getcwd()}")
    print("Files found:")
    for file in sorted(os.listdir()):
        if file.endswith('.csv'):
            print(f"  • {file}")
    
    print("\nReading CSV files...")
    
    # Check if files exist
    if not os.path.exists('watsons_products_simple.csv'):
        print("\n❌ ERROR: watsons_products_simple.csv not found!")
        print("Please make sure the file is in the current directory.")
        print("\nLooking for similar files...")
        csv_files = [f for f in os.listdir() if 'watsons' in f.lower() and f.endswith('.csv')]
        if csv_files:
            print(f"Found these files: {csv_files}")
            print("Please rename one of them to 'watsons_products_simple.csv'")
        return
    
    if not os.path.exists('brandlist.csv'):
        print("\n❌ ERROR: brandlist.csv not found!")
        print("Please make sure the file is in the current directory.")
        print("\nLooking for similar files...")
        csv_files = [f for f in os.listdir() if 'brand' in f.lower() and f.endswith('.csv')]
        if csv_files:
            print(f"Found these files: {csv_files}")
            print("Please rename one of them to 'brandlist.csv'")
        return
    
    # Read files with encoding detection
    watsons_df = read_csv_with_encoding('watsons_products_simple.csv')
    if watsons_df is None:
        return
        
    brandlist_df = read_csv_with_encoding('brandlist.csv')
    if brandlist_df is None:
        return
    
    # Clean column names (remove whitespace)
    watsons_df.columns = watsons_df.columns.str.strip()
    brandlist_df.columns = brandlist_df.columns.str.strip()
    
    print(f"\n" + "="*70)
    print(f"FILE INFORMATION")
    print(f"="*70)
    print(f"Watsons products (to check): {len(watsons_df)} products")
    print(f"Brandlist (already taken): {len(brandlist_df)} entries")
    
    print(f"\nWatsons columns: {watsons_df.columns.tolist()}")
    print(f"Brandlist columns: {brandlist_df.columns.tolist()}")
    
    # Display first few rows to understand structure
    print(f"\n" + "="*70)
    print(f"SAMPLE DATA FROM WATSONS FILE")
    print(f"="*70)
    if len(watsons_df) > 0:
        print(watsons_df.head(3).to_string(index=False))
    else:
        print("Watsons file is empty!")
    
    print(f"\n" + "="*70)
    print(f"SAMPLE DATA FROM BRANDLIST FILE")
    print(f"="*70)
    if len(brandlist_df) > 0:
        print(brandlist_df.head(3).to_string(index=False))
    else:
        print("Brandlist file is empty!")
    
    # Find product name column in brandlist
    print(f"\n" + "="*70)
    print(f"ANALYZING BRANDLIST STRUCTURE")
    print(f"="*70)
    
    # Common column names for product names
    common_product_columns = ['product_name', 'productName', 'product', 'name', 'product name', 
                             'item', 'description', 'Product', 'Product Name', 'PRODUCT_NAME']
    
    product_column = None
    for possible_col in common_product_columns:
        if possible_col in brandlist_df.columns:
            product_column = possible_col
            print(f"✓ Found product column: '{product_column}'")
            break
    
    if product_column is None:
        # Try to detect by content
        for col in brandlist_df.columns:
            if brandlist_df[col].astype(str).str.len().mean() > 5:  # Product names are usually longer
                product_column = col
                print(f"✓ Detected product names in column: '{product_column}' (based on content length)")
                break
    
    if product_column is None and len(brandlist_df.columns) > 0:
        # Use the last column (often contains product names)
        product_column = brandlist_df.columns[-1]
        print(f"⚠ Using last column '{product_column}' for product names")
    
    # Extract and clean taken product names
    if product_column:
        taken_products = brandlist_df[product_column].dropna().astype(str).str.strip().unique()
        print(f"\n✓ Found {len(taken_products)} unique product names in brandlist.csv")
        if len(taken_products) > 0:
            print(f"Sample of taken products:")
            for i, product in enumerate(taken_products[:5]):
                print(f"  {i+1}. {product[:80]}{'...' if len(product) > 80 else ''}")
    else:
        print("❌ ERROR: Could not identify product column in brandlist.csv!")
        return
    
    # Find brand column in brandlist
    common_brand_columns = ['brand_name', 'brandName', 'brand', 'company', 'manufacturer', 
                           'Brand', 'Brand Name', 'BRAND_NAME']
    
    brand_column = None
    for possible_col in common_brand_columns:
        if possible_col in brandlist_df.columns:
            brand_column = possible_col
            print(f"✓ Found brand column: '{brand_column}'")
            break
    
    # Check if watsons file has the expected columns
    print(f"\n" + "="*70)
    print(f"PREPARING FOR MATCHING")
    print(f"="*70)
    
    # Clean watsons data
    watsons_df = watsons_df.copy()
    
    # Ensure watsons has the required columns
    required_watsons_cols = []
    if 'product_name' in watsons_df.columns:
        watsons_df['product_name_clean'] = watsons_df['product_name'].astype(str).str.strip().str.lower()
        required_watsons_cols.append('product_name')
    elif 'Product Name' in watsons_df.columns:
        watsons_df['product_name_clean'] = watsons_df['Product Name'].astype(str).str.strip().str.lower()
        required_watsons_cols.append('Product Name')
    else:
        print("❌ ERROR: Could not find product_name column in watsons file!")
        print(f"Available columns: {watsons_df.columns.tolist()}")
        return
    
    if 'brand_name' in watsons_df.columns:
        watsons_df['brand_name_clean'] = watsons_df['brand_name'].astype(str).str.strip().str.lower()
        required_watsons_cols.append('brand_name')
    elif 'Brand Name' in watsons_df.columns:
        watsons_df['brand_name_clean'] = watsons_df['Brand Name'].astype(str).str.strip().str.lower()
        required_watsons_cols.append('Brand Name')
    
    # Clean taken products
    taken_products_clean = [str(p).strip().lower() for p in taken_products]
    
    # If brand column exists in brandlist, also match by brand
    if brand_column:
        taken_brands = brandlist_df[brand_column].dropna().astype(str).str.strip().str.lower().unique()
        print(f"✓ Found {len(taken_brands)} unique brands in brandlist.csv")
        
        # Function to check if product is taken
        def is_product_taken(row):
            clean_product = str(row['product_name_clean']).strip()
            clean_brand = str(row.get('brand_name_clean', '')).strip()
            
            # Check if brand is in taken brands
            if clean_brand and clean_brand in taken_brands:
                return True
            
            # Check if product name is similar to any taken product
            for taken in taken_products_clean:
                if taken and clean_product:
                    # Check for partial matches
                    if (taken in clean_product or clean_product in taken) and len(taken) > 3:
                        return True
            
            return False
        
        print("🔍 Matching products by brand AND product name...")
        mask = watsons_df.apply(is_product_taken, axis=1)
        
    else:
        # Function to check if product is taken (by product name only)
        def is_product_taken(product_name):
            clean_name = str(product_name).strip().lower()
            for taken in taken_products_clean:
                if taken and clean_name:
                    # Check for partial matches
                    if taken in clean_name or clean_name in taken:
                        return True
            return False
        
        print("🔍 Matching products by product name only...")
        mask = watsons_df['product_name_clean'].apply(is_product_taken)
    
    # Create filtered dataframe
    filtered_df = watsons_df[~mask].copy()
    removed_df = watsons_df[mask].copy()
    
    # Remove temporary clean columns
    columns_to_drop = ['product_name_clean', 'brand_name_clean']
    for col in columns_to_drop:
        if col in filtered_df.columns:
            filtered_df = filtered_df.drop(col, axis=1)
        if col in removed_df.columns:
            removed_df = removed_df.drop(col, axis=1)
    
    print(f"\n" + "="*70)
    print(f"RESULTS")
    print(f"="*70)
    print(f"📊 Total watsons products: {len(watsons_df)}")
    print(f"✅ Remaining products (not taken): {len(filtered_df)}")
    print(f"❌ Removed products (already taken): {len(removed_df)}")
    
    if len(removed_df) > 0:
        print(f"\n📋 Sample of removed products:")
        sample_cols = [col for col in required_watsons_cols if col in removed_df.columns]
        if sample_cols:
            print(removed_df[sample_cols].head(5).to_string(index=False))
        
        # Show brand distribution
        if 'brand_name' in removed_df.columns:
            brand_counts = removed_df['brand_name'].value_counts()
            print(f"\n🏷️ Top brands in removed products:")
            for brand, count in brand_counts.head(10).items():
                print(f"  {brand}: {count} products")
    
    # Save results
    print(f"\n" + "="*70)
    print(f"SAVING RESULTS")
    print(f"="*70)
    
    # Save filtered products
    output_file = 'watsons_products_remaining.csv'
    filtered_df.to_csv(output_file, index=False, encoding='utf-8')
    print(f"💾 Saved {len(filtered_df)} remaining products to: {output_file}")
    
    # Save removed products for reference
    if len(removed_df) > 0:
        removed_file = 'watsons_products_removed.csv'
        removed_df.to_csv(removed_file, index=False, encoding='utf-8')
        print(f"💾 Saved {len(removed_df)} removed products to: {removed_file}")
    
    # Save summary
    summary_file = 'filter_summary.txt'
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write("WATSONS PRODUCT FILTERING SUMMARY\n")
        f.write("=" * 40 + "\n\n")
        f.write(f"Date: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"\n📁 Input files:\n")
        f.write(f"  • watsons_products_simple.csv: {len(watsons_df)} products\n")
        f.write(f"  • brandlist.csv: {len(brandlist_df)} entries\n")
        f.write(f"\n📊 Results:\n")
        f.write(f"  • Products remaining: {len(filtered_df)}\n")
        f.write(f"  • Products removed: {len(removed_df)}\n")
        
        if len(removed_df) > 0:
            f.write(f"\n🗑️ Removed products by brand:\n")
            brand_counts = removed_df.get('brand_name', removed_df.get('Brand Name', pd.Series())).value_counts()
            for brand, count in brand_counts.items():
                f.write(f"  • {brand}: {count}\n")
    
    print(f"📝 Summary saved to: {summary_file}")
    
    print(f"\n" + "="*70)
    print(f"🎉 FILTERING COMPLETE!")
    print(f"="*70)
    print(f"✅ {len(filtered_df)} Watsons products remaining for photo capture")
    print(f"❌ {len(removed_df)} Watsons products already taken (removed)")
    
    # Show sample of remaining products
    if len(filtered_df) > 0:
        print(f"\n🔍 Verification (sample of remaining products):")
        sample_cols = [col for col in required_watsons_cols if col in filtered_df.columns]
        if sample_cols:
            print(filtered_df[sample_cols].head(3).to_string(index=False))
    
    print(f"\n📂 Output files created:")
    print(f"  1. {output_file} - Products to photograph")
    if len(removed_df) > 0:
        print(f"  2. {removed_file} - Products already taken")
    print(f"  3. {summary_file} - Summary report")
    
    print(f"\n" + "="*70)

if __name__ == "__main__":
    remove_taken_products()