# Portfolio Performance compatible JSON for `Achmea opkomende markten aandelen fonds A` fund
Quotes are updated daily using GitHub actions.\
\
Quotes for this specific fund are not generally available in popular sources since it was only recently founded in May 2023.\
\
This script pulls the API behind the rates graph at `https://www.achmeainvestmentmanagement.nl/particulier/beleggingsfondsen/koersen` and converts the rates to a JSON file compatible with [Portfolio Performance](https://www.portfolio-performance.info/en/).

## How-to
In Portfolio Performance select JSON as the provider in the “Historical Quotes” tab of the security, and use the following values:

Feed URL = `https://raw.githubusercontent.com/RamonH93/process-json-achmea-opkomende-markten/master/AchmeaOpkomendeMarkten.json`\
Path to Date = `$.rates[*].Date`\
Path to Close = `$.rates[*].CloseQuote`
