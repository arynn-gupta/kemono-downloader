# kemono.party downloader

This is a kemono.party scraper that extracts all post's and download's the following links in a structured format :

- [x] Google Drive File Link 
- [x] Google Drive Folder Link 
- [x] Youtube Video Link 
- [x] kemono.party Link 
- [x] kemono.party Image Link
- [x] kemono.party Text Content 

Unsupported links are saved in a separate `links.txt` file.

Scraped Text Content is saved in `readme.txt` file.

Failed download links are savd in `errors.txt` file.

# Usage
Install dependencies using :
`pip install -r requirements.txt`

Then run the main.py file using:
`python main.py`
