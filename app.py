import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import statistics

st.set_page_config(page_title="FlipIT", layout="wide")

# Initialize favorites in session state if not already
if "favorites" not in st.session_state:
    st.session_state.favorites = []

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

        if title_tag and price_tag and link_tag:
            title = title_tag.text.strip()
            if "Shop on eBay" in title:
                continue

            price = extract_first_price(price_tag.text)
            if price:
                listings.append({
                    "title": title,
                    "price": price,
                    "url": link_tag["href"]
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
        img_tag = item.select_one(".s-item__image-img")

        if title_tag and price_tag and link_tag:
            title = title_tag.text.strip()
            if "Shop on eBay" in title:
                continue

            price = extract_first_price(price_tag.text)
            img_url = img_tag["src"] if img_tag else ""

            if price:
                listings.append({
                    "title": title,
                    "price": price,
                    "url": link_tag["href"],
                    "img": img_url
                })

    return listings

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

        filtered_current = [item for item in current_listings if item["price"] <= 0.85 * avg_price]
        sketchy_listings = [
            item for item in current_listings
            if item not in filtered_current and "case" not in item["title"].lower()
            and "shell" not in item["title"].lower()
            and "part" not in item["title"].lower()
            and "Shop on eBay" not in item["title"]
        ]

        # Add flip scores
        for item in filtered_current + sketchy_listings:
            item["flip_score"] = round(100 * (avg_price - item["price"]) / avg_price, 2)

        # Add sorting dropdown
        sort_option = st.selectbox("📊 Sort listings by:", ["Flip Score (High → Low)", "Price (Low → High)", "Price (High → Low)"])

        def sort_listings(listings):
            if sort_option == "Flip Score (High → Low)":
                return sorted(listings, key=lambda x: x["flip_score"], reverse=True)
            elif sort_option == "Price (Low → High)":
                return sorted(listings, key=lambda x: x["price"])
            elif sort_option == "Price (High → Low)":
                return sorted(listings, key=lambda x: x["price"], reverse=True)
            return listings

        # Include sketchy listings toggle
        include_sketchy = st.checkbox("Include Sketchy Listings", value=True)

        if filtered_current:
            st.subheader(f"🟢 Current Listings Under 85% of Average Price for '{search_query}'")
            for item in sort_listings(filtered_current):
                color = "green" if item["flip_score"] > 50 else ("orange" if item["flip_score"] > 30 else "gray")
                st.image(item["img"], width=100)
                st.markdown(f"**{item['title']}** — ${item['price']}  ")
                st.markdown(f"[🔗 View Listing]({item['url']})  ")
                st.markdown(f"<span style='color:{color}'>🔥 Flip Score: {item['flip_score']}%</span>", unsafe_allow_html=True)
                if st.button(f"💾 Save to Favorites — {item['title']}"):
                    st.session_state.favorites.append(item)

        if include_sketchy and sketchy_listings:
            st.subheader("⚠️ Sketchy Listings (Might Still Be Useful)")
            for item in sort_listings(sketchy_listings):
                color = "green" if item["flip_score"] > 50 else ("orange" if item["flip_score"] > 30 else "gray")
                st.image(item["img"], width=100)
                st.markdown(f"*{item['title']}* — ${item['price']}  ")
                st.markdown(f"[Are you sure? 🔗]({item['url']})")
                st.markdown(f"<span style='color:{color}'>🔥 Flip Score: {item['flip_score']}%</span>", unsafe_allow_html=True)
                if st.button(f"💾 Save to Favorites — {item['title']}"):
                    st.session_state.favorites.append(item)

        if st.session_state.favorites:
            st.subheader("⭐ Favorites")
            for item in st.session_state.favorites:
                st.markdown(f"- **{item['title']}** — ${item['price']} [🔗 View Listing]({item['url']})")
    else:
        st.error("No sold listings found. Try another search term.")


