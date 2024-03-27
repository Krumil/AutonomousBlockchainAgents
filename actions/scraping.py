from seleniumbase import Driver

# import undetected_chromedriver as uc
import time


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
    # driver = uc.Chrome(headless=False, use_subprocess=False, version_main=121)
    driver.execute_script(f"""window.open("{url}","_blank");""")  # open page in new tab
    time.sleep(5)  # wait until page has loaded
    driver.switch_to.window(window_name=driver.window_handles[0])  # switch to first tab
    driver.close()  # close first tab
    driver.switch_to.window(
        window_name=driver.window_handles[0]
    )  # switch back to new tab
    time.sleep(2)
    driver.get("https://google.com")
    time.sleep(2)
    driver.get(url)
    time.sleep(5)
    driver.save_screenshot(image_path)
    driver.quit()
    return True


def scrape_dexscreener():
    url = "https://dexscreener.com/solana"
    scrape_site(url, image_path="dexscreener.png")
    return True


# main to scrape the site
if __name__ == "__main__":
    scrape_dexscreener()
