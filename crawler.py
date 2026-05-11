import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time

# 目标网站列表
SITES = [
    {
        "name": "国家药监局",
        "url": "https://www.nmpa.gov.cn/ylqx/index.html",
        "selector": "a",  # 链接选择器
        "date_pattern": r'(\d{4}[-年]\d{1,2}[-月]\d{1,2}日)'
    },
    {
        "name": "食药评价中心",
        "url": "https://www.nifdc.org.cn/nifdc/bshff/ylqxbzhgl/index.html",
        "selector": "a",
        "date_pattern": r'(\d{4}[-年]\d{1,2}[-月]\d{1,2}日)'
    },
    {
        "name": "标管中心数据公开",
        "url": "app.nifdc.org.cn/biaogzx/dataGkZqyj.do?formAction=listHbbp&type=nlx",
        "selector": "a",
        "date_pattern": r'(\d{4}[-年]\d{1,2}[-月]\d{1,2}日)'
    },
    {
        "name": "法规解读",
        "url": "https://www.nifdc.org.cn/nifdc/bshff/ylqxbzhgl/qxxxgk/fljd/index.html",
        "selector": "a",
        "date_pattern": r'(\d{4}[-年]\d{1,2}[-月]\d{1,2}日)'
    },
    {
        "name": "标准资料",
        "url": "app.nifdc.org.cn/biaogzx/dataGkZqyj.do?formAction=listHbbp&type=bzca",
        "selector": "a",
        "date_pattern": r'(\d{4}[-年]\d{1,2}[-月]\d{1,2}日)'
    },
    {
        "name": "国家标准委",
        "url": "https://std.samr.gov.cn/gb/gbQuery",
        "selector": "a",
        "date_pattern": r'(\d{4}[-年]\d{1,2}[-月]\d{1,2}日)'
    },
    {
        "name": "医疗器械审评中心",
        "url": "https://www.cmde.org.cn/index.html",
        "selector": "a",
        "date_pattern": r'(\d{4}[-年]\d{1,2}[-月]\d{1,2}日)'
    },
    {
        "name": "新闻动态",
        "url": "https://www.cmde.org.cn/xwdt/index.html",
        "selector": "a",
        "date_pattern": r'(\d{4}[-年]\d{1,2}[-月]\d{1,2}日)'
    },
    {
        "name": "科普信息",
        "url": "https://www.cmde.org.cn/spkx/index.html",
        "selector": "a",
        "date_pattern": r'(\d{4}[-年]\d{1,2}[-月]\d{1,2}日)'
    },
    {
        "name": "活动交流",
        "url": "https://www.cmde.org.cn/hdjl/hdjlwthf/index.html",
        "selector": "a",
        "date_pattern": r'(\d{4}[-年]\d{1,2}[-月]\d{1,2}日)'
    },
    {
        "name": "医疗器械创新",
        "url": "https://cfdi.org.cn/cfdi/index?module=A004&m1=10&m2=&nty=STA024&tcode=STA026",
        "selector": "a",
        "date_pattern": r'(\d{4}[-年]\d{1,2}[-月]\d{1,2}日)'
    },
]

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

def fetch_webpage(url):
    """获取网页内容"""
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.encoding = 'utf-8'
        return resp.text
    except:
        return None

def extract_links(text, site_info):
    """从网页提取链接"""
    soup = BeautifulSoup(text, 'html.parser')
    links = []
    
    # 根据选择器提取
    selector = site_info.get('selector', 'a')
    items = soup.find_all(selector, href=True)
    
    for item in items:
        link = item.get('href')
        text = item.get_text().strip()
        
        # 跳过纯图标或无意义链接
        if len(text) < 3 or '返回首页' in text:
            continue
        
        # 提取日期
        date_match = re.search(site_info['date_pattern'], text)
        if date_match:
            date_str = date_match.group(1).replace('年', '-').replace('月', '-').replace('日', '')
        else:
            date_str = datetime.now().strftime('%Y-%m-%d')
        
        links.append({
            'site': site_info['name'],
            'title': text,
            'url': link,
            'date': date_str,
            'content': text[:200]  # 内容摘要
        })
    
    return links

def filter_today_info(all_links):
    """只保留当天的信息"""
    today = datetime.now().strftime('%Y-%m-%d')
    today_info = [link for link in all_links if link['date'] == today]
    return today_info

def generate_email_content(today_info):
    """生成邮件正文"""
    content = f"今日工作通知 ({datetime.now().strftime('%Y-%m-%d')})\n"
    content += "=" * 50 + "\n\n"
    
    if not today_info:
        content += "今日暂无更新\n"
    else:
        content += f"共找到 {len(today_info)} 条更新:\n\n"
        
        for i, item in enumerate(today_info, 1):
            content += f"{i}. [{item['site']}] {item['title']}\n"
            content += f"   日期: {item['date']}\n"
            content += f"   摘要: {item['content']}\n"
            content += f"   链接: {item['url']}\n\n"
            content += "-" * 50 + "\n"
    
    return content

def send_email(content, site_info):
    """发送邮件"""
    try:
        from_addr = site_info['email_user']
        password = site_info['email_password']
        to_addr = site_info['email_to']
        
        msg = MIMEMultipart()
        msg['From'] = from_addr
        msg['To'] = to_addr
        msg['Subject'] = f"今日工作通知 - {datetime.now().strftime('%Y-%m-%d')}"
        
        msg.attach(MIMEText(content, 'plain', 'utf-8'))
        
        server = smtplib.SMTP_SSL('smtp.qq.com', 465)
        server.login(from_addr, password)
        server.sendmail(from_addr, to_addr, msg.as_string())
        server.quit()
        print("邮件发送成功")
        
    except Exception as e:
        print(f"邮件发送失败: {e}")

def main():
    """主函数"""
    print("开始抓取...")
    
    all_links = []
    
    # 抓取所有网站
    for site in SITES:
        print(f"正在抓取: {site['name']}")
        text = fetch_webpage(site['url'])
        if text:
            links = extract_links(text, site)
            all_links.extend(links)
            print(f"  找到 {len(links)} 条")
        time.sleep(1)  # 避免请求过快
    
    # 筛选当天信息
    today_info = filter_today_info(all_links)
    print(f"\n当天信息: {len(today_info)} 条")
    
    # 生成邮件内容
    content = generate_email_content(today_info)
    
    # 保存为本地文件（方便查看）
    with open('today_report.txt', 'w', encoding='utf-8') as f:
        f.write(content)
    
    # 发送邮件
    email_info = {
        'email_user': 'YOUR_EMAIL@qq.com',  # 替换为你的邮箱
        'email_password': 'YOUR_AUTH_CODE',  # 替换为你的授权码
        'email_to': 'YOUR_EMAIL@qq.com'  # 替换为接收邮箱
    }
    
    send_email(content, email_info)
    
    print("完成！")

if __name__ == '__main__':
    main()
