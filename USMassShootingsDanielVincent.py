"""
Name:       Daniel Vincent
CS230:      Section 5
Data:       US Mass Shootings
URL:

Description: This program visualizes US mass shooting data. It allows users to filter the data by
year, state, gender, race, prior signs of mental illness, and assault weapon usage.
The application displays a scatter plot, a map of shooting incidents, bar and pie charts, and a pivot table to provide
other insights into the data.
"""

# Import needed packages
# Added Altair for charts
# Added Numpy for using colors between scatter and map
import streamlit as st
import pandas as pd
import altair as alt
import pydeck as pdk
import numpy as np

# Function for citations page
def References():
    st.title("Citations")
    st.write("""
    https://docs.streamlit.io/library/api-reference/charts \n
    https://numpy.org/doc/stable/reference/generated/numpy.tile.html \n
    https://blog.streamlit.io/building-a-pivottable-report-with-streamlit-and-ag-grid/ \n
    https://discuss.streamlit.io/t/streamlit-pysrt/38012/5
    """)

# Function that holds all the main page data
def home():
# Load the CSV file
    path = "C:/Users/danv/OneDrive - Bentley University/Spring2023/CS230/PycharmFiles/FinalProject/"
    data = pd.read_csv(path + "USMassShootings.csv", encoding="ISO-8859-1")
# Added encoding because I was getting errors on streamlit

# Function for filtering data
    def filterData(data, year_range, selected_states, selected_genders, selected_races, selected_prior_signs,
                    selected_assaults):
        return data[
            (data['YEAR'] >= year_range[0]) & (data['YEAR'] <= year_range[1]) &
            data['STATE'].isin(selected_states) &
            data['GENDER'].isin(selected_genders) &
            data['RACE'].isin(selected_races) &
            data['PRIORSIGNSOFMENTALILLNESS'].isin(selected_prior_signs) &
            data['ASSAULT'].isin(selected_assaults)
            ]

# Define functions later used for bar and pie charts
    def countShootingsByRace(data):
        return data.groupby('RACE').size().reset_index(name='Count')

    def countShootingsByMentalIllness(data):
        return data.groupby('PRIORSIGNSOFMENTALILLNESS').size().reset_index(name='Count')

    def countShootingsByAssaultWeapon(data):
        return data.groupby('ASSAULT').agg({'TOTALVICTIMS': 'sum'}).reset_index()

# Sidebar widgets
    st.sidebar.title('Filters')
    min_year = int(data['YEAR'].min())
    max_year = int(data['YEAR'].max())
    year_range = st.sidebar.slider('Year Range', min_year, max_year, (min_year, max_year))

    state_options = sorted(data['STATE'].unique().tolist())
    state_options.insert(0, 'All')
    selected_states = st.sidebar.multiselect('States', state_options, default='All')

# If all is selected in multiselect -> Choose all items
    if 'All' in selected_states:
        selected_states = state_options[1:]

    selected_genders = st.sidebar.radio('Genders', ['All'] + sorted(data['GENDER'].unique()))
    selected_races = st.sidebar.multiselect('Races', ['All'] + sorted(data['RACE'].unique()), default='All')
    selected_prior_signs = st.sidebar.radio('Prior Signs of Mental Illness',
                                            ['All'] + sorted(data['PRIORSIGNSOFMENTALILLNESS'].unique()))
    selected_assaults = st.sidebar.radio('Assault', ['All'] + sorted(data['ASSAULT'].unique()))

    if selected_genders == 'All':
        selected_genders = sorted(data['GENDER'].unique())
    else:
        selected_genders = [selected_genders]

    if 'All' in selected_races:
        selected_races = sorted(data['RACE'].unique())

    if selected_prior_signs == 'All':
        selected_prior_signs = sorted(data['PRIORSIGNSOFMENTALILLNESS'].unique())
    else:
        selected_prior_signs = [selected_prior_signs]

    if selected_assaults == 'All':
        selected_assaults = sorted(data['ASSAULT'].unique())
    else:
        selected_assaults = [selected_assaults]

# Take filtered data and alter based on widgets
    filtered_data = filterData(data, year_range, selected_states, selected_genders, selected_races,
                                selected_prior_signs, selected_assaults)

# Group data by Year and State
    grouped_data = filtered_data.groupby(['YEAR', 'STATE']).agg({'TOTALVICTIMS': 'sum'}).reset_index()

# Color mapping function used for both scatter and map
    def state_color_mapping(state, unique_states, color_scheme):
        state_index = unique_states.index(state)
        return [int(color_scheme[state_index][1:3], 16), int(color_scheme[state_index][3:5], 16),
                int(color_scheme[state_index][5:], 16)]

