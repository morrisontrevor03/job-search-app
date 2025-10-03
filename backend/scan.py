from googleapiclient.discovery import build
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
import time


load_dotenv()

key = os.getenv("key")
id = os.getenv("id")
wait = 30
run = True
role = "product analyst"

def search(query: str, key: str, id: str, num: int):
    service = build("customsearch", "v1", developerKey=key)
    res = service.cse().list(q=query, cx=id, num=num, sort="date:d:s").execute()

    if "items" not in res:
        print("no results")
        return
    
    results = []
    for item in res["items"]:
        results.append(item['link'])

    return results

def buildQuery(keyword: str):
    return f'site:lever.co OR site:greenhouse.io OR site:ashbyhq.com "{keyword}" new grad'



