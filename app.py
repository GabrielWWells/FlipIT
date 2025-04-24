import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import statistics

st.set_page_config(page_title="FlipIT", layout="wide")

# Session state for saved favorites
if "favorites" not in st.session_state:
    st.session_state.favorites = set()

def listing_key(item):
    return f"{item['title']}_{item['price']:.2f}"

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

        if title_tag and price_tag and link_tag:
            title = title_tag.text.strip()
            if "Shop on eBay" in title:
                continue

            price = extract_first_price(price_tag.text)
            if price:
                listings.append({
                    "title": title,
                    "price": price,
                    "url": link_tag["href"],
                    "image": image_tag["src"] if image_tag else None
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

        if title_tag and price_tag and link_tag:
            title = title_tag.text.strip()
            if "Shop on eBay" in title:
                continue

            price = extract_first_price(price_tag.text)
            if price:
                listings.append({
                    "title": title,
                    "price": price,
                    "url": link_tag["href"],
                    "image": image_tag["src"] if image_tag else None
                })

    return listings

def flip_score(price, avg_price):
    return max(0, min(100, round((1 - (price / avg_price)) * 100)))

def flip_color(score):
    if score >= 90:
        return "green"
    elif score >= 70:
        return "gold"
    elif score >= 40:
        return "orange"
    else:
        return "red"

st.title("FlipIT: eBay Price Checker")

# Favorites section at the top
with st.expander("⭐ View Favorites", expanded=False):
    if st.session_state.favorites:
        for item in st.session_state.favorites:
            col1, col2 = st.columns([1, 4])
            with col1:
                if item['image']:
                    st.image(item['image'], width=90)
            with col2:
                color = flip_color(item.get("flip_score", 50))
                st.markdown(f"**{item['title']}** — ${item['price']}  \n"
                            f"[🔗 View Listing]({item['url']})  \n"
                            f"<span style='color:{color}'>📈 Flip Score: {item.get('flip_score', 'N/A')}/100</span>",
                            unsafe_allow_html=True)
    else:
        st.info("No favorites saved yet.")

search_query = st.text_input("🔍 Enter a product name to search:")

if search_query:
    sold_listings = scrape_ebay_sold(search_query)
    current_listings = scrape_ebay_current(search_query)

    if sold_listings:
        sold_prices = [item["price"] for item in sold_listings]
        avg_price = round(statistics.mean(sold_prices), 2)
        st.success(f"Average Sold Price for '{search_query}': ${avg_price}")

        for item in current_listings:
            item["flip_score"] = flip_score(item["price"], avg_price)

        prices = [item["price"] for item in current_listings]
        min_price, max_price = st.slider("💸 Filter by Price Range ($)", min_value=float(min(prices)), max_value=float(max(prices)), value=(float(min(prices)), float(max(prices))))

        filtered_current = [item for item in current_listings if item["price"] <= 0.85 * avg_price and min_price <= item["price"] <= max_price]
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

                    key = listing_key(item)
                    already_saved = any(listing_key(fav) == key for fav in st.session_state.favorites)

                    if already_saved:
                        st.button("✅ Saved", key=f"saved_{key}", disabled=True)
                    else:
                        if st.button("💾 Save to Favorites", key=f"save_{key}"):
                            st.session_state.favorites.add(item)

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

                    key = listing_key(item)
                    already_saved = any(listing_key(fav) == key for fav in st.session_state.favorites)

                    if already_saved:
                        st.button("✅ Saved", key=f"saved_sketch_{key}", disabled=True)
                    else:
                        if st.button("💾 Save to Favorites", key=f"save_sketch_{key}"):
                            st.session_state.favorites.add(item)
    else:
        st.error("No sold listings found. Try another search term.")


