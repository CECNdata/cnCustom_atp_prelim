#!/usr/bin/env python
# coding=utf-8

url="http://www.customs.gov.cn/customs/302249/zfxxgk/2799825/302274/myzs75/zgdwmyzs/5668765/index.html"
sub_url_xpath="""//*[contains(., "贸易指数") and contains(@opentype, "more")]/following-sibling::*[contains(.,"更多")]//a"""
latest_year_xpath="""(//*[@class="portlet"]//ul[@class="nav_sj"]//a)[1]"""
if_currency=None
if_upload_github=True
atp="CN-JF-GACC-TradeIndex-MTH"

#download mapping
files={
    "表一 20" : {
        "filename": "cnCustoms-prelim-table1-<currcy>_<month><year>_<time>.csv",
        "table": "全国出口商品贸易同比指数（HS2分类）",
    },
    "表十三 20" : {
        "filename": "cnCustoms-prelim-table2-<currcy>_<month><year>_<time>.csv",
        "table": "全国进口商品贸易同比指数（HS2分类）",
    },
    "表二 20" : {
        "filename": "cnCustoms-prelim-table3-<currcy>_<month><year>_<time>.csv",
        "table": "全国出口商品贸易同比指数（SITC2分类）",
    },
    "表十四 20" : {
        "filename": "cnCustoms-prelim-table4-<currcy>_<month><year>_<time>.csv",
        "table": "全国进口商品贸易同比指数（SITC2分类）",
    },
    "表三 20" : {
        "filename": "cnCustoms-prelim-table5-<currcy>_<month><year>_<time>.csv",
        "table": "全国出口商品贸易同比指数（BEC分类）",
    },
    "表十五 20" : {
        "filename": "cnCustoms-prelim-table6-<currcy>_<month><year>_<time>.csv",
        "table": "全国进口商品贸易同比指数（BEC分类）",
    },
    "表四 20" : {
        "filename": "cnCustoms-prelim-table7-<currcy>_<month><year>_<time>.csv",
        "table": "全国出口商品贸易同比指数（国民经济行业分类）",
    },
    "表十六 20" : {
        "filename": "cnCustoms-prelim-table8-<currcy>_<month><year>_<time>.csv",
        "table": "全国进口商品贸易同比指数（国民经济行业分类）",
    },
}

import os
import re
import pandas as pd
from io import StringIO
import lxml
import time

if 'repo_token' in os.environ:
    repo_token = os.environ['repo_token']
    print(f"The value of repo_token is: {repo_token}")
else:
    print("The repo_token environment variable is not set.")
    repo_token=None

for file in files.keys():
    files[file]["xpath"]=[]
    if if_currency:
        for currency_index in ["1","2"]:
            files[file]["xpath"].append(f"""((//td[contains(text(),"{file}")])[{currency_index}]/..//a[@href])[last()]""")
    else:
         files[file]["xpath"].append(f"""((//td[contains(text(),"{file}")])/..//a[@href])[last()]""")

from playwright.sync_api import sync_playwright

import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
import datetime
def cn_time_string():
    today                = datetime.datetime.utcnow()
    cn_today             = today + datetime.timedelta(hours = 8)
    return(cn_today.strftime("%Y%m%d%H%M%ST+8"))

