import streamlit as st
from bs4 import BeautifulSoup
import requests
import re  # Add for regular expressions

# Headers for requests
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
}

EXCLUDE_KEYWORDS = [
    "broken", "not working", "for parts", "repair", "no sound", 
    "empty box", "box only", "case", "charging case", "replacement", 
    "parts only", "read description", "as-is", "defective", "damaged", 
    "left only", "right only", "left ear", "right ear", "a2031", "a2032",
    "shop on ebay", "headphones", "bluetooth headset", "shop on ebay — $20.00"
]

# Function to check if a title contains excluded keywords or specific phrases
def title_is_clean(title):
    title_lower = title.lower()
    if any(keyword in title_lower for keyword in EXCLUDE_KEYWORDS):
        return False

    # Use regex to exclude "Shop on eBay — $20.00" variations
    if re.search(r"shop on ebay\s*[-—]?\s*\$?20\.00", title.lower()):
        return False

    return True

def get_sold_prices(search_term="AirPods 2nd Generation"):
    search_term = search_term.replace(" ", "+")
    url = f'https://www.ebay.com/sch/i.html?_nkw={search_term}&_sop=12&LH_Sold=1&LH_Complete=1'
    response = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(response.text, 'html.parser')

    sold_items = []
    for item in soup.select('.s-item'):
        title = item.select_one('.s-item__title')
        price = item.select_one('.s-item__price')
        if title and price and title_is_clean(title.text):
            try:
                price_text = price.text.replace('$', '').replace(',', '').split(' ')[0]
                price_float = float(price_text)
                sold_items.append((title.text.strip(), price_float))
            except ValueError:
                continue
    return sold_items

def get_current_listings(search_term="AirPods 2nd Generation"):
    search_term = search_term.replace(" ", "+")
    url = f'https://www.ebay.com/sch/i.html?_nkw={search_term}&_sop=12&LH_BIN=1'
    response = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(response.text, 'html.parser')

    clean = []
    sketchy = []
    for item in soup.select('.s-item'):
        title = item.select_one('.s-item__title')
        price = item.select_one('.s-item__price')
        if title and price:
            try:
                price_text = price.text.replace('$', '').replace(',', '').split(' ')[0]
                price_float = float(price_text)
                title_text = title.text.strip()
                # Apply the title_is_clean check to both clean and sketchy listings
                if title_is_clean(title_text):
                    clean.append((title_text, price_float))
                else:
                    # Ensure "Shop on eBay — $20.00" is excluded from the sketchy list as well
                    if not re.search(r"shop on ebay\s*[-—]?\s*\$?20\.00", title_text.lower()):
                        sketchy.append((title_text, price_float))
            except ValueError:
                continue
    return clean, sketchy

# Streamlit interface
def main():
    st.title("eBay Price Checker")

    # User input for search term
    search_term = st.text_input("Search eBay for:", "AirPods 2nd Generation")

    # Fetch sold prices for the average price calculation
    sold_items = get_sold_prices(search_term)
    if sold_items:
        avg_price = sum(price for _, price in sold_items) / len(sold_items)
        st.write(f"💰 Average Sold Price for '{search_term}': ${avg_price:.2f}")

        # Display sold items
        st.header("📦 Sold Listings")
        for title, price in sold_items[:10]:  # limit for clarity
            st.write(f"{title} — ${price:.2f}")
    else:
        st.write("No sold data found.")

    # Fetch current listings
    clean_listings, sketchy_listings = get_current_listings(search_term)

    # Show potential flips (15% off the average price)
    st.header(f"🟢 Current Listings Under 85% of Average Price for '{search_term}'")
    for title, price in clean_listings:
        if price < avg_price * 0.85:
            st.write(f"{title} — ${price:.2f} (Possible Flip!)")

    # Show sketchy listings
    st.header("⚠️ Sketchy Listings (Might Still Be Useful)")
    for title, price in sketchy_listings:
        st.write(f"{title} — ${price:.2f}")

if __name__ == "__main__":
    main()