# Create color scheme and unique states list
# Unable to make unique colors for all 50 states. Tried using Matplotlib but didn't work
    unique_states = sorted(data['STATE'].unique())
    color_scheme = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22',
                    '#17becf']
    color_scheme = np.tile(color_scheme, (len(unique_states) // len(color_scheme) + 1))[:len(unique_states)]
# Array using NumPy package

# Create a color dictionary for the scatter plot
    scatter_color_dict = {state: f'rgb({color[0]}, {color[1]}, {color[2]})' for state, color in zip(unique_states, [
        state_color_mapping(state, unique_states, color_scheme) for state in unique_states])}

# Filter scatter color dictionary
    selected_scatter_color_dict = {state: scatter_color_dict[state] for state in selected_states}

# Create scatter plot
    st.title('Number of Victims by Year and State')
    scatter_plot = alt.Chart(grouped_data).mark_circle().encode(
        x='YEAR:O',
        y='TOTALVICTIMS:Q',
        size='TOTALVICTIMS',
        color=alt.Color('STATE', scale=alt.Scale(domain=list(selected_scatter_color_dict.keys()),
                                                 range=list(selected_scatter_color_dict.values()))),
        tooltip=['YEAR', 'STATE', 'TOTALVICTIMS']
    ).properties(
        width=600,
        height=400
    )
    st.altair_chart(scatter_plot)

# Create map
    st.title("Map of Shooting Incidents")

    view_state = pdk.ViewState(latitude=39.8283, longitude=-98.5795, zoom=3)
    layer = pdk.Layer(
        "ScatterplotLayer",
        data=filtered_data.to_dict(orient='records'),
        get_position=["LONGITUDE", "LATITUDE"],
        get_radius="TOTALVICTIMS * 1000",
        get_fill_color="color",
        pickable=True,
        auto_highlight=True,
    )

# Apply state color mapping
    layer.data = [{k: (None if pd.isna(v) else v) for k, v in record.items()} for record in layer.data]
    for record in layer.data:
        record['color'] = state_color_mapping(record['STATE'], unique_states, color_scheme)

    tooltip = {
        "html": "<b>Location:</b> {LOCATION}, {STATE}<br/><b>Year:</b> {YEAR}",
        "style": {"backgroundColor": "steelblue", "color": "white"},
    }
    incident_map = pdk.Deck(layers=[layer], initial_view_state=view_state, tooltip=tooltip)

    st.pydeck_chart(incident_map)

# Color scheme for the bar chart
    bar_chart_color_scheme = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f',
                              '#bcbd22', '#17becf']

# Bar chart: Number of perpetrators by race
    race_data = countShootingsByRace(filtered_data)
    race_bar_chart = alt.Chart(race_data).mark_bar().encode(
        x='RACE:O',
        y='Count:Q',
        color=alt.Color('RACE', scale=alt.Scale(domain=sorted(data['RACE'].unique()), range=bar_chart_color_scheme)),
        tooltip=['RACE', 'Count']
    ).properties(
        title='Number of Perpetrators by Race',
        width=600,
        height=400
    )
    st.altair_chart(race_bar_chart)

# Pie chart: Number of shootings with people with prior signs of mental illness
    mental_illness_data = countShootingsByMentalIllness(filtered_data)
    mental_illness_pie_chart = alt.Chart(mental_illness_data).mark_arc(innerRadius=50).encode(
        theta='Count:Q',
        color=alt.Color('PRIORSIGNSOFMENTALILLNESS:O', scale=alt.Scale(domain=['No', 'Yes'], range=['red', 'green'])),
        tooltip=['PRIORSIGNSOFMENTALILLNESS', 'Count']
    ).properties(
        title='Number of Perpetrators with Prior Signs of Mental Illness',
        width=600,
        height=400
    )
    st.altair_chart(mental_illness_pie_chart)

# Pie chart: Number of victims related to whether an assault weapon was used
    assault_data = countShootingsByAssaultWeapon(filtered_data)
    assault_pie_chart = alt.Chart(assault_data).mark_arc(innerRadius=50).encode(
        theta='TOTALVICTIMS:Q',
        color=alt.Color('ASSAULT:O', scale=alt.Scale(domain=['No', 'Yes'], range=['red', 'green'])),
        tooltip=['ASSAULT', 'TOTALVICTIMS']
    ).properties(
        title='Number of Victims Related to Assault Weapon Usage',
        width=600,
        height=400
    )

    st.altair_chart(assault_pie_chart)

# Pivot table with whole csv data to be transparent about the data set being used -> Shows the bias in the data
    pivot_table = pd.pivot_table(
        data,
        index=["YEAR", "STATE"],
        values=["CASE", "GENDER", "SHOOTINGTYPE", "RACE", "LOCATION", "DATE", "SUMMARY", "FATALITIES", "WOUNDED",
                "TOTALVICTIMS", "LOCATIONTYPE", "PRIORSIGNSOFMENTALILLNESS", "MENTALHEALTHNOTES",
                "WEAPONSOBTAINEDLEGALLY", "WHEREWEAPONOBTAINED", "TYPEOFWEAPONS", "NUMWEAPONS", "ASSAULT",
                "WEAPONDETAILS", "SOURCES", "MENTALHEALTHSOURCES", "LATITUDE", "LONGITUDE"],
        aggfunc=lambda x: ', '.join(x.astype(str)),
        fill_value=''
    )

# Display the pivot table
    st.title("US Mass Shootings CSV")
    st.write(pivot_table)


# Pages of app
pages = {
    "Home": home,
    "Citations": References,
}

# Add a selectbox to the sidebar for navigation
page = st.sidebar.selectbox("Choose a page:", list(pages.keys()))

# Display the selected pages
pages[page]()
