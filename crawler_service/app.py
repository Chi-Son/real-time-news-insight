import requests
from bs4 import BeautifulSoup
url ='https://vnexpress.net/noi-hinh-thanh-dong-dat-du-doi-nhat-the-gioi-4921099.html'
response = requests.get(url)
html = response.text
soup = BeautifulSoup(html, "html.parser")

#lay noi dung bat dau tu day
title = soup.find("h1", class_="title-detail").get_text(strip=True)
content_div = soup.find("article", class_="fck_detail")
paragraphs = content_div.find_all("p")

content = "\n".join(p.get_text(strip=True) for p in paragraphs)

print(content)