from __future__ import annotations

import importlib.util
import os
import random
import re
from copy import deepcopy
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus

if importlib.util.find_spec("requests") is not None:
    import requests
else:
    import compat_requests as requests

if importlib.util.find_spec("bs4") is not None:
    from bs4 import BeautifulSoup
else:
    from compat_bs4 import BeautifulSoup

if importlib.util.find_spec("flask") is not None:
    from flask import Flask, jsonify, request, send_from_directory
else:
    from compat_flask import Flask, jsonify, request, send_from_directory

app = Flask(__name__, static_folder=".")

BASE_DIR = Path(__file__).resolve().parent
PLATFORMS: list[dict[str, Any]] = [
    {
        "name": "Amazon",
        "domain": "amazon.in",
        "accent": "#ff9900",
        "search_url": "https://www.amazon.in/s?k={query}",
    },
    {
        "name": "Flipkart",
        "domain": "flipkart.com",
        "accent": "#2874f0",
        "search_url": "https://www.flipkart.com/search?q={query}",
    },
    {
        "name": "Meesho",
        "domain": "meesho.com",
        "accent": "#f43397",
        "search_url": "https://www.meesho.com/search?q={query}",
    },
    {
        "name": "Myntra",
        "domain": "myntra.com",
        "accent": "#ff3f6c",
        "search_url": "https://www.myntra.com/{query}",
    },
]

