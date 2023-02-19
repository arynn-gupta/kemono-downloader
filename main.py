
import requests, urllib.request, math, os ,re
from urllib.parse import urlparse
from contextlib import contextmanager
from bs4 import BeautifulSoup
import yt_dlp
import gdown

URL_PATH = "https://kemono.party"
README_FILE = "readme.txt"
DEBUG_FILE_NAME = "errors.txt"
LINKS_FILE_NAME = "links.txt"
IMAGES_FOLDER = "images"
YTDL_OPTIONS = {
    'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio',
}
VALID_DIR_NAME = r'[\\/:\*\?"<>\|]'
VALID_IMAGE = r'^[\w,\s-]+\.(jpg|jpeg|png|gif|bmp|tiff|ico)$'

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

def get_info(url, last_article):
    print("\nGET PAGE INFO : " + url, end='\n')
    r = requests.get(url)
    soup = BeautifulSoup(r.content, 'html5lib')
    artist_name = soup.find('span', attrs = {'itemprop':'name'}).text
    paginator_div = soup.find('div', attrs = {'id':'paginator-top'}) 
    total_articles = paginator_div.small.text.split()[-1]
    total_pages = math.ceil(int(total_articles) / 50)
    urls = []
    for i in range(0,total_pages):
        urls.append(url+'?o='+str(i*50))
    articles=[]
    for url in urls:
        articles.extend(get_articles(url))
    if last_article:
        n = int(last_article)
        if n<=len(articles):
            articles = articles[:-n]
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
            links.append(link['href'])
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

def download_posts(articles, artist_name):
    if len(articles)==0:
        print("No Posts found !")
    else :
        print("DOWNLOADING POSTS....", end='\n')
        for idx, article in enumerate(articles):
            reverse_index = len(articles) - idx
            path = clean_text_for_directory_name(artist_name)+"/"+str(reverse_index)+". "+clean_text_for_directory_name(article["article_name"])+"/"
            print(path)

            post = get_post(article)
            if not os.path.exists(path):
                os.makedirs(path)

            with cwd(path):

                error =""

                print("Downloading Readme....")
                if post['post_content']:
                    try:
                        if not os.path.isfile(README_FILE):
                            f=open(README_FILE,"w")
                            f.write(post['post_content'])
                            f.close()
                    except:
                        error=post['post_content']
                        errors = open(DEBUG_FILE_NAME,"a+")
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
                            errors = open(DEBUG_FILE_NAME,"a+")
                            errors.write(error+"\n")
                            errors.close()

                print("Downloading Links....")
                if post['post_links']:
                    for link in post['post_links']:
                        try:
                            link_url = link
                            if link.startswith('/'):
                                link_url = URL_PATH+link
                                parsed_url = urlparse(link_url)
                                file_name = os.path.basename(parsed_url.path)
                                file_path = ""
                                if is_valid_image_filename(file_name):
                                    file_path = IMAGES_FOLDER+"/"
                                file_name=file_path+file_name
                                if os.path.isfile(file_name):
                                    os.remove(file_name)
                                urllib.request.urlretrieve(link_url,file_name)
                            elif link.startswith('https://youtu.be/') or link.startswith('https://www.youtube.com/'):
                                with yt_dlp.YoutubeDL(YTDL_OPTIONS) as ydl:
                                    ydl.download([link_url])
                            elif link.startswith("https://drive.google.com/file/"):
                                gdown.download(link_url, quiet=False)
                            elif link.startswith("https://drive.google.com/drive/folders/"):
                                gdown.download_folder(link_url, quiet=False)
                            else :
                                f=open(LINKS_FILE_NAME,"a+")
                                f.write(link_url+"\n")
                                f.close()
                        except:
                            error=link
                            errors = open(DEBUG_FILE_NAME,"a+")
                            errors.write(error+"\n")
                            errors.close()
                

URL = input("Enter Artist URL : ")
LAST_ARTICLE = input("Enter last downloaded post : ")
INFO = get_info(URL, LAST_ARTICLE)
ARTIST_NAME = INFO["artist_name"]
URLS = INFO['urls']
ARTICLES = INFO['articles']

download_posts(ARTICLES, ARTIST_NAME)
   
