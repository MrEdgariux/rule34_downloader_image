from json import JSONDecodeError
import requests, os
import customtkinter as ctk
import tkinter.messagebox as msg
import threading
import sys

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")
sema = threading.Semaphore(8)

def download_image(image_url, location, image_id, sema):
    dot = ".jpg"
    if '.gif' in image_url:
        dot = ".gif"
    if '.mp4' in image_url or '.mkv' in image_url:
        dot = ".mp4"
    
    try:
        sema.acquire()
        img_data = requests.get(image_url).content
        with open(location + 'image_' + str(image_id) + dot, 'wb') as handler:
            handler.write(img_data)
    except:
        print("Failed to download image: " + str(image_id))
        sema.release()
    finally:
        sema.release()

def killdw():
    """Kills all downloads"""
    confirmation = msg.askyesno("Kill Threads", "Are you sure that you want to kill all downloading content?")
    if confirmation:
        confirmation2 = msg.askyesnocancel("Are you really sure?", "IF YOU PROCEED, IT MIGHT LEAD TO CORRUPTED IMAGES! ARE YOU REALLY SURE?")
        if confirmation2:
            print("Killing application")
            sys.exit()
        else:
            return
    else:
        return
        

def download(ats, search_term):
    yra = len(ats)
    skaiciavimas = 0
    skipped_ids = []

    location = __file__ + '/../images/' + search_term + '/'

    
    for i in ats:
        image_url = i["file_url"]

        dot = ".jpg"
        if '.gif' in image_url:
            dot = ".gif"
        if '.mp4' in image_url or '.mkv' in image_url:
            dot = ".mp4"
        
        if (os.path.isdir(location)):
            if (os.path.exists(location + 'image_' + str(i["id"]) + dot)):
                skipped_ids.append(i['id'])
                yra = yra - 1
                continue
            else:
                t = threading.Thread(target=download_image, args=(image_url, location, i["id"], sema))
                t.start()
                skaiciavimas = skaiciavimas + 1
        else:
            if not os.path.isdir(__file__ + '/../images/'):
                os.mkdir(__file__ + '/../images/')
            if not os.path.isdir(__file__ + '/../images/' + search_term + '/'):
                os.mkdir(__file__ + '/../images/' + search_term + '/')

            t = threading.Thread(target=download_image, args=(image_url, location, i["id"], sema))
            t.start()
            skaiciavimas = skaiciavimas + 1
    if len(skipped_ids) != 0:
        print("Skipped: " + str(len(skipped_ids)) + " images with id's: ")
        for id in skipped_ids:
            print(str(id))
    msg.showinfo("Downloading", "Successfully started to download " + str(skaiciavimas) + " images!")

def my_thread(tags):
    atsakas = []
    p = 0
    atsa = 0
    while True:
        ats = requests.get('https://api.rule34.xxx/index.php?page=dapi&tags=' + tags + '&s=post&q=index&json=1&limit=1000&pid=' + str(p))
        if ats == "":
            errors.configure(text="No content was found!", font= ('Helvetica 13'))
            break
        else:
            try:
                atsj = ats.json()
                atsakas.extend(atsj)
                if (len(atsj) < 1000):
                    atsa += len(atsj)
                    info.configure(text="We found " + str(atsa) + " content to download, waiting for confirmation")
                    # Ask for confirmation
                    confirmation = msg.askyesno("Start download?", "We found " + str(atsa) + " content, do you want download it?")

                    # Check the user's response
                    if confirmation:
                        print("You have confirmed, that you want to download " + str(atsa) + " content of " + tags)
                        download(atsakas, tags)
                        info.configure(text="")
                        break
                    else:
                        print("You have cancelled download " + str(atsa) + " content of " + tags)
                        errors.configure(text="You have cancelled your operation", font= ('Helvetica 13'))
                        info.configure(text="")
                        break
                info.configure(text="We found " + str(atsa) + " content to download, loading more...")
                p += 1
                atsa += 1000
                print(str(p) + " sekmingai pratęstas! Atsiųsta iš viso " + str(atsa))
            except JSONDecodeError:
                errors.configure(text="No content was found!", font= ('Helvetica 13'))
                break

def data():
    atsakas = []
    tags = text_1.get()
    p = 0
    print(tags)
    if (checkbox_1.get() == 1):
        t = threading.Thread(target=my_thread, args=(tags,))
        t.start()
        info.configure(text="Content will be searched and this message will be updated with information!")
    else:
        pagea = page.get()
        if not pagea:
            msg.showerror("CRITICAL", "Please enter an number to continue")
        if 'kids' in tags:
            errors.configure(text="This isn't allowed there!", font= ('Helvetica 13'))
            return
        if 'child' in tags:
            errors.configure(text="This isn't allowed there!", font= ('Helvetica 13'))
            return
        if pagea:
            p = str(pagea)
            ats = requests.get('https://api.rule34.xxx/index.php?page=dapi&tags=' + tags + '&s=post&q=index&json=1&limit=1000&pid=' + p)
            if ats == "":
                errors.configure(text="No content was found!", font= ('Helvetica 13'))
                return
            else:
                try:
                    ats = ats.json()
                    atsakas.extend(ats)
                except JSONDecodeError:
                    errors.configure(text="No content was found!", font= ('Helvetica 13'))
                    return
            download(atsakas, tags)

def toggle_entry_state():
    if checkbox_1.get() == True:
        page.pack_forget()
    else:
        page.pack(pady=20, padx=10)


ct = ctk.CTk()


ct.title("Rule 34 downloader")
ct.geometry(f"{1100}x{580}")

frame_1 = ctk.CTkFrame(master=ct)
frame_2 = ctk.CTkFrame(master=ct)
frame_1.pack(pady=20, padx=30, fill="both", expand=True)
frame_2.pack(pady=20, padx=30, fill="both", expand=True)

errors = ctk.CTkLabel(master=frame_1, text="", text_color="red")
errors.pack(pady=10, padx=10)

info = ctk.CTkLabel(master=frame_1, text="")
info.pack(pady=10, padx=10)

text_1 = ctk.CTkEntry(master=frame_2, placeholder_text="What tags do you preffer?", width=300)
text_1.pack(pady=10, padx=10)

page = ctk.CTkEntry(master=frame_2, placeholder_text="Page to download", width=300)
page.pack(pady=20, padx=10)

checkbox_1 = ctk.CTkCheckBox(master=frame_2, text="Download everything", command=toggle_entry_state)
checkbox_1.pack(pady=10, padx=10)

button_1 = ctk.CTkButton(master=frame_2, text="Start", command=data)
button_1.pack(pady=10, padx=10)

button_em = ctk.CTkButton(master=frame_2, text="Kill download", command=killdw)
button_em.pack(pady=10, padx=10)
try:
    ct.mainloop()
except KeyboardInterrupt:
    exit(0)