CATALOG_SEEDS: list[dict[str, Any]] = [
    {
        "product": "iPhone 15 128GB",
        "category": "Phones",
        "keywords": ["iphone 15", "apple phone", "128gb"],
        "base_price": 79999,
        "image": "https://images.unsplash.com/photo-1695048133142-1a20484d2569?auto=format&fit=crop&w=900&q=80",
        "reviews": [
            "Premium feel and cameras are excellent.",
            "Battery easily lasts a full day.",
            "A smooth upgrade for Apple users.",
        ],
    },
    {
        "product": "Samsung Galaxy S24",
        "category": "Phones",
        "keywords": ["samsung s24", "galaxy phone"],
        "base_price": 68999,
        "image": "https://images.unsplash.com/photo-1610945265064-0e34e5519bbf?auto=format&fit=crop&w=900&q=80",
        "reviews": [
            "Bright display and fast performance.",
            "AI features are surprisingly useful.",
            "Camera handles low light very well.",
        ],
    },
    {
        "product": "OnePlus 12R",
        "category": "Phones",
        "keywords": ["oneplus 12r", "oneplus phone"],
        "base_price": 39999,
        "image": "https://images.unsplash.com/photo-1598327105666-5b89351aff97?auto=format&fit=crop&w=900&q=80",
        "reviews": [
            "Fast charging is super convenient.",
            "Gaming performance is rock solid.",
            "Feels flagship-like for the price.",
        ],
    },
    {
        "product": "Nothing Phone 2",
        "category": "Phones",
        "keywords": ["nothing phone", "glyph"],
        "base_price": 37999,
        "image": "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?auto=format&fit=crop&w=900&q=80",
        "reviews": [
            "Unique design stands out instantly.",
            "Clean Android experience is a plus.",
            "Good balance of style and speed.",
        ],
    },
    {
        "product": "Redmi Note 13 Pro",
        "category": "Phones",
        "keywords": ["redmi note", "xiaomi phone"],
        "base_price": 25999,
        "image": "https://images.unsplash.com/photo-1580910051074-3eb694886505?auto=format&fit=crop&w=900&q=80",
        "reviews": [
            "Sharp display and loud speakers.",
            "Camera is good for everyday shots.",
            "Excellent value for students.",
        ],
    },
    {
        "product": "Realme Narzo 70",
        "category": "Phones",
        "keywords": ["realme narzo", "budget phone"],
        "base_price": 16999,
        "image": "https://images.unsplash.com/photo-1603899122634-f086ca5f5ddd?auto=format&fit=crop&w=900&q=80",
        "reviews": [
            "Battery backup is seriously good.",
            "Looks stylish despite the price.",
            "Great starter phone for daily use.",
        ],
    },
    {
        "product": "Samsung Buds FE",
        "category": "Audio",
        "keywords": ["samsung earbuds", "buds fe"],
        "base_price": 6999,
        "image": "https://images.unsplash.com/photo-1606220588913-b3aacb4d2f46?auto=format&fit=crop&w=900&q=80",
        "reviews": [
            "Comfortable fit for long calls.",
            "ANC works well on commutes.",
            "Pairs instantly with Samsung phones.",
        ],
    },
    {
        "product": "Apple AirPods 3",
        "category": "Audio",
        "keywords": ["airpods", "apple earbuds"],
        "base_price": 18999,
        "image": "https://images.unsplash.com/photo-1606220945770-b5b6c2c55bf1?auto=format&fit=crop&w=900&q=80",
        "reviews": [
            "Easy pairing and spatial audio are great.",
            "Mic quality is very clear.",
            "Case is compact and easy to carry.",
        ],
    },
    {
        "product": "boAt Airdopes 141",
        "category": "Audio",
        "keywords": ["boat earbuds", "airdopes"],
        "base_price": 1499,
        "image": "https://images.unsplash.com/photo-1572536147248-ac59a8abfa4b?auto=format&fit=crop&w=900&q=80",
        "reviews": [
            "Budget-friendly and dependable.",
            "Bass is punchy for Bollywood playlists.",
            "Case feels sturdy enough for travel.",
        ],
    },
    {
        "product": "Sony WH-CH520",
        "category": "Audio",
        "keywords": ["sony headphones", "wireless headphones"],
        "base_price": 4499,
        "image": "https://images.unsplash.com/photo-1546435770-a3e426bf472b?auto=format&fit=crop&w=900&q=80",
        "reviews": [
            "Lightweight for all-day usage.",
            "Battery life is excellent.",
            "Balanced sound without harsh treble.",
        ],
    },
    {
        "product": "JBL Tune 770NC",
        "category": "Audio",
        "keywords": ["jbl headphones", "noise cancelling"],
        "base_price": 6499,
        "image": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=900&q=80",
        "reviews": [
            "Noise cancellation is effective indoors.",
            "Good app controls for EQ tweaks.",
            "Cushions stay comfortable over time.",
        ],
    },
    {
        "product": "Noise ColorFit Pro 5",
        "category": "Wearables",
        "keywords": ["smartwatch", "noise watch"],
        "base_price": 3999,
        "image": "https://images.unsplash.com/photo-1546868871-7041f2a55e12?auto=format&fit=crop&w=900&q=80",
        "reviews": [
            "Bright screen and useful calling feature.",
            "Tracks steps reliably enough.",
            "Looks premium for the price range.",
        ],
    },
    {
        "product": "Fire-Boltt Ninja Call Pro",
        "category": "Wearables",
        "keywords": ["fire boltt", "smartwatch"],
        "base_price": 1999,
        "image": "https://images.unsplash.com/photo-1523275335684-37898b6baf30?auto=format&fit=crop&w=900&q=80",
        "reviews": [
            "Affordable and packed with features.",
            "Bluetooth calling is handy.",
            "Good option for first-time smartwatch buyers.",
        ],
    },
    {
        "product": "HP Victus Gaming Laptop",
        "category": "Laptops",
        "keywords": ["gaming laptop", "hp victus"],
        "base_price": 62999,
        "image": "https://images.unsplash.com/photo-1496181133206-80ce9b88a853?auto=format&fit=crop&w=900&q=80",
        "reviews": [
            "Handles popular games smoothly.",
            "Keyboard feels satisfying to use.",
            "Thermals stay manageable for long sessions.",
        ],
    },
    {
        "product": "Lenovo IdeaPad Slim 5",
        "category": "Laptops",
        "keywords": ["lenovo laptop", "ideapad"],
        "base_price": 57999,
        "image": "https://images.unsplash.com/photo-1517336714739-489689fd1ca8?auto=format&fit=crop&w=900&q=80",
        "reviews": [
            "Great productivity laptop for office work.",
            "Slim body is easy to travel with.",
            "Battery life is decent for hybrid work.",
        ],
    },
    {
        "product": "ASUS Vivobook 15",
        "category": "Laptops",
        "keywords": ["asus vivobook", "student laptop"],
        "base_price": 45999,
        "image": "https://images.unsplash.com/photo-1484788984921-03950022c9ef?auto=format&fit=crop&w=900&q=80",
        "reviews": [
            "Solid everyday laptop for classes.",
            "Display is pleasant for binge watching.",
            "Good keyboard for assignments.",
        ],
    },
    {
        "product": "Dell Inspiron 14",
        "category": "Laptops",
        "keywords": ["dell inspiron", "work laptop"],
        "base_price": 54999,
        "image": "https://images.unsplash.com/photo-1593642632823-8f785ba67e45?auto=format&fit=crop&w=900&q=80",
        "reviews": [
            "Reliable for routine work tasks.",
            "Build quality feels dependable.",
            "Trackpad and keyboard are comfortable.",
        ],
    },
    {
        "product": "Logitech MX Master 3S",
        "category": "Accessories",
        "keywords": ["mouse", "logitech"],
        "base_price": 8995,
        "image": "https://images.unsplash.com/photo-1527864550417-7fd91fc51a46?auto=format&fit=crop&w=900&q=80",
        "reviews": [
            "Excellent ergonomics for long workdays.",
            "Scroll wheel feels premium.",
            "Multi-device switching is seamless.",
        ],
    },
    {
        "product": "Portronics Toad Keyboard",
        "category": "Accessories",
        "keywords": ["keyboard", "portronics"],
        "base_price": 1499,
        "image": "https://images.unsplash.com/photo-1511467687858-23d96c32e4ae?auto=format&fit=crop&w=900&q=80",
        "reviews": [
            "Compact and easy to carry.",
            "Good typing feel for the price.",
            "Pairs quickly with tablets and laptops.",
        ],
    },
    {
        "product": "Amazon Kindle Paperwhite",
        "category": "Tablets",
        "keywords": ["kindle", "ebook reader"],
        "base_price": 14999,
        "image": "https://images.unsplash.com/photo-1544717305-2782549b5136?auto=format&fit=crop&w=900&q=80",
        "reviews": [
            "Perfect for readers who travel often.",
            "Display is easy on the eyes.",
            "Battery lasts for weeks, not days.",
        ],
    },
    {
        "product": "Samsung Galaxy Tab S9 FE",
        "category": "Tablets",
        "keywords": ["tablet", "samsung tab"],
        "base_price": 36999,
        "image": "https://images.unsplash.com/photo-1544244015-0df4b3ffc6b0?auto=format&fit=crop&w=900&q=80",
        "reviews": [
            "S Pen adds a lot of value.",
            "Good for notes, streaming, and study.",
            "Screen quality is excellent indoors.",
        ],
    },
    {
        "product": "Apple iPad 10th Gen",
        "category": "Tablets",
        "keywords": ["ipad", "apple tablet"],
        "base_price": 34999,
        "image": "https://images.unsplash.com/photo-1561154464-82e9adf32764?auto=format&fit=crop&w=900&q=80",
        "reviews": [
            "Smooth performance for creative apps.",
            "Display feels crisp and vibrant.",
            "Great all-round tablet for families.",
        ],
    },
    {
        "product": "Prestige Air Fryer 4.5L",
        "category": "Home",
        "keywords": ["air fryer", "kitchen"],
        "base_price": 4999,
        "image": "https://images.unsplash.com/photo-1585515656661-44f7753ef2f8?auto=format&fit=crop&w=900&q=80",
        "reviews": [
            "Makes quick snacks with less oil.",
            "Basket is easy to clean.",
            "Good pick for small families.",
        ],
    },
    {
        "product": "Philips Mixer Grinder",
        "category": "Home",
        "keywords": ["mixer grinder", "kitchen appliance"],
        "base_price": 3299,
        "image": "https://images.unsplash.com/photo-1570222094114-d054a817e56b?auto=format&fit=crop&w=900&q=80",
        "reviews": [
            "Powerful enough for chutneys and masalas.",
            "Jars feel durable.",
            "Useful staple for Indian kitchens.",
        ],
    },
    {
        "product": "Milton Thermosteel Bottle",
        "category": "Home",
        "keywords": ["water bottle", "milton"],
        "base_price": 799,
        "image": "https://images.unsplash.com/photo-1602143407151-7111542de6e8?auto=format&fit=crop&w=900&q=80",
        "reviews": [
            "Keeps water cold for long hours.",
            "Leak-proof lid is reliable.",
            "Easy to carry to office or school.",
        ],
    },
    {
        "product": "Puma Running Shoes",
        "category": "Fashion",
        "keywords": ["shoes", "puma"],
        "base_price": 2999,
        "image": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=900&q=80",
        "reviews": [
            "Comfortable cushioning for daily walks.",
            "Looks sporty and stylish.",
            "Good grip on regular roads.",
        ],
    },
    {
        "product": "Adidas Essentials T-Shirt",
        "category": "Fashion",
        "keywords": ["tshirt", "adidas"],
        "base_price": 1299,
        "image": "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?auto=format&fit=crop&w=900&q=80",
        "reviews": [
            "Fabric feels breathable in summer.",
            "Simple styling works with jeans.",
            "Fit is consistent and comfortable.",
        ],
    },
    {
        "product": "Levis Slim Fit Jeans",
        "category": "Fashion",
        "keywords": ["jeans", "levis"],
        "base_price": 2499,
        "image": "https://images.unsplash.com/photo-1541099649105-f69ad21f3246?auto=format&fit=crop&w=900&q=80",
        "reviews": [
            "Classic fit that works for daily wear.",
            "Denim quality feels premium.",
            "Stitching and finish are impressive.",
        ],
    },
    {
        "product": "Myntra Kurta Set",
        "category": "Fashion",
        "keywords": ["kurta", "ethnic wear"],
        "base_price": 1899,
        "image": "https://images.unsplash.com/photo-1617137968427-85924c800a22?auto=format&fit=crop&w=900&q=80",
        "reviews": [
            "Great festive look for the price.",
            "Fabric and print look elegant.",
            "Comfortable for family functions.",
        ],
    },
    {
        "product": "Mamaearth Vitamin C Face Wash",
        "category": "Beauty",
        "keywords": ["face wash", "skincare"],
        "base_price": 249,
        "image": "https://images.unsplash.com/photo-1556228578-8c89e6adf883?auto=format&fit=crop&w=900&q=80",
        "reviews": [
            "Leaves skin feeling fresh.",
            "Pleasant citrus fragrance.",
            "Good daily use cleanser for humid weather.",
        ],
    },
    {
        "product": "Maybelline Fit Me Foundation",
        "category": "Beauty",
        "keywords": ["foundation", "makeup"],
        "base_price": 599,
        "image": "https://images.unsplash.com/photo-1522335789203-aabd1fc54bc9?auto=format&fit=crop&w=900&q=80",
        "reviews": [
            "Blends nicely with a natural finish.",
            "Great shade range for Indian skin tones.",
            "Works well for long office days.",
        ],
    },
    {
        "product": "Lakme Eyeconic Kajal",
        "category": "Beauty",
        "keywords": ["kajal", "eyeliner"],
        "base_price": 179,
        "image": "https://images.unsplash.com/photo-1631214540242-1f7d86d88ad5?auto=format&fit=crop&w=900&q=80",
        "reviews": [
            "Easy to apply even in a hurry.",
            "Dark pigment stands out well.",
            "Popular everyday makeup essential.",
        ],
    },
    {
        "product": "Mi Smart TV 43 Inch",
        "category": "Electronics",
        "keywords": ["smart tv", "mi tv"],
        "base_price": 26999,
        "image": "https://images.unsplash.com/photo-1593784991095-a205069470b6?auto=format&fit=crop&w=900&q=80",
        "reviews": [
            "Good picture quality for OTT streaming.",
            "PatchWall offers plenty of content.",
            "Installation was quick and smooth.",
        ],
    },
    {
        "product": "Sony Bravia 55 Inch",
        "category": "Electronics",
        "keywords": ["sony tv", "4k tv"],
        "base_price": 64999,
        "image": "https://images.unsplash.com/photo-1461151304267-38535e780c79?auto=format&fit=crop&w=900&q=80",
        "reviews": [
            "Excellent picture clarity and motion.",
            "Audio is better than expected.",
            "Premium TV experience overall.",
        ],
    },
    {
        "product": "Canon EOS 1500D",
        "category": "Cameras",
        "keywords": ["camera", "canon dslr"],
        "base_price": 38999,
        "image": "https://images.unsplash.com/photo-1516035069371-29a1b244cc32?auto=format&fit=crop&w=900&q=80",
        "reviews": [
            "Great starter DSLR for learners.",
            "Image quality is crisp in daylight.",
            "Manual controls are easy to understand.",
        ],
    },
    {
        "product": "GoPro Hero 12",
        "category": "Cameras",
        "keywords": ["gopro", "action camera"],
        "base_price": 45999,
        "image": "https://images.unsplash.com/photo-1502920917128-1aa500764cbd?auto=format&fit=crop&w=900&q=80",
        "reviews": [
            "Perfect for travel and bike rides.",
            "Stabilization is seriously impressive.",
            "Video quality looks very sharp.",
        ],
    },
    {
        "product": "TP-Link Archer Router",
        "category": "Networking",
        "keywords": ["router", "wifi"],
        "base_price": 2499,
        "image": "https://images.unsplash.com/photo-1647427060118-4911c9821b82?auto=format&fit=crop&w=900&q=80",
        "reviews": [
            "Easy setup through the app.",
            "Coverage is enough for apartments.",
            "Stable connection for work and streaming.",
        ],
    },
    {
        "product": "Amazfit Bip 5",
        "category": "Wearables",
        "keywords": ["amazfit watch", "fitness watch"],
        "base_price": 5499,
        "image": "https://images.unsplash.com/photo-1508685096489-7aacd43bd3b1?auto=format&fit=crop&w=900&q=80",
        "reviews": [
            "Battery life stands out immediately.",
            "Screen is large and readable.",
            "Useful tracking for basic fitness goals.",
        ],
    },
    {
        "product": "TCL 1.5 Ton AC",
        "category": "Home",
        "keywords": ["air conditioner", "ac"],
        "base_price": 35999,
        "image": "https://images.unsplash.com/photo-1631049307264-da0ec9d70304?auto=format&fit=crop&w=900&q=80",
        "reviews": [
            "Cools room quickly even in peak summer.",
            "Remote is simple to use.",
            "Decent value compared to bigger brands.",
        ],
    },
    {
        "product": "IFB Front Load Washing Machine",
        "category": "Home",
        "keywords": ["washing machine", "ifb"],
        "base_price": 28999,
        "image": "https://images.unsplash.com/photo-1626806787461-102c1bfaaea1?auto=format&fit=crop&w=900&q=80",
        "reviews": [
            "Wash quality is noticeably good.",
            "Multiple programs cover daily laundry needs.",
            "Drum size works well for families.",
        ],
    },
    {
        "product": "Syska LED Bulb Pack",
        "category": "Home",
        "keywords": ["led bulb", "lighting"],
        "base_price": 499,
        "image": "https://images.unsplash.com/photo-1513694203232-719a280e022f?auto=format&fit=crop&w=900&q=80",
        "reviews": [
            "Simple and useful household purchase.",
            "Brightness is good for bedrooms.",
            "Energy efficient and long lasting.",
        ],
    },
    {
        "product": "Fastrack Analog Watch",
        "category": "Fashion",
        "keywords": ["watch", "fastrack"],
        "base_price": 1499,
        "image": "https://images.unsplash.com/photo-1523170335258-f5ed11844a49?auto=format&fit=crop&w=900&q=80",
        "reviews": [
            "Youthful design works with casual outfits.",
            "Dial is easy to read.",
            "Nice gifting option under budget.",
        ],
    },
    {
        "product": "American Tourister Cabin Bag",
        "category": "Travel",
        "keywords": ["luggage", "travel bag"],
        "base_price": 2799,
        "image": "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=900&q=80",
        "reviews": [
            "Rolls smoothly at airports.",
            "Storage space is practical.",
            "Sturdy shell for frequent travel.",
        ],
    },
    {
        "product": "Wildcraft Hiking Backpack",
        "category": "Travel",
        "keywords": ["backpack", "wildcraft"],
        "base_price": 2199,
        "image": "https://images.unsplash.com/photo-1500534314209-a25ddb2bd429?auto=format&fit=crop&w=900&q=80",
        "reviews": [
            "Comfortable straps for long use.",
            "Enough pockets for quick organization.",
            "Reliable choice for weekend trips.",
        ],
    },
    {
        "product": "Classmate Notebook Pack",
        "category": "Stationery",
        "keywords": ["notebook", "school supplies"],
        "base_price": 399,
        "image": "https://images.unsplash.com/photo-1517842645767-c639042777db?auto=format&fit=crop&w=900&q=80",
        "reviews": [
            "Good quality paper for everyday notes.",
            "Useful bulk pack for students.",
            "Pages feel thick and smooth enough.",
        ],
    },
    {
        "product": "Parker Vector Pen",
        "category": "Stationery",
        "keywords": ["pen", "parker"],
        "base_price": 349,
        "image": "https://images.unsplash.com/photo-1455390582262-044cdead277a?auto=format&fit=crop&w=900&q=80",
        "reviews": [
            "Classic writing instrument for gifting.",
            "Ink flow feels smooth.",
            "Looks elegant in meetings.",
        ],
    },
    {
        "product": "Nescafe Coffee Jar",
        "category": "Grocery",
        "keywords": ["coffee", "nescafe"],
        "base_price": 549,
        "image": "https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?auto=format&fit=crop&w=900&q=80",
        "reviews": [
            "Convenient daily coffee option.",
            "Aroma is pleasant and familiar.",
            "Mixes well for quick morning brews.",
        ],
    },
    {
        "product": "Saffola Gold Oil 5L",
        "category": "Grocery",
        "keywords": ["cooking oil", "saffola"],
        "base_price": 899,
        "image": "https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?auto=format&fit=crop&w=900&q=80",
        "reviews": [
            "Trusted cooking staple for households.",
            "Large pack lasts a long time.",
            "Often available with good discounts.",
        ],
    },
    {
        "product": "Cadbury Celebration Pack",
        "category": "Grocery",
        "keywords": ["chocolate gift", "cadbury"],
        "base_price": 399,
        "image": "https://images.unsplash.com/photo-1511381939415-e44015466834?auto=format&fit=crop&w=900&q=80",
        "reviews": [
            "Popular festive gifting choice.",
            "Nice assortment for sharing.",
            "Packaging looks cheerful and premium enough.",
        ],
    },
    {
        "product": "Yoga Mat 6mm",
        "category": "Fitness",
        "keywords": ["yoga mat", "exercise"],
        "base_price": 999,
        "image": "https://images.unsplash.com/photo-1518611012118-696072aa579a?auto=format&fit=crop&w=900&q=80",
        "reviews": [
            "Good grip for home workouts.",
            "Thickness feels comfortable on knees.",
            "Easy to roll and store away.",
        ],
    },
    {
        "product": "Boldfit Resistance Bands",
        "category": "Fitness",
        "keywords": ["resistance bands", "workout"],
        "base_price": 799,
        "image": "https://images.unsplash.com/photo-1517836357463-d25dfeac3438?auto=format&fit=crop&w=900&q=80",
        "reviews": [
            "Useful for quick strength sessions.",
            "Multiple resistance levels help progression.",
            "Compact enough to carry while traveling.",
        ],
    },
]


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def format_inr(value: int | float) -> str:
    return f"₹{int(round(value)):,}"


