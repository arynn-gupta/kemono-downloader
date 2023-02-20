import os, re
import os.path

files_with_errors = []
drive_links = []
youtube_links = []
unknown_links = []
errors =[]
YTDL_OPTIONS = {
    'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio',
}

def extract_drive_id(url):
    match = re.search(r'([\w-]{25,})', url)
    if match:
        return match.group(1)
    return None

for dirpath, dirnames, filenames in os.walk("."):
    for filename in [f for f in filenames if f.endswith("errors.txt")]:
        files_with_errors.append(os.path.join(dirpath, filename))

for file in files_with_errors:
    f = open(file, 'r')
    print("\n"+file,end="\n")
    for line in f:
        line = line.rstrip('\n')
        print(line,end="\n")
        if line:
            if line.startswith("https://drive.google.com/"):
                drive_links.append(line)
            elif line.startswith('https://youtu.be/') or line.startswith('https://www.youtube.com/'):
                youtube_links.append(line)
            else:
                unknown_links.append(line)
    f.close()

# -----fix drive errors--------

# import gdown
# for link in drive_links:
#     try:
#         id = extract_drive_id(link)
#         if link.startswith("https://drive.google.com/drive/folders/"):
#             gdown.download_folder(id, quiet=False)
#         gdown.download(id=id, quiet=False)
#     except:
#         errors.append(link)
# print(*errors,sep='\n')

# -----fix youtube errors--------

# import yt_dlp
# for link in youtube_links:
#     try:
#         with yt_dlp.YoutubeDL(YTDL_OPTIONS) as ydl:
#             ydl.download([link])
#     except:
#         errors.append(link)
# print(*errors,sep='\n')

print("\nGoogle Drive Errors : \n")
print(*drive_links,sep='\n')

print("\nUnkwon URL Errors : \n")
print(*unknown_links,sep='\n')

print("\nYoutube Errors : \n")
print(*youtube_links,sep='\n')