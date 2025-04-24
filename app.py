import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import statistics

st.set_page_config(page_title="FlipIT", layout="wide")

def extract_first_price(text):
    matches = re.findall(r"\d+\.\d{2}", text.replace(",", ""))
    return float(matches[0]) if matches else None

def scrape_ebay_sold(search_term):
    url = f"https://www.ebay.com/sch/i.html?_nkw={search_term}&_sop=13&LH_Complete=1&LH_Sold=1"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    listings = []

    for item in soup.select(".s-item"):
        title_tag = item.select_one(".s-item__title")
        price_tag = item.select_one(".s-item__price")
        link_tag = item.select_one(".s-item__link")
        image_tag = item.select_one(".s-item__image-img")
        buy_it_now_tag = item.select_one(".s-item__purchase-options")
        
        if title_tag and price_tag and link_tag:
            title = title_tag.text.strip()
            if "Shop on eBay" in title:
                continue

            price = extract_first_price(price_tag.text)
            if price:
                # Check if it's a Buy It Now or Auction listing
                listing_type = "Buy It Now" if buy_it_now_tag else "Auction"

                listings.append({
                    "title": title,
                    "price": price,
                    "url": link_tag["href"],
                    "image": image_tag["src"] if image_tag else None,
                    "listing_type": listing_type
                })

    return listings

def scrape_ebay_current(search_term):
    url = f"https://www.ebay.com/sch/i.html?_nkw={search_term}&_sop=12"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    listings = []

    for item in soup.select(".s-item"):
        title_tag = item.select_one(".s-item__title")
        price_tag = item.select_one(".s-item__price")
        link_tag = item.select_one(".s-item__link")
        image_tag = item.select_one(".s-item__image-img")
        buy_it_now_tag = item.select_one(".s-item__purchase-options")
        
        if title_tag and price_tag and link_tag:
            title = title_tag.text.strip()
            if "Shop on eBay" in title:
                continue

            price = extract_first_price(price_tag.text)
            if price:
                # Check if it's a Buy It Now or Auction listing
                listing_type = "Buy It Now" if buy_it_now_tag else "Auction"

                listings.append({
                    "title": title,
                    "price": price,
                    "url": link_tag["href"],
                    "image": image_tag["src"] if image_tag else None,
                    "listing_type": listing_type
                })

    return listings

def flip_score(price, avg_price):
    score = max(0, min(100, round((1 - (price / avg_price)) * 100)))
    return score

def flip_color(score):
    if score >= 90:
        return "green"
    elif score >= 70:
        return "gold"
    elif score >= 40:
        return "orange"
    else:
        return "red"

# UI
st.title("FlipIT: eBay Price Checker")
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

        # Separate by listing type (Buy It Now vs Auction)
        buy_it_now_listings = [item for item in filtered_current if item["listing_type"] == "Buy It Now"]
        auction_listings = [item for item in filtered_current if item["listing_type"] == "Auction"]

        # Sketchy listings filtering
        sketchy_listings = [
            item for item in current_listings
            if item not in filtered_current and "case" not in item["title"].lower()
            and "shell" not in item["title"].lower()
            and "part" not in item["title"].lower()
            and "Shop on eBay" not in item["title"]
            and min_price <= item["price"] <= max_price
        ]
        sketchy_listings = sorted(sketchy_listings, key=lambda x: x["flip_score"], reverse=True)

        # Display Buy It Now Listings
        if buy_it_now_listings:
            st.subheader(f"🟢 Buy It Now Listings Under 85% of Average Price for '{search_query}'")
            for item in buy_it_now_listings:
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

        # Display Auction Listings
        if auction_listings:
            st.subheader(f"⚠️ Auction Listings Under 85% of Average Price for '{search_query}'")
            for item in auction_listings:
                col1, col2 = st.columns([1, 4])
                with col1:
                    if item['image']:
                        st.image(item['image'], width=90)
                with col2:
                    color = flip_color(item["flip_score"])
                    st.markdown(f"*{item['title']}* — ${item['price']}  \n"
                                f"[🔗 View Listing]({item['url']})  \n"
                                f"<span style='color:{color}'>📈 Flip Score: {item['flip_score']}/100</span>",
                                unsafe_allow_html=True)

        # Display Sketchy Listings
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

