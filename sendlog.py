import sqlite3
import datetime
import csv
import email
import smtplib
import ssl
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


to = ['adfsmonitor@rmc.ca']

today = datetime.date.today() - datetime.timedelta(1)
todaystr = today.strftime("%Y-%m-%d")
csvfile = f"C:\\Users\\wanpeng\\PycharmProjects\\adsf\\{todaystr}.csv"
conn = sqlite3.connect("C:\\Users\\wanpeng\\PycharmProjects\\adsf\\log.db")
c = conn.cursor()

def export_csv():
    sql = f"SELECT quote(timestamp),quote(login_ok),quote(inbox_ok), quote(time_used), quote(note) from log where timestamp like '{todaystr}%'"
    with open(csvfile,'w+',encoding='utf-8', newline='') as file:
        csv.writer(file).writerow(("'timestamp'","'login_ok'","'inbox_ok'","'time_used'","'note'"))
        csv.writer(file).writerows(c.execute(sql))
export_csv()

subject = f"ADFS monitor logs for {todaystr}"
body = "Please find the logs in the attachment"
gmail_user = 'adfsmonitor@gmail.com'
gmail_pw = 'testpassword'
sent_from = gmail_user
receiver_emails = ','.join(to)

message = MIMEMultipart()
message["From"] = sent_from
message["To"] = receiver_emails
message["Subject"] = subject

message.attach(MIMEText(body, "plain"))

with open(csvfile, "rb") as attachment:
    part = MIMEBase("application", "octet-stream")
    part.set_payload(attachment.read())

encoders.encode_base64(part)

part.add_header("Content-Disposition", f"attachment; filename= {todaystr}.csv",)

message.attach(part)
text = message.as_string()

context = ssl.create_default_context()
with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
    server.login(gmail_user, gmail_pw)
    server.sendmail(sent_from, to, text)
conn.close()
