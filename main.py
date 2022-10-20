import os
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
import time

SEASONS = list(range(2016, 2023))

DATA_DIR = "data2"
STANDING_DIR = os.path.join(DATA_DIR, "standings")
SCORES_DIR = os.path.join(DATA_DIR, "scores")

async def get_html(url, selector, sleep=5, retries=3):
    html = None
    for i in range(1, retries + 1):
        time.sleep(sleep * 1)

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch()
                page = await browser.new_page()
                await page.goto(url)
                print(await page.title())
                html = await page.inner_html(selector)
        except PlaywrightTimeout:
            print(f"Timeout error on {url}")
            continue
        else:
            break
    return html

async def scrape_season(season):
    url = f"https://www.basketball-reference.com/league/NBA_{season}_games.html"
    html = await get_html(url, "#content .filter")

    soup = BeautifulSoup(html)
    links = soup.find_all("a")
    href = [l["href"] for l in links]
    standings_pages = [f"https://basketball-references.com{l}" for l in href]

    for url in standings_pages:
        save_path = os.path.join(STANDING_DIR, url.split("/")[-1])
        if os.path.exists(save_path):
            continue

        html = await get_html(url, "#all_schedule")
        with open(save_path, "w+") as f:
            f.write(html)

for season in SEASONS:
    await scrape_season(season)

standings_files = os.listdir(STANDING_DIR)

async def scrape_game(standings_file):
    with open(standings_file, 'r') as f:
        html = f.read()

    soup = BeautifulSoup(html)
    links = soup.find_all("a")
    hrefs = [l.get('href') for l in links]
    box_scores = [f"https://basketball-references.com{l}" for l in hrefs if l and "boxscore" in l and '.html' in l]

    for url in box_scores:
        save_path = os.path.join(SCORES_DIR, url.split("/")[-1])
        if os.path.exists(save_path):
            continue

        html = await get_html(url, "#content")
        if not html:
            continue
        with open(save_path, "w+") as f:
            f.write(html)

    import pandas as pd

    for season in SEASONS:
        files = [s for s in standings_files if str(season) in s]

        for f in files:
            filepath = os.path.join(STANDING_DIR, f)

            await scrape_game(filepath)
