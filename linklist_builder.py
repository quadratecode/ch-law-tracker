from bs4 import BeautifulSoup
from selenium import webdriver
from urllib.parse import urljoin
import time
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver import FirefoxOptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

# function to gather URLs


def get_links(driver, url):
    driver.get(url)
    delay = 60  # max delay in seconds until element is present
    WebDriverWait(driver, delay).until(
        EC.visibility_of_element_located((By.ID, "content")))
    time.sleep(5)

    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")

    if soup.find("div", "overflow-x-auto") != None:
        soup = soup.find("div", "overflow-x-auto")
    else:
        next(link)

    links = []

    for new_url in soup.find_all('a', href=True):
        new_url = new_url.get('href')
        new_url = urljoin(url, new_url)
        links.append(new_url)

    return links

# utilize headless browser


opts = FirefoxOptions()
opts.add_argument("--incognito")
opts.add_argument("--headless")
driver = webdriver.Firefox(
    executable_path=GeckoDriverManager().install(), options=opts)

# root domain and start URLs

domain = 'https://www.fedlex.admin.ch/'  # to filter external links
start_urls = ["https://www.fedlex.admin.ch/en/cc/internal-law/1/", # ENG
              "https://www.fedlex.admin.ch/en/cc/internal-law/2/",
              "https://www.fedlex.admin.ch/en/cc/internal-law/3/",
              "https://www.fedlex.admin.ch/en/cc/internal-law/4/",
              "https://www.fedlex.admin.ch/en/cc/internal-law/5/",
              "https://www.fedlex.admin.ch/en/cc/internal-law/6/",
              "https://www.fedlex.admin.ch/en/cc/internal-law/7/",
              "https://www.fedlex.admin.ch/en/cc/internal-law/8/",
              "https://www.fedlex.admin.ch/en/cc/internal-law/9/"] # Add other languages below


max_level = 2  # Max search level

# Open linklist and collect links
with open("linklist.txt", "a") as f:
    for start_url in start_urls:
        links_visited = set([start_url])  # Test against already visited links
        links_with_levels = [(start_url, 0)]  # Test against max lvl

        for link, level in links_with_levels:
            if level >= max_level:
                print('skip:', level, link)  # Skip if lvl is above max lvl
                continue

            print('visit:', level, link)

            links = get_links(driver, link)

            print('found:', len(links))
            links = list(set(links) - links_visited)
            print('after filtering:', len(links))
            print(*links, sep="\n", file=f)  # Print unique links to file

            level += 1

            for new_link in links:
                if new_link.startswith(domain):  # Filter external links
                    links_visited.add(new_link)
                    links_with_levels.append((new_link, level))

        for link, level in links_with_levels:
            print('skip:', level, link)

# Cleanup TXT file
# Remove URLs containing a specific substring
with open("linklist.txt", "r+") as f:
    new_f = f.readlines()
    f.seek(0)
    for line in new_f:
        if "internal-law" not in line:  # Define substring
            f.write(line)
    f.truncate()

# Remove empty lines
with open("linklist.txt", "r+") as f:
    new_f = f.readlines()
    f.seek(0)
    f.writelines(line for line in new_f if line.strip())
    f.truncate()
