from json import JSONDecodeError
import json, requests, os, threading, sys, sqlite3, re, logging, configparser
import customtkinter as ctk
import tkinter.messagebox as msg

version = "2.7"
config_ver = "1.0"

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
    config.set('File Paths', 'sqlite db folder', os.path.join(roaming_folder, 'nsfw_project'))
    config.set('File Paths', 'image folder', os.path.join(script_directory, 'images'))
    config.set('File Paths', 'videos folder', os.path.join(script_directory, 'videos'))
    config.set('File Paths', 'gif folder', os.path.join(script_directory, 'animations'))
    config.set('File Paths', 'logs folder', os.path.join(roaming_folder, 'nsfw_project', 'logs'))
    config.add_section('File Naming')
    config.set('File Naming', 'prefix', 'image_')
    with open('config.ini', 'w') as configfile:
        config.write(configfile)

if os.path.exists("config.ini"):
    config = load_config()
    if config.get('Software', 'configversion') != config_ver:
        os.remove("config.ini")
        create_config(version, config_ver)
else:
    create_config(version, config_ver)
    config = load_config()


# -- Begin of config file loaders --

path_logs = config.get('File Paths', 'logs folder')
if not os.path.exists(path_logs):
    os.makedirs(path_logs)

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


if not os.path.exists(config.get('File Paths', 'sqlite db folder')):
    os.makedirs(config.get('File Paths', 'sqlite db folder'))
    logging.info("Folder path for database created")
# -- End of config file loaders --

conn = sqlite3.connect(os.path.join(config.get('File Paths', 'sqlite db folder'), 'content.db'))
c = conn.cursor()
# Create the 'Images' table
c.execute('''CREATE TABLE IF NOT EXISTS Images (
                id INTEGER PRIMARY KEY,
                image_id INTEGER,
                entity TEXT,
                datetime DATETIME DEFAULT CURRENT_TIMESTAMP)''')

# Create the 'Videos' table
c.execute('''CREATE TABLE IF NOT EXISTS Videos (
                id INTEGER PRIMARY KEY,
                image_id INTEGER,
                entity TEXT,
                datetime DATETIME DEFAULT CURRENT_TIMESTAMP)''')

# Create the 'Animations' table
c.execute('''CREATE TABLE IF NOT EXISTS Animations (
                id INTEGER PRIMARY KEY,
                image_id INTEGER,
                entity TEXT,
                datetime DATETIME DEFAULT CURRENT_TIMESTAMP)''')

# Commit the changes to the database
conn.commit()
conn.close()

left_images_download = 0
total_images_need = 0
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")
sema = threading.Semaphore(8)

def sanitize_filename(filename):
    # Replace all characters that are not letters or digits with an underscore
    return re.sub(r'[^a-zA-Z0-9]', '_', filename)

def download_image(image_url, entity, location, image_id, sema):
    global left_images_download
    global total_images_need
    config = load_config()
    prefix = config.get("File Naming", 'prefix')
    conna = sqlite3.connect(os.path.join(config.get('File Paths', 'sqlite db folder'), 'content.db'))
    ca = conna.cursor()
    dot = ".jpg"
    table = "Images"
    if '.gif' in image_url:
        dot = ".gif"
        table = "Animations"
    elif '.mp4' in image_url or '.mkv' in image_url:
        dot = ".mp4"
        table = "Videos"
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
            query = "INSERT INTO {} (image_id, entity) VALUES (?,?)".format(table)
            ca.execute(query, (image_id,entity))
            conna.commit()
        conna.close()
        sema.release()
        

