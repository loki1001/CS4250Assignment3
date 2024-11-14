#-------------------------------------------------------------------------
# AUTHOR: Lokaranjan Munta
# FILENAME: crawler.py
# SPECIFICATION: The program has is a web crawler that starts at the seed URL (www.cpp.edu/sci/computer-science/) and
# crawls through the .html and .shtml pages looking for the Permanent Faculty target page. It uses MongoDB to store the
# crawled pages and flags the target page. Furthermore, it uses a Frontier class to track the visited and need to visit
# URLs.
# FOR: CS 4250- Assignment #3
# TIME SPENT: 2 hours
#-----------------------------------------------------------*/

import re
import urllib.parse as urlparse
from urllib.error import HTTPError
from urllib.request import urlopen
from bs4 import BeautifulSoup
from pymongo import MongoClient

# Create Frontier class to manage the visited URLs and the URLs that need to be crawled
class Frontier:
    def __init__(self):
        # Set to store visited URLs
        self.visitedURLs = set()
        # List to store URLs that need to be visited
        self.needToVisitURLs = []

    def addURL(self, url):
        # Add if URL is not already visited
        if url not in self.visitedURLs:
            self.visitedURLs.add(url)
            self.needToVisitURLs.append(url)

    def nextURL(self):
        # Get next URL to crawl
        if self.needToVisitURLs:
            return self.needToVisitURLs.pop(0)
        else:
            return None

    def done(self):
        # Check if there are remaining URLs
        return len(self.needToVisitURLs) == 0

    def clear_frontier(self):
        # Clear the URLs that are needed to visit (when target is found)
        self.needToVisitURLs.clear()

def connectDataBase():
    # Create a database connection object using pymongo
    client = MongoClient('mongodb://localhost:27017/')
    db = client['Assignment3']
    return db


def retrieveHTML(url):
    # Get and decode HTML page from URL
    try:
        html = urlopen(url)
        return html.read().decode('utf-8')
    except HTTPError as e:
        print(f"HTTP error: {e}")
        return None


def storePage(db, url, html):
    # Store HTML and URL of a page into MongoDB pages collection
    pages = db['pages']
    pages.insert_one({
        'url': url,
        'html': html
    })


def isTargetPage(html):
    # Check if page is the target by checking if Permanent Faculty is in the heading
    bs = BeautifulSoup(html, 'html.parser')
    target = bs.find('h1', {'class': 'cpp-h1'}, text=re.compile('^Permanent Faculty$'))
    return target


def flagTargetPage(db, url):
    # Mark the target page in MongoDB by setting target to True
    pages = db['pages']
    pages.update_one({'url': url}, {'$set': {'target': True}})


def parse(html, baseURL):
    bs = BeautifulSoup(html, 'html.parser')
    # Set to store the URLs
    urls = set()

    # Find all a tags with a href link
    for link in bs.find_all('a', href=True):
        # Extract href from the link
        href = link['href']

        # Convert relative URLs to absolute URLs using the baseURL
        fullAddress = urlparse.urljoin(baseURL, href)

        # Only keep .html and .shtml
        if fullAddress.endswith(('.html', '.shtml')):
            # Add the fullAddress to the discovered URLs
            urls.add(fullAddress)
            print(f"Discovered URL: {fullAddress}")

    # Return the set of discovered URLs
    return urls


def crawlerThread(db, frontier):
    while not frontier.done():
        # Get next URL to process
        url = frontier.nextURL()
        print(f"Crawling {url}")

        # Retrieve and store the page
        html = retrieveHTML(url)
        storePage(db, url, html)

        # Check if target page
        if isTargetPage(html):
            print("Target page found")
            # Flag the target page in MongoDB
            flagTargetPage(db, url)
            # Stop crawling once target is found
            frontier.clear_frontier()
            break
        else:
            # Add the discovered URLs to frontier
            for url in parse(html, url):
                frontier.addURL(url)


def main():
    # Connect to db
    db = connectDataBase()

    # Initialize frontier and set the seed
    frontier = Frontier()
    seed = "https://www.cpp.edu/sci/computer-science/"
    frontier.addURL(seed)

    # Start crawling process
    print(f"Starting crawling from: {seed}")
    crawlerThread(db, frontier)


if __name__ == '__main__':
    main()