from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException
from datetime import datetime
import browser_cookie3
import asyncio
import requests

import discord


API_KEY = "*** INSERT 2CAPTCHA CREDENTIAL HERE ***"

LOGIN_PAGE = "https://logement.cesal.fr/espace-resident/cesal_login.php"
# Not credential, related to captcha
SITE_KEY = "6LfBVJoqAAAAADuyp4FwrsXz7voSeR91MpN_QwJQ"

FIRST_PAGE = "https://logement.cesal.fr"
MAIN_PAGE = "https://logement.cesal.fr/espace-resident/index.php"
RESA_PAGE = "https://logement.cesal.fr/espace-resident/cesal_mon_logement_reservation.php"

CESAL_MAIL = "*** INSERT CESAL CREDENTIAL HERE ***"
CESAL_PASSWORD = "*** INSERT CESAL CREDENTIAL HERE ***"

DISCORD_TOKEN = "*** INSERT DISCORD APP CREDENTIAL HERE ***"
DISCORD_USERS = []  # List of Discord user IDs to notify

END_DATE = "30/06/2026"  # Enter desired end of stay at Cesal JJ/MM/YYYY

COOKIE_FILE = "/Path/to/cookiesfile.txt"


######################
# Selenium functions #
######################


def write_cookies_to_file(cookie_string):
    with open(COOKIE_FILE, "w") as f:
        f.write(cookie_string)


def add_cookies(driver):
    with open(COOKIE_FILE, "r") as f:
        for line in f:
            name, value, domain = line.strip().split(';')
            driver.add_cookie(
                {'name': name, 'value': value, 'domain': domain})


def get_cookies():
    cj = browser_cookie3.chrome(domain_name=FIRST_PAGE)
    cookie_string = "\n".join([f"{c.name};{c.value};{c.domain}" for c in cj])
    write_cookies_to_file(cookie_string)
    return cj


async def solve_recaptcha(api_key, site_key, page_url):
    print("[*] Sending CAPTCHA solving request...")
    resp = requests.post("http://2captcha.com/in.php", data={
        'key': api_key,
        'method': 'userrecaptcha',
        'googlekey': site_key,
        'pageurl': page_url,
        'json': 1
    }).json()

    if resp['status'] != 1:
        raise Exception(f"[!] Failed to submit CAPTCHA: {resp['request']}")

    captcha_id = resp['request']
    print(f"[*] CAPTCHA submitted. ID = {captcha_id}")

    # Polling for result
    fetch_url = f"http://2captcha.com/res.php?key={api_key}&action=get&id={captcha_id}&json=1"
    for _ in range(30):
        await asyncio.sleep(5)
        res = requests.get(fetch_url).json()
        if res['status'] == 1:
            print("[+] CAPTCHA solved!")
            return res['request']
        print("[*] Waiting for result...")

    raise Exception("[!] CAPTCHA solving timed out.")


