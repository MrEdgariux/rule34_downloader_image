from json import JSONDecodeError
import json
import requests, os
import customtkinter as ctk
import tkinter.messagebox as msg
import threading
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")
sema = threading.Semaphore(8)

def download_image(image_url, search_term, p, image_id, sema):
    dot = ".jpg"
    if '.gif' in image_url:
        dot = ".gif"
    if '.mp4' in image_url or '.mkv' in image_url:
        dot = ".mp4"
    
    try:
        sema.acquire()
        img_data = requests.get(image_url).content
        with open(__file__ + '/../images/' + search_term + '/' + str(p) + '/image_' + str(image_id) + dot, 'wb') as handler:
            handler.write(img_data)
    except:
        print("Failed to download image: " + str(image_id))
        msg.showwarning("Failed to download", "Image with id " + str(image_id) + " failed to download!")
        sema.release()
    finally:
        sema.release()
        

def download(ats, p, search_term):
    downloaded_data = []
    yra = len(ats)
    skaiciavimas = 0
    
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
                yra = yra - 1
                continue
            else:
                t = threading.Thread(target=download_image, args=(image_url, search_term, p, i["id"], sema))
                t.start()
                downloaded_data.append(i['id'])
                skaiciavimas = skaiciavimas + 1
        else:
            if not os.path.isdir(__file__ + '/../images/'):
                os.mkdir(__file__ + '/../images/')
            os.mkdir(__file__ + '/../images/' + search_term + '/')
            os.mkdir(__file__ + '/../images/' + search_term + '/' + str(p) + '/')
            t = threading.Thread(target=download_image, args=(image_url, search_term, p, i["id"], sema))
            t.start()
            downloaded_data.append(i['id'])
            skaiciavimas = skaiciavimas + 1
    
    msg.showinfo("Downloading", "Successfully started to download " + str(skaiciavimas) + " images!")


def data():
    tags = text_1.get()
    pagea = page.get()

    print(tags)

    if 'kids' in tags:
        errors.configure(text="This isn't allowed there!", font= ('Helvetica 13'))
        return
    if 'child' in tags:
        errors.configure(text="This isn't allowed there!", font= ('Helvetica 13'))
        return
    p = str(pagea)

    ats = requests.get('https://api.rule34.xxx/index.php?page=dapi&tags=' + tags + '&s=post&q=index&json=1&limit=1000&pid=' + p)
    if ats == "":
        errors.configure(text="No content was found!", font= ('Helvetica 13'))
        return
    else:
        try:
            ats = ats.json()
        except JSONDecodeError:
            errors.configure(text="No content was found!", font= ('Helvetica 13'))
            return
    download(ats, p, tags)



ct = ctk.CTk()


ct.title("Rule 34 downloader")
ct.geometry(f"{1100}x{580}")

frame_1 = ctk.CTkFrame(master=ct)
frame_1.pack(pady=20, padx=60, fill="both", expand=True)

errors = ctk.CTkLabel(master=frame_1, text="", text_color="red")
errors.pack(pady=10, padx=10)

progressbar_1 = ctk.CTkProgressBar(master=frame_1)
progressbar_1.pack(pady=10, padx=10)

text_1 = ctk.CTkEntry(master=frame_1)
text_1.pack(pady=10, padx=10)

page = ctk.CTkEntry(master=frame_1, placeholder_text="Page, default 0", text="0")
page.pack(pady=20, padx=10)

button_1 = ctk.CTkButton(master=frame_1, command=data)
button_1.pack(pady=10, padx=10)
try:
    ct.mainloop()
except KeyboardInterrupt:
    exit(0)