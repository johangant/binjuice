import os
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
from html2text import html2text
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Load environment variables from .env file
load_dotenv()

def send_email(subject, body):
    # Get SendGrid API key from environment variable
    sendgrid_api_key = os.getenv('SENDGRID_API_KEY')

    # Check if the API key is not set
    if not sendgrid_api_key:
        print("SendGrid API key not set. Please set the SENDGRID_API_KEY environment variable.")
        return

    # Set sender and recipient email addresses
    from_email = os.getenv('FROM_EMAIL')
    to_email = os.getenv('TO_EMAIL')

    # Set up the message
    msg = MIMEMultipart()
    msg['From'] = 'BinJuice <' + from_email + '>'
    msg['To'] = to_email
    msg['Subject'] = subject

    # Attach the HTML content as plain text
    msg.attach(MIMEText(body, 'plain'))

    # Connect to SendGrid SMTP server
    try:
        print("Connecting to SendGrid SMTP server...")
        server = smtplib.SMTP_SSL('smtp.sendgrid.net', 465)
        print("Connected.")

        print("Logging in to SendGrid SMTP server...")
        server.login('apikey', sendgrid_api_key)
        print("Logged in.")

        print(f"Sending email to {to_email}...")
        server.sendmail(from_email, to_email, msg.as_string())
        print("Email sent successfully!")

        print("Closing connection to SendGrid SMTP server.")
        server.quit()
    except Exception as e:
        print("Error sending email:", e)

url = "https://collections-midandeastantrim.azurewebsites.net/WSCollExternal.asmx"
xml_request = '''<?xml version="1.0" encoding="utf-8" ?>
<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
<soap:Body><getRoundCalendarForUPRN xmlns="http://webaspx-collections.azurewebsites.net/"><council>MidAndEastAntrim</council><UPRN>187222891</UPRN><from>Chtml</from></getRoundCalendarForUPRN></soap:Body></soap:Envelope>'''

try:
    # Send HTTP POST request and capture response
    response = requests.post(url, headers={"Content-Type": "text/xml"}, data=xml_request)
    response_content = response.text

    # Extract content between <getRoundCalendarForUPRNResult> tags
    soup = BeautifulSoup(response_content, 'xml')
    # Extract content between <getRoundCalendarForUPRNResult> tags
    xml_content = soup.find('getRoundCalendarForUPRNResult').text

    # URL decode the HTML content
    decoded_html_content = xml_content.encode('utf-8').decode('unicode_escape')

    # Remove <img> elements
    soup_without_img = BeautifulSoup(decoded_html_content, 'html.parser')
    for img in soup_without_img.find_all('img'):
        img.decompose()

    # Remove <table> elements
    for table in soup_without_img.find_all('table'):
        table.decompose()

    # Remove elements containing 'Key:RefuseRecyclingGarden'
    for element in soup_without_img.find_all(lambda tag: 'Key:RefuseRecyclingGarden' in tag.text):
        element.decompose()

    html_without_img_table_filtered = str(soup_without_img)

    # Convert HTML without <img>, <table>, and filtered elements to Markdown
    markdown_content = html2text(html_without_img_table_filtered)

    # Print the results
    print("\nHTML Content without <img>, <table>, and filtered elements:")
    print(html_without_img_table_filtered)
    print("\nMarkdown Content:")
    print(markdown_content)

    # Send the Markdown content as an email via SendGrid
    send_email("Bin collection for the week", markdown_content)

except Exception as e:
    # Log any exceptions
    print("An error occurred:", e)
