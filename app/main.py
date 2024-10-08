import asyncio
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from playwright.async_api import async_playwright

app = FastAPI()

origins = [
    "http://localhost:3000",
    "https://www.echub.net",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/{keyword}")
async def scrape_products(keyword: str):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        results = await asyncio.gather(
            scrape_mercari(keyword, browser),
            scrape_yahoo(keyword, browser),
            scrape_paypay_fleamarket(keyword, browser),
        )
        await browser.close()

    sorted_results = []

    # 商品の並べ替え
    max_items = max(len(r) for r in results)
    for i in range(max_items):
        for r in results:
            if i < len(r):
                sorted_results.append(r[i])

    return JSONResponse(content=sorted_results)


async def scrape_mercari(keyword: str, browser):
    url = f"https://jp.mercari.com/search?keyword={keyword}&status=on_sale"
    context = await browser.new_context()
    page = await context.new_page()
    
    await page.goto(url)

    try:
        await page.wait_for_selector("li[data-testid='item-cell']", timeout=20000)
    except Exception:
        await context.close()
        return []


    products = []

    items_list = await page.query_selector_all("li[data-testid='item-cell']")
    for item in items_list:
        a_tag = await item.query_selector("a")
        name_tag = await item.query_selector("span[data-testid='thumbnail-item-name']")
        price_tag = await item.query_selector("span[class='number__6b270ca7']")
        img_tag = await item.query_selector("img")

        if (a_tag == None or name_tag == None or price_tag == None or img_tag == None):
            break

        url = "https://jp.mercari.com" + await a_tag.get_attribute("href")
        name = await name_tag.text_content()
        price = await price_tag.text_content() + "円"
        image = await img_tag.get_attribute("src")

        products.append({"url": url, "name": name, "price": price, "image": image, "site": "メルカリ"})

    await context.close()

    return products

async def scrape_yahoo(keyword: str, browser):
    url = f"https://auctions.yahoo.co.jp/search/search?auccat=&tab_ex=commerce&ei=utf-8&aq=-1&oq=&sc_i=&fr=auc_top&p={keyword}&x=0&y=0"
    context = await browser.new_context()
    page = await context.new_page()

    await page.goto(url)

    try:
        await page.wait_for_selector("li[class='Product']", timeout=5000)
    except Exception:
        await context.close()
        return []

    products = []

    items_list = await page.query_selector_all("li[class='Product']")
    for item in items_list:
        a_tag = await item.query_selector("a")

        if (a_tag == None):
            break

        url = await a_tag.get_attribute("href")
        name = await a_tag.get_attribute("data-auction-title")
        price = await a_tag.get_attribute("data-auction-price") + "円"
        image = await a_tag.get_attribute("data-auction-img")

        products.append({"url": url, "name": name, "price": price, "image": image, "site": "ヤフオク"})

    await context.close()

    return products


async def scrape_paypay_fleamarket(keyword: str, browser):
    url = f"https://paypayfleamarket.yahoo.co.jp/search/{keyword}?page=1"
    context = await browser.new_context()
    page = await context.new_page()

    await page.goto(url)
    
    try:
        await page.wait_for_selector("a[class='sc-776687b6-0 kRccgt']", timeout=10000)
    except Exception:
        await context.close()
        return []

    products = []

    items_list = await page.query_selector_all("a[class='sc-776687b6-0 kRccgt']")
    for item in items_list:
        img_tag = await item.query_selector("img[loading='lazy']")
        price_tag = await item.query_selector("p")

        if (price_tag == None or img_tag == None):
            break

        url = "https://paypayfleamarket.yahoo.co.jp" + await item.get_attribute("href")
        name = await img_tag.get_attribute("alt")
        price = await price_tag.text_content()
        image = await img_tag.get_attribute("src")

        products.append({"url": url, "name": name, "price": price, "image": image, "site": "ペイペイフリマ"})

    await context.close()

    return products