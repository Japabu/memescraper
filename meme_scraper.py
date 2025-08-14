import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import time
import os
import requests
from urllib.parse import urlparse

"""
Required packages:

pip install selenium requests

Auf r/MemeVideos gibts manchmal Beiträge. Die Kommentare haben einfach die besten mêmes. Kannst du ne gallerie zusammenstellen so webcrawler mässig?
AK:
- code der unterschiedliche bilder aus den kommentaren aus einem subreddit downloaden kann
- bilder haben source quali
- code gehört Jan
"""

# Configuration
SUBREDDIT = "MemeVideos"  # Change this to your desired subreddit
IMAGE_DOMAINS = ['i.redd.it', 'i.imgur.com', 'imgur.com', 'preview.redd.it']
IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
OUTPUT_DIR = "reddit_images"
HEADLESS = True  # Set to False to see the browser

# Setup Selenium
options = webdriver.ChromeOptions()
if HEADLESS:
    options.add_argument("--headless")
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3")
driver = webdriver.Chrome(options=options)


def create_directory():
    """Create output directory if it doesn't exist"""
    path = os.path.join(OUTPUT_DIR, SUBREDDIT)
    os.makedirs(path, exist_ok=True)
    return path


def dismiss_login_modal():
    """Try to dismiss the Reddit login modal"""
    try:
        WebDriverWait(driver, 3).until(
            EC.element_to_be_clickable((By.XPATH, '//button[text()="Not Now"]'))
        ).click()
    except (NoSuchElementException, TimeoutException):
        pass


def is_valid_image(url):
    """Check if URL points to a valid image"""
    parsed = urlparse(url)
    if any(parsed.netloc == domain for domain in IMAGE_DOMAINS):
        return True
    if any(parsed.path.lower().endswith(ext) for ext in IMAGE_EXTENSIONS):
        return True
    return False


def download_image(url, save_path):
    """Download and save an image from URL"""
    try:
        response = requests.get(url, stream=True, timeout=10)
        if response.status_code == 200:
            filename = os.path.basename(urlparse(url).path)
            if not any(filename.lower().endswith(ext) for ext in IMAGE_EXTENSIONS):
                filename += ".jpg"

            full_path = os.path.join(save_path, filename)
            with open(full_path, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            print(f"Downloaded: {filename}")
    except Exception as e:
        print(f"Failed to download {url}: {str(e)}")


def scrape_subreddit():
    total_scraped = 0
    save_path = create_directory()

    # Get subreddit page
    driver.get(f"https://www.reddit.com/r/{SUBREDDIT}/")
    dismiss_login_modal()

    # Scroll and collect posts incrementally
    post_links = []

    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(random.randrange(2, 3))

        # Find current posts on page
        posts = driver.find_elements(By.TAG_NAME, 'shreddit-post')
        new_posts = 0

        for post in posts:
            try:
                link = post.find_element(By.TAG_NAME, 'a')
                href = link.get_attribute('href')

                if href and '/comments/' in href and href not in post_links:
                    if not href.startswith('http'):
                        href = f'https://www.reddit.com{href}'

                    post_links.append(href)
                    new_posts += 1

            except NoSuchElementException:
                continue

        print(f"Found {new_posts} new posts (Total: {len(post_links)})")

        # Exit if we have reached the bottom
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    print(f"Processing {len(post_links)} posts...")

    # Process each post
    for idx, post_url in enumerate(post_links):
        try:
            driver.get(post_url)
            dismiss_login_modal()

            # Scroll to load all comments
            last_height = driver.execute_script("return document.body.scrollHeight")
            while True:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1.5)
                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height

            # Find comments and get image urls
            image_urls = set()
            comments = driver.find_elements(By.TAG_NAME, 'shreddit-comment')
            for comment in comments:
                try:
                    figure = comment.find_element(By.TAG_NAME, 'figure')
                    href = figure.find_element(By.TAG_NAME, 'a').get_attribute('href')
                    if href and is_valid_image(href):
                        image_urls.add(href)
                except NoSuchElementException:
                    continue
            print(f"[{idx + 1}/{len(post_links)}] Found {len(image_urls)} images in the comments of {post_url}")

            # Download images
            for url in image_urls:
                download_image(url, save_path)
                total_scraped += 1
                time.sleep(random.randrange(1, 3))
        except Exception as e:
            print(f"Error processing {post_url}: {str(e)}")
    print(f"Finished scraping {SUBREDDIT}! Got {total_scraped} images!")
    driver.quit()

if __name__ == "__main__":
    scrape_subreddit()
