import streamlit as st
import requests
import pandas as pd
import pytz
from datetime import datetime, timedelta
from PIL import Image

# Display logo
image_path = 'fc-utrecht.png'
image = Image.open(image_path)
st.image(image, width = 60)

# Sidebar filters
display_mode = st.sidebar.radio("Display Mode", ["Short Names", "Full Names"])

# Define the function to get match data
def get_match_data(league_id, season_id):
    headers = {
        'authority': 'api.sofascore.com',
        'accept': '*/*',
        'accept-language': 'nl-NL,nl;q=0.9,en-US;q=0.8,en;q=0.7',
        'cache-control': 'max-age=0',
        'if-none-match': 'W/"510b2b225e"',
        'origin': 'https://www.sofascore.com',
        'referer': 'https://www.sofascore.com/',
        'sec-ch-ua': '"Chromium";v="116", "Not)A;Brand";v="24", "Google Chrome";v="116"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
    }

    headers['If-Modified-Since'] = 'Tue, 22 Aug 2023 00:00:00 GMT'
    url = f'https://api.sofascore.com/api/v1/unique-tournament/{league_id}/season/{season_id}/events/next/0'
    response = requests.get(url, headers=headers)

    games = response.json().get('events', [])

    match_data = []
    amsterdam_tz = pytz.timezone('Europe/Amsterdam')

    for game in games:

        if display_mode == "Full Names":
            home_team_name = game['homeTeam']['name']
            away_team_name = game['awayTeam']['name']
        else:
            home_team_name = game['homeTeam']['shortName']
            away_team_name = game['awayTeam']['shortName']

        data = {
            'league': game['tournament']['uniqueTournament']['name'],
            'country': game['tournament']['uniqueTournament']['category']['name'],
            'league_id': game['tournament']['uniqueTournament']['id'],
            'timestamp': game['startTimestamp'],
            'game_id': game['id'],
            'game_custom_id': game['customId'],
            'slug': game['slug'],
            'home_team': home_team_name,
            'home_id': game['homeTeam']['id'],
            'away_team': away_team_name,
            'away_id': game['awayTeam']['id']
        }

        match_data.append(data)

    for data in match_data:
        start_timestamp = data['timestamp']
        start_datetime = datetime.utcfromtimestamp(start_timestamp).replace(tzinfo=pytz.utc)
        amsterdam_start_datetime = start_datetime.astimezone(amsterdam_tz)
        data['startDateTime'] = amsterdam_start_datetime.strftime('%Y-%m-%d %H:%M:%S')

    match_df = pd.DataFrame(match_data)
    match_df.drop(columns=['timestamp'], inplace=True)
    
    return match_df

# Define league IDs and season IDs
league_seasons = [
    {'league_id': 9, 'season_id': 52384},   #ChallengerProLeague
    {'league_id': 26, 'season_id': 49483},  #U21EURO.Q
    {'league_id': 37, 'season_id': 52554},  #Eredivisie
    {'league_id': 38, 'season_id': 52383},  #ProLeague
    {'league_id': 39, 'season_id': 52172},  #Superligaen
    {'league_id': 44, 'season_id': 52607},  #2.Bundesliga
    {'league_id': 47, 'season_id': 52329},  #1.Division
    {'league_id': 131, 'season_id': 52556}, #KeukenKampioenDivisie
    {'league_id': 491, 'season_id': 52815}, #3.Liga
    {'league_id': 493, 'season_id': 52841}, #RegionalligaWest
    {'league_id': 810, 'season_id': 53101}  #A-JuniorenWest
]

# Get match data for each league and season
all_match_data = []
for ls in league_seasons:
    match_df = get_match_data(ls['league_id'], ls['season_id'])
    all_match_data.append(match_df)

# Combine match data from all leagues into a single DataFrame
combined_match_df = pd.concat(all_match_data, ignore_index=True)

# Convert 'startDateTime' column to datetime objects
combined_match_df['startDateTime'] = pd.to_datetime(combined_match_df['startDateTime'])

# Mapping of values to be renamed
league_mapping = {
    'A-Jun-BL West': 'A-Junioren West',
    'U21 Euro Qualification': 'U21 EURO Q',
    'Eerste Divisie': 'Keuken Kampioen Div.',
    'Superliga': 'Superligaen',
    '2. Bundesliga': '2e Bundesliga',
    '3. Liga': '3e Liga'
}

# Apply the mapping to the 'league' column
combined_match_df['league'] = combined_match_df['league'].replace(league_mapping)

# Create a new column to track favourite games
combined_match_df['is_fav'] = False

# Sidebar filters
all_leagues = combined_match_df['league'].unique()
selected_leagues = st.sidebar.multiselect("Select Leagues", all_leagues, default=['Eredivisie', 'Keuken Kampioen Div.'])
days_filter = st.sidebar.number_input("Show Matches in Next .. Days", value=14)

# Apply filters
current_datetime = datetime.now()
filtered_df = combined_match_df[
    (combined_match_df['league'].isin(selected_leagues)) &
    (combined_match_df['startDateTime'] <= current_datetime + timedelta(days=days_filter))
]

# Sort by date
sorted_df = filtered_df.sort_values(by='startDateTime')

# Grouping matches by day
sorted_df['Date'] = sorted_df['startDateTime'].dt.date
grouped_by_day = sorted_df.groupby('Date')

# Dictionary to map country names to flag emojis
country_flags = {
    "Netherlands": "nl.png",
    "Belgium": "be.png",
    "Denmark": "dk.png",
}

# Display filtered and sorted data as cards per day
for date, group in grouped_by_day:
    # Add a line under the subheader using HTML
    st.markdown(f"<h2 style = 'font-size: 22px; border-bottom: 1px solid #f79b9b; margin-bottom: 10px;'>{date.strftime('%A, %B %d, %Y')}</h2>", unsafe_allow_html=True)
    
    for index, row in group.iterrows():
        col1, col2, col3, col4 = st.columns([0.05, 0.4, 0.25, 0.95])

        # Display the flag image in col1
        flag_filename = country_flags.get(row['country'])
        if flag_filename:
            flag_image_path = flag_filename
            flag_image = Image.open(flag_image_path)
            with col1:
                st.image(flag_image, width=12)
        
        col2.write(f"{row['league']}")

        # Add a clock icon before the time using Font Awesome
        clock_icon = ':clock1:'
        time_with_icon = f"{clock_icon} {row['startDateTime'].strftime('%H:%M')}"
        col3.write(time_with_icon, unsafe_allow_html=True)

        col4.write(f"**{row['home_team']}** vs **{row['away_team']}**")

        # Add a '+' icon in the fourth column with a unique key
        #button_key = f"button_{index}"  # Using the row index as a key
        #plus_icon = ':heavy_plus_sign:'  