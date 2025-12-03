import pandas as pd

def remove_taken_products():
    """
    Remove products from sephora_product_all.csv that are already in brandlist.csv
    """
    
    # Read the CSV files
    print("Reading CSV files...")
    sephora_df = pd.read_csv('sephora_product_all.csv')
    brandlist_df = pd.read_csv('brandlist.csv')
    
    # Clean column names (remove whitespace)
    sephora_df.columns = sephora_df.columns.str.strip()
    brandlist_df.columns = brandlist_df.columns.str.strip()
    
    print(f"\n=== File Information ===")
    print(f"Sephora products (to check): {len(sephora_df)} products")
    print(f"Brandlist (already taken): {len(brandlist_df)} entries")
    
    print(f"\nSephora columns: {sephora_df.columns.tolist()}")
    print(f"Brandlist columns: {brandlist_df.columns.tolist()}")
    
    # Display first few rows to understand structure
    print("\nFirst 3 rows from sephora_product_all.csv:")
    print(sephora_df[['brandName', 'productName']].head(3).to_string(index=False))
    
    print("\nFirst 3 rows from brandlist.csv:")
    print(brandlist_df.head(3).to_string(index=False))
    
    # METHOD 1: Extract product names from brandlist
    # Assuming product names are in the second column (index 1)
    # Let's identify which column has product names
    print("\n" + "="*60)
    print("Analyzing brandlist.csv structure...")
    
    # Find the column with product names (longer text entries)
    product_column = None
    for col in brandlist_df.columns:
        # Check if this column contains product-like names (longer strings)
        if brandlist_df[col].astype(str).str.len().mean() > 10:  # Assuming product names are longer
            product_column = col
            print(f"Detected product names in column: '{product_column}'")
            break
    
    if product_column is None:
        # If we can't detect, use the second column
        product_column = brandlist_df.columns[1] if len(brandlist_df.columns) > 1 else brandlist_df.columns[0]
        print(f"Using column '{product_column}' for product names")
    
    # Extract and clean taken product names
    taken_products = brandlist_df[product_column].dropna().astype(str).str.strip().unique()
    print(f"\nFound {len(taken_products)} unique product names in brandlist.csv")
    print(f"Sample taken products: {taken_products[:5]}")
    
    # Clean sephora product names for matching
    sephora_df['productName_clean'] = sephora_df['productName'].astype(str).str.strip().str.lower()
    taken_products_clean = [str(p).strip().lower() for p in taken_products]
    
    # Create a function to check if product is in taken list
    def is_product_taken(product_name):
        clean_name = str(product_name).strip().lower()
        for taken in taken_products_clean:
            if taken in clean_name or clean_name in taken:
                return True
        return False
    
    # Apply the matching
    print("\n" + "="*60)
    print("Matching products...")
    
    # Find which sephora products are in the taken list
    mask = sephora_df['productName_clean'].apply(is_product_taken)
    
    # Create filtered dataframe (products NOT taken)
    filtered_df = sephora_df[~mask].copy()
    removed_df = sephora_df[mask].copy()
    
    # Remove the temporary clean column
    filtered_df = filtered_df.drop('productName_clean', axis=1)
    removed_df = removed_df.drop('productName_clean', axis=1)
    
    print(f"\n=== Results ===")
    print(f"Total sephora products: {len(sephora_df)}")
    print(f"Remaining products (not taken): {len(filtered_df)}")
    print(f"Removed products (already taken): {len(removed_df)}")
    
    if len(removed_df) > 0:
        print("\nSample of removed products:")
        print(removed_df[['brandName', 'productName']].head(10).to_string(index=False))
        
        # Show brand distribution of removed products
        brand_counts = removed_df['brandName'].value_counts()
        print(f"\nTop brands in removed products:")
        for brand, count in brand_counts.head(10).items():
            print(f"  {brand}: {count} products")
    
    # Save results
    print("\n" + "="*60)
    
    # Save filtered products
    filtered_df.to_csv('sephora_products_remaining.csv', index=False)
    print(f"✓ Saved remaining products to: sephora_products_remaining.csv")
    
    # Save removed products for reference
    if len(removed_df) > 0:
        removed_df.to_csv('sephora_products_removed.csv', index=False)
        print(f"✓ Saved removed products to: sephora_products_removed.csv")
    
    # Save a summary report
    with open('filter_summary.txt', 'w') as f:
        f.write(f"Product Filtering Summary\n")
        f.write(f"=======================\n")
        f.write(f"Date: {pd.Timestamp.now()}\n")
        f.write(f"\nInput files:\n")
        f.write(f"- sephora_product_all.csv: {len(sephora_df)} products\n")
        f.write(f"- brandlist.csv: {len(brandlist_df)} entries\n")
        f.write(f"\nResults:\n")
        f.write(f"- Products remaining: {len(filtered_df)}\n")
        f.write(f"- Products removed: {len(removed_df)}\n")
        f.write(f"\nRemoved products by brand:\n")
        for brand, count in removed_df['brandName'].value_counts().items():
            f.write(f"  {brand}: {count}\n")
    
    print(f"✓ Saved summary to: filter_summary.txt")
    
    # Show final stats
    print("\n" + "="*60)
    print("FILTERING COMPLETE!")
    print(f"• {len(filtered_df)} products remaining for photo capture")
    print(f"• {len(removed_df)} products already taken (removed)")
    
    # Quick verification
    print("\nVerification (sample of remaining products):")
    print(filtered_df[['brandName', 'productName']].head(5).to_string(index=False))

if __name__ == "__main__":
    remove_taken_products()