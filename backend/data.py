import time
import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException, NoSuchElementException, TimeoutException

# Initialize WebDriver
driver = webdriver.Chrome()

# Open Google Maps search URL
driver.get('https://www.google.com/maps/search/restaurants+in+Johar+Town,+Lahore/')

def scroll_to_load_more():
    """Scrolls down to load more search results"""
    scrollable_div = driver.find_element(By.XPATH, '//*[@id="QA0Szd"]/div/div/div[1]/div[2]/div/div[2]')
    last_height = driver.execute_script("return arguments[0].scrollHeight", scrollable_div)

    while True:
        driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", scrollable_div)
        time.sleep(3)  # Increased wait time to ensure content loads
        
        # Click "Show more results" button if present
        try:
            show_more = driver.find_element(By.CSS_SELECTOR, "button[aria-label='Show more results']")
            driver.execute_script("arguments[0].click();", show_more)
            time.sleep(2)
        except NoSuchElementException:
            pass

        new_height = driver.execute_script("return arguments[0].scrollHeight", scrollable_div)
        if new_height == last_height:
            time.sleep(2)  # Extra wait to ensure no more content
            new_height = driver.execute_script("return arguments[0].scrollHeight", scrollable_div)
            if new_height == last_height:
                break
        last_height = new_height

try:
    # Wait for search results container
    container = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '//*[@id="QA0Szd"]/div/div/div[1]/div[2]/div/div[1]/div/div/div[1]/div[1]'))
    )

    # Scroll to load more results
    scroll_to_load_more()

    # Get all search results (using more specific selector)
    processed_names = set()  # Track processed restaurants
    search_results = container.find_elements(By.CSS_SELECTOR, "div.Nv2PK")

    # Open CSV file to store results
    with open("restaurants.csv", "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Restaurant Name", "Phone Number", "Rating", "Website Link"])

        for element in search_results:
            try:
                # Get name before processing
                try:
                    name = element.find_element(By.CSS_SELECTOR, "div.qBF1Pd").text.strip()
                except NoSuchElementException:
                    continue

                # Skip if already processed
                if not name or name in processed_names:
                    continue

                processed_names.add(name)

                # Ensure element is visible
                driver.execute_script("arguments[0].scrollIntoView();", element)
                time.sleep(1)  # Short pause for stability
                
                # Click using JavaScript
                driver.execute_script("arguments[0].click();", element)
                time.sleep(2)  # Allow details to load

                # Extract details
                phone = "N/A"
                try:
                    phone_elem = driver.find_element(By.XPATH, '//button[contains(@aria-label, "Call")]')
                    phone = phone_elem.get_attribute("aria-label").replace("Call ", "")
                except NoSuchElementException:
                    pass

                rating = "N/A"
                try:
                    rating_elem = driver.find_element(By.CLASS_NAME, "MW4etd")
                    rating = rating_elem.text
                except NoSuchElementException:
                    pass

                website = "N/A"
                try:
                    website_elem = driver.find_element(By.XPATH, '//a[contains(@aria-label, "Website")]')
                    website = website_elem.get_attribute("href")
                except NoSuchElementException:
                    pass

                # Write data to CSV
                writer.writerow([name, phone, rating, website])

            except StaleElementReferenceException:
                print("Element went stale, refetching...")
                search_results = container.find_elements(By.CSS_SELECTOR, "div.Nv2PK")  # Refetch elements
            except NoSuchElementException:
                print("Element not found, skipping...")

finally:
    driver.quit()
