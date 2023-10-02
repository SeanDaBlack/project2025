import argparse
import os
import time
import faker, random
import requests
from selenium.webdriver.remote.remote_connection import LOGGER
from faker_e164.providers import E164Provider
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.chrome.service import Service

from resume_faker import make_resume
from email_data import *
import random
from constants import IDs, CLOUD_ENABLED, CLOUD_DISABLED
import json

fake = faker.Faker()
fake.add_provider(E164Provider)

parser = argparse.ArgumentParser("SCRIPT_DESCRIPTION")
parser.add_argument('--cloud', action='store_true', default=CLOUD_DISABLED,
                    required=False, help="Run in cloud", dest='cloud')
#add limit argument to limit number of applications
parser.add_argument('--limit', type=int, default=1,
                    required=False, help="limits the number of prompts", dest='limit')
args = parser.parse_args()


def random_email(name=None):
    if name is None:
        name = fake.name()

    mailGens = [
        lambda fn, ln, *names: fn + ln,
        lambda fn, ln, *names: fn + "." + ln,
        lambda fn, ln, *names: fn + "_" + ln,
        lambda fn, ln, *names: fn[0] + "." + ln,
        lambda fn, ln, *names: fn[0] + "_" + ln,
        lambda fn, ln, *names: fn + ln + str(int(1 / random.random() ** 3)),
        lambda fn, ln, *names: fn + "." + ln + str(int(1 / random.random() ** 3)),
        lambda fn, ln, *names: fn + "_" + ln + str(int(1 / random.random() ** 3)),
        lambda fn, ln, *names: fn[0] + "." + ln + str(int(1 / random.random() ** 3)),
        lambda fn, ln, *names: fn[0] + "_" + ln + str(int(1 / random.random() ** 3)),
    ]

    emailChoices = [float(line[2]) for line in EMAIL_DATA]

    return (
        random.choices(mailGens, MAIL_GENERATION_WEIGHTS)[0](*name.split(" ")).lower()
        + "@"
        + random.choices(EMAIL_DATA, emailChoices)[0][1]
    )


def gen_fake_number():
    return "".join(
        [
            "{}".format(random.randint(100, 999)),
            "{}".format(random.randint(100, 999)),
            "{}".format(random.randint(100, 999)),
        ]
    )

#
def createFakeIdentity():
    # age = random.randint(18, 55)
    fake_identity = {
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "email": "",
        "phone": fake.safe_e164(region_code="US").replace("+1", ""),
        "address": fake.street_address(),
        "city": fake.city(),
        "zip": (random.randint(10000, 99999)),
    }
    fake_identity.update(
        {
            "email": random_email(
                fake_identity.get("first_name") + " " + fake_identity.get("last_name")
            )
        }
    )

    return fake_identity

def start_driver(url):
    if args.cloud == CLOUD_ENABLED:
        s = Service("/bin/chromedriver")
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        options.add_argument("window-size=1920x1080")
        driver = webdriver.Chrome(service=s, options=options)
        # driver = webdriver.Chrome(
        #     'chromedriver', options=options)
    else:
        s = Service(ChromeDriverManager().install())
        options = webdriver.ChromeOptions()
        # options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36")

        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-setuid-sandbox")
        options.add_argument(  # Enable the WebGL Draft extension.
            "--enable-webgl-draft-extensions"
        )
        options.add_argument("--disable-infobars")  # Disable popup
        options.add_argument("--disable-popup-blocking")  # and info bars.
        # chrome_options.add_extension("./extensions/Tampermonkey.crx")
        driver = webdriver.Chrome(service=s, options=options)
    return driver


def test_success(driver):
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, IDs["first_name"]))
        )
        return False
    except:
        return True


def click_element(driver, element):
    driver.execute_script("arguments[0].click()", element)


def get_prompts(limit=10):
    index = random.randint(0, 400000)
    r = requests.post(
        "https://us-east4-get-spammed.cloudfunctions.net/get-prompt",
        json={"index": index,
              "limit": limit
              },
    )

    return json.loads(r.text)

