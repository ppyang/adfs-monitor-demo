from selenium import webdriver
from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.firefox.options import Options as Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import WebDriverException
import datetime
import time
import smtplib
from pushover import Client
import sqlite3



filename = "C:\\Users\\wanpeng\\PycharmProjects\\adfs\\adfs_down_log.txt"
down_limit = 2
url = 'https://mail.rmc.ca'
un = 'testeruser'
pw = 'fakepassword'
run_headleass = True
to = ['adfsmonitor@rmc.ca']
pushover_only = False


conn = sqlite3.connect("C:\\Users\\wanpeng\\PycharmProjects\\adfs\\log.db")
c = conn.cursor()


def get_time_used(tick):
    seconds_passed = time.time() - tick
    timeused = f"{seconds_passed:.2f}"
    return timeused

def get_last_problem ():
    sql = f'''SELECT * from problem order by id desc LIMIT 1 '''
    c.execute(sql)
    rows = c.fetchone()
    return rows
def create_problem(id):
    t = (id,)
    sql = f"insert into problem (started_id) values (?)"
    c.execute(sql, t)

def update_problem(id, ended_id=None, down_email_sent=0, up_email_sent=0):
    sql = f"update problem set ended_id = ?, down_email_sent = ?, up_email_sent = ? where started_id = ?"
    t = (ended_id, down_email_sent, up_email_sent, id)
    c.execute(sql,t)







#######send email#######
def send_mail(subject, body,pushover_only=False):
    client = Client("clientun", api_token="replacewithtoken")
    client.send_message(body, title=subject)
    if pushover_only:
        return
    gmail_user = 'testinguser@gmail.com'
    gmail_pw = 'testingpassword'
    sent_from = gmail_user

    email_text = "\r\n".join([
        f"From: {sent_from}",
        f"To: {', '.join(to)}",
        f"Subject: {subject}",
        "",
        body
    ])

    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.ehlo()
        server.login(gmail_user, gmail_pw)
        server.sendmail(sent_from, to, email_text)
        server.close()
    except:
        print('Email sent Error')


def save_result (login_ok, inbox_ok,tick, note = ''):
    timestamp = str(datetime.datetime.now())
    time_used = get_time_used(tick)
    t = (timestamp, login_ok, inbox_ok, time_used, note)
    c.execute('insert into log (timestamp, login_ok, inbox_ok, time_used, note) values (?,?,?,?,?)', t)
    last_id = c.lastrowid
    last_problem = get_last_problem()
    consecutive_downs = 0
    if last_problem:
        started_id = last_problem[1]
        ended_id = last_problem[2]
        down_email_sent = last_problem[3]
        up_email_sent = last_problem[4]

    if login_ok ==0 or inbox_ok == 0:
        if not last_problem or (started_id and ended_id):
            create_problem(last_id)
        elif started_id and not ended_id and not down_email_sent:
            consecutive_downs = last_id - started_id
            if not down_email_sent and consecutive_downs == down_limit-1:
                print('send email here for down time')
                send_mail(subject='Webmail ADFS is DOWN!', body=f"Check WAP and ADFS.",
                                      pushover_only=pushover_only)
                update_problem(id=started_id, down_email_sent=1)
    elif login_ok == 1 and inbox_ok == 1:
        if started_id and not ended_id:
            ended_id = last_id
            up_email_sent = 0
            if down_email_sent:
                print('send up email')
                send_mail(subject='Webmail ADFS is back UP!', body=f"Everything is fine.",
                      pushover_only=pushover_only)
                up_email_sent = 1

            update_problem(id=started_id, ended_id=ended_id, down_email_sent=down_email_sent, up_email_sent=up_email_sent)
    conn.commit()


options = Options()
if run_headleass:
    options.add_argument("--headless")
else:
    options.headless = False
try:
    browser = webdriver.Chrome(options=options)
except WebDriverException:
    send_mail(subject='Need to upgrade Chromedriver', body='Check the Chromedriver on win1 for adfs.', pushover_only=True)
    exit(0)

browser.delete_all_cookies()
tick = time.time()
browser.get(url)
try:
    username_input = browser.find_element_by_id('userNameInput')
    password_input = browser.find_element_by_id('passwordInput')
    submit_button = browser.find_element_by_id('submitButton')

    username_input.send_keys(un)
    password_input.send_keys(pw)
    submit_button.click()
except NoSuchElementException:
    note = browser.page_source
    browser.close()
    browser.quit()
    save_result(login_ok=0, inbox_ok=0, tick=tick,note=note)
    exit(0)

login_ok = 1

if run_headleass:
    try:
        inbox = WebDriverWait(browser, 30).until(EC.presence_of_element_located((By.LINK_TEXT, 'Inbox')))
    except TimeoutException:
        print(browser.page_source)
        note = browser.page_source
        inbox_ok = 0
        save_result(login_ok, inbox_ok, tick, note)

        browser.get('https://adfs.rmc.ca/adfs/ls/?wa=wsignout1.0')
        browser.close()
        browser.quit()
        exit(0)
else:
    try:
        inbox = WebDriverWait(browser, 30).until(EC.presence_of_element_located((By.CLASS_NAME, 'folderHeaderLabel')))
    except TimeoutException:
        note = browser.page_source
        inbox_ok = 0
        save_result(login_ok, inbox_ok, tick, note)
        browser.get('https://adfs.rmc.ca/adfs/ls/?wa=wsignout1.0')
        browser.close()
        browser.quit()
        exit(0)
inbox_ok = 1
save_result(login_ok, inbox_ok, tick)
browser.get('https://adfs.rmc.ca/adfs/ls/?wa=wsignout1.0')
browser.close()
browser.quit()
conn.close()
print("everything is fine")