def generate_mock_catalog() -> dict[str, list[dict[str, Any]]]:
    catalog: dict[str, list[dict[str, Any]]] = {}
    platform_bias = {"Amazon": 0.03, "Flipkart": -0.02, "Meesho": -0.06, "Myntra": 0.01}

    for seed in CATALOG_SEEDS:
        query_key = slugify(seed["product"])
        entries: list[dict[str, Any]] = []
        for index, platform in enumerate(PLATFORMS):
            rng = random.Random(f"{seed['product']}::{platform['name']}")
            price_factor = (
                1 + platform_bias[platform["name"]] + rng.uniform(-0.04, 0.05)
            )
            price = max(149, int(seed["base_price"] * price_factor))
            original = max(price + 100, int(price / (1 - rng.uniform(0.05, 0.28))))
            rating = round(min(4.9, max(3.8, rng.uniform(4.0, 4.8))), 1)
            reviews = deepcopy(seed["reviews"])
            rng.shuffle(reviews)
            entries.append(
                {
                    "platform": platform["name"],
                    "domain": platform["domain"],
                    "price": format_inr(price),
                    "price_value": price,
                    "original": format_inr(original),
                    "original_value": original,
                    "discount": f"{round((1 - price / original) * 100)}%",
                    "rating": rating,
                    "reviews": reviews[:3],
                    "url": platform["search_url"].format(
                        query=quote_plus(seed["product"])
                    ),
                    "image": seed["image"],
                    "stock": rng.random() > 0.12,
                    "category": seed["category"],
                    "badge": (
                        "LOWEST"
                        if index == 2
                        else ("TRENDING" if index == 1 else "POPULAR")
                    ),
                    "delivery": f"{rng.randint(1, 4)}-{rng.randint(4, 8)} days",
                    "seller": f"{platform['name']} Verified",
                    "source": "mock",
                    "matchedProduct": seed["product"],
                }
            )
        catalog[query_key] = sorted(entries, key=lambda item: item["price_value"])
        for term in {seed["product"], *seed["keywords"]}:
            query_key = slugify(term)
            entries: list[dict[str, Any]] = []
            for index, platform in enumerate(PLATFORMS):
                rng = random.Random(f"{seed['product']}::{platform['name']}")
                price_factor = (
                    1 + platform_bias[platform["name"]] + rng.uniform(-0.04, 0.05)
                )
                price = max(149, int(seed["base_price"] * price_factor))
                original = max(price + 100, int(price / (1 - rng.uniform(0.05, 0.28))))
                rating = round(min(4.9, max(3.8, rng.uniform(4.0, 4.8))), 1)
                reviews = deepcopy(seed["reviews"])
                rng.shuffle(reviews)
                entries.append(
                    {
                        "platform": platform["name"],
                        "domain": platform["domain"],
                        "price": format_inr(price),
                        "price_value": price,
                        "original": format_inr(original),
                        "original_value": original,
                        "discount": f"{round((1 - price / original) * 100)}%",
                        "rating": rating,
                        "reviews": reviews[:3],
                        "url": platform["search_url"].format(
                            query=quote_plus(seed["product"])
                        ),
                        "image": seed["image"],
                        "stock": rng.random() > 0.12,
                        "category": seed["category"],
                        "badge": (
                            "LOWEST"
                            if index == 2
                            else ("TRENDING" if index == 1 else "POPULAR")
                        ),
                        "delivery": f"{rng.randint(1, 4)}-{rng.randint(4, 8)} days",
                        "seller": f"{platform['name']} Verified",
                        "source": "mock",
                    }
                )
            catalog[query_key] = sorted(entries, key=lambda item: item["price_value"])
    return catalog


