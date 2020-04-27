#################################
##### Name: Runa Morioka    #####
##### Uniqname: runam       #####
#################################

from bs4 import BeautifulSoup
from flask import Flask, render_template
import plotly.graph_objs as go
import html5lib
import pandas as pd
import sqlite3
import requests
import json
import secrets

api_key = secrets.API_KEY
country_url = 'https://covid-193.p.rapidapi.com/statistics'
us_url = 'https://www.worldometers.info/coronavirus/country/us/'
CACHE_FILE_NAME = 'cache.json'
CACHE_DICT = {}

app = Flask(__name__)

def load_cache():
    try:
        cache_file = open(CACHE_FILE_NAME, 'r')
        cache_file_contents = cache_file.read()
        cache = json.loads(cache_file_contents)
        cache_file.close()
    except:
        cache = {}
    return cache

def save_cache(cache):
    cache_file = open(CACHE_FILE_NAME,'w')
    contents_to_write = json.dumps(cache)
    cache_file.write(contents_to_write)
    cache_file.close()

def make_url_request_using_cache(url,cache):
    if(url in cache.keys()):
        return cache(url)
    else:
        response = requests.get(url)
        cache[url] = response.text
        save_cache(cache)
        return cache[url]
        
#create sqlite database 
DB_NAME = 'covid_19.sqlite'
def create_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    drop_countries_sql = 'DROP TABLE IF EXISTS "Countries"'
    drop_states_sql = 'DROP TABLE IF EXISTS "States"'

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

    create_states_sql = '''
        CREATE TABLE IF NOT EXISTS 'States'(
            'State' TEXT NOT NULL PRIMARY KEY,
            'CountryName' TEXT NOT NULL,
            'TotalCases' INTEGER NOT NULL,
            'TotalDeaths' INTEGER,
            'TotalTests' INTEGER NOT NULL
        )
    '''
    cur.execute(drop_countries_sql)
    cur.execute(drop_states_sql)
    cur.execute(create_countries_sql)
    cur.execute(create_states_sql)
    conn.commit()
    conn.close()

