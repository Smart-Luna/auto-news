import requests
from bs4 import BeautifulSoup

# 目标网页地址
url = "https://你的工作网站.com"

# 获取网页内容
resp = requests.get(url)
soup = BeautifulSoup(resp.text, 'html.parser')

# 抓取标题
titles = soup.find_all('h2')
for title in titles:
    print(title.get_text())