import base64
import traceback
import json
import random
def send_log_github(repo     : str = "CECNdata/cnCustom_atp_prelim" ,
                    filename : str = "anylog.log"        ,
                    token    : str = repo_token          ,
                    content  : str = "content"           ,
                    ) -> bool:
    try:
        # print(content)
        if token == "None":
            print(f"need gihtub repo <{repo}> token (at least gist write)")
            return(False)
        else:
            content=base64.b64encode(content.encode("utf-8")).decode('utf-8')
            headers = {
                'User-Agent'    : 'HTTPie/1.0.3'            ,
                'Accept'        : 'application/json, */*'   ,
                'Connection'    : 'keep-alive'              ,
                'Content-Type'  : 'application/json'        ,
                'Authorization' : 'token '+token            ,
            }
            data    = {
                "message"       : "upload csv"                                    ,
                "committer"     : { "name"  : "cecndata"                          ,
                                    "email" : "CECNdata@users.noreply.github.com" , } ,
                "content"       : content
            }
            repo     = f"https://api.github.com/repos/{repo}/contents/"
            filename = f"{filename}"
            r        = requests.put(repo+filename, headers = headers, data = json.dumps(data))

            if str(r.status_code)[:2] == "20":
                print(f"upload csv to github <{repo}> success with {r.status_code}")
                return(True)
            else:
                print(f"[Anylog] github-api PUT return: \n{r.text}")
                print(f"upload csv to github <{repo}> failed with {r.status_code}")
                return(False)
    except Exception as e:
        print(e)
        print(traceback.format_exc())
        return(False)

def save(page,fullTitle,filename,f,atp):
    date=re.search(r'(?P<year>20\d{2})年(?P<month>\d{1,2})月', fullTitle)
    year=date.group("year")
    month=date.group("month").zfill(2)

    filename=filename.replace("<month>",month)
    filename=filename.replace("<year>",year)

    print(fullTitle)

    if if_currency:
        if "人民币" in fullTitle:
            filename=filename.replace("<currcy>","RMB")
        elif "美元" in fullTitle:
            filename=filename.replace("<currcy>","USD")
        else:
            raise ValueError("not sure rmb or usd, maybe page is not correct")
    else:
        filename=filename.replace("<currcy>","default")

    try:os.mkdir("download")
    except:pass

    html_io = StringIO(page.content())
    tables = pd.read_html(html_io)
    for _,df in enumerate(tables):
        if df.stack().str.contains(f, case=False).unstack().any(axis=1).any():
            result=df.to_csv(index = None, header = None)
            if result and result.strip()!="":
                if not if_upload_github:
                    with open(f"./download/{filename}", "w") as fr:
                        fr.write(result)
                else:
                    final_path=f"{atp}/{filename}".replace("<time>",cn_time_string())
                    while not send_log_github(filename=final_path,content=result):
                        time.sleep(random.randint(3,6))
                break



def run(playwright):
    browser = playwright.firefox.launch(headless=False)
    context = browser.new_context()
    
    context.set_default_timeout(30000)  
    context.set_default_navigation_timeout(60000) 

    #context.add_init_script(path="stealth.min.js")
    page = context.new_page()
    
    page.goto(url,wait_until="domcontentloaded")
    page.wait_for_timeout(5000)
    
    #if sub_url_xpath:
    #    page.locator(sub_url_xpath).click() ##  click the latest year
    #    page.wait_for_timeout(5000)
    #    page = context.pages[-1]

    if latest_year_xpath:
        latest_url=page.locator(latest_year_xpath).get_attribute("href") ##  click the latest year
        if latest_url not in page.url:
            page.locator(latest_year_xpath).click() ##  click the latest year
            page.wait_for_timeout(5000)
            page = context.pages[-1]

    from urllib.parse import urljoin
    for f in files.keys():
        files[f]["link"]=[]
        for xpath in files[f]["xpath"]:
            l=(page.locator(xpath).get_attribute("href")) 
            l=urljoin("http://www.customs.gov.cn/",l)
            files[f]["link"].append(l)

    for f in files.keys():
        for l in files[f]["link"]:
            page.goto(l,wait_until="domcontentloaded")
            page.wait_for_timeout(30000)

            fullTitle = page.locator(f"""xpath=//h2[contains(.,"{f}")]""").inner_text()
            try:
                save(page,fullTitle,files[f]["filename"],files[f]["table"],atp)
            except Exception as e:
                print(str(e))

    browser.close()


with sync_playwright() as playwright:
    run(playwright)

