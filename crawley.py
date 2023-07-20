#Copyright (c) Microsoft Corporation. All rights reserved.
#Licensed under the MIT License.

# -*- coding: utf-8 -*-

import json
import os
from pprint import pprint
import requests
import time
import datetime
import argparse, sys # Pass arguments
from serpapi import GoogleSearch
import os
import urllib.parse
import string
import requests
import base64
from urllib.parse import urlparse
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def extract_urls(html_string):
    url_pattern = re.compile(r'(?:http[s]?://)?(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
    urls = re.findall(url_pattern, html_string)
    return urls

def extract_urlsBS(base_url, html_string):
    soup = BeautifulSoup(html_string, 'html.parser')
    urls = []
    for tag in soup.find_all(['a', 'img', 'script', 'link', 'iframe']):
        if 'src' in tag.attrs:
            url = urljoin(base_url, tag.attrs['src'])
            urls.append(url)
        if 'href' in tag.attrs:
            url = urljoin(base_url, tag.attrs['href'])
            urls.append(url)
    return urls

def printProgressBar (iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█', printEnd = "\r", color="black", overwrite=True):
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    if overwrite != True:
        print(f'\r{prefix} |{bar}| {iteration}/{total} | {percent}% {suffix} ')
    else:
        print(f'\r{prefix} |{bar}| {iteration}/{total} | {percent}% {suffix} ', end="\r")
    if iteration == total:
        print()

def extract_base_url(url):
    parsed_url = urlparse(url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    return base_url

def url_to_filename(url):
    return ''.join(c for c in urllib.parse.quote(url, safe=string.ascii_letters + string.digits) if c not in ['/', ':', '*'])

def filename_to_url(filename):
    return urllib.parse.unquote(filename)


# ts stores the time in seconds
ts = time.time()

now = datetime.datetime.now()
# print(now.year, now.month, now.day, now.hour, now.minute, now.second)

# Arguments
parser=argparse.ArgumentParser()
parser.add_argument("--query", "-q", help="Bing Query")
parser.add_argument("--offset", "-o", help="Offset on results (default is 0)")
parser.add_argument("--mkt", "-m", help="Target market (default: en-US)")
parser.add_argument("--count", "-c", help="Count of results per page (default is 10, max for Bing 30, for Google 100)")
parser.add_argument("--engine", "-e", help="Bing or google (serp.api)")
parser.add_argument("--all", "-a", help="All engines")
parser.add_argument("--validate", "-v", help="Validate", action='store_true')
parser.add_argument("--links", "-l", help="Follow links", action='store_true')
args=parser.parse_args()

'''
This sample makes a call to the Bing Web Search API with a query and returns relevant web search.
Documentation: https://docs.microsoft.com/en-us/bing/search-apis/bing-web-search/overview
'''

# Add your Bing Search V7 subscription key and endpoint to your environment variables.
subscription_key = 'd29a941ec17645faaf727f050d01fc25'
endpoint = "https://api.bing.microsoft.com/v7.0/search"

keys = []

with open('keys.txt', 'r', encoding='utf-8') as file:
    for line in file:
        keys.append(line)

print(f"Available keys: {len(keys)}")
# sys.exit()

os.makedirs('results', exist_ok=True)
os.makedirs('resultsHTML', exist_ok=True)
config = json.load(open('config.json', 'r', encoding='utf-8'))
prevResults = json.load(open('validatedSites.json', 'r', encoding='utf-8'))

# Arguments parse



if args.links:
    searchedSites = []

    folder = 'results'
    print(f"Result files total: {len(os.listdir(folder))}")
    # sys.exit()
    folderSitesLen = len(os.listdir(folder))
    countSites = 0
    for filename in os.listdir(folder):
        countSites = countSites + 1
        filepath = os.path.join(folder, filename)
        result = json.load(open(filepath, 'r', encoding='utf-8'))
        if "organic_results" in result:
            print(len(result["organic_results"]))
            for oRes in result["organic_results"]:
                searchedSites.append(oRes["link"])

    print(f"Total URLs from search: {len(searchedSites)}")
    # sys.exit()

    allURLs = []
    encounteredSites = []

    if os.path.exists('triedSites.json'):
        triedSites = json.load(open('triedSites.json', 'r', encoding='utf-8'))
    else:
        triedSites = []

    countHTMLLinks = 0
    folderHTML = 'resultsHTML'
    folderHTMLLen = len(os.listdir(folderHTML))
    for filename in os.listdir(folderHTML):
        countHTMLLinks = countHTMLLinks + 1

        site = extract_base_url(filename_to_url(filename))

        checkPlatform = False
        for platformType in prevResults:
            if site in prevResults[platformType]:
                checkPlatform = True
        if checkPlatform and filename_to_url(filename) in searchedSites: #Also make sure that newly downloaded HTML from links is discarded
            try:
                with open(folderHTML + '/' + filename, 'r', encoding='utf-8') as f:
                    contents = f.read()
                    urls = extract_urlsBS(extract_base_url(filename_to_url(filename)), contents)
                    for url in urls:
                        base = extract_base_url(url)
                        if site not in url and base not in encounteredSites:
                            encounteredSites.append(base)
                            allURLs.append(url)

                            filenameFromURL = url_to_filename(url)
                            print(url)
                            if url not in triedSites and not os.path.exists(folderHTML + '/' + filenameFromURL):
                                try:
                                    response = requests.get(url, timeout=5)
                                    with open(folderHTML + '/' + filenameFromURL, 'w', encoding='utf-8') as f:
                                        f.write(response.text)
                                except Exception as e:
                                    print(e)
                                    triedSites.append(url)
                                    with open("triedSites.json", "w", encoding='utf8') as outfile:
                                        json.dump(triedSites, outfile, indent=4, ensure_ascii=False)
                            else:
                                print(f'already downloaded: {url}')

                            print(f"Total external urls: {len(allURLs)}")

                # for platformType in config:
                #     for validationCritereon in config[platformType]["validate"]:
                #         if not platformType in validatedSites:
                #             validatedSites[platformType] = {}
                #         if validationCritereon.lower() in contents.lower():
                #             site = extract_base_url(filename_to_url(filename))
                #             if not site in validatedSites[platformType]:
                #                 validatedSites[platformType][site] = []
                #             if validationCritereon not in validatedSites[platformType][site]:
                #                 validatedSites[platformType][site].append(validationCritereon)
                    # print(platformType)
            except Exception as e:
                print(e)
        printProgressBar(countHTMLLinks, folderHTMLLen, prefix = 'Script progress (links)', suffix = 'Valid platform HTMLs parsed', length = 50, color="black", overwrite=False)

    # sys.exit()

if args.validate or args.links:
    htmlLog = []
    validatedSites = {}
    if os.path.exists('triedSites.json'):
        triedSites = json.load(open('triedSites.json', 'r', encoding='utf-8'))
    else:
        triedSites = []

    folderHTML = 'resultsHTML'
    for filename in os.listdir(folderHTML):
        htmlLog.append(filename_to_url(filename))

    print(f"Currently HTMLs downloaded: {len(htmlLog)}")
    # sys.exit()

    folder = 'results'
    print(f"Result files total: {len(os.listdir(folder))}")
    # sys.exit()
    folderSitesLen = len(os.listdir(folder))
    countSites = 0
    for filename in os.listdir(folder):
        countSites = countSites + 1
        filepath = os.path.join(folder, filename)
        result = json.load(open(filepath, 'r', encoding='utf-8'))
        if "organic_results" in result:
            print(len(result["organic_results"]))
            for oRes in result["organic_results"]:
                if oRes["link"] not in htmlLog and oRes["link"] not in triedSites:
                    filenameFromURL = url_to_filename(oRes["link"])
                    print(oRes["link"])
                    # sys.exit()
                    try:
                        response = requests.get(oRes["link"], timeout=5)
                        with open(folderHTML + '/' + filenameFromURL, 'w', encoding='utf-8') as f:
                            f.write(response.text)
                    except Exception as e:
                        print(e)
                        triedSites.append(oRes["link"])
                        with open("triedSites.json", "w", encoding='utf8') as outfile:
                            json.dump(triedSites, outfile, indent=4, ensure_ascii=False)
                    # sys.exit()
                else:
                    print(f'already downloaded: {oRes["link"]}')
                    # sys.exit()
            # sys.exit()
        printProgressBar(countSites, folderSitesLen, prefix = 'Script progress (2)', suffix = 'Result page htmls downloaded', length = 50, color="black")

    folderHTMLLen = len(os.listdir(folderHTML))
    countHTML = 0
    for filename in os.listdir(folderHTML):
        countHTML = countHTML + 1
        # htmlLog.append(filename_to_url(filename))
        try:
            with open(folderHTML + '/' + filename, 'r', encoding='utf-8') as f:
                contents = f.read()
            for platformType in config:
                for validationCritereon in config[platformType]["validate"]:
                    if not platformType in validatedSites:
                        validatedSites[platformType] = {}
                    if validationCritereon.lower() in contents.lower():
                        site = extract_base_url(filename_to_url(filename))
                        if not site in validatedSites[platformType]:
                            validatedSites[platformType][site] = []
                        if validationCritereon not in validatedSites[platformType][site]:
                            validatedSites[platformType][site].append(validationCritereon)
                # print(platformType)
        except Exception as e:
            print(e)
        printProgressBar(countHTML, folderHTMLLen, prefix = 'Script progress (3)', suffix = 'HTMLs parsed', length = 50, color="black")

    print(validatedSites)
    with open("validatedSites.json", "w", encoding='utf8') as outfile:
        # outfile.write(json_object)
        json.dump(validatedSites, outfile, indent=4, ensure_ascii=False)

    for platformType in validatedSites:
        print(f"{platformType} total: {len(validatedSites[platformType])}")
    sys.exit()

query = None
if not args.query: #"\"Powered by Semantic MediaWiki.\""
    raise Exception('No Query defined!')
else:
    query = args.query

mkt = args.mkt
if not args.mkt:
    mkt = "en-US"

offset = 0
if args.offset:
    offset = int(args.offset)

count = 10
if args.count:
    count = int(args.count)

engine = "None"
if args.engine:
    engine = args.engine

# if engine == "Bing":
#     # Construct a request
#     mkt = 'en-US'
#     params = { 'q': query, 'mkt': mkt, 'count': count, 'offset': offset}
#     headers = { 'Ocp-Apim-Subscription-Key': subscription_key }
#
#     # Call the API
#     try:
#         response = requests.get(endpoint, headers=headers, params=params)
#         response.raise_for_status()
#         # print("Headers:")
#         # print(response.headers)
#         # print("JSON Response:")
#         # pprint(response.json())
#     except Exception as ex:
#         raise ex
#
#     ##############################################
#     # Serializing json
#     resJSON = response.json()
#
#     json_object = json.dumps(resJSON)
#
#     print(f"Total estimated maches:{resJSON['webPages']['totalEstimatedMatches']}")
#
#     count = 0
#     for site in resJSON['webPages']['value']:
#         count = count + 1
#         url = site["url"]
#         name = site["name"]
#         print(f"{offset + count} / {count}: {url} | {name}")
#     print(str(count))
#
#     # Writing to sample.json
#     with open(f"results/result_{now.year}_{now.month}_{now.day}_{now.hour}_{now.minute}_{now.second}_{ts}.json", "w") as outfile:
#         outfile.write(json_object)

# print(config)
# with open("config2.json", "w", encoding='utf8') as outfile2:
#     json.dump(config, outfile2, indent=4, ensure_ascii=False)
#
# sys.exit()

def searchesLeft(key):
    search = GoogleSearch({"api_key": key})
    account = search.get_account()
    # print(f"Searches left: {account['total_searches_left']} | on key: {key}")
    return account['total_searches_left']
# sys.exit()

def saveResults(search):
    result = search.get_dict()
    # json_object = json.dump(result, ensure_ascii=False)
    filename = f"results/result_{now.year}_{now.month}_{now.day}_{now.hour}_{now.minute}_{now.second}_{ts}.json"
    with open(filename, "w", encoding='utf8') as outfile:
        # outfile.write(json_object)
        json.dump(result, outfile, indent=4, ensure_ascii=False)
    print(f"Engine: {engine} | Query: {query} | Count: {count} | Offset: {offset} | File: {filename}")
    print(f"Organic results len: {len(result['organic_results'])}")
    resultsOrganic = result['organic_results']
    try:
        resultsOrganicString = ""
        lastResult = ""
        for r in resultsOrganic:
            resultsOrganicString = resultsOrganicString + '\n' + r['link']
            lastResult = r['link']
        print(f"Last: {lastResult}")
    except Exception as e:
        print(e)

search = None

key = "e29035ffa6b2e6db5957817a9915c96875f275ba48695b76b1e568e4dbd00ae3"
for k in keys:
    searchesLeftCheck = searchesLeft(k)
    print(f"Searches left: {searchesLeftCheck} | on key: {k}")
    if searchesLeftCheck > 0:
        print(f"Key to be used: {k}")
        key = k
        break

if args.all or engine == "Google":
    search = GoogleSearch({
        "q": query,
        "filter":0,
        "start":offset,
        "num":count,
        "api_key": key
      })
    saveResults(search)
if args.all or engine == "Bing":
    search = GoogleSearch({
        "q": query,
        "first":offset, # 50, 100 etc
        "count":count, # 50 max
        "api_key": key,
        "engine": "bing"
      })
    saveResults(search)
if args.all or engine == "Yandex":
    search = GoogleSearch({
        "text": query,
        "p":offset, # Pages 1,2,3
        "api_key": key,
        "engine": "yandex"
      })
    saveResults(search)
if args.all or engine == "Yahoo":
    search = GoogleSearch({
        "p": query,
        "b":offset, #1, 11, 21
        "api_key": key,
        "engine": "yahoo"
      })
    saveResults(search)
if args.all or engine == "DuckDuckGo":
    search = GoogleSearch({
        "q": query,
        "start":offset, #Returns 50 results
        "api_key": key,
        "engine": "duckduckgo",
        "safe": -2
      })
    saveResults(search)
if args.all or engine == "Baidu":
    search = GoogleSearch({
        "q": query,
        "pn":offset, #Pages 0,1,2,3
        "rn":count, #10,20,50
        "api_key": key,
        "engine": "baidu",
        "ct": 1
      })
    saveResults(search)
if args.all or engine == "Naver":
    search = GoogleSearch({
        "query": query,
        "page":offset, #1,2,3, Starts from 1
        "num":count, #50,100 (max)
        "api_key": key,
        "engine": "Naver",
        "where":"web"
      })
    saveResults(search)
# Append-adds at last
# with open(f"queryLogs.json", "a") as outfile:
#     outfile.write(f"Engine: {engine} | Query: {query} | Count: {count} | Offset: {offset} | File: resultsGoogle/result_{now.year}_{now.month}_{now.day}_{now.hour}_{now.minute}_{now.second}_{ts}.json")