async def get_availability(cookiejar=None):
    try:
        # Setup
        driver = webdriver.Chrome()
        msg = ""

        driver.get(FIRST_PAGE)
        driver.delete_all_cookies()
        if cookiejar is not None:  # Debug case
            for c in cookiejar:
                driver.add_cookie(
                    {'name': c.name, 'value': c.value, 'domain': c.domain})
        else:  # Normal case
            add_cookies(driver)
        driver.get(MAIN_PAGE)
        WebDriverWait(driver, 10).until(
            lambda d: d.execute_script(
                'return document.readyState') == 'complete')
        cururl = driver.current_url

        # If not logged in
        if cururl == LOGIN_PAGE:
            print("Not logged in, updating cookies")

            token = await solve_recaptcha(API_KEY, SITE_KEY, LOGIN_PAGE)
            driver.execute_script("""
        document.getElementById("g-recaptcha-response").style.display = "";
        document.getElementById("g-recaptcha-response").value = arguments[0];
        """, token)

            driver.find_element(
                By.ID, "login-email").send_keys(CESAL_MAIL)
            driver.find_element(
                By.ID, "login-password").send_keys(CESAL_PASSWORD)
            remember_me = driver.find_element("id", "login-remember-me")
            driver.execute_script("arguments[0].click();", remember_me)
            driver.find_element(By.ID, "login_button").click()
            WebDriverWait(driver, 10).until(
                EC.url_changes(driver.current_url)
            )

            # Now in, saving cookies
            cookies = driver.get_cookies()
            cookie_string = "\n".join(
                [f"{c['name']};{c['value']};{c['domain']}" for c in cookies])
            write_cookies_to_file(cookie_string)
            msg = msg + "Cookies reloaded"

        # Now anyway connected:
        driver.get(RESA_PAGE)

        select_element = driver.find_element(
            By.NAME, "date_arrivee")
        select = Select(select_element)
        latest_date = select.options[-1].text  # Get latest date
        print("Latest date:", latest_date)

        # Fill in reservation form fields.
        driver.find_element(By.NAME, "date_arrivee").send_keys(latest_date)
        driver.find_element(By.NAME, "date_sortie").send_keys(END_DATE)
        WebDriverWait(driver, 20).until(
            EC.invisibility_of_element_located((By.ID, "page_loading"))
        )
        print("Date selection : " + latest_date + " - 30-06-2026")

        # Now sumbit form
        valider_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//button[@type="submit"]'))
        )
        valider_btn.click()

        # Waiting Java Text to load
        WebDriverWait(driver, 20).until(EC.presence_of_element_located(
            (By.ID, "residence_1_logements_disponibles")))

        # Extract availability
        avail_tab = []
        avail_string = ""
        for i in range(1, 7):
            try:
                element_REZ = driver.find_element(
                    By.ID, "residence_"+str(i)+"_logements_disponibles")
                print("Résidence " + str(i) + " : " + element_REZ.text)
                if element_REZ.text == "Aucun logement disponible":
                    avail_tab.append(False)
                else:
                    avail_tab.append(True)
                avail_string += "Résidence " + \
                    str(i) + " : " + element_REZ.text + "\n"
            except NoSuchElementException:
                print("Element" + str(i) + "not found")

        driver.close()
        return avail_tab, avail_string, msg
    except Exception as e:
        print(f"An error occurred: {e}")
        return None, None, str(e)
    finally:
        try:
            driver.quit()
        except:
            pass


###############
# Discord Bot #
###############


intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

# List of user IDs to send messages to
to_message = DISCORD_USERS


async def send_all(users, msg):
    for user in users:
        await user.send(msg)


def is_auto_fetch_running():
    # Check if any auto_fetch task is already running
    return any(task.get_coro().__name__ == "auto_fetch" for task in asyncio.all_tasks())


@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')
    if not is_auto_fetch_running():
        users = [await client.fetch_user(id) for id in to_message]
        asyncio.create_task(auto_fetch(users))
    else:
        print("auto_fetch task is already running")


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('$logement'):
        await message.channel.send("checking availability...")
        _, avail, msg = await get_availability()
        if avail is None:
            await message.channel.send("Error")
        else:
            print(avail)
            await message.channel.send(avail)
        if msg != "":
            await message.channel.send(msg)
    if message.content.startswith('$cstring:'):
        text = message.content
        cookie_string = text[len('$cstring:'):].strip()
        write_cookies_to_file(cookie_string)
        await message.channel.send("cookiesfile.txt updated with provided string")
    if message.content.startswith('$restart'):
        if not is_auto_fetch_running():
            users = [await client.fetch_user(id) for id in to_message]
            asyncio.create_task(auto_fetch(users))
        else:
            await message.channel.send("auto_fetch task is already running")

# async def auto_shutdown():
#     await asyncio.sleep(360)
#     print("Shut down in 30 seconds")
#     await asyncio.sleep(30)
#     print("Shut down")
#     await client.close()


async def auto_fetch(users):
    cpt = 0
    while True:
        try:
            avail_tab, avail, msg = await get_availability()
            if avail is None:
                for user in users:
                    await user.send("Erreur")
            elif (avail_tab is not None) and any(avail_tab):
                print(avail)
                for user in users:
                    await user.send(f"<@{user.id}> : Availaible housing \n" + avail)
            elif cpt % (12*6) == 0:  # Reminder bot is running every 6 hours, remove if not needed
                for user in users:
                    await user.send("No available housing since the last time")
            for user in users:
                if msg != "":
                    await user.send(msg)
        except Exception as e:
            for user in users:
                await user.send(f"Error in auto_fetch: {e}")
        cpt += 1
        await asyncio.sleep(5*60)  # Change to modify refresh rate (here 5 min)


client.run(DISCORD_TOKEN)