MOCK_CATALOG = generate_mock_catalog()


STOPWORDS = {"for", "with", "and", "the", "a", "an", "buy", "latest", "best", "new"}
ACCESSORY_TERMS = {
    "case",
    "cover",
    "charger",
    "cable",
    "protector",
    "glass",
    "strap",
    "skin",
    "adapter",
    "back",
}


def tokenize(value: str) -> list[str]:
    return [
        token
        for token in re.findall(r"[a-z0-9]+", value.lower())
        if token and token not in STOPWORDS
    ]


def numeric_tokens(tokens: list[str]) -> set[str]:
    return {token for token in tokens if any(char.isdigit() for char in token)}


def accessory_query(tokens: list[str]) -> bool:
    return any(token in ACCESSORY_TERMS for token in tokens)


def seed_terms(seed: dict[str, Any]) -> set[str]:
    return {
        slugify(term).replace("-", " ") for term in [seed["product"], *seed["keywords"]]
    }


def score_seed_match(product: str, seed: dict[str, Any]) -> float:
    query_norm = slugify(product).replace("-", " ")
    query_tokens = tokenize(product)
    if not query_tokens:
        return 0.0

    aliases = seed_terms(seed)
    if query_norm in aliases:
        return 1.0

    seed_product_tokens = tokenize(seed["product"])
    seed_keyword_tokens = {token for term in aliases for token in term.split()}
    overlap = len(set(query_tokens) & seed_keyword_tokens)
    overlap_ratio = overlap / max(len(set(query_tokens)), 1)
    sequence_ratio = max(
        SequenceMatcher(None, query_norm, alias).ratio() for alias in aliases
    )

    query_numbers = numeric_tokens(query_tokens)
    seed_numbers = numeric_tokens(list(seed_keyword_tokens))
    if query_numbers and not query_numbers.issubset(seed_numbers):
        return 0.0

    if accessory_query(query_tokens) and not accessory_query(seed_product_tokens):
        return 0.0

    brand_match = (
        0.2 if query_tokens and query_tokens[0] in seed_keyword_tokens else 0.0
    )
    token_bonus = 0.2 if set(query_tokens).issubset(seed_keyword_tokens) else 0.0
    return round(
        (overlap_ratio * 0.55) + (sequence_ratio * 0.25) + brand_match + token_bonus, 4
    )


