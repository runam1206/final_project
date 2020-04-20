#################################
##### Name: Runa Morioka    #####
##### Uniqname: runam       #####
#################################

from bs4 import BeautifulSoup
import requests
import json
import secrets

api_key = secrets.API_KEY

#website scraping access code
BASE_URL = 'https://www.worldometers.info/coronavirus/country/us'
response = requests.get(BASE_URL)
soup = BeautifulSoup(response.text, 'html.parser')

stat_table = soup.find_all('table',id='usa_table_countries_today')
stat_table = stat_table[0]
for row in stat_table.find_all('tr'):
    for cell in row.find_all('td'):
        print(cell.text)
    
#API accessing code
url = "https://covid-193.p.rapidapi.com/statistics"
headers={'x-rapidapi-key':"dd7abe1932msh3833cb16c91c97ap1e4ed2jsn901d3a8f0136",'x-rapidapi-host':'covid-193.p.rapidapi.com'}
response = requests.get(url, headers=headers).json()
print(response)




