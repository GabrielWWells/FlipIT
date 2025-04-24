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

        def flip_score(price):
            score = max(0, min(100, round((1 - (price / avg_price)) * 100)))
            return score

        if filtered_current:
            st.subheader(f"🟢 Current Listings Under 85% of Average Price for '{search_query}'")
            for item in filtered_current:
                col1, col2 = st.columns([1, 4])
                with col1:
                    if item['image']:
                        st.image(item['image'], width=90)
                with col2:
                    st.markdown(f"**{item['title']}** — ${item['price']}  \n"
                                f"[🔗 View Listing]({item['url']})  \n"
                                f"📈 **Flip Score**: {flip_score(item['price'])}/100")

        include_sketchy = st.checkbox("Include sketchy listings")
        if include_sketchy and sketchy_listings:
            st.subheader("⚠️ Sketchy Listings (Might Still Be Useful)")
            for item in sketchy_listings:
                col1, col2 = st.columns([1, 4])
                with col1:
                    if item['image']:
                        st.image(item['image'], width=90)
                with col2:
                    st.markdown(f"*{item['title']}* — ${item['price']}  \n"
                                f"[Are you sure? 🔗]({item['url']})  \n"
                                f"📈 Flip Score: {flip_score(item['price'])}/100", unsafe_allow_html=True)
    else:
        st.error("No sold listings found. Try another search term.")