def resume_generation(identity):
    resume_filename = identity['last_name']+'-Resume'
    make_resume(identity['first_name']+' '+identity['last_name'], identity['email'], identity['phone'], resume_filename)
    # images = convert_from_path(resume_filename+'.pdf')


"""
FORM CODE STUFF!!!!!
"""


def fill_out_form(driver, identity, prompts):
    # Title
    Select(driver.find_element(By.ID, IDs["title"])).select_by_index(
        random.randint(2, 9)
    )

    # First name
    driver.find_element(By.ID, IDs["first_name"]).send_keys(identity["first_name"])
    # Last name
    driver.find_element(By.ID, IDs["last_name"]).send_keys(identity["last_name"])
    # Email
    driver.find_element(By.ID, IDs["email"]).send_keys(identity["email"])
    # Phone
    driver.find_element(By.ID, IDs["phone"]).send_keys(identity["phone"])
    # address
    driver.find_element(By.ID, IDs["address"]).send_keys(identity["address"])
    # city
    driver.find_element(By.ID, IDs["city"]).send_keys(identity["city"])

    # State
    Select(driver.find_element(By.ID, IDs["state"])).select_by_index(
        random.randint(1, 53)
    )
    # zip
    driver.find_element(By.ID, IDs["zip"]).send_keys(identity["zip"])

    # philosophy
    Select(driver.find_element(By.ID, IDs["philosophy"])).select_by_visible_text(prompts[list(prompts.keys())[4]])
    # explain
    driver.find_element(By.ID, IDs["explain"]).send_keys(prompts[list(prompts.keys())[3]])
    # person
    driver.find_element(By.ID, IDs["person"]).send_keys(prompts[list(prompts.keys())[1]])
    # book
    driver.find_element(By.ID, IDs["book"]).send_keys(prompts[list(prompts.keys())[0]])
    # policy_figure
    driver.find_element(By.ID, IDs["policy_figure"]).send_keys(prompts[list(prompts.keys())[1]])
    # policy
    driver.find_element(By.ID, IDs["policy"]).send_keys(prompts[list(prompts.keys())[2]])


    # hear
    Select(driver.find_element(By.ID, IDs["hear"])).select_by_value(str(random.randint(321, 324)))

    #agrees and stuf idk bro
    for i in range(19, 37):
        Select(driver.find_element(By.ID, "QUESTION_ID_" + str(i))).select_by_index(
            random.randint(1, 3)
        )

    #remove disabled attribute from submit button
    driver.execute_script(f"document.getElementById('{IDs['submit']}').removeAttribute('disabled');")
    #upload resume
    # driver.find_element(By.ID, IDs["resume"]).send_keys(os.getcwd()+'/'+identity['last_name']+'-Resume.pdf')

    time.sleep(5)
    
    # Select(driver.find_element(By.ID, "QUESTION_ID_36")).select_by_index(
    #         random.randint(1, 2)
    #     )
    click_element(driver, driver.find_element(By.ID, IDs["resume"]))
    #submit
    click_element(driver, driver.find_element(By.ID, IDs["submit"]))
    #scroll to submit button
    driver.execute_script("arguments[0].scrollIntoView();", driver.find_element(By.ID, IDs["submit"]))
    time.sleep(1)
    #submit
    click_element(driver, driver.find_element(By.ID, IDs["submit"]))


def sendApplicationCount():
    requests.post(
        "https://us-east4-trackingapi-398123.cloudfunctions.net/Add-Data-Count"
    )


def main():
    # PROMPT HANDLER
    url = "https://apply.project2025.org/ords/r/p25/pub/questionnaire"
    print("Fetching prompts...")
    # print(args.limit)
    prompts = get_prompts(limit=args.limit)
    for prompt in prompts:
        # print(prompt)
        print("Creating fake identity...")
        identity = createFakeIdentity()
        # resume_generation(identity)
        print("Starting driver...")
        driver = start_driver(url)
        driver.get(url)
        test_success(driver)
        time.sleep(2)
        print("Filling out form...")
        fill_out_form(driver, identity, prompt)
        print("Application submitted!")
        # driver.maximize_window()
        time.sleep(5)
    # os.remove(identity['last_name']+'-Resume.pdf')
    # time.sleep(10000)


while True:
    main()
