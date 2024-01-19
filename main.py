import json
from fastapi import FastAPI, HTTPException

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

app = FastAPI()
GOOGLE_CHROME_PATH = '/app/.apt/usr/bin/google_chrome'
CHROMEDRIVER_PATH = '/app/.chromedriver/bin/chromedriver'


def check_price(domains):
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--headless')
    chrome_options.binary_location = GOOGLE_CHROME_PATH

    driver = webdriver.Chrome(options=chrome_options)
    results = []

    try:
        opened_windows = []

        for i, domain in enumerate(domains):
            if i == 0:
                driver.get(f"https://www.namecheap.com/domains/registration/results/?domain={domain}")
            else:
                driver.execute_script(
                    f"window.open('https://www.namecheap.com/domains/registration/results/?domain={domain}', '_blank');")
            current_window = driver.window_handles[-1]
            opened_windows.append(current_window)

        for i, domain in enumerate(domains):
            driver.switch_to.window(opened_windows[i])

            try:
                WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

                section = driver.find_element(By.CLASS_NAME, "standard")
                article = WebDriverWait(section, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "article.available, article.unavailable"))
                )

                article_class = article.get_attribute("class")

                domain_status = "available" if "available" in article_class and "unavailable" not in article_class else "Domain not available"

                if domain_status == "available":
                    price = article.find_element(By.TAG_NAME, "strong").text
                else:
                    price = "unavailable"

                result = {"domain": domain, "price": price}
                results.append(result)

            except Exception as e:
                result = {"domain": domain, "price": "Domain not available"}
                results.append(result)

    finally:
        driver.quit()

    return results


@app.post("/check_price")
async def check_price_api(data: dict):
    try:
        if "domains" in data and isinstance(data["domains"], list):
            results = check_price(data["domains"])
            return results
        else:
            raise HTTPException(status_code=400, detail="Incorrect input data format in JSON.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
