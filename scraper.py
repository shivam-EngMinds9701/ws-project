import requests
from bs4 import BeautifulSoup as bs
import json
import time
from requests.exceptions import ProxyError, HTTPError
import argparse 


class Scraper:
    def __init__(self, base_url, base_headers, output_file):
        self.base_url = base_url
        self.base_headers = base_headers
        self.output_file = output_file

    def get_product_links(self, query, page_number=1):
        url = f"{self.base_url}search?q={query}&page={page_number}"
        response = requests.get(url, headers=self.base_headers)
        soup = bs(response.text, "html.parser")
        links = soup.find_all("a", {"class": "CGtC98"})
        product_links = [link["href"] for link in links]
        return product_links

    def extract_product_info(self, product_url):
        max_retries = 5
        backoff_factor = 3

        for attempt in range(max_retries):
            try:
                url = f"{self.base_url}{product_url}"
                response = requests.get(url, headers=self.base_headers)
                response.raise_for_status()
                soup = bs(response.text, "html.parser")
                filtered_data_string = soup.find("script", {"id": "jsonLD"})

                data = json.loads(filtered_data_string.string)[0]
                product_info = None
                if data["@type"] == "Product":
                    product_info = {
                        "product_name": data["name"],
                        "brand_name": data["brand"]["name"],
                        "aggregate_rating": data["aggregateRating"]["ratingValue"],
                        "review_count": data["aggregateRating"]["reviewCount"],
                        "price": data["offers"]["price"],
                        "price_currency": data["offers"]["priceCurrency"],
                    }
                
                return product_info

            except (ProxyError, HTTPError) as e:
                if attempt < max_retries - 1:
                    print(f"Error: {e}. Retrying in {backoff_factor} seconds...")
                    time.sleep(backoff_factor)
                    backoff_factor *= 2
                else:
                    print(f"Error: {e}. Skipping product.")
                    return None


def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Accept query and number of pages to scrape from Flipkart")

    # Add arguments
    parser.add_argument("--query","-q", type=str, help="Search query")
    parser.add_argument("--num_pages", "-n", type=int, help="Number of pages to scrape")

    # Parse arguments
    args = parser.parse_args()
    query = args.query if args.query else "laptop"
    num_pages = args.num_pages if args.num_pages else 5
    print(f"Scraping {num_pages} pages for query: {query}")

    # Add Base URL and Headers
    OUTPUT_FILE = "temp2.json"
    BASE_URL = "https://www.flipkart.com/"
    BASE_HEADERS = {
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "en-US,en;q=0.9,en-IN;q=0.8",
    }
    sc = Scraper(BASE_URL, BASE_HEADERS, "test.json")

    with open(OUTPUT_FILE, "w") as f:
        page_number = 1
        while True:
            print(f"Scraping page {page_number}")
            product_links = sc.get_product_links("laptop", page_number)

            if not product_links or page_number > 5:
                print("No more products found. Exiting...")
                break

            for i, product_link in enumerate(product_links):
                print(
                    f"Scraping product {i+1} of {len(product_links)}"
                )
                product_info = sc.extract_product_info(product_link)
                if product_info:
                    f.write(json.dumps(product_info) + "\n")

            page_number += 1


if __name__ == "__main__":
    main()
