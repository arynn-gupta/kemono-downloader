
import requests, urllib.request, math, os ,re
from urllib.parse import urlparse
from contextlib import contextmanager
from bs4 import BeautifulSoup
import yt_dlp
import gdown

URL_PATH = "https://kemono.party"
README_FILE = "readme.txt"
DEBUG_FILE = "errors.txt"
LINKS_FILE = "links.txt"
WHITELIST_FILE = "whitelist.txt"
IMAGES_FOLDER = "images"
YTDL_OPTIONS = {
    'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio',
}
VALID_DIR_NAME = r'[\\/:\*\?"<>\|]'
VALID_IMAGE = r'^[\w,\s-]+\.(jpg|jpeg|png|gif|bmp|tiff|ico)$'
GOOGLE_DRIVE_ID = r'([\w-]{25,})'
DWN_PREFIX = "Download "

@contextmanager
def cwd(path):
    oldpwd = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(oldpwd)

def get_articles(url):
    print("GET ARTICLES : " + url)
    r = requests.get(url)
    soup = BeautifulSoup(r.content, 'html5lib')
    articles_div = soup.find('div', attrs = {'class':'card-list__items'})
    articles = [] 
    for article in articles_div.findAll('article', attrs = {'class':'post-card'}):
        link = article.a['href']
        name = article.a.header.text.strip()
        articles.append({
            "article_name": name,
            "article_link": URL_PATH+link
        })
    return articles

def get_info(url, start, end):
    print("\nGET PAGE INFO : " + url, end='\n')
    r = requests.get(url)
    soup = BeautifulSoup(r.content, 'html5lib')
    artist_name = soup.find('span', attrs = {'itemprop':'name'}).text
    total_pages=1
    try:
        paginator_div = soup.find('div', attrs = {'id':'paginator-top'}) 
        total_articles = paginator_div.small.text.split()[-1]
        total_pages = math.ceil(int(total_articles) / 50)
    except:
        pass
    urls = []
    for i in range(0,total_pages):
        urls.append(url+'?o='+str(i*50))
    articles=[]
    for url in urls:
        articles.extend(get_articles(url))

    if start or end:
        s = int(start.strip() or 1)
        e = int(end.strip() or 1)
        if s<1:
            s=1
        if e<1:
            e=1
        if s>e:
            e=s
        if s>len(articles):
            s=len(articles)
        if e>len(articles):
            e=len(articles)
        if s-1<=0:
            articles = articles[-e:]
        else:
            articles = articles[-e:-(s-1)]

    return {
        "artist_name":artist_name,
        "urls":urls,
        "articles":articles
    }

def get_post(article):
    url = article["article_link"]
    r = requests.get(url)
    soup = BeautifulSoup(r.content, 'html5lib')
    post__body = soup.find('div', attrs = {'class':'post__body'})

    images=[]
    links=[]
    text=""

    try:
        for link in post__body.findAll('a'):
            links.append({
                'url': link['href'],
                'name': link.text.strip() or ""
                })
    except:
        pass

    try:
        for image in post__body.findAll('img'):
            images.append(image['src'])
    except:
        pass

    try:
        text = post__body.find('div', attrs = {'class':'post__content'}).get_text(separator="\n\n")
    except:
        pass

    return {
        "post_content":text, 
        "post_links":links, 
        "post_images":images
        }

def clean_text_for_directory_name(text):
    text = text.strip()
    text = re.sub(VALID_DIR_NAME, ' ', text)
    text = text.rstrip('. ')
    text = text[:255]
    return text

def is_valid_image_filename(filename):
    pattern = re.compile(VALID_IMAGE, re.IGNORECASE)
    return bool(pattern.match(filename))


def extract_drive_id(url):
    match = re.search(GOOGLE_DRIVE_ID, url)
    if match:
        return match.group(1)
    return None

def download_posts(articles, artist_name):
    if len(articles)==0:
        print("No Posts found !")
    else :
        print("\nDOWNLOADING POSTS....", end='\n')
        for idx, article in enumerate(articles):
            reverse_index = len(articles) - idx
            path = clean_text_for_directory_name(artist_name)+"/"+str(reverse_index)+". "+clean_text_for_directory_name(article["article_name"])+"/"
            print("\n"+path)

            post = get_post(article)
            if not os.path.exists(path):
                os.makedirs(path)

            with cwd(path):

                error =""

                whitelist_urls = []
                f=open(WHITELIST_FILE,"r")
                whitelist_urls = [line.strip() for line in f.readlines()]
                f.close()

                print("Downloading Readme....")
                if post['post_content']:
                    try:
                        if not os.path.isfile(README_FILE):
                            f=open(README_FILE,"w")
                            f.write(post['post_content'])
                            f.close()
                    except:
                        error=post['post_content']
                        errors = open(DEBUG_FILE,"a+")
                        errors.write(error+"\n")
                        errors.close()

                print("Downloading Images....")
                if post['post_images']:
                    images_path = IMAGES_FOLDER+"/"
                    if not os.path.exists(images_path):
                        os.makedirs(images_path)
                    for image in post['post_images']:
                        try:
                            image_url = image
                            if image.startswith('/'):
                                image_url = URL_PATH+image
                            parsed_url = urlparse(image_url)
                            file_name = images_path+os.path.basename(parsed_url.path)
                            if not os.path.isfile(file_name):
                                urllib.request.urlretrieve(image_url,file_name)
                        except :
                            error=image
                            errors = open(DEBUG_FILE,"a+")
                            errors.write(error+"\n")
                            errors.close()

                print("Downloading Links....")
                if post['post_links']:
                    for item in post['post_links']:
                        try:
                            link = item['url']
                            file_name = item['name'].replace(DWN_PREFIX, "", 1)
                            base_name, file_extension = os.path.splitext(item['name'])
                            if link.startswith('/'):
                                link = URL_PATH+link
                                parsed_url = urlparse(link)
                                if not base_name or not file_extension:
                                    file_name = os.path.basename(parsed_url.path)
                                file_path = ""
                                if is_valid_image_filename(file_name):
                                    file_path = IMAGES_FOLDER+"/"
                                file_name=file_path+file_name
                                if os.path.isfile(file_name):
                                    os.remove(file_name)
                                urllib.request.urlretrieve(link,file_name)
                            elif any(link.startswith(url) for url in whitelist_urls):
                                parsed_url = urlparse(link)
                                file_name = os.path.basename(parsed_url.path)
                                urllib.request.urlretrieve(link,file_name)
                            elif link.startswith('https://youtu.be/') or link.startswith('https://www.youtube.com/'):
                                with yt_dlp.YoutubeDL(YTDL_OPTIONS) as ydl:
                                    ydl.download([link])
                            elif link.startswith("https://drive.google.com/"):
                                id = extract_drive_id(link)
                                if link.startswith("https://drive.google.com/drive/folders/"):
                                    gdown.download_folder(id, quiet=False)
                                gdown.download(id=id, quiet=False)
                            else :
                                f=open(LINKS_FILE,"a+")
                                f.write(link+"\n")
                                f.close()
                        except:
                            error=link
                            errors = open(DEBUG_FILE,"a+")
                            errors.write(error+"\n")
                            errors.close()
                
if __name__ == '__main__':
    try:
        URL = input("Enter Artist URL : ")
        START = input("START from Article No. : ")
        END = input("END at Article No. : ")
        INFO = get_info(URL, START, END)
        ARTIST_NAME = INFO["artist_name"]
        URLS = INFO['urls']
        ARTICLES = INFO['articles']
        download_posts(ARTICLES, ARTIST_NAME)
    except:
        pass
   
