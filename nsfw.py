from json import JSONDecodeError
import json, requests, os, threading, sys, sqlite3, re, logging, configparser
import customtkinter as ctk
import tkinter.messagebox as msg

version = "2.9"
config_ver = "1.2"

def load_config():
    config = configparser.ConfigParser()
    config.read('config.ini')
    return config

def create_config(ver, configver):
    config = configparser.ConfigParser()
    script_directory = os.path.dirname(os.path.abspath(__file__))
    roaming_folder = os.path.expanduser('~\\AppData\\Roaming')
    # Config creation task.
    config.add_section('Software')
    config.set('Software', 'version', ver)
    config.set('Software', 'configversion', configver)
    config.add_section('File Paths')
    config.set('File Paths', 'image folder', os.path.join(script_directory, 'images'))
    config.set('File Paths', 'videos folder', os.path.join(script_directory, 'videos'))
    config.set('File Paths', 'gif folder', os.path.join(script_directory, 'animations'))
    config.set('File Paths', 'logs folder', os.path.join(roaming_folder, 'nsfw_project', 'logs'))
    config.set('File Paths', 'cache folder', os.path.join(roaming_folder, 'nsfw_project', 'cache'))
    config.add_section('File Naming')
    config.set('File Naming', 'prefix', 'image_')
    config.add_section('Download')
    config.set('Download', 'max threads', '16')
    with open('config.ini', 'w') as configfile:
        config.write(configfile)

if os.path.exists("config.ini"):
    config = load_config()
    if config.get('Software', 'configversion') != config_ver:
        config.clear()
        os.remove("config.ini")
        create_config(version, config_ver)
        config = load_config()
else:
    create_config(version, config_ver)
    config = load_config()


# -- Begin of config file loaders --

path_logs = config.get('File Paths', 'logs folder')
cache_fold = config.get('File Paths', 'cache folder')
if not os.path.exists(path_logs):
    os.makedirs(path_logs)

if not os.path.exists(cache_fold):
    os.makedirs(cache_fold)

