import os
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
from html2text import html2text
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

load_dotenv()

def send_email(subject, body_text, body_html=None):
    """
    Send an email via Brevo SMTP relay with verbose logging.
    """
    smtp_login = os.getenv('BREVO_SMTP_LOGIN')
    smtp_key = os.getenv('BREVO_SMTP_KEY')
    from_email = os.getenv('FROM_EMAIL')
    to_email = os.getenv('TO_EMAIL')
    from_name = os.getenv('FROM_NAME', 'BinJuice')

    missing = [k for k, v in {
        'BREVO_SMTP_LOGIN': smtp_login,
        'BREVO_SMTP_KEY': smtp_key,
        'FROM_EMAIL': from_email,
        'TO_EMAIL': to_email
    }.items() if not v]
    if missing:
        raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")

    print(f"[EMAIL] Preparing email: subject='{subject}', from='{from_email}', to='{to_email}'")

    msg = MIMEMultipart('alternative')
    msg['From'] = f"{from_name} <{from_email}>"
    msg['To'] = to_email
    msg['Subject'] = subject

    msg.attach(MIMEText(body_text or "", 'plain'))
    if body_html:
        msg.attach(MIMEText(body_html, 'html'))
        print("[EMAIL] Added both plain-text and HTML versions")

    print("[EMAIL] Connecting to Brevo SMTP relay (smtp-relay.brevo.com:587)...")
    with smtplib.SMTP('smtp-relay.brevo.com', 587, timeout=30) as server:
        server.set_debuglevel(1)  # enable smtplib debug output
        server.ehlo()
        print("[EMAIL] Starting TLS encryption...")
        server.starttls()
        server.ehlo()
        print(f"[EMAIL] Logging in as '{smtp_login}'")
        server.login(smtp_login, smtp_key)
        print("[EMAIL] Sending message...")
        server.sendmail(from_email, [to_email], msg.as_string())
    print("[EMAIL] Email successfully sent via Brevo!")

url = "https://collections-midandeastantrim.azurewebsites.net/WSCollExternal.asmx"
xml_request = '''<?xml version="1.0" encoding="utf-8" ?>
<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
<soap:Body><getRoundCalendarForUPRN xmlns="http://webaspx-collections.azurewebsites.net/"><council>MidAndEastAntrim</council><UPRN>187222891</UPRN><from>Chtml</from></getRoundCalendarForUPRN></soap:Body></soap:Envelope>'''

try:
    print("[HTTP] Sending SOAP request to council endpoint...")
    r = requests.post(url, headers={"Content-Type": "text/xml"}, data=xml_request, timeout=30)
    print(f"[HTTP] Response status code: {r.status_code}")
    r.raise_for_status()

    print("[PARSER] Extracting SOAP response content...")
    soup = BeautifulSoup(r.text, 'xml')
    result_node = soup.find('getRoundCalendarForUPRNResult')
    if not result_node or not result_node.text:
        raise ValueError("Could not find getRoundCalendarForUPRNResult in SOAP response")
    print("[PARSER] Found result node.")

    print("[PARSER] Decoding HTML content from SOAP result...")
    decoded_html = result_node.text.encode('utf-8').decode('unicode_escape')

    print("[CLEANUP] Parsing HTML and removing unwanted elements...")
    h = BeautifulSoup(decoded_html, 'html.parser')
    removed_imgs = len(h.find_all('img'))
    removed_tables = len(h.find_all('table'))
    h = h
    for img in h.find_all('img'):
        img.decompose()
    for table in h.find_all('table'):
        table.decompose()
    for el in h.find_all(lambda tag: tag.string and 'Key:RefuseRecyclingGarden' in tag.string):
        el.decompose()
    print(f"[CLEANUP] Removed {removed_imgs} <img>, {removed_tables} <table>, and 'Key:RefuseRecyclingGarden' elements.")

    cleaned_html = str(h)
    print("[CLEANUP] Cleaned HTML ready.")

    print("[FORMAT] Converting cleaned HTML to Markdown/plain text...")
    markdown_content = html2text(cleaned_html)
    print("[FORMAT] Conversion complete.")

    print("[MAIN] Triggering email send...")
    send_email("Bin collection for the week", markdown_content, body_html=cleaned_html)

except Exception as e:
    print("[ERROR] An error occurred:", e)
