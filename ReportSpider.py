import json
import os
from time import sleep
from urllib import parse
import xlrd

import time
import requests
import urllib3
from urllib.parse import *
from io import BytesIO
import os
import re
from ftplib import FTP


ftp = FTP()


def login(host='192.168.61.76',
          port=21,
          username='uftp',
          password='amarsoft'):
    ftp.connect(host, port)
    ftp.encoding = 'utf-8'
    ftp.login(username, password)


def download_pdf(text, code):
    # print()
    # if 'ST长油：2018年年度报告.PDF' in ftp.nlst('/CNINFO/files'):
    #     print('ST长油：2018年年度报告.PDF')

    count = 0
    hreftext = text
    hreftext_list = hreftext.split('/')

    i = 0
    while i < 3:
        try:
            bid = re.findall('\d+', hreftext_list[2])[0]
            href_url = 'http://www.cninfo.com.cn/new/announcement/download?bulletinId=' + bid + '&announceTime=' + \
                       hreftext_list[1]
            print(href_url)
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            resp = requests.head(href_url, verify=False, timeout=(5, 15))
            if resp.status_code == 200:
                login()
                filename = resp.headers['Content-Disposition'].split('filename=')[-1].strip('"')
                filename = unquote_plus(filename)
                print(filename)
                if code not in ftp.nlst('/CNINFO/'):
                    ftp.mkd('/CNINFO/%s' % code)
                if filename not in ftp.nlst('/CNINFO/%s' % code):
                    resp = requests.get(href_url, verify=False, timeout=(30, 90))
                    time.sleep(1)
                    # fileflow = resp.content
                    fileflow = BytesIO(resp.content)
                    # with open(f'files/{filename}', 'wb+') as f:
                    #     f.write(fileflow)
                    filepath = '/CNINFO/%s/%s' % (code, filename)
                    ftp.storbinary('STOR %s' % filepath, fileflow, blocksize=1024)
                ftp.close()
            i += 3
            count = count + 1
        except Exception as e:
            i += 1
            print(f'Download Failed({i}): {e}')
            time.sleep(10)
    ftp.close()


def get_adress(company_name):
    url = "http://www.cninfo.com.cn/new/information/topSearch/detailOfQuery"
    data = {
        'keyWord': company_name,
        'maxSecNum': 10,
        'maxListNum': 5,
    }
    hd = {
        'Host': 'www.cninfo.com.cn',
        'Origin': 'http://www.cninfo.com.cn',
        'Pragma': 'no-cache',
        'Accept-Encoding': 'gzip,deflate',
        'Connection': 'keep-alive',
        'User-Agent': 'Mozilla/5.0(Windows NT 10.0;Win64;x64) AppleWebKit / 537.36(KHTML, likeGecko) Chrome / 75.0.3770.100Safari / 537.36',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Accept': 'application/json,text/plain,*/*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    }
    r = requests.post(url, headers=hd, data=data)
    r = r.content
    m = str(r, encoding="utf-8")
    pk = json.loads(m)
    if len(pk["keyBoardList"]) > 0:
        for row in range(len(pk["keyBoardList"])):
            if (pk["keyBoardList"][row]["category"] == 'A股'):
                orgI = pk["keyBoardList"][row]["orgId"]  # 获取参数
                code = pk["keyBoardList"][row]["code"]
                if int(company_name) > 600000:
                    plate, column = 'sh', 'sse'
                else:
                    plate, column = 'sz', 'szse'
                print(orgI, plate, code, column)
                return orgI, plate, code, column
    return '', '', '', ''


def get_PDF(orgI, plate, code, column, pagenum, syear=2019):
    url = "http://www.cninfo.com.cn/new/hisAnnouncement/query"
    data = {
        'stock': f'{code},{orgI}',
        'tabName': 'fulltext',
        'pageSize': 30,
        'pageNum': pagenum,
        'column': column,
        'category': 'category_ndbg_szsh;category_bndbg_szsh;category_yjdbg_szsh;category_shdbg_szsh;',
        'plate': plate,
        'seDate': f'{syear}-01-01~{syear + 1}-01-01',
        'searchkey': '',
        'secid': '',
        'sortName': '',
        'sortType': '',
        'isHLtitle': 'true',
    }
    hd = {
        'Host': 'www.cninfo.com.cn',
        'Origin': 'http://www.cninfo.com.cn',
        'Pragma': 'no-cache',
        'Accept-Encoding': 'gzip,deflate',
        'Connection': 'keep-alive',
        'User-Agent': 'User-Agent:Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/533.20.25 (KHTML, like Gecko) Version/5.0.4 Safari/533.20.27',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Accept': 'application/json,text/plain,*/*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'X-Requested-With': 'XMLHttpRequest',
    }
    data = parse.urlencode(data)
    resp = requests.post(url, headers=hd, data=data)
    r = json.loads(str(resp.content, encoding="utf-8"))
    reports_list = r['announcements']
    if reports_list:
        for report in reports_list:
            secCode = report['secCode']
            secName = report['secName']
            title = report['announcementTitle']
            down_url = report['adjunctUrl']
            text = str(len(reports_list)) + '<次数>' + str(secCode) + secName + ':' + title + '——' + down_url + '\n'
            download_pdf(text, code)
            with open("all_20190101_20200101.txt", "r+") as f1:
                if text not in f1.readlines():
                    f1.write(text)

if __name__ == '__main__':
    with open('company_id.txt') as file:
        lines = file.readlines()
        for stock in lines:
            g_orgId, g_plate, g_code, g_column = get_adress(stock)
            if g_orgId and g_plate and g_code and g_column:
                p_num = 1
                get_PDF(g_orgId, g_plate, g_code, g_column, p_num)
            print("next one !!!")
        print("all done !!!")
