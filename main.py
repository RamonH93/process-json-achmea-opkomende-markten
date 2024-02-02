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

# import logging
# import logging.handlers
# import os

# import requests

# logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)
# logger_file_handler = logging.handlers.RotatingFileHandler(
#     "status.log",
#     maxBytes=1024 * 1024,
#     backupCount=1,
#     encoding="utf8",
# )
# formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
# logger_file_handler.setFormatter(formatter)
# logger.addHandler(logger_file_handler)

# try:
#     SOME_SECRET = os.environ["SOME_SECRET"]
# except KeyError:
#     SOME_SECRET = "Token not available!"
#     #logger.info("Token not available!")
#     #raise


# if __name__ == "__main__":
#     logger.info(f"Token value: {SOME_SECRET}")

#     r = requests.get('https://weather.talkpython.fm/api/weather/?city=Berlin&country=DE')
#     if r.status_code == 200:
#         data = r.json()
#         temperature = data["forecast"]["temp"]
#         logger.info(f'Weather in Berlin: {temperature}')