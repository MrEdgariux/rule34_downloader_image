from json import JSONDecodeError
import requests, os

def data(tags, page):
    p = str(page)

    ats = requests.get('https://api.rule34.xxx/index.php?page=dapi&tags=' + tags + '&s=post&q=index&json=1&limit=1000&pid=' + p)
    if ats == "":
        print("No content found.")
        os.system("pause")
        exit(0)
    else:
        try:
            ats = ats.json()
        except JSONDecodeError:
            print("No content found by your searching phrase.")
            os.system("pause")
            exit(0)
    download(ats, page, tags)


def download(ats, p, search_term):
    try:
        for i in ats:
            image_url = i["file_url"]
            dot = ".jpg"
            if '.gif' in image_url:
                dot = ".gif"
            if '.mp4' in image_url or '.mkv' in image_url:
                dot = ".mp4"

            if (os.path.isdir(__file__ + '/../images/' + search_term + '/' + str(p) + '/')):
                if (os.path.exists(__file__ + '/../images/' + search_term + '/' + str(p) + '/image_' + str(i["id"]) + dot)):
                    print("File " + str(i['id']) + " exist, skipping.")
                    pass
                else:
                    img_data = requests.get(image_url).content
                    with open(__file__ + '/../images/' + search_term + '/' + str(p) + '/image_' + str(i["id"]) + dot, 'wb') as handler:
                        handler.write(img_data)
                    print("Downloaded: " + str(i['id']) + " success")
            else:
                os.mkdir(__file__ + '/../images/')
                os.mkdir(__file__ + '/../images/' + search_term + '/')
                os.mkdir(__file__ + '/../images/' + search_term + '/' + str(p) + '/')
                img_data = requests.get(image_url).content
                with open(__file__ + '/../images/' + search_term + '/' + str(p) + '/image_' + str(i["id"]) + dot, 'wb') as handler:
                    handler.write(img_data)
                print("Downloaded: " + str(i['id']) + " success")
        print("All images successfully downloaded.")
        os.system("pause")
    except KeyboardInterrupt:
        print("Downloading cancelled by user.")
        exit(0)



t = input("Write the phrase, that are you looking for: ")
"""
Įrašyti ieškomos frazės čia
"""

p = 0
"""
Įrašyti puslapį čia
"""
data(t, p)