def find_best_seed(product: str) -> Any:
def find_best_seed(product: str) -> tuple[dict[str, Any] | None, float]:
    best_seed: dict[str, Any] | None = None
    best_score = 0.0
    for seed in CATALOG_SEEDS:
        score = score_seed_match(product, seed)
        if score > best_score:
            best_seed = seed
            best_score = score
    return best_seed, best_score


def fallback_results(product: str) -> Any:
def fallback_results(
    product: str,
) -> tuple[list[dict[str, Any]], dict[str, Any] | None, float]:
    seed, score = find_best_seed(product)
    if not seed or score < 0.72:
        return [], None, score

    results = deepcopy(MOCK_CATALOG[slugify(seed["product"])])
    for item in results:
        item["queryMatched"] = product
        item["matchedProduct"] = seed["product"]
        item["source"] = "mock"
    return results, seed, score
def fallback_results(product: str) -> list[dict[str, Any]]:
    query = slugify(product)
    if query in MOCK_CATALOG:
        return deepcopy(MOCK_CATALOG[query])

    search_terms = set(query.split("-"))
    scored: list[tuple[int, str]] = []
    for key in MOCK_CATALOG:
        score = sum(1 for token in search_terms if token and token in key)
        if score:
            scored.append((score, key))

    if scored:
        best_key = max(scored, key=lambda item: (item[0], len(item[1])))[1]
        results = deepcopy(MOCK_CATALOG[best_key])
    else:
        results = deepcopy(next(iter(MOCK_CATALOG.values())))
        for item in results:
            item["reviews"] = [
                "Search adjusted to a comparable product.",
                *item["reviews"][:2],
            ]

    for item in results:
        item["queryMatched"] = product
        item["source"] = "mock"
    return results


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-IN,en;q=0.9",
}


