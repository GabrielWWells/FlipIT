import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import statistics

st.set_page_config(page_title="FlipIT", layout="wide")

# Function to extract the first price
def extract_first_price(text):
    matches = re.findall(r"\d+\.\d{2}", text.replace(",", ""))
    return float(matches[0]) if matches else None

# Function to calculate the flip score
def flip_score(price, avg_price):
    score = max(0, min(100, round((1 - (price / avg_price)) * 100)))
    return score

# Function to fetch listings from a given category URL
def fetch_top_deals(category_url):
    response = requests.get(category_url)
    soup = BeautifulSoup(response.text, "html.parser")
    listings = []

    # Scrape top 10 listings
    for item in soup.select(".s-item")[:10]:  # Limit to top 10 results
        title_tag = item.select_one(".s-item__title")
        price_tag = item.select_one(".s-item__price")
        link_tag = item.select_one(".s-item__link")
        image_tag = item.select_one(".s-item__image-img")

        if title_tag and price_tag and link_tag:
            title = title_tag.text.strip()
            price = extract_first_price(price_tag.text)
            if price:
                listings.append({
                    "title": title,
                    "price": price,
                    "url": link_tag["href"],
                    "image": image_tag["src"] if image_tag else None
                })

    return listings

# Function to fetch top deals, filter by price, and calculate flip scores
def fetch_and_filter_deals(category_url):
    listings = fetch_top_deals(category_url)

    if not listings:
        return []

    # Calculate average price for the category listings
    avg_price = statistics.mean([item['price'] for item in listings])

    # Filter listings below 85% of average price and calculate flip score
    filtered_listings = []
    for item in listings:
        item['flip_score'] = flip_score(item['price'], avg_price)
        if item['price'] <= 0.85 * avg_price:  # Below 85% of the average price
            filtered_listings.append(item)

    # Sort by flip score in descending order (highest score first)
    sorted_listings = sorted(filtered_listings, key=lambda x: x['flip_score'], reverse=True)

    return sorted_listings[:10]  # Return the top 10 deals

# UI for Top Deals Section
categories = {
    "Motors": "https://www.ebay.com/b/Motors/6000/bn_5675",
    "Electronics": "https://www.ebay.com/b/Electronics/293/",
    "Collectables & Art": "https://www.ebay.com/b/Collectibles/1/bn_56797006",
    "Clothing, Shoes & Accessories": "https://www.ebay.com/b/Clothing-Shoes-Accessories/11450/bn_56766055",
    "Sporting Goods": "https://www.ebay.com/b/Sporting-Goods/2860/bn_56751089",
    "Toys & Hobbies": "https://www.ebay.com/b/Toys-Hobbies/2606/bn_56747636",
    "Home & Garden": "https://www.ebay.com/b/Home-Garden/11700/bn_56703287",
    "Jewelry & Watches": "https://www.ebay.com/b/Jewelry-Watches/2600/bn_56750256",
    "Books, Movies & Music": "https://www.ebay.com/b/Books-Movies-Music/11232/bn_56753416",
    "Health & Beauty": "https://www.ebay.com/b/Health-Beauty/26395/bn_56753647",
    "Business & Industrial": "https://www.ebay.com/b/Business-Industrial/12576/bn_56750391",
    "Baby Essentials": "https://www.ebay.com/b/Baby-Essentials/2994/bn_56753074",
    "Pet Supplies": "https://www.ebay.com/b/Pet-Supplies/1282/bn_56752185",
    "Others": "https://www.ebay.com/b/Others/1806/bn_56751974",
}

# Set up page
st.title("FlipIT: eBay Price Checker")

# Today's Top Deals Section
st.header("Today's Top Deals")
selected_categories = st.multiselect(
    "Select categories to view",
    options=list(categories.keys()),
    default=list(categories.keys())  # Default: show all categories
)

for category in selected_categories:
    st.subheader(f"Top Deals in {category}")
    category_url = categories[category]
    top_deals = fetch_and_filter_deals(category_url)
    
    # Display top deals for the selected category
    if top_deals:
        for item in top_deals:
            col1, col2 = st.columns([1, 3])
            with col1:
                if item["image"]:
                    st.image(item["image"], width=100)
            with col2:
                st.markdown(f"**{item['title']}** - ${item['price']}  \n[🔗 View Listing]({item['url']})")
    else:
        st.write("No top deals found.")

# Search Functionality (same as before)
search_query = st.text_input("🔍 Enter a product name to search:")

if search_query:
    sold_listings = scrape_ebay_sold(search_query)
    current_listings = scrape_ebay_current(search_query)

    if sold_listings:
        sold_prices = [item["price"] for item in sold_listings]
        avg_price = round(statistics.mean(sold_prices), 2)
        st.success(f"Average Sold Price for '{search_query}': ${avg_price}")

        # Assign flip score to each listing
        for item in current_listings:
            item["flip_score"] = flip_score(item["price"], avg_price)

        # Sliders for price filtering
        prices = [item["price"] for item in current_listings]
        min_price, max_price = st.slider("💸 Filter by Price Range ($)", min_value=float(min(prices)), max_value=float(max(prices)), value=(float(min(prices)), float(max(prices))))

        # Filter current listings
        filtered_current = [item for item in current_listings if item["price"] <= 0.85 * avg_price and min_price <= item["price"] <= max_price]

        # Sort by flip score
        filtered_current = sorted(filtered_current, key=lambda x: x["flip_score"], reverse=True)

        sketchy_listings = [
            item for item in current_listings
            if item not in filtered_current and "case" not in item["title"].lower()
            and "shell" not in item["title"].lower()
            and "part" not in item["title"].lower()
            and "Shop on eBay" not in item["title"]
            and min_price <= item["price"] <= max_price
        ]
        sketchy_listings = sorted(sketchy_listings, key=lambda x: x["flip_score"], reverse=True)

        if filtered_current:
            st.subheader(f"🟢 Current Listings Under 85% of Average Price for '{search_query}'")
            for item in filtered_current:
                col1, col2 = st.columns([1, 4])
                with col1:
                    if item['image']:
                        st.image(item['image'], width=90)
                with col2:
                    color = flip_color(item["flip_score"])
                    st.markdown(f"**{item['title']}** — ${item['price']}  \n"
                                f"[🔗 View Listing]({item['url']})  \n"
                                f"<span style='color:{color}'>📈 Flip Score: {item['flip_score']}/100</span>",
                                unsafe_allow_html=True)

        include_sketchy = st.checkbox("Include sketchy listings")
        if include_sketchy and sketchy_listings:
            st.subheader("⚠️ Sketchy Listings (Might Still Be Useful)")
            for item in sketchy_listings:
                col1, col2 = st.columns([1, 4])
                with col1:
                    if item['image']:
                        st.image(item['image'], width=90)
                with col2:
                    color = flip_color(item["flip_score"])
                    st.markdown(f"*{item['title']}* — ${item['price']}  \n"
                                f"[Are you sure? 🔗]({item['url']})  \n"
                                f"<span style='color:{color}'>📈 Flip Score: {item['flip_score']}/100</span>",
                                unsafe_allow_html=True)
    else:
        st.error("No sold listings found. Try another search term.")

