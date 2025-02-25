from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver import ActionChains
from selenium.webdriver.common.actions.wheel_input import ScrollOrigin
from selenium.common.exceptions import TimeoutException, WebDriverException
from bs4 import BeautifulSoup
import time
import pandas as pd

def initialize_driver():
    """Initialize Chrome driver with proper options"""
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(options=chrome_options)

def scroll_and_load_results(driver, scroll_pause=2, max_scroll_attempts=20):
    """
    Scrolls through the results panel until a stable number of results is reached.
    """
    try:
        action = ActionChains(driver)
        results = driver.find_elements(By.CLASS_NAME, "hfpxzc")
        attempts = 0

        while attempts < max_scroll_attempts:
            current_count = len(results)
            print(f"Found {current_count} results so far...")
            
            if current_count == 0:
                time.sleep(scroll_pause)
                results = driver.find_elements(By.CLASS_NAME, "hfpxzc")
                continue

            # Scroll to the last element
            scroll_origin = ScrollOrigin.from_element(results[-1])
            action.scroll_from_origin(scroll_origin, 0, 1000).perform()
            time.sleep(scroll_pause)
            
            try:
                new_results = driver.find_elements(By.CLASS_NAME, "hfpxzc")
                if len(new_results) == current_count:
                    attempts += 1
                else:
                    attempts = 0
                    results = new_results
            except WebDriverException:
                print("Error while scrolling, retrying...")
                time.sleep(scroll_pause)
                continue
                
        return results
    except Exception as e:
        print(f"Error in scroll_and_load_results: {str(e)}")
        return []

def main():
    filename = 'Restaurants.csv'
    data_record = []
    visited_places = []
    
    driver = initialize_driver()
    
    try:
        # Load the page
        driver.get('https://www.google.com/maps/search/restaurants+in+Lahore/@31.4572792,74.3013971,15z/data=!3m1!4b1?entry=ttu&g_ep=EgoyMDI1MDIxOS4xIKXMDSoASAFQAw%3D%3D')
        
        # Wait for initial load
        wait = WebDriverWait(driver, 20)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "hfpxzc")))
        
        # Step 1: Scroll to load results
        print("Scrolling to load all results...")
        results = scroll_and_load_results(driver)
        
        if not results:
            print("No results found!")
            return
            
        # Step 2: Scrape details
        print("Scraping restaurant details...")
        
        # Test with first 10 restaurants
        test_limit = 10
        results = results[:test_limit]
        print(f"Testing with first {test_limit} restaurants")
        
        for idx, result in enumerate(results):
            try:
                print(f"\nProcessing restaurant {idx + 1} of {test_limit}")
                
                # Click on the result and wait for details to load
                driver.execute_script("arguments[0].click();", result)
                time.sleep(2)

                # Wait for the details panel to load
                wait = WebDriverWait(driver, 10)
                
                try:
                    # Try multiple possible selectors for the name
                    name_element = wait.until(
                        EC.presence_of_element_located((
                            By.CSS_SELECTOR, 
                            "h1.DUwDvf, h1.fontHeadlineLarge, div.DUwDvf"
                        ))
                    )
                    name = name_element.text.strip()
                    print(f"Found name: {name}")
                    
                    # Get address
                    address_element = wait.until(
                        EC.presence_of_element_located((
                            By.CSS_SELECTOR, 
                            "button[data-item-id='address']"
                        ))
                    )
                    address = address_element.text.strip()
                    
                    # Get phone (if available)
                    try:
                        phone_element = wait.until(
                            EC.presence_of_element_located((
                                By.CSS_SELECTOR, 
                                "button[data-item-id*='phone']"
                            ))
                        )
                        phone = phone_element.text.strip()
                    except:
                        phone = "N/A"
                    
                    # Get rating
                    try:
                        rating_element = wait.until(
                            EC.presence_of_element_located((
                                By.CSS_SELECTOR, 
                                "div.F7nice span.ceNzKf"
                            ))
                        )
                        rating = rating_element.text.strip()
                    except:
                        rating = "N/A"
                    
                    # Get website (if available)
                    try:
                        website_element = wait.until(
                            EC.presence_of_element_located((
                                By.CSS_SELECTOR, 
                                "a[data-item-id='authority']"
                            ))
                        )
                        website = website_element.get_attribute('href')
                    except:
                        website = "N/A"
                    
                    print(f"Scraped: {name}, {phone}, {address}, {website}, Rating: {rating}")
                    data_record.append({
                        "Name": name,
                        "Phone": phone,
                        "Address": address,
                        "Website": website,
                        "Rating": rating
                    })

                except Exception as e:
                    print(f"Error extracting details: {str(e)}")
                    continue

                # Go back to results
                back_button = wait.until(
                    EC.element_to_be_clickable((
                        By.CSS_SELECTOR, 
                        "button.iRxY3GoUYUY__button[aria-label='Back']"
                    ))
                )
                back_button.click()
                time.sleep(2)

            except Exception as e:
                print(f"Error processing restaurant {idx + 1}: {str(e)}")
                continue

        print("\nTest run completed!")
        print(f"Successfully scraped data: {len(data_record)} restaurants")

    except Exception as e:
        print(f"An error occurred: {str(e)}")
    finally:
        try:
            driver.quit()
        except:
            pass
        
        # Save whatever data we have
        if data_record:
            df = pd.DataFrame(data_record)
            df.to_csv(filename, index=False, encoding='utf-8')
            print(f"Data saved to {filename}")
        else:
            print("No data was collected to save")

if __name__ == "__main__":
    main()