# Logs Initiation
logging.basicConfig(filename=os.path.join(path_logs, 'logs.log'), level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Create a logger for error logs
el = logging.getLogger('error_logs')
error_handler = logging.FileHandler(os.path.join(path_logs, 'error_logs.log'))
error_handler.setLevel(logging.ERROR)
error_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
error_handler.setFormatter(error_formatter)
el.addHandler(error_handler)

# Create a logger for warning logs
wl = logging.getLogger('warn_logs')
warn_handler = logging.FileHandler(os.path.join(path_logs, 'warn_logs.log'))
warn_handler.setLevel(logging.WARNING)
warn_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
warn_handler.setFormatter(warn_formatter)
wl.addHandler(warn_handler)

sema = threading.Semaphore(int(config.get('Download', 'max threads')))
# -- End of config file loaders --

left_images_download = 0
total_images_need = 0
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

def sanitize_filename(filename):
    # Replace all characters that are not letters or digits with an underscore
    return re.sub(r'[^a-zA-Z0-9]', '_', filename)

def load_cache():
    config = load_config()
    cache_file = os.path.join(config.get('File Paths', 'cache folder'), "cache.json")
    
    if os.path.exists(cache_file):
        with open(cache_file, 'r') as file:
            return json.load(file)
    else:
        return {}
    
def check_cache(entity):
    cache = load_cache()
    if 'entity' not in cache:
        cache['entity'] = {}
    
    if entity in cache['entity']:
        return list(cache['entity'].values())
    else:
        return None

def save_cache(data):
    config = load_config()
    cache_file = os.path.join(config.get('File Paths', 'cache folder'), "cache.json")
    
    with open(cache_file, 'w') as file:
        json.dump(data, file, indent=4)

def update_cache(entity, data):
    cache = load_cache()
    
    if 'entity' not in cache:
        cache['entity'] = {}
        
    cache['entity'][entity] = data
    save_cache(cache)

def download_image(image_url, location, image_id, sema):
    global left_images_download
    global total_images_need
    config = load_config()
    prefix = config.get("File Naming", 'prefix')
    dot = ".jpg"
    if '.gif' in image_url:
        dot = ".gif"
    elif '.mp4' in image_url or '.mkv' in image_url:
        dot = ".mp4"
    failed = False
    try:
        sema.acquire()
        img_data = requests.get(image_url).content
        with open(os.path.join(location, f"{prefix}{image_id}{dot}"), "wb") as handler:
            handler.write(img_data)
        
    except Exception as e:
        wl.warning(f"Failed to download image with id: {image_id} from source {image_url}")
        el.error(f"Error while downloading {image_id} : {e}")
        print(f"Failed to download image: {image_id}")
        failed = True
        sema.release()
    finally:
        if not failed:
            left_images_download -= 1
            progress_txt.configure(text="Download left: " + str(left_images_download))
        sema.release()
        

def download(ats, search_term, tipas):
    global left_images_download
    global total_images_need
    config = load_config()
    if total_images_need != 0 and left_images_download == 0:
        total_images_need = 0
    elif total_images_need != 0 and left_images_download == 1:
        total_images_need = 0
        left_images_download = 0
    yra = len(ats)
    skipped_ids = []
    threads = []
    entity = search_term
    search_term = sanitize_filename(search_term)

    gif_loc = config.get('File Paths', 'gif folder')
    image_loc = config.get('File Paths', 'image folder')
    videos_loc = config.get('File Paths', 'videos folder')
    prefix = config.get('File Naming', 'prefix')
    for i in ats:
        image_url = i['file_url']
        if tipas != "All":
            if tipas == "Videos" and '.mp4' in image_url:
                dot = ".mp4"
                if not os.path.isdir(os.path.join(videos_loc, search_term)):
                    os.makedirs(os.path.join(videos_loc, search_term))
                location = os.path.join(videos_loc, search_term)
            
            elif tipas == "Images" and '.jpg' in image_url:
                dot = ".jpg"
                if not os.path.isdir(os.path.join(image_loc, search_term)):
                    os.makedirs(os.path.join(image_loc, search_term))
                location = os.path.join(image_loc, search_term)

            elif tipas == "Animations" and '.gif' in image_url:
                dot = ".gif"
                if not os.path.isdir(os.path.join(gif_loc, search_term)):
                    os.makedirs(os.path.join(gif_loc, search_term))
                location = os.path.join(gif_loc, search_term)
            else:
                continue

            if (os.path.isdir(location)):
                if (os.path.exists(os.path.join(location, f"{prefix}{i['id']}{dot}"))):
                    skipped_ids.append(i['id'])
                    yra = yra - 1
                    continue
                else:
                    left_images_download += 1
                    total_images_need += 1
                    t = threading.Thread(target=download_image, args=(image_url, location, i["id"], sema))
                    threads.append(t)
            else:
                if dot == ".gif":
                    if not os.path.isdir(os.path.join(gif_loc, search_term)):
                        os.makedirs(os.path.join(gif_loc, search_term))
                elif dot == ".mp4":
                    if not os.path.isdir(os.path.join(videos_loc, search_term)):
                        os.makedirs(os.path.join(videos_loc, search_term))
                else:
                    if not os.path.isdir(os.path.join(image_loc, search_term)):
                        os.makedirs(os.path.join(image_loc, search_term))
                left_images_download += 1
                total_images_need += 1
                t = threading.Thread(target=download_image, args=(image_url, location, i["id"], sema))
                threads.append(t)
        else:
            image_url = i["file_url"]

            if '.gif' in image_url:
                dot = ".gif"
                location = os.path.join(gif_loc, search_term)
            elif '.mp4' in image_url or '.mkv' in image_url:
                dot = ".mp4"
                location = os.path.join(videos_loc, search_term)
            else:
                dot = ".jpg"
                location = os.path.join(image_loc, search_term)

            # Iterate over the results and print them out
            if (os.path.isdir(location)):
                if (os.path.exists(os.path.join(location, f"{prefix}{i['id']}{dot}"))):
                    skipped_ids.append(i['id'])
                    yra = yra - 1
                    continue
                else:
                    left_images_download += 1
                    total_images_need += 1
                    t = threading.Thread(target=download_image, args=(image_url, location, i["id"], sema))
                    threads.append(t)
            else:
                if dot == ".gif":
                    if not os.path.isdir(os.path.join(gif_loc, search_term)):
                        os.makedirs(os.path.join(gif_loc, search_term))
                elif dot == ".mp4":
                    if not os.path.isdir(os.path.join(videos_loc, search_term)):
                        os.makedirs(os.path.join(videos_loc, search_term))
                else:
                    if not os.path.isdir(os.path.join(image_loc, search_term)):
                        os.makedirs(os.path.join(image_loc, search_term))
                left_images_download += 1
                total_images_need += 1
                t = threading.Thread(target=download_image, args=(image_url, location, i["id"], sema))
                threads.append(t)
    # update_cache(entity, ats)
    logging.info(f"Starting all threads of {entity} - {len(threads)}...")
    for thread in threads:
        thread.start()
    logging.info(f"Download of {entity} started successfully.")
    msg.showinfo("Downloading", "Successfully started to download " + str(total_images_need) + " images!")
    logging.info(f"{yra} images downloading queued.")
    if len(skipped_ids) != 0:
        print("Skipped: " + str(len(skipped_ids)) + " images")
        logging.info(f"{len(skipped_ids)} images skipped.")

def my_thread(tags, tipas, end = -1, start = 0):
    atsakas = []
    p = start
    atsa = 0
    logging.info(f" --- Data fetching of {tags} started --- ")
    while True:
        if end != -1:
            if p == end:
                info.configure(text=f"Found {atsa} content")
                logging.info(f"{atsa} of {tags} found to download")
                # Ask for confirmation
                confirmation = msg.askyesno("Confirmation", f"{atsa} content found, start downloading process?")

                # Check the user's response
                if confirmation:
                    logging.info(f"{atsa} of {tags} started queuing.")
                    download(atsakas, tags, tipas)
                    info.configure(text="")
                    break
                else:
                    print(f"{tags} download cancelled")
                    logging.info(f"{atsa} of {tags} cancelled")
                    info.configure(text="")
                    break
        try:
            ats = requests.get('https://api.rule34.xxx/index.php?page=dapi&tags=' + tags + '&s=post&q=index&json=1&limit=1000&pid=' + str(p))
        except requests.exceptions.SSLError:
            errors.configure(text="Error code: 02")
            el.error("Failed to get API response.")
            el.error("Error code: 02")
            el.error("Error occured by: SSLError, no sertificate detected")
            break
        except requests.exceptions.ConnectionError:
            errors.configure(text="Error code: 03")
            el.error("Failed to get API response.")
            el.error("Error code: 03")
            el.error("Error occured by: ConnectionError, no available internet connection found")
            break
        except:
            errors.configure(text="Error code: 04") # This might occur internet blocking / firewall or something like this ;)
            el.error("Failed to get API response.")
            el.error("Error code: 04")
            el.error("Error occured by: No connection between available, maybe a firewall or just internet provider blocking the api")
            break
        if ats == "":
            errors.configure(text="No content was found!")
            logging.info(f"{tags} has no content to download")
            break
        else:
            try:
                atsj = ats.json()
                for item in atsj:
                    atsj_2 = {
                        "id": item['id'],
                        "file_url": item['file_url']
                    }
                    atsakas.append(atsj_2)
                    atsj_2 = None
                if (len(atsj) < 1000):
                    atsa += len(atsj)
                    info.configure(text=f"Found {atsa} content")
                    logging.info(f"{atsa} of {tags} found to download")
                    # Ask for confirmation
                    confirmation = msg.askyesno("Confirmation", f"{atsa} content found, start downloading process?")

                    # Check the user's response
                    if confirmation:
                        logging.info(f"{atsa} of {tags} started queuing.")
                        download(atsakas, tags, tipas)
                        info.configure(text="")
                        break
                    else:
                        print(f"{tags} download cancelled")
                        logging.info(f"{atsa} of {tags} cancelled")
                        info.configure(text="")
                        break
                atsj = None
                p += 1
                atsa += 1000
                info.configure(text=f"{tags} - {atsa}")
                logging.info(f"{tags} - {p} - {atsa}")
                print(f"{p} will be fetched...")
            except JSONDecodeError:
                errors.configure(text="No content was found!")
                logging.info(f"No content of {tags} was found")
                break
    logging.info(f" --- Data fetching of {tags} ended --- ")

def data():
    tags = text_1.get()
    tipas = type.get()
    print(tags)
    if (checkbox_1.get() == 1):
        t = threading.Thread(target=my_thread, args=(tags,tipas,))
        t.start()
    else:
        range_input = page.get()
        if "-" in range_input:
            range_values = range_input.split("-")

            if len(range_values) != 2:
                print("Invalid input. Please use the format 'start-end'.")
                return
            try:
                start = int(range_values[0])
                end = int(range_values[1])
            except ValueError:
                msg.showerror("Invalid input", "Please enter valid numbers.")
                return
            if start > end:
                msg.showerror("Invalid range", "Start value should be less than end value.")
                return
            
            t = threading.Thread(target=my_thread, args=(tags,tipas,end,start,))
            t.start()
        else:
            try:
                pagea = int(page.get())
            except ValueError:
                msg.showerror("CRITICAL", "You must enter number OR range number (start-end)")
                return
            if not pagea:
                msg.showerror("CRITICAL", "Please enter how many pages you want to download")
            else:
                t = threading.Thread(target=my_thread, args=(tags,tipas,pagea,))
                t.start()

def toggle_entry_state():
    if checkbox_1.get() == True:
        page.pack_forget()
    else:
        page.pack(pady=20, padx=10)


ct = ctk.CTk()

logging.info(" --- Building application --- ")
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

progress_txt = ctk.CTkLabel(master=frame_2, text="Downloaded: 0")
progress_txt.pack(pady=10, padx=10)

text_1 = ctk.CTkEntry(master=frame_2, placeholder_text="What tags do you preffer?", width=300)
text_1.pack(pady=10, padx=10)

page = ctk.CTkEntry(master=frame_2, placeholder_text="How much pages to download", width=300)
page.pack(pady=20, padx=10)

tipai = [
    "All",
    "Images",
    "Videos",
    "Animations"
]

type = ctk.CTkComboBox(frame_2, values=tipai, state="readonly")
type.set("All")
type.pack(pady=20, padx=10)

checkbox_1 = ctk.CTkCheckBox(master=frame_2, text="Download everything", command=toggle_entry_state)
checkbox_1.pack(pady=10, padx=10)

button_1 = ctk.CTkButton(master=frame_2, text="Start", command=data)
button_1.pack(pady=10, padx=10)
try:
    logging.info("Application started successfully")
    ct.mainloop()
except KeyboardInterrupt:
    el.error(" --- Application crashed --- ")
    exit(0)