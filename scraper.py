#!/usr/bin/env python3
"""
Goodreads Book Scraper
Scrapes your "read" books from Goodreads with manual login
Outputs data to both JSON and CSV formats
"""

import time
import json
import csv
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import re

class GoodreadsScraper:
    def __init__(self):
        self.driver = None
        self.books = []
        
    def setup_driver(self):
        """Initialize Chrome driver with options"""
        chrome_options = Options()
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        except Exception as e:
            print(f"Error setting up Chrome driver: {e}")
            print("Please make sure ChromeDriver is installed and in your PATH")
            return False
        return True
    
    def manual_login(self):
        """Open login page and wait for user to log in manually"""
        print("Opening Goodreads login page...")
        self.driver.get("https://www.goodreads.com/user/sign_in")
        
        print("\n" + "="*50)
        print("MANUAL LOGIN REQUIRED")
        print("="*50)
        print("1. Please log in to your Goodreads account in the browser window")
        print("2. Once you're logged in and see your dashboard, come back here")
        print("3. Press Enter to continue with scraping...")
        print("="*50)
        
        input("Press Enter after you've successfully logged in...")
        
        # Verify login by checking if we can access the user's profile
        try:
            # Try to find user menu or profile link
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "siteHeader__personal"))
            )
            print("✓ Login verified! Proceeding with scraping...")
            return True
        except:
            print("⚠ Could not verify login. Proceeding anyway...")
            return True
    
    def get_total_pages(self, base_url):
        """Get total number of pages to scrape with better detection"""
        print("Checking total pages...")
        self.driver.get(base_url)
        time.sleep(3)
        
        try:
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Try multiple selectors for pagination
            pagination = (soup.find('div', {'class': 'pagination'}) or
                         soup.find('div', class_=re.compile('pagination')) or
                         soup.find('nav', class_=re.compile('pagination')))
            
            if pagination:
                # Look for page numbers
                page_links = pagination.find_all('a')
                page_numbers = []
                for link in page_links:
                    text = link.get_text().strip()
                    if text.isdigit():
                        page_numbers.append(int(text))
                
                if page_numbers:
                    max_page = max(page_numbers)
                    print(f"Found pagination: max page {max_page}")
                    return max_page
            
            # Alternative: look for "showing X-Y of Z" text
            showing_text = soup.find(string=re.compile(r'showing.*of.*\d+', re.I))
            if showing_text:
                total_match = re.search(r'of\s+(\d+)', showing_text, re.I)
                if total_match:
                    total_books = int(total_match.group(1))
                    books_per_page = 20  # Goodreads default
                    total_pages = (total_books + books_per_page - 1) // books_per_page
                    print(f"Calculated {total_pages} pages from total books: {total_books}")
                    return total_pages
            
            print("Could not determine pagination, assuming multiple pages exist...")
            # Try to navigate to page 2 to see if it exists
            page_2_url = f"{base_url}&page=2"
            self.driver.get(page_2_url)
            time.sleep(2)
            
            # Check if page 2 has books
            soup_2 = BeautifulSoup(self.driver.page_source, 'html.parser')
            book_rows_2 = (soup_2.find_all('tr', {'class': 'bookalike review'}) or
                          soup_2.find_all('tr', class_=re.compile('bookalike')) or
                          [row for row in soup_2.find_all('tr') if row.find('img') and 'goodreads.com' in str(row)])
            
            if book_rows_2:
                print("Page 2 exists, will discover pages dynamically")
                return 999  # We'll discover the actual limit during scraping
            else:
                print("Only 1 page exists")
                return 1
                
        except Exception as e:
            print(f"Error determining total pages: {e}")
            return 999  # We'll discover pages dynamically
    
    def debug_html_structure(self, book_row):
        """Debug function to print the HTML structure"""
        print("="*50)
        print("DEBUG: HTML STRUCTURE FOR ONE BOOK ROW")
        print("="*50)
        print(str(book_row)[:2000])  # Print first 2000 characters
        print("="*50)
    
    def clean_review_text(self, raw_review):
        """Simple review text cleaning function"""
        if not raw_review:
            return ''
        
        # Remove "review" header if present (case insensitive)
        review_text = re.sub(r'^review\s*\n?', '', raw_review, flags=re.IGNORECASE).strip()
        
        # Remove trailing "...more" patterns
        review_text = re.sub(r'\n?\.\.\.s*more\s*$', '', review_text, flags=re.IGNORECASE)
        
        # Remove trailing [edit] markers
        review_text = re.sub(r'\n?\[edit\]\s*$', '', review_text, flags=re.IGNORECASE)
        
        # Replace newlines with spaces and clean up multiple spaces
        review_text = re.sub(r'\n+', ' ', review_text)
        review_text = re.sub(r'\s+', ' ', review_text)
        
        # Final cleanup
        review_text = review_text.strip()
        
        # Filter out common non-review text
        if review_text.lower() in ['write a review', '[edit]', '...more']:
            return ''
        
        return review_text
    
    def extract_book_data(self, book_row, debug=False):
        """Extract data from a single book row with improved selectors and fixed author extraction"""
        try:
            soup = BeautifulSoup(str(book_row), 'html.parser')
            
            #if debug:
            #    self.debug_html_structure(book_row)
            
            book_data = {}
            
            # Initialize with defaults
            book_data['title'] = "Unknown"
            book_data['author'] = "Unknown"
            
            # Extract title from title cell
            title_cell = soup.find('td', {'class': 'field title'})
            if title_cell:
                title_link = (title_cell.find('a', {'class': 'bookTitle'}) or 
                             title_cell.find('a', title=True) or 
                             title_cell.find('a'))
                
                if title_link:
                    # Clean up title text - remove extra whitespace and newlines
                    raw_title = title_link.text.strip()
                    # Replace multiple whitespace (including newlines) with single spaces
                    book_data['title'] = re.sub(r'\s+', ' ', raw_title)
                else:
                    # Fallback to any text in the title cell
                    title_text = title_cell.get_text().strip()
                    cleaned_title = re.sub(r'\s+', ' ', title_text) if title_text else "Unknown"
                    book_data['title'] = cleaned_title.split('\n')[0] if '\n' in cleaned_title else cleaned_title
            
            # Extract author from dedicated author cell
            author_cell = soup.find('td', {'class': 'field author'})
            if author_cell:
                author_link = author_cell.find('a')
                if author_link:
                    book_data['author'] = author_link.text.strip()
                else:
                    # Fallback to any text in the author cell
                    book_data['author'] = author_cell.get_text().strip() or "Unknown"
            else:
                book_data['author'] = "Unknown"
            
            # Cover image
            cover_cell = soup.find('td', {'class': 'field cover'})
            if cover_cell:
                img = cover_cell.find('img')
                book_data['cover_url'] = img.get('src', '') if img else ''
            else:
                book_data['cover_url'] = ''
            
            # Rating - FIXED to use data-rating attribute
            rating_cell = soup.find('td', {'class': 'field rating'})
            if rating_cell:
                # Look for div with class 'stars' and data-rating attribute
                stars_div = rating_cell.find('div', {'class': 'stars'})
                if stars_div and stars_div.has_attr('data-rating'):
                    try:
                        rating_value = stars_div.get('data-rating')
                        # Handle case where data-rating might be "null" or empty
                        if rating_value and rating_value.lower() != 'null':
                            book_data['my_rating'] = int(rating_value)
                        else:
                            book_data['my_rating'] = 0
                    except (ValueError, TypeError):
                        book_data['my_rating'] = 0
                else:
                    # Fallback to old method if new structure not found
                    rating_spans = (rating_cell.find_all('span', {'class': 'staticStars'}) or
                                   rating_cell.find_all('span', class_=re.compile('stars')) or
                                   rating_cell.find_all('div', class_=re.compile('stars')))
                    
                    if rating_spans:
                        rating_text = rating_spans[0].get('title', '') or rating_spans[0].get_text()
                        rating_match = re.search(r'(\d+)', rating_text)
                        book_data['my_rating'] = int(rating_match.group(1)) if rating_match else 0
                    else:
                        # Try to find star images or other rating indicators
                        star_imgs = rating_cell.find_all('img', src=re.compile('star'))
                        filled_stars = [img for img in star_imgs if 'filled' in img.get('src', '')]
                        book_data['my_rating'] = len(filled_stars) if filled_stars else 0
            else:
                book_data['my_rating'] = 0
            
            # Date Read - flexible approach with better cleaning
            date_read_cell = soup.find('td', {'class': 'field date_read'})
            if date_read_cell:
                date_text = (date_read_cell.find('div', {'class': 'date_read_value'}) or
                            date_read_cell.find('span', {'class': 'date_read_value'}) or
                            date_read_cell)
                
                if date_text:
                    raw_date = date_text.get_text().strip()
                    # Clean up the date read field
                    # Remove "date read" header and extra whitespace
                    cleaned_date = re.sub(r'date read\s*', '', raw_date, flags=re.IGNORECASE)
                    # Remove [edit] markers
                    cleaned_date = re.sub(r'\[edit\]', '', cleaned_date, flags=re.IGNORECASE)
                    # Replace multiple whitespace with single spaces and strip
                    cleaned_date = re.sub(r'\s+', ' ', cleaned_date).strip()
                    
                    # Check if it's "not set" or empty
                    if not cleaned_date or cleaned_date.lower() in ['not set', '']:
                        book_data['date_read'] = 'Date read not set'
                    else:
                        book_data['date_read'] = cleaned_date
                else:
                    book_data['date_read'] = 'Date read not set'
            else:
                book_data['date_read'] = 'Date read not set'
            
            # Date Added - flexible approach with header removal
            date_added_cell = soup.find('td', {'class': 'field date_added'})
            if date_added_cell:
                date_text = (date_added_cell.find('div', {'class': 'date_added_value'}) or
                            date_added_cell.find('span', {'class': 'date_added_value'}) or
                            date_added_cell)
                if date_text:
                    raw_date = date_text.get_text().strip()
                    # Remove "date added" header if present
                    if raw_date.lower().startswith('date added'):
                        # Split by newlines and take the last non-empty line
                        lines = [line.strip() for line in raw_date.split('\n') if line.strip()]
                        book_data['date_added'] = lines[-1] if lines and lines[-1].lower() != 'date added' else ''
                    else:
                        book_data['date_added'] = raw_date
                else:
                    book_data['date_added'] = ''
            else:
                book_data['date_added'] = ''
            
            # Review - Target the full review text specifically
            review_cell = soup.find('td', {'class': 'field review'})
            if review_cell:
                # Find the span containing the full review text.
                # This span usually has an ID starting with 'freeText' and is initially hidden,
                # but contains the complete review.
                full_review_span = review_cell.find('span', id=lambda x: x and x.startswith('freeText') and not x.startswith('freeTextContainer'))
                if full_review_span:
                    review_text = full_review_span.get_text().strip()
                else:
                    # Fallback: If the specific span isn't found, try get_text() but be more careful.
                    # This might still risk duplication but is better than nothing.
                    # Example: Get text directly inside the 'value' div, ignoring labels and links if possible.
                    value_div = review_cell.find('div', {'class': 'value'})
                    if value_div:
                        # Get text, potentially excluding script/style/link tags if present
                        review_text = value_div.get_text(separator=' ', strip=True)
                        # Basic attempt to remove the '[edit]' link text if it sneaks in
                        review_text = review_text.split('[edit]', 1)[0].strip()
                    else:
                        review_text = review_cell.get_text().strip()

                book_data['review'] = self.clean_review_text(review_text)
            else:
                book_data['review'] = ''
            
            # Average Rating
            avg_rating_cell = soup.find('td', {'class': 'field avg_rating'})
            if avg_rating_cell:
                rating_text = avg_rating_cell.get_text().strip()
                try:
                    rating_match = re.search(r'(\d+\.?\d*)', rating_text)
                    book_data['avg_rating'] = float(rating_match.group(1)) if rating_match else 0.0
                except:
                    book_data['avg_rating'] = 0.0
            else:
                book_data['avg_rating'] = 0.0
            
            # Number of Pages
            pages_cell = soup.find('td', {'class': 'field num_pages'})
            if pages_cell:
                pages_text = pages_cell.get_text()
                pages_match = re.search(r'(\d+)', pages_text)
                book_data['pages'] = int(pages_match.group(1)) if pages_match else 0
            else:
                book_data['pages'] = 0
            
            # Publication Year
            pub_cell = soup.find('td', {'class': 'field date_pub'})
            if pub_cell:
                pub_text = pub_cell.get_text()
                year_match = re.search(r'\d{4}', pub_text)
                book_data['publication_year'] = int(year_match.group()) if year_match else 0
            else:
                book_data['publication_year'] = 0
            
            #if debug:
            #    print(f"DEBUG: Extracted - Title: '{book_data['title']}', Author: '{book_data['author']}'")
            
            return book_data
        
        except Exception as e:
            print(f"Error extracting book data: {e}")
            return None
    
    def scrape_page(self, url, page_num, debug_first_book=False):
        """Scrape a single page of books"""
        print(f"Scraping page {page_num}...")
        self.driver.get(url)
        time.sleep(3)  # Increased delay
        
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        
        # Try different selectors for book rows
        book_rows = (soup.find_all('tr', {'class': 'bookalike review'}) or
                    soup.find_all('tr', class_=re.compile('bookalike')) or
                    soup.find_all('tr', class_=re.compile('review')))
        
        if not book_rows:
            print("No book rows found with standard selectors, trying alternatives...")
            # Try to find any table rows that might contain books
            all_rows = soup.find_all('tr')
            book_rows = [row for row in all_rows if row.find('img') and 'goodreads.com' in str(row)]
            print(f"Found {len(book_rows)} rows with images")
        
        #if not book_rows:
        #    print("Still no rows found. Saving page HTML for debugging...")
        #    with open(f'debug_page_{page_num}.html', 'w', encoding='utf-8') as f:
        #        f.write(self.driver.page_source)
        #    print(f"Saved page HTML to debug_page_{page_num}.html")
        
        page_books = []
        for i, row in enumerate(book_rows):
            # Debug first book if requested
            debug_this = debug_first_book and i == 0
            book_data = self.extract_book_data(row, debug=debug_this)
            if book_data:
                page_books.append(book_data)
        
        print(f"Found {len(page_books)} books on page {page_num}")
        return page_books
    
    def scrape_books(self, user_id):
        """Main scraping function with dynamic page discovery"""
        base_url = f"https://www.goodreads.com/review/list/{user_id}?shelf=read&per_page=20"
        
        # Get initial page count estimate
        estimated_pages = self.get_total_pages(base_url)
        print(f"Starting scrape - estimated {estimated_pages} page(s)")
        
        # If we got 999 (dynamic discovery), we'll keep going until we hit an empty page
        dynamic_discovery = estimated_pages == 999
        
        page = 1
        consecutive_empty_pages = 0
        
        while True:
            page_url = f"{base_url}&page={page}"
            
            # Debug first book on first page only
            debug_first = (page == 1)
            page_books = self.scrape_page(page_url, page, debug_first_book=debug_first)
            
            if page_books:
                self.books.extend(page_books)
                consecutive_empty_pages = 0
                print(f"✓ Page {page}: {len(page_books)} books (total so far: {len(self.books)})")
            else:
                consecutive_empty_pages += 1
                print(f"✗ Page {page}: No books found")
                
                # Stop if we hit 2 consecutive empty pages, or if we exceeded estimated pages
                if consecutive_empty_pages >= 2 or (not dynamic_discovery and page > estimated_pages):
                    print(f"Stopping scrape after {consecutive_empty_pages} empty pages")
                    break
            
            page += 1
            
            # Safety limit
            if page > 50:
                print("Safety limit reached (50 pages), stopping")
                break
            
            # Small delay between pages
            time.sleep(1.5)
        
        print(f"\n✓ Scraping complete! Found {len(self.books)} total books across {page-1} pages")
        return self.books
    
    def save_to_json(self, filename="goodreads_books.json"):
        """Save books to JSON file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump({
                    'scrape_date': datetime.now().isoformat(),
                    'total_books': len(self.books),
                    'books': self.books
                }, f, indent=2, ensure_ascii=False)
            print(f"✓ Saved to {filename}")
        except Exception as e:
            print(f"Error saving JSON: {e}")
    
    def save_to_csv(self, filename="goodreads_books.csv"):
        """Save books to CSV file"""
        try:
            if not self.books:
                print("No books to save")
                return
            
            # Get all possible field names
            fieldnames = set()
            for book in self.books:
                fieldnames.update(book.keys())
            fieldnames = sorted(list(fieldnames))
            
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(self.books)
            
            print(f"✓ Saved to {filename}")
        except Exception as e:
            print(f"Error saving CSV: {e}")
    
    def run(self, user_id):
        """Main run function"""
        print("Goodreads Book Scraper")
        print("=" * 30)
        
        if not self.setup_driver():
            return
        
        try:
            # Manual login
            if not self.manual_login():
                return
            
            # Scrape books
            self.scrape_books(user_id)
            
            if self.books:
                # Save to both formats
                self.save_to_json()
                self.save_to_csv()
                
                print(f"\n📚 Summary:")
                print(f"   Total books scraped: {len(self.books)}")
                print(f"   Files created: goodreads_books.json, goodreads_books.csv")
            else:
                print("No books found. Please check your user ID and shelf settings.")
        
        except KeyboardInterrupt:
            print("\n\nScraping interrupted by user")
        except Exception as e:
            print(f"Error during scraping: {e}")
        finally:
            if self.driver:
                self.driver.quit()
                print("Browser closed")


def main():
    # Extract user ID from your URL. eg:
    # https://www.goodreads.com/user/show/your-userID
    # user_id = "your-userID"

    user_id = "171519754-trevor-redmond"
    
    scraper = GoodreadsScraper()
    scraper.run(user_id)

if __name__ == "__main__":
    main()