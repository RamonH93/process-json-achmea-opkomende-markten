# Portfolio Performance compatible JSON for "Achmea opkomende markten aandelen fonds A" fund.

## How-to
In Portfolio Performance select JSON as the provider in the “Historical Quotes” tab of the security, and use the following values:

Feed URL = https://raw.githubusercontent.com/RamonH93/process-json-achmea-opkomende-markten/master/AchmeaOpkomendeMarkten.json
Path to Date = $.rates[*].Date
Path to Close = $.rates[*].CloseQuote
