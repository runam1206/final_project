import sqlite3
import requests

DB_NAME = 'covid_19.sqlite'
def create_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    drop_countries_sql = 'DROP TABLE IF EXISTS "Countries"'

    create_countries_sql = '''
        CREATE TABLE IF NOT EXISTS 'Countries'(
            'Country' TEXT NOT NULL PRIMARY KEY,
            'NewCase' INTEGER,
            'Recovered' INTEGER NOT NULL,
            'TotalConfirmed' INTEGER NOT NULL,
            'TotalTested' INTEGER,
            'TotalDeaths' INTEGER NOT NULL,
            'Date' NUMERIC NOT NULL,
            'Time' NUMERIC NOT NULL 
        )
    '''
    cur.execute(drop_countries_sql)
    cur.execute(create_countries_sql)
    conn.commit()
    conn.close()

def load_countries():
    base_url = 'https://covid-193.p.rapidapi.com/statistics'
    headers={'x-rapidapi-key':"dd7abe1932msh3833cb16c91c97ap1e4ed2jsn901d3a8f0136",'x-rapidapi-host':'covid-193.p.rapidapi.com'}
    response = requests.get(base_url,headers=headers).json()
    list_country_info = response['response']

    insert_country_sql = '''
        INSERT INTO COuntries
        VALUES(?,?,?,?,?,?,?,?)
    '''

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    for country_info in list_country_info:
        cur.execute(insert_country_sql,
            [
                country_info['country'],
                country_info['cases']['new'],
                country_info['cases']['recovered'],
                country_info['cases']['total'],
                country_info['tests']['total'],
                country_info['deaths']['total'],
                country_info['day'],
                country_info['time']
            ]
        )
    conn.commit()
    conn.close()

create_db()
load_countries()

