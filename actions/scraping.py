from seleniumbase import Driver


def scrape_site(url, image_path="screenshot.png"):
    driver = Driver(
        browser="chrome",
        uc=True,
        headless2=True,
        incognito=True,
        agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.3",
        do_not_track=True,
        undetectable=True,
    )
    driver.get(url)
    driver.sleep(5)
    driver.save_screenshot(image_path)
    return True


def scrape_dexscreener():
    url = "https://dexscreener.com/solana"
    scrape_site(url, image_path="dexscreener.png")
    return True