def download(ats, search_term):
    global left_images_download
    global total_images_need
    config = load_config()
    if total_images_need != 0 and left_images_download == 0:
        total_images_need = 0
    elif total_images_need != 0 and left_images_download == 1:
        total_images_need = 0
        left_images_download = 0
    conn = sqlite3.connect(os.path.join(config.get('File Paths', 'sqlite db folder'), 'content.db'))
    c = conn.cursor()
    yra = len(ats)
    skipped_ids = []
    entity = search_term
    search_term = sanitize_filename(search_term)

    gif_loc = config.get('File Paths', 'gif folder')
    image_loc = config.get('File Paths', 'image folder')
    videos_loc = config.get('File Paths', 'videos folder')
    prefix = config.get('File Naming', 'prefix')
    for i in ats:
        image_url = i["file_url"]

        if '.gif' in image_url:
            dot = ".gif"
            location = os.path.join(gif_loc, search_term)
            c.execute("SELECT * FROM Animations WHERE image_id = ?", (i["id"],))
        elif '.mp4' in image_url or '.mkv' in image_url:
            dot = ".mp4"
            location = os.path.join(videos_loc, search_term)
            c.execute("SELECT * FROM Videos WHERE image_id = ?", (i["id"],))
        else:
            dot = ".jpg"
            location = os.path.join(image_loc, search_term)
            c.execute("SELECT * FROM Images WHERE image_id = ?", (i["id"],))

        # Iterate over the results and print them out
        if len(c.fetchall()) > 0:
            if os.path.exists(os.path.join(location, f"{prefix}{i['id']}{dot}")):
                skipped_ids.append(i['id'])
                yra = yra - 1
                continue
        if (os.path.isdir(location)):
            if (os.path.exists(os.path.join(location, f"{prefix}{i['id']}{dot}"))):
                skipped_ids.append(i['id'])
                yra = yra - 1
                continue
            else:
                left_images_download += 1
                total_images_need += 1
                t = threading.Thread(target=download_image, args=(image_url, entity, location, i["id"], sema))
                t.start()
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
            t = threading.Thread(target=download_image, args=(image_url, entity, location, i["id"], sema))
            t.start()
    msg.showinfo("Downloading", "Successfully started to download " + str(total_images_need) + " images!")
    logging.info(f"Download of {entity} started successfully.")
    logging.info(f"{yra} images downloading queued.")
    if len(skipped_ids) != 0:
        print("Skipped: " + str(len(skipped_ids)) + " images")
        logging.info(f"{len(skipped_ids)} images skipped.")
    conn.close()
def my_thread(tags):
    atsakas = []
    p = 0
    atsa = 0
    logging.info(f" --- Data fetching of {tags} started --- ")
    while True:
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
                atsakas.extend(atsj)
                if (len(atsj) < 1000):
                    atsa += len(atsj)
                    info.configure(text=f"Found {atsa} content")
                    logging.info(f"{atsa} of {tags} found to download")
                    # Ask for confirmation
                    confirmation = msg.askyesno("Confirmation", f"{atsa} content found, start downloading process?")

                    # Check the user's response
                    if confirmation:
                        logging.info(f"{atsa} of {tags} started queuing.")
                        download(atsakas, tags)
                        info.configure(text="")
                        break
                    else:
                        print(f"{tags} download cancelled")
                        logging.info(f"{atsa} of {tags} cancelled")
                        info.configure(text="")
                        break
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
    atsakas = []
    tags = text_1.get()
    p = 0
    print(tags)
    if (checkbox_1.get() == 1):
        t = threading.Thread(target=my_thread, args=(tags,))
        t.start()
    else:
        pagea = page.get()
        if not pagea:
            msg.showerror("CRITICAL", "Please enter an number to continue")
        if 'kid' in tags:
            errors.configure(text="This isn't allowed there!")
            wl.warning(f"Your request of {tags} was rejected by filtering system that detected word: kid")
            return
        if 'child' in tags:
            errors.configure(text="This isn't allowed there!")
            wl.warning(f"Your request of {tags} was rejected by filtering system that detected word: child")
            return
        if pagea:
            logging.info(f" --- Data fetching of {tags} started --- ")
            p = str(pagea)
            try:
                ats = requests.get('https://api.rule34.xxx/index.php?page=dapi&tags=' + tags + '&s=post&q=index&json=1&limit=1000&pid=' + p)
                if ats == "":
                    errors.configure(text="No content was found!")
                    logging.info(f"No content of {tags} was found")
                    return
                else:
                    try:
                        ats = ats.json()
                        atsakas.extend(ats)
                    except JSONDecodeError:
                        errors.configure(text="No content was found!")
                        logging.info(f"No content of {tags} was found")
                        return
            except requests.exceptions.SSLError:
                errors.configure(text="Error code: 02")
                return
            download(atsakas, tags)
    logging.info(f" --- Data fetching of {tags} ended --- ")


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

page = ctk.CTkEntry(master=frame_2, placeholder_text="Page to download", width=300)
page.pack(pady=20, padx=10)

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