def load_countries():
    headers={'x-rapidapi-key':"dd7abe1932msh3833cb16c91c97ap1e4ed2jsn901d3a8f0136",'x-rapidapi-host':'covid-193.p.rapidapi.com'}
    response = requests.get(country_url,headers=headers).json()
    list_country_info = response['response']

    insert_country_sql = '''
        INSERT INTO Countries
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

def load_states():
    response = make_url_request_using_cache(us_url,CACHE_DICT)
    soup = BeautifulSoup(response, 'html.parser')
    stat_table = soup.find_all('table',id='usa_table_countries_today')
    stat_table = stat_table[0]
    state_info_summary = []

    for row in stat_table.find_all('tr'): 
        state = row.contents[1].text.strip()
        total_case = row.contents[3].text.strip()
        total_death = row.contents[7].text.strip()
        total_test = row.contents[17].text.strip()
        row = [state, total_case, total_death,total_test]
        state_info_summary.append(row)
    state_info_summary = state_info_summary[2:-1]
    for state_info in state_info_summary:
        state_info.insert(1, 'United States')
    insert_states_sql = '''
        INSERT INTO States
        VALUES (?,?,?,?,?)
    '''

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    for state in state_info_summary:
        cur.execute(insert_states_sql,
            [
                state[0],
                state[1],
                state[2],
                state[3],
                state[4]
                
        ])
    conn.commit()
    conn.close()

create_db()
load_countries()
load_states()

def get_world_data():
    conn = sqlite3.connect('covid_19.sqlite')
    cur = conn.cursor()
    q = '''
        SELECT *
        FROM Countries
        DESC
    '''

    results = cur.execute(q). fetchall()
    conn.close()
    return results

def get_us_data():
    conn = sqlite3.connect('covid_19.sqlite')
    cur = conn.cursor()
    
    q = f'''
        SELECT State, TotalCases, TotalDeaths, TotalTests
        FROM States
        DESC
    '''

    results = cur.execute(q).fetchall()
    conn.close()
    return results

@app.route ('/')
def index():
    return render_template('index.html')

@app.route ('/about')
def about():
    return render_template('about.html')

@app.route('/world')
def world():
    results = get_world_data()
    return render_template('world.html', results=results)

#choropleth map 
@app.route('/us') #after pressing us button from index.html, the map shows up 
def us_plot():
    response = requests.get(us_url)
    df = pd.read_html(response.text, flavor=['bs4','html5lib'])
    state_code = ['NY','NJ','MA','CA','PA','IL','MI','FL','LA','CT','TX','GA','MD','OH','IN','WA','VA','CO','TN','NC','MO','RI','AZ','AL','MS','WI','SC','NV','IA','UT','KY','DC','DE','OK','MN','KS','AR','NM','OR','SD','NE','ID','NH','WV','ME','VT','ND','HI','WY','MT','AK']
    new_df = df[0].iloc[1:52]
    new_df['code'] = state_code

    fig = go.Figure(data=go.Choropleth(
        locations=new_df['code'], # Spatial coordinates
        z = new_df['TotalCases'].astype(int), # Data to be color-coded
        locationmode = 'USA-states', # set of locations match entries in `locations`
        colorscale = [[0, 'rgb(240, 239, 239)'],[0.1, 'rgb(222, 146, 139 )'],[0.2, 'rgb(222, 146, 139  )'],[0.3, 'rgb(207, 125, 117)'],[0.4, 'rgb(207, 125, 117)'],[0.5, 'rgb(207, 125, 117)'],[0.6, 'rgb(202, 114, 105   )'],[0.7, 'rgb(190, 102, 93   )'],[0.8, 'rgb(191, 87, 77  )'],[0.9, 'rgb(191, 73, 61 )'],[1, 'rgb(183, 53, 40)']],
        marker_line_color='white',
        colorbar_title = "Total Cases",

    ))

    fig.update_layout(
        geo_scope='usa' # limite map scope to USA
        
    )
  
    fig.update_layout(margin={"r":0,"t":50,"l":0,"b":0})
    
    div = fig.to_html(full_html=False)
    results = get_us_data()

    #donut chart 
    totalcase = []
    state_list = [0,1,2,3,4,5,6,7,8,9]
    for state in state_list:
        totalcase.append(new_df.iloc[state]['TotalCases'])
    other_states = df[0].iloc[11:52]
    sum = other_states.sum(axis=0,skipna = True)

    labels = ['New York','New Jersey','Massachusetts','Illinois','California','Pennsylvania','Michigan','Florida','Louisiana','Connecticut','Other States']
    values = [totalcase[0],totalcase[1] , totalcase[2], totalcase[3],totalcase[4],totalcase[5],totalcase[6],totalcase[7],totalcase[8],totalcase[9],sum['TotalCases']]

    # Use `hole` to create a donut-like pie chart
    fig_pie = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.5, marker={'colors': [
                     '#a43820',
                     '#364761',
                     '#627da8',
                     '#a87262',
                     '#61917f',
                     '#8fbaa5',
                     '#a1834d',
                     '#c9bbb3',
                     '#537a78',
                     '#364d4b',
                     '#dedcdc'
                     
                    ]
    },)])

    fig_pie.update_layout(margin={"r":0,"t":150,"l":0,"b":20})
    div_pie = fig_pie.to_html(full_html=False)
    div = fig.to_html(full_html=False)
    return render_template("us.html", results=results, plot_div=div,plot_div_pie=div_pie)

@app.route('/us/totaldeaths')
def total_deaths():
    response = requests.get(us_url)
    df = pd.read_html(response.text, flavor=['bs4','html5lib'])
    state_code = ['NY','NJ','MA','CA','PA','IL','MI','FL','LA','CT','TX','GA','MD','OH','IN','WA','VA','CO','TN','NC','MO','RI','AZ','AL','MS','WI','SC','NV','IA','UT','KY','DC','DE','OK','MN','KS','AR','NM','OR','SD','NE','ID','NH','WV','ME','VT','ND','HI','WY','MT','AK']
    new_df = df[0].iloc[1:52]
    new_df['code'] = state_code
    #print(new_df)

    fig = go.Figure(data=go.Choropleth(
        locations=new_df['code'], # Spatial coordinates
        z = new_df['TotalDeaths'].astype(int), # Data to be color-coded
        locationmode = 'USA-states', # set of locations match entries in `locations`
        colorscale = [[0, 'rgb(240, 239, 239)'],[0.1, 'rgb(222, 146, 139 )'],[0.2, 'rgb(222, 146, 139  )'],[0.3, 'rgb(207, 125, 117)'],[0.4, 'rgb(207, 125, 117)'],[0.5, 'rgb(207, 125, 117)'],[0.6, 'rgb(202, 114, 105   )'],[0.7, 'rgb(190, 102, 93   )'],[0.8, 'rgb(191, 87, 77  )'],[0.9, 'rgb(191, 73, 61 )'],[1, 'rgb(183, 53, 40)']],
        marker_line_color='white',
        colorbar_title = "Total Deaths",
    ))
    fig.update_layout(
        geo_scope='usa', # limite map scope to USA
    )
    fig.update_layout(margin={"r":0,"t":50,"l":0,"b":0})

    #donut chart 
    totaldeaths = []
    state_list = [0,1,2,3,4,5,6,7,8,9]
    for state in state_list:
        totaldeaths.append(new_df.iloc[state]['TotalDeaths'])
    other_states = df[0].iloc[11:52]
    sum = other_states.sum(axis=0,skipna = True)

    labels = ['New York','New Jersey','Massachusetts','Illinois','California','Pennsylvania','Michigan','Florida','Louisiana','Connecticut','Other States']
    values = [totaldeaths[0],totaldeaths[1] , totaldeaths[2], totaldeaths[3],totaldeaths[4],totaldeaths[5],totaldeaths[6],totaldeaths[7],totaldeaths[8],totaldeaths[9],sum['TotalDeaths']]

    # Use `hole` to create a donut-like pie chart
    
    fig_pie = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.5, marker={'colors': [
                     '#a43820',
                     '#364761',
                     '#627da8',
                     '#a87262',
                     '#61917f',
                     '#8fbaa5',
                     '#a1834d',
                     '#c9bbb3',
                     '#537a78',
                     '#364d4b',
                     '#dedcdc'
                     
                    ]
    },)])
    fig_pie.update_layout(margin={"r":0,"t":150,"l":0,"b":20})
    div_pie = fig_pie.to_html(full_html=False)
    div = fig.to_html(full_html=False)
    return render_template('death.html', plot_div=div, plot_div_pie=div_pie)

@app.route('/us/totaltests')
def total_tests():
    response = requests.get(us_url)
    df = pd.read_html(response.text, flavor=['bs4','html5lib'])
    state_code = ['NY','NJ','MA','CA','PA','IL','MI','FL','LA','CT','TX','GA','MD','OH','IN','WA','VA','CO','TN','NC','MO','RI','AZ','AL','MS','WI','SC','NV','IA','UT','KY','DC','DE','OK','MN','KS','AR','NM','OR','SD','NE','ID','NH','WV','ME','VT','ND','HI','WY','MT','AK']
    new_df = df[0].iloc[1:52]
    new_df['code'] = state_code

    # choropleth map 
    fig = go.Figure(data=go.Choropleth(
        locations=new_df['code'], # Spatial coordinates
        z = new_df['TotalTests'].astype(int), # Data to be color-coded
        locationmode = 'USA-states', # set of locations match entries in `locations`
        colorscale = [[0, 'rgb(240, 239, 239)'],[0.1, 'rgb(222, 146, 139 )'],[0.2, 'rgb(222, 146, 139  )'],[0.3, 'rgb(207, 125, 117)'],[0.4, 'rgb(207, 125, 117)'],[0.5, 'rgb(207, 125, 117)'],[0.6, 'rgb(202, 114, 105   )'],[0.7, 'rgb(190, 102, 93   )'],[0.8, 'rgb(191, 87, 77  )'],[0.9, 'rgb(191, 73, 61 )'],[1, 'rgb(183, 53, 40)']],
        marker_line_color='white',
        colorbar_title = "Total Tests",
    ))
    fig.update_layout(
        geo_scope='usa' # limite map scope to USA
    )
    fig.update_layout(margin={"r":0,"t":50,"l":0,"b":0})

    #donut chart 
    totaltests = []
    state_list = [0,1,2,3,4,5,6,7,8,9]
    for state in state_list:
        totaltests.append(new_df.iloc[state]['TotalTests'])
    other_states = df[0].iloc[11:52]
    sum = other_states.sum(axis=0,skipna = True)

    labels = ['New York','New Jersey','Massachusetts','Illinois','California','Pennsylvania','Michigan','Florida','Louisiana','Connecticut','Other States']
    values = [totaltests[0],totaltests[1] , totaltests[2], totaltests[3],totaltests[4],totaltests[5],totaltests[6],totaltests[7],totaltests[8],totaltests[9],sum['TotalTests']]

    # Use `hole` to create a donut-like pie chart
    fig_pie = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.5, marker={'colors': [
                     '#a43820',
                     '#364761',
                     '#627da8',
                     '#a87262',
                     '#61917f',
                     '#8fbaa5',
                     '#a1834d',
                     '#c9bbb3',
                     '#537a78',
                     '#364d4b',
                     '#dedcdc'
                     
                    ]
    },)])
    fig_pie.update_layout(margin={"r":0,"t":150,"l":0,"b":20})
    div_pie = fig_pie.to_html(full_html=False)
    div = fig.to_html(full_html=False)
    return render_template('tests.html', plot_div=div, plot_div_pie=div_pie)

if __name__ =='__main__':
    print('starting Flask app', app.name)  
    app.run(debug=True)
