# Goodreads Book Scraper

A Python web scraper that extracts your "read" books from Goodreads and exports them to JSON and CSV formats. Perfect for book enthusiasts who want to analyze their reading data, display their book collection on personal websites, or create backups of their reading history.

## Why This Exists

Goodreads discontinued their public API in December 2020, making it impossible for developers to programmatically access user reading data. This scraper fills that gap by automating the process of collecting your book data directly from your Goodreads profile.

## Features

- 📚 **Comprehensive Data Extraction**: Scrapes title, author, your rating, average rating, pages, publication year, dates read/added, and reviews
- 🔄 **Multiple Output Formats**: Exports data to both JSON and CSV for maximum compatibility
- 🛡️ **Robust Scraping**: Handles pagination automatically and includes error recovery
- 👤 **Manual Login**: Secure login process - you log in manually, no stored credentials
- 🔍 **Smart Detection**: Automatically discovers the number of pages to scrape
- 📝 **Clean Data**: Removes HTML artifacts and cleans up text fields

## Prerequisites

- Python 3.6+
- Google Chrome browser
- ChromeDriver (must be in your system PATH)

## Installation

1. **Clone or download the scraper**:
   ```bash
   git clone https://github.com/tredmond107/goodreads-scraper.git
   cd goodreads-scraper
   ```

2. **Install required Python packages**:
   ```bash
   pip install selenium beautifulsoup4
   ```

3. **Install ChromeDriver**:
   - **macOS**: `brew install chromedriver`
   - **Windows**: Download from [ChromeDriver website](https://chromedriver.chromium.org/) and add to PATH
   - **Linux**: `sudo apt-get install chromium-chromedriver`

## Setup

1. **Find your Goodreads User ID**:
   - Go to your Goodreads profile
   - Look at the URL: `https://www.goodreads.com/user/show/12345678-your-name`
   - Your User ID is the full string: `12345678-your-name`

2. **Update the script**:
   ```python
   # In scraper.py, Line 522 replace "your-userID" with your actual User ID
   user_id = "12345678-your-name"  # Your actual Goodreads User ID
   ```

## Usage

1. **Run the scraper**:
   ```bash
   python scraper.py
   ```

2. **Login manually**:
   - A Chrome browser window will open to the Goodreads login page
   - Log in to your Goodreads account normally
   - Once you see your dashboard, return to the terminal and press Enter

3. **Wait for completion**:
   - The scraper will automatically navigate through all pages of your "read" books
   - Progress will be displayed in the terminal
   - Files will be saved when complete

## Output Files

The scraper creates two files in the same directory:

### `goodreads_books.json`
```json
{
  "scrape_date": "2024-01-15T10:30:00",
  "total_books": 42,
  "books": [
    {
      "title": "The Hitchhiker's Guide to the Galaxy",
      "author": "Douglas Adams",
      "my_rating": 5,
      "avg_rating": 4.21,
      "pages": 224,
      "publication_year": 1979,
      "date_read": "Dec 15, 2023",
      "date_added": "Nov 20, 2023",
      "review": "Absolutely brilliant and hilarious...",
      "cover_url": "https://images.gr-assets.com/books/..."
    }
  ]
}
```

### `goodreads_books.csv`
A spreadsheet-compatible file with the same data, perfect for analysis in Excel, Google Sheets, or data analysis tools.

## Use Cases

- **Personal Website**: Display your reading history on your blog or portfolio
- **Reading Analytics**: Analyze your reading patterns, favorite authors, or rating trends
- **Data Backup**: Keep a local copy of your Goodreads data
- **Book Recommendations**: Build recommendation systems based on your reading history
- **Reading Goals**: Track progress and set future reading targets

## Data Fields Extracted

| Field | Description |
|-------|-------------|
| `title` | Book title |
| `author` | Primary author name |
| `my_rating` | Your rating (0-5 stars, 0 if unrated) |
| `avg_rating` | Goodreads average rating |
| `pages` | Number of pages |
| `publication_year` | Year of publication |
| `date_read` | When you marked it as read |
| `date_added` | When you added it to Goodreads |
| `review` | Your written review (if any) |
| `cover_url` | URL to book cover image |

## Troubleshooting

### "ChromeDriver not found"
- Ensure ChromeDriver is installed and in your system PATH
- Try running `chromedriver --version` in terminal to verify

### "No books found"
- Verify your User ID is correct
- Make sure you have books in your "read" shelf
- Check that you're properly logged in

### Books missing or incomplete data
- Some older Goodreads entries may have missing fields
- The scraper handles missing data gracefully with default values

### Rate limiting
- The scraper includes delays between requests to be respectful
- If you encounter issues, try increasing the sleep delays in the code

## Legal and Ethical Considerations

- This scraper is intended for personal use with your own Goodreads data
- Please respect Goodreads' terms of service and don't overload their servers
- Consider the scraping frequency and be mindful of rate limits
- Only scrape data you own or have permission to access

## Contributing

Issues and pull requests are welcome! Areas for improvement:
- Support for other shelves (want-to-read, currently-reading)
- Better error handling and retry logic
- Export to additional formats
- GUI interface

## License

This project is provided as-is for educational and personal use.