def parse_price(text: str | None) -> int | None:
    if not text:
        return None
    digits = re.sub(r"[^0-9]", "", text)
    if not digits:
        return None
    return int(digits)


SCRAPE_SELECTORS: dict[str, dict[str, list[str]]] = {
    "Amazon": {
        "card": ['div[data-component-type="s-search-result"]'],
        "price": ["span.a-price-whole"],
        "title": ["h2 span"],
        "link": ["h2 a"],
    },
    "Flipkart": {
        "card": ["div[data-id]", "div._1AtVbE"],
        "price": ["div.Nx9bqj", "div._30jeq3"],
        "title": ["div.KzDlHZ", "a.s1Q9rs", "div._4rR01T"],
        "link": ["a.CGtC98", "a.s1Q9rs", "a._1fQZEK"],
    },
    "Meesho": {
        "card": ["div.sc-gKXOVf", "div.NewProductCardstyled__CardStyled-sc-6y2tys-0"],
        "price": ["h5.sc-eDvSVe", "span.sc-eDvSVe"],
        "title": [
            "p.sc-eDvSVe",
            "p.NewProductCardstyled__StyledDesktopProductTitle-sc-6y2tys-5",
        ],
        "link": ["a"],
    },
    "Myntra": {
        "card": ["li.product-base"],
        "price": ["span.product-discountedPrice", "span.product-price"],
        "title": ["h4.product-product", "h3.product-brand"],
        "link": ["a"],
    },
}


