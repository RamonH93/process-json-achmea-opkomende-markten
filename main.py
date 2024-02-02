import datetime
import json
import requests
import sys

REMOTE = "https://www.achmeainvestmentmanagement.nl/Rates/GetAllRatesByFundGroup?code=ODV"
# REMOTE = "https://tools.morningstar.nl/api/rest.svc/timeseries_price/8qe8f2nger?currencyId=EUR&idtype=Morningstar&frequency=daily&outputType=JSON&startDate=2014-02-01&id=F00001697F]2]0]FONLD$$ALL"
REMOTE_COPY = "AchmeaOpkomendeMarkten_orig.json"
OUT = "AchmeaOpkomendeMarkten.json"
# OUT = "MorningStar.json"
FETCH = True
DATEFORMAT = '%Y-%m-%d'

data_remote = {}

if FETCH:
    r = requests.get(REMOTE)
    if r.status_code == 200:
        data_remote = r.json()
        with open(OUT, "w") as f:
            json.dump(data_remote, f, indent=4)
else:
    try:
        with open(REMOTE_COPY) as f:
            data_remote = json.load(f)
    except:
        pass

if len(data_remote) == 0:
    print("ERROR: no data.")
    sys.exit(1)

data_out = {
    'fund': data_remote['funds'][7]['title'],
    'lastUpdated': datetime.datetime.today().strftime(DATEFORMAT),
    'rates': []
}

for item in data_remote['funds'][7]['rates']:
    epoch = item['x'] / 1000
    quote = str(item['y'])
    date = datetime.datetime.fromtimestamp(epoch).strftime(DATEFORMAT)
    data_out['rates'].append({
        "Date": date,
        "CloseQuote": quote
    })

with open(OUT, "w") as f:
    json.dump(data_out, f, indent=4)

