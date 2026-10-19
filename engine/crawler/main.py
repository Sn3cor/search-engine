import requests
import json
from collections import deque
import time

class Crawler:
    def __init__(self, category:str, max_pages = 70000, max_depth = 0, output_file = "data.jsonl"):
        self.api_url = "https://en.wikipedia.org/w/api.php"
        self.max_pages = max_pages
        self.max_depth = max_depth
        self.output_path = f"./../data/{output_file}"

        self.seen_pages = set()
        self.seen_categories = set()
        self.seen_categories.add(category)

        self.session = requests.Session()
        self.session.headers['User-Agent'] = 'MyCrawler/1.0 (jakub.krupa23@gmail.com) python-requests/2.34.2'

        self.queue = deque([(0,f"{category}")])


    def _fetch(self, params, attempts = 3):
        for i in range(attempts):
            timeout = 3
            try:
                res = self.session.get(self.api_url, params=params, timeout=10)
                res.raise_for_status()
                data = res.json()
                return data
            
            except requests.exceptions.HTTPError as e:
                print(f"HTTP Error: {e}\n")
                if e.response:
                    timeout = e.response.headers.get("Retry-After")
                

            except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
                print(f"Failed to fetch: {e}\n")
                
            time.sleep(timeout)

        return {}
    
    def _extract_article_info(self, article_data, page_id):
        page_info = article_data.get("query", {}).get("pages", {}).get(str(page_id), {})
        
        text = page_info.get("extract", "")
        url = page_info.get("canonicalurl", "")
        
        return text, url

    def crawl(self):
        with open(self.output_path, "w", encoding="utf-8") as f:
            print(f"Starting crawling {self.max_pages} pages\n")

            while self.queue and len(self.seen_pages)<=self.max_pages:
                depth, current_category = self.queue.popleft()

                if depth > self.max_depth:
                    print(f"Skipping category {current_category}; Achieved max depth of {self.max_depth}")
                    continue

                print(f"Current category: {current_category}\n")

                continue_token = {}

                while True:
                    params = {
                        "action": "query",
                        "list": "categorymembers",
                        "cmtitle": f"{current_category}",
                        "cmlimit": "500",
                        "format": "json",
                        **continue_token
                    }

                    category_data = self._fetch(params=params)
                    time.sleep(1)
                    if not category_data: break
                    
                    pages_list = category_data.get("query", {}).get("categorymembers", [])
                    if not pages_list:break

                    for page in pages_list:
                        if len(self.seen_pages) >= self.max_pages:
                            break
                        page_id = page["pageid"]
                        ns = page["ns"]
                        title = page["title"]

                        if ns == 0 and page_id not in self.seen_pages:
                            params = {
                                "action": "query",
                                "prop": "extracts|info",
                                "inprop": "url",
                                "pageids": page_id,
                                "explaintext": True,
                                "format": "json"
                            }
                            
                            article = self._fetch(params=params)
                            time.sleep(1)
                            if not article: continue
                            text, url = self._extract_article_info(article,page_id)
                            
                            document = {
                                "id": page_id,
                                "title": title,
                                "url" : url,
                                "text": text
                            }

                            f.write((json.dumps(document, ensure_ascii=False) + "\n"))
                            f.flush()

                            self.seen_pages.add(page_id)

                            time.sleep(1)

                        elif ns == 14 and title not in self.seen_categories:
                            if depth < self.max_depth:
                                self.seen_categories.add(title)
                                self.queue.append((depth+1, title))

                    if "continue" in category_data:
                        continue_token = category_data["continue"]
                    else:
                        break
                    
            print(f"\nFinished crawling. Fetched {len(self.seen_pages)} pages.")


if __name__ == "__main__":
    crawler = Crawler("Category:History", max_pages=100000, max_depth=5)
    crawler.crawl()