def first_text(node: BeautifulSoup, selectors: list[str]) -> str | None:
    for selector in selectors:
        found = node.select_one(selector)
        if found:
            text = found.get_text(" ", strip=True)
            if text:
                return text
    return None


def first_link(node: BeautifulSoup, selectors: list[str], base_url: str) -> str | None:
    for selector in selectors:
        found = node.select_one(selector)
        if found and found.get("href"):
            href = found["href"]
            if href.startswith("http"):
                return href
            if href.startswith("/"):
                return f"{base_url}{href}"
    return None


def title_matches_query(query: str, title: str) -> bool:
    query_tokens = tokenize(query)
    title_tokens = set(tokenize(title))
    if not query_tokens or not title_tokens:
        return False

    query_numbers = numeric_tokens(query_tokens)
    if query_numbers and not query_numbers.issubset(title_tokens):
        return False

    if accessory_query(query_tokens) != accessory_query(list(title_tokens)):
        return False

    overlap = len(set(query_tokens) & title_tokens)
    overlap_ratio = overlap / max(len(set(query_tokens)), 1)
    phrase_ratio = SequenceMatcher(
        None, slugify(query).replace("-", " "), slugify(title).replace("-", " ")
    ).ratio()
    return overlap_ratio >= 0.65 or (overlap_ratio >= 0.5 and phrase_ratio >= 0.7)


def scrape_platform(
    platform: dict[str, Any], product: str, fallback_image: str
) -> dict[str, Any] | None:
def scrape_platform(platform: dict[str, Any], product: str) -> dict[str, Any] | None:
    selectors = SCRAPE_SELECTORS.get(platform["name"])
    if not selectors:
        return None

    base_url = f"https://{platform['domain']}"
    url = platform["search_url"].format(query=quote_plus(product))
    response = requests.get(url, headers=HEADERS, timeout=6)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    cards: list[Any] = []
    for selector in selectors["card"]:
        cards = soup.select(selector)
        if cards:
            break
    if not cards:
        return None

    for card in cards[:10]:
        title = first_text(card, selectors["title"])
        price_value = parse_price(first_text(card, selectors["price"]))
        link = first_link(card, selectors["link"], base_url)
        if not title or not price_value or not link:
            continue
        if not title_matches_query(product, title):
            continue

        rating_seed = random.Random(f"scrape::{platform['name']}::{title}")
        original_value = int(price_value / (1 - rating_seed.uniform(0.05, 0.2)))
        return {
            "platform": platform["name"],
            "domain": platform["domain"],
            "price": format_inr(price_value),
            "price_value": price_value,
            "original": format_inr(original_value),
            "original_value": original_value,
            "discount": f"{round((1 - price_value / original_value) * 100)}%",
            "rating": round(rating_seed.uniform(4.0, 4.6), 1),
            "reviews": [
                f"Live listing detected on {platform['name']}.",
                "Review snippets unavailable in scraper mode.",
                "Use the Buy Now link to verify latest seller details.",
            ],
            "url": link,
            "image": fallback_image,
            "image": fallback_results(product)[0]["image"],
            "stock": True,
            "category": "Live result",
            "badge": "LIVE",
            "delivery": "Check on platform",
            "seller": f"{platform['name']} marketplace",
            "source": "scraped",
            "title": title,
        }
    return None


def compare_product(product: str, sort_by: str = "price_asc") -> Any:
def compare_product(
    product: str, sort_by: str = "price_asc"
) -> tuple[list[dict[str, Any]], list[str], str | None, float]:
    base_results, matched_seed, confidence = fallback_results(product)
    notices: list[str] = []
    if not matched_seed:
        notices.append(
            "No confident product match was found in the offline catalog. Please refine the model name, capacity, size, or variant."
        )
        return [], notices, None, confidence

    fallback_image = matched_seed["image"]

    for idx, platform in enumerate(PLATFORMS):
        try:
            scraped = scrape_platform(platform, product, fallback_image)
            if scraped:
                base_results[idx] = scraped
                notices.append(f"Live price refreshed for {platform['name']}.")
            else:
                notices.append(
                    f"{platform['name']} did not return a confident match for the exact requested product, so curated pricing is shown."
                )
) -> tuple[list[dict[str, Any]], list[str]]:
    base_results = fallback_results(product)
    notices: list[str] = []

    for idx, platform in enumerate(PLATFORMS):
        try:
            scraped = scrape_platform(platform, product)
            if scraped:
                base_results[idx] = scraped
                notices.append(f"Live price refreshed for {platform['name']}.")
        except Exception:
            notices.append(
                f"{platform['name']} live scrape unavailable, showing curated mock data."
            )

    reverse = sort_by == "price_desc"
    base_results = sorted(
        base_results, key=lambda item: item["price_value"], reverse=reverse
    )
    if base_results:
        lowest = min(base_results, key=lambda item: item["price_value"])["price_value"]
        for item in base_results:
            if item["price_value"] == lowest:
                item["badge"] = "LOWEST"
    return base_results, notices, matched_seed["product"], confidence
    return base_results, notices


@app.get("/")
def index() -> Any:
    return send_from_directory(BASE_DIR, "index.html")


@app.get("/api/products")
def api_products() -> Any:
    samples = [seed["product"] for seed in CATALOG_SEEDS[:12]]
    return jsonify({"products": samples, "total": len(CATALOG_SEEDS)})
    return jsonify({"products": samples, "total": len(MOCK_CATALOG)})


@app.post("/api/compare")
def api_compare() -> Any:
    payload = request.get_json(silent=True) or {}
    product = str(payload.get("product", "")).strip()
    sort_by = str(payload.get("sort", "price_asc")).strip() or "price_asc"

    if len(product) < 2:
        return (
            jsonify({"error": "Please enter at least 2 characters to compare prices."}),
            400,
        )

    results, notices, matched_product, confidence = compare_product(product, sort_by)
    return jsonify(
        {
            "product": product,
            "matchedProduct": matched_product,
            "matchConfidence": confidence,
    results, notices = compare_product(product, sort_by)
    return jsonify(
        {
            "product": product,
            "sort": sort_by,
            "count": len(results),
            "results": results,
            "notices": notices,
            "offlineReady": True,
        }
    )


@app.get("/health")
def health() -> Any:
    return jsonify({"status": "ok", "products": len(MOCK_CATALOG)})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
