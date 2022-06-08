#from functools import cache
#from json import load
#from os import write
#from altair.vegalite.v4.api import concat
#from numpy import concatenate
#from pandas.core.frame import DataFrame
#from pyarrow import ListValue
from unittest import result
from PIL.Image import TRANSPOSE
import streamlit as st
import pandas as pd
from datetime import datetime
from gspread_pandas import Spread, Client
import gspread 
from google.oauth2 import service_account
import requests
import seaborn as sns
import matplotlib as mlp
import matplotlib.pyplot as plt
import altair as alt
import seaborn as sns
from lxml import html
import itertools
import random
#from gsheetsdb import connect


# Telegram options
chat_id = st.secrets["telegram"]['chat_id']
bot_id = st.secrets["telegram"]['bot_id']

verde_elo = "#00CC00"
rosso_elo = "Red"


# Streamlit CONFIGURATION settings
About = "App per l'inserimento dei duelli, la gestione del database dei duelli e il calcolo del punteggio ELO."

st.set_page_config( 
    page_title='YGO ELO', 
    page_icon = "🃏", 
    layout = 'centered', 
    initial_sidebar_state = 'collapsed'
    , menu_items = {
       "About": About
    }
)

# Code snippet to hide the menu and the "made with streamlit" banner
hide_streamlit_style = """
            <style>
            #MainMenu {visibility: show;}
            footer {visibility: hidden;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True) 


# Check if 'update_flag' already exists in session_state
# If not, then initialize it
if 'update_flag' not in st.session_state:
    st.session_state.update_flag = 0




# Create a Google authentication connection object
scope = ["https://www.googleapis.com/auth/spreadsheets", 
         "https://www.googleapis.com/auth/drive"]

credentials = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"], scopes = scope )
client = Client(scope=scope, creds=credentials)
spreadsheetname = "ELO db" 
spread = Spread(spreadsheetname, client = client)

# Check if the connection is established
#  Call our spreadsheet
sh = client.open(spreadsheetname)
#     worksheet_list = sh.worksheets()
#     st.write(worksheet_list)



#@st.cache
# Get the sheet as dataframe
def load_the_spreadsheet(spreadsheetname):
    worksheet = sh.worksheet(spreadsheetname)
    df = pd.DataFrame(worksheet.get_all_records(head=1))
    return df



# Update to Sheet
def update_the_spreadsheet(spreadsheetname, dataframe):
    col = ['Compound CID','Time_stamp']
    spread.df_to_sheet(dataframe[col],sheet = spreadsheetname,index = False)
    st.sidebar.info('Updated to GoogleSheet')



# DOWNLOAD THE DATA
@st.cache(allow_output_mutation=True)
def download_data():
    matches = load_the_spreadsheet("matches")
    lista_mazzi = load_the_spreadsheet("mazzi")
    tournaments = load_the_spreadsheet("tournaments")
    return matches, lista_mazzi, tournaments

matches, lista_mazzi, tournaments = download_data()



##### TELEGRAM
# Send message - guide: https://www.youtube.com/watch?v=M9IGRWFX_1w
def telegram_send_message(message, bot_id, chat_id):
    url_req = "https://api.telegram.org/bot" + bot_id + "/sendMessage" + "?chat_id=" + chat_id + "&text=" + message + "&parse_mode=HTML"
    requests.get(url_req)
    return True



def telegram_duello_message(deck_1, deck_2, outcome, elo_deck1, elo_after_1, elo_deck2, elo_after_2, emoji_flag = True):
    outcome_1, outcome_2, pointer = (" - ", " - ", "")
    if emoji_flag:
        outcome_1 = " ✅ - ❌ "
        outcome_2 = " ❌ - ✅ "
    else: 
        pointer = "⯈"

    message = ""
    if outcome == "1":
        message = pointer + "<b> " + deck_1 + "</b>" + outcome_1 + deck_2 + "\n"
        message = message + str(elo_after_1) + " (▲ " + str(round(elo_after_1- elo_deck1, 1)) + ") - " + str(elo_after_2) + " (▼ " + str(round(elo_after_2 - elo_deck2, 1)) + ")" 
    else: 
        message = deck_1 + outcome_2 + pointer + "<b> " + deck_2 + "</b>" + "\n" 
        message = message + str(elo_after_1) + " (▼ " + str(round(elo_after_1- elo_deck1, 1)) + ") - " + str(elo_after_2) + " (▲ " + str(round(elo_after_2 - elo_deck2, 1)) + ")" 
    return message
#  ❌ - ✅ 


#ELO calculation functions
def elo_calculation(elo_before, elo_opponent, outcome, K = 32):
    """ funzione per calcolare il nuoo rating ELO
    elo_before: elo del giocatore prima della partita
    elo_opponent: elo del giocatore sfidante
    outcome: 1=vittoria, 0=sconfitta
    K: parametro, vedere fonte
    - - - -
    return: nuovo punteggio elo, arrotondato a 1 cifra significativa
    - - - -
    Fonte: https://metinmediamath.wordpress.com/2013/11/27/how-to-calculate-the-elo-rating-including-example/
    """
    # Transformed rating to simplify further computations
    transformed_1 = 10**(elo_before / 400)
    transformed_2 = 10**(elo_opponent / 400) 
    
    expected_score_1 = transformed_1 / (transformed_1 + transformed_2)
    # expected_score_2 = transformed_2 / (transformed_1 + transformed_2)

    score = outcome

    elo_after = elo_before + K * (score - expected_score_1)
    return round(elo_after, 1)



def display_change_elo(deck_name, elo_before, elo_after):
    """ funzione che stampa le metriche con le modifiche al punteggio ELO dopo una partita
    return: True. La funzione stampa a video l'elemento metric
    """
    string_metric = str(round(elo_after - elo_before, 1))
    st.metric(deck_name, elo_after, string_metric)
    return True



def get_deck_elo(deck_name, mazzi):
    deck_elo = mazzi[mazzi["deck_name"] == deck_name]["elo"]
    return deck_elo.iloc[0]



def update_deck_elo(deck_name1, deck_name2, elo_updated1, elo_updated2, score1, score2, lista_mazzi, verbose = True):
    """ function to update the entire deck list, with the new elo
    """

    for i in lista_mazzi.index:
        if lista_mazzi.loc[i , "deck_name"] == deck_name1:
            lista_mazzi.loc[i, "elo"] = elo_updated1
            if score1 == 1:
                lista_mazzi.loc[i, "vinte"] += 1
            else: 
                lista_mazzi.loc[i, "perse"] += 1
            v = lista_mazzi.loc[i, "vinte"]
            p = lista_mazzi.loc[i, "perse"]
            lista_mazzi.loc[i, "percentage"] = v / (v + p)
        elif lista_mazzi.loc[i , "deck_name"] == deck_name2:
            lista_mazzi.loc[i, "elo"] = elo_updated2
            if score2 == 1:
                lista_mazzi.loc[i, "vinte"] += 1
            else: 
                lista_mazzi.loc[i, "perse"] += 1
            v = lista_mazzi.loc[i, "vinte"]
            p = lista_mazzi.loc[i, "perse"]
            lista_mazzi.loc[i, "percentage"] = v / (v + p)        
    spread.df_to_sheet(lista_mazzi, sheet = "mazzi", index = False)

    return True



def probabilità_vittoria(elo_deck, elo_opponent):
    R1 = 10**(elo_deck/400)
    R2 = 10**(elo_opponent/400)
    return R1/(R1+R2)



def duello_vinto_format(row):
    """https://queirozf.com/entries/pandas-dataframe-examples-styling-cells-and-conditional-formatting#highlight-cell-if-condition"""
    vittoria = 'background-color: #248f24'
    sconfitta = 'background-color: #990000'
    default = ''

    if row["Risultato"] == 1:
        return [vittoria, sconfitta, default]
    else:
        return [sconfitta, vittoria, default]



def storico_duelli(deck1, deck2, matches):
    """ DEPRECATED"""
    matches_horizontal = pd.DataFrame(columns=["Data", "Deck 1", "Deck 2", "Risultato", "Elo deck 1", "Elo deck 2"])
    for index, row in matches.iterrows():
        if matches.loc[index]["deck_pos"] == 1:
            deck_name = matches.loc[index]["deck_name"]
            if deck_name == deck1 or deck_name == deck2:
                deck_name2 = matches.loc[index+1]["deck_name"]
                if deck_name2 == deck1 or deck_name2 == deck2:
                    data = matches.loc[index]["date"]
                    elo_deck1 = matches.loc[index]["elo_before"]
                    elo_deck2 = matches.loc[index+1]["elo_before"]
                    if matches.loc[index]["win_flag"] == 1: risultato = 1
                    else: risultato = 2
                    match_horizontal = [data, deck_name, deck_name2, risultato, elo_deck1, elo_deck2 ]
                    match_horizontal = pd.Series(match_horizontal, index = matches_horizontal.columns)
                    matches_horizontal = matches_horizontal.append(match_horizontal, ignore_index=True)
    # matches_horizontal.style.format(precision=0, formatter={("Elo deck 1"): "{:.1f}"})
    st.dataframe(
        matches_horizontal.style.format(
            precision=0, 
            formatter = { 
                ("Elo deck 1"): "{:.0f}",
                ("Elo deck 2"): "{:.0f}"
                }).apply(
                    duello_vinto_format, subset=["Deck 1","Deck 2", "Risultato"], axis = 1
                )
    )
    return True



def filter_matches(matches, deck_1 = "", deck_2 = "", date = []):
    """ Funzione che filtra l alista dei duelli disputati (matches)
    OPTIONS: 
        - filtrare per singolo deck
        - filtrare per coppia di deck per avere duelli esclusivamente tra i due deck
        - filtrare per data
    INPUT: 
        - matches: lista dei match. la funzione lo filtra, 
                    ma l'input può essere preventivamente filtrato 
        - deck_1: nome del deck come in lista_mazzi. Default = ""
        - deck_2: nome del deck come in lista_mazzi. Default = ""
        - date: stringa di data della stessa forma del dataset matches. Default: ""
    """
    if date != []:
            matches = matches[matches["date"].isin(date)]
        
    if deck_1 != "":
        id_match_list = []
        for index, row in matches.iterrows():
            if row["deck_name"] == deck_1:
                id_match_list.append(row["id_match"])
        matches = matches[matches["id_match"].isin(id_match_list)]
    if deck_2 != "":
        id_match_list = []
        for index, row in matches.iterrows():
            if row["deck_name"] == deck_2:
                id_match_list.append(row["id_match"])
        matches = matches[matches["id_match"].isin(id_match_list)]

    return matches



def print_duelli(matches, condensed = False):
    """ funzione che scrive a video lista dei duelli disputati:
    Input:
    - condensed = False: se True ritorna i duelli in maniera condensata. 
        e.g. deck_A 2-1 deck_B
    """
    output = ""

    for index, row in matches.iterrows():
        if matches.loc[index]["deck_pos"] == 1:
            deck_name1 = matches.loc[index]["deck_name"]
            id_match = row["id_match"]
            win_flag_1 = row["win_flag"]
            deck_name2 = matches[(matches["id_match"] == id_match) & (matches["deck_pos"] == 2)].reset_index()
            deck_name2 = deck_name2.loc[0]["deck_name"]
            if win_flag_1 == 1: 
                output = output + f'<font color={verde_elo}>' + deck_name1 + '</font>'
                output = output + " - "
                output = output + f'<font color={rosso_elo}>' + deck_name2 + '</font>  \n'
            else:
                output = output + f'<font color={rosso_elo}>' + deck_name1 + '</font>'
                output = output + " - "
                output = output + f'<font color={verde_elo}>' + deck_name2 + '</font>  \n'

    st.markdown(output, unsafe_allow_html = True)
    return True



def output_info_mazzo_serata(lista_mazzi_selezionati):
    """Funzione per preparare output con statistiche del mazzo per dataset mazzi per serata.
    Usato in:
        Highlights serata. Per la preparazione di output con info di base del deck durante la serata
    ·🞄 """
    output = ""
    for index, row in lista_mazzi_selezionati.iterrows():
        output = output + f" ⬩ **{row['deck_name']}** - {row['duelli_serata']} duelli "
        output = output + f"({ int( (row['vittorie_serata'] / row['duelli_serata']) * 100) }%) ⬩ "
        if int(row['delta_elo_serata']) > 0: output = output + f"<font color={verde_elo}>+"
        elif int(row['delta_elo_serata']) < 0: output = output + f"<font color={rosso_elo}>"
        else: f"<font>"
        output = output + f"{int(row['delta_elo_serata'])}</font> punti  \n"
    return output 



def get_deck_matches(matches, deck):
    """ get a dataframe of the matches (with elo changes linked to them) for a single deck 
    Add the opponent for each match and a few of his statistics. 
    - - - - - - -
    USED IN:
     - plots functions
     - statistics functions
     - functions for highlights serata """

    # # Extract deck data
    matches_copy = matches.copy()
    deck_matches = matches_copy[matches_copy['deck_name'] == deck].reset_index()

    # # Add opponent statistics
    # add empty columns
    deck_matches['opponent_name'] = range(0, len(deck_matches))
    deck_matches['opponent_elo_before'] = range(0, len(deck_matches))
    deck_matches['opponent_elo_after'] = range(0, len(deck_matches))
    i = 0
    for id_match in deck_matches['id_match']:
        #opponent_row = matches[matches['id_match'] == id_match and matches['deck_name'] != deck]
        opponent_row = matches_copy.query('id_match == @id_match and deck_name != @deck').reset_index()
        deck_matches.loc[deck_matches.index[0], 'opponent_name'] = opponent_row.loc[opponent_row.index[0], 'deck_name']
        deck_matches.loc[deck_matches.index[0], 'opponent_elo_before'] = opponent_row.loc[opponent_row.index[0], 'elo_before']
        deck_matches.loc[deck_matches.index[0], 'opponent_elo_after'] = opponent_row.loc[opponent_row.index[0], 'elo_after']
        i += 1
    
    return deck_matches



def insert_match2(matches, deck1, deck2, outcome, tournament, lista_mazzi):

    if deck1 == deck2: 
        st.error("Errore. Mazzo 1 e Mazzo 2 combaciano.")
        return False

    ws = sh.worksheet("matches")

    date = str(datetime.now().strftime("%d/%m/%Y"))
    time = str(datetime.now().strftime("%H:%M"))

    id_match = max(matches["id_match"]) + 1

    elo_deck1 = get_deck_elo(deck1, lista_mazzi)
    elo_deck2 = get_deck_elo(deck2, lista_mazzi)

    if outcome=="1": win_flag_1 = 1
    else: win_flag_1 = 0

    elo_after_1 = elo_calculation(elo_deck1, elo_deck2, win_flag_1)

    data_list_1 = {
        "match_key": [10*id_match+1],
        "id_match": id_match,
        "deck_pos": [1], #fixed
        "date": [date],
        "time": [time],
        "deck_name": [deck_1],
        "win_flag": [win_flag_1],
        "elo_before": [elo_deck1],
        "elo_after": [elo_after_1],
        "id_tournament": [tournament]
    }

    if outcome=="2": win_flag_2 = 1
    else: win_flag_2 = 0

    elo_after_2 = elo_calculation(elo_deck2, elo_deck1, win_flag_2)

    data_list_2 = {
        "match_key": [10*id_match + 2],
        "id_match": id_match,
        "deck_pos": [2], # fixed
        "date": [date],
        "time": [time],
        "deck_name": [deck_2],
        "win_flag": [win_flag_2],
        "elo_before": [elo_deck2],
        "elo_after": [elo_after_2],
        "id_tournament": [tournament]
    }

    c1, c2  = st.columns((1, 1))

    # ▲ ▼ 
    with c1: 
        display_change_elo(deck1, elo_deck1, elo_after_1)
    with c2:
        display_change_elo(deck2, elo_deck2, elo_after_2)

    data_list_1 = pd.DataFrame(data_list_1)
    data_list_2 = pd.DataFrame(data_list_2)
    data_list = pd.concat([data_list_1, data_list_2], axis=0)
    matches = matches.append(data_list, ignore_index=True)

    # statistiche dei duelli tra i due deck
    statistiche_duelli(deck1, deck2, matches)
    # storico_duelli(deck1, deck2, matches)
    print_duelli(filter_matches(matches, deck1, deck2))
    # # # # # # # # # # # # 

    # scheda con dettaglio dei duelli tra i due deck

    spread.df_to_sheet(matches, sheet = "matches", index = False)

    update_deck_elo(deck1, deck2, elo_after_1, elo_after_2, win_flag_1, win_flag_2, lista_mazzi)
    


    # Invio messaggio con duello eseguito:
    telegram_send_message(
        telegram_duello_message(
            deck1, deck2, outcome, 
            elo_deck1, elo_after_1, 
            elo_deck2, elo_after_2, 
            True), 
        bot_id, chat_id)
    # # # # # # # # # # # # 

    return True



def get_image_from_api(card_name, language = "it"):
    """ prints the image of the card, downloading it from the API
        API guide: https://db.ygoprodeck.com/api-guide/
    requires: card_name (correct and complete name of the card)
    additional param: language ("it", "en" ... )"""
    parameters = {
    "name": card_name,
    "language": language
    }
    api_response = requests.get("https://db.ygoprodeck.com/api/v7/cardinfo.php", params=parameters)
    st.markdown("## " + card_name)
    if api_response.status_code == 200:
        data = api_response.json()
        id_card = data["data"][0]["id"]

        st.image("https://storage.googleapis.com/ygoprodeck.com/pics/" + str(id_card) +".jpg")

    return True



######## PLOTTING SECTION ######################

def get_max_elo(deck_matches):
    if len(deck_matches) == 0:
        return False
    max_elo, index = 0, 0
    for i, elo in enumerate(deck_matches["elo_after"]):
        if elo > max_elo:
            max_elo = elo
            index = i
    return index + 1, max_elo



def get_min_elo(deck_matches):
    if len(deck_matches) == 0:
        return False
    min_elo, index = 999999, 0
    for i, elo in enumerate(deck_matches["elo_after"]):
        if elo < min_elo:
            min_elo = elo
            index = i
    return index + 1, min_elo



def ELO_plot(deck_matches):
    if len(deck_matches) == 0:
        return False
    mlp.rcdefaults() 
    fig = plt.figure(figsize=(5, 4))
    # sns.set(rc={'axes.facecolor':'#E8ECEC', 'figure.facecolor':'#E8ECEC'})
    # plt.style.use("classic")
    plt.ylim(0.8*min(deck_matches["elo_after"]), 1.2*max(deck_matches["elo_after"]))
    plt.grid(False)
    titolo = "Andamento ELO - " + deck_matches.loc[0, 'deck_name']
    sns.lineplot(
        x = range(1, len(deck_matches)+1), 
        y = "elo_after", 
        data=deck_matches).set(title=titolo)
    plt.xlabel('Duelli')
    plt.ylabel('ELO')
    # max
    index_max, elo_max = get_max_elo(deck_matches)
    plt.scatter(x = index_max, y = elo_max, color = "green")
    plt.annotate(str(elo_max), xy = (index_max-0.5, elo_max+50), color = "green")
    # min
    index_min, elo_min = get_min_elo(deck_matches)
    plt.scatter(x = index_min, y = elo_min, color = "red")
    plt.annotate(str(elo_min), xy = (index_min-0.5, elo_min-100), color = "red")
    #
    st.pyplot(fig)
    return True



def ELO_plot_altair(deck_matches):
    if len(deck_matches) == 0:
        return False

    deck_matches['x'] = range(1, len(deck_matches) + 1)
    elo_chart = alt.Chart(deck_matches).mark_trail().encode(
        x=alt.X('x',
            title = 'Duelli'),
        y=alt.Y('elo_after',
            scale=alt.Scale(
                domain=(
                    0.8*min(deck_matches["elo_after"]), 
                    1.2*max(deck_matches["elo_after"]) ) ),
            title = 'ELO'),
        size=alt.Size('elo_after', legend=None)
    ).properties(
    title = "Andamento ELO - " + deck_matches.loc[0, 'deck_name']
    ).configure_axis( 
        grid=False
    ).interactive()

    st.altair_chart(elo_chart, use_container_width=True)

    return True



def ELO_plot_multiple_altair(deck_list, matches):
    """ function that plots the ELO trend for multiple decks in the same plot
    input: 
        deck_list: a list of names of decks
        matches: list of matches """
    list_of_deck_matches = []
    data = pd.DataFrame(columns=["deck_name", "elo_after", "index"])
    for i, deck_name in enumerate(deck_list):
        list_of_deck_matches.append(get_deck_matches(matches, deck_name))
        duelli_mazzo = get_deck_matches(matches, deck_name)[["deck_name", "elo_after"]]
        duelli_mazzo["index"] = duelli_mazzo.index
        duelli_mazzo=duelli_mazzo.reset_index()
        duelli_mazzo = duelli_mazzo.drop('level_0', axis=1)
        data = pd.concat([data, duelli_mazzo], sort=False)
    
    multiple_chart = alt.Chart(
        data = data,
        height = 1000
        ).mark_line().encode(
        x = alt.X(
            'index',
            title = "Duelli"),
        y = alt.Y(
            'elo_after',
            title = "ELO",
            scale=alt.Scale(
                domain=(
                    0.8*min(data["elo_after"]), 
                    1.2*max(data["elo_after"]) ) ), ),
        color = alt.Color(
            'deck_name', 
            legend = alt.Legend(
                title = "Deck",
                orient = 'bottom',
                columns= 2)),
        strokeDash='deck_name',
    )
    
    st.altair_chart(multiple_chart, use_container_width=True)
        
    return True
### DEBUG utils
# ELO_plot_multiple_altair(lista_mazzi["deck_name"], matches)
# ELO_plot_multiple_altair(["Slifer", "Alieno", "Eroi Mascherati", "Zombie"], matches)
# ELO_plot_altair(get_deck_matches(matches, "Slifer"))



def plot_distribuzione_mazzi(lista_mazzi): 
    """ Altair histogram to plot the distribution of elo 
    Used in:
     - Classifica """
    distribuzione_mazzi = alt.Chart(lista_mazzi, height = 400).mark_bar().encode(
        alt.X("elo", bin=True, title="ELO"),
        alt.Y('count()', title="Numero mazzi"),
        color = alt.Color(
            'deck_category', 
            legend = alt.Legend(
                title = "Categoria",
                orient = 'bottom',
                columns= 1)),
                tooltip=['deck_name', 'elo', 'owner' ]
    )
    st.altair_chart(distribuzione_mazzi)
    return True



def heatmap_duelli(matches):
    years = []
    months = []
    for row in matches.date:
        giorno = datetime.strptime(row, "%d/%m/%Y")
        years.append(giorno.year)
        months.append(giorno.month)
    matches['year'] = years
    matches['month'] = months

    heatmap_data = pd.pivot_table(
        data = matches,
        values= 'date',
        index = 'year',
        columns = 'month',
        aggfunc = 'count'
    )
    heatmap_data = heatmap_data / 2

    fig, ax = plt.subplots(1, 1, figsize = (10, 1), dpi=300)
    sns.heatmap(heatmap_data, annot=True, cbar=False)
    ax.set_ylabel('')
    ax.set_xlabel('')
    st.pyplot(fig)
    return True



######## STATISTICHE SECTION ######################

def stat_perc_vittorie(deck1, vittorie_1, vittorie_2, duelli_totali):
    """ Statistiche delle percentuali di vittoria
    funzione utilizzata nelle statistiche duelli, per rappresentare la percentuale di vittoria contro
    l'altro mazzo con elementi st.metric """
    delta_color_str = "normal"
    if vittorie_1 == vittorie_2:
        delta_color_str = "off"
    elif vittorie_1 < vittorie_2:
        delta_color_str = "inverse"
    st.metric(
        label = "% vittorie "+ deck1, 
        value = str(round(vittorie_1/(duelli_totali) * 100, 0)) + " %", 
        delta = str(vittorie_1) + " duelli vinti",
        delta_color = delta_color_str)



def statistiche_duelli(deck1, deck2, matches):
    duelli_totali = 0
    vittorie_1 = 0
    vittorie_2 = 0

    for index, row in matches.iterrows():
        if matches.loc[index]["deck_pos"] == 1:
            deck_name = matches.loc[index]["deck_name"]
            if deck_name == deck1 or deck_name == deck2:
                deck_name2 = matches.loc[index+1]["deck_name"]
                if deck_name2 == deck1 or deck_name2 == deck2:
                    duelli_totali +=1
                    if matches.loc[index]["win_flag"] == 1 and deck_name == deck1:
                        vittorie_1 += 1
                    elif matches.loc[index]["win_flag"] == 1 and deck_name == deck2:
                        vittorie_2 += 1
                    elif matches.loc[index+1]["win_flag"] == 1 and deck_name2 == deck1:
                        vittorie_1 += 1
                    else:
                        vittorie_2 += 1
    
    st.subheader("Statistiche dei duelli tra " + deck1 + " e " + deck2)
    st.write("Numero totale di duelli: " +  str(duelli_totali))
    if duelli_totali > 0:
        stat_perc_vittorie(deck1, vittorie_1, vittorie_2, duelli_totali)
        stat_perc_vittorie(deck2, vittorie_2, vittorie_1, duelli_totali)

    return True



def statistiche_mazzo(deck_name, deck_matches, mazzi = lista_mazzi):
    """ Funzione che ritorna a schermo le statistiche del mazzo """
    ELO_mazzo = get_deck_elo(deck_name, mazzi)
    numero_duelli = len(deck_matches)
    if numero_duelli == 0:
        st.markdown(
            f"Punteggio attuale mazzo: {ELO_mazzo}  \n"
            f"Numero di duelli: **{numero_duelli}**"
        )
        return True
    
    numero_vittorie = sum(deck_matches['win_flag'])
    percentuale_vittorie = int(round(numero_vittorie/numero_duelli*100, 0))
    semaforo_percentuale = "🟢" if percentuale_vittorie>=70 else ("🟡" if percentuale_vittorie>=30  else "🔴")

    st.markdown(
        f"Punteggio attuale mazzo: **{ELO_mazzo}**  \n"
        f"Numero di duelli: **{numero_duelli}**  \n"
        f"Percentuale di vittorie: **{percentuale_vittorie} %** - {semaforo_percentuale}"
    )
    
    return True 



def get_deck_rank(deck_name, ):
    return True



######### TOURNAMENT #############################

def probabilità_vittoria_torneo_a_eliminazione(elo_deck_1, elo_deck_2, elo_deck_3, elo_deck_4):
    P1 = probabilità_vittoria(elo_deck_1, elo_deck_2)
    P3 = probabilità_vittoria(elo_deck_3, elo_deck_4)
    P4 = probabilità_vittoria(elo_deck_4, elo_deck_3)
    PA_3 = probabilità_vittoria(elo_deck_1, elo_deck_3)
    PA_4 = probabilità_vittoria(elo_deck_1, elo_deck_4)
    PW1 = P1*(PA_3*P3) + P1*(PA_4*P4) 
    return PW1




### APP ########################

st.markdown("# YGO ELO app")

# SIDEBAR
st.sidebar.write( "[🔗 Link to Google Sheets](" + spread.url + ")" )
## Indice:
pagina_selezionata = st.sidebar.radio("Menu:", 
                     options = [
                         "➕ Aggiungi un duello", 
                         "🏆 Classifiche",
                         "🔍 Confronta mazzi",
                         "✨ Highlights serata",
                         "🏅 Torneo",
                         "📈 Statistiche mazzo",
                         "📝 Info ELO",
                         "🛒 Cardmarket"])




################################
# SEZIONE: "Debug"
if st.secrets["debug"]['debug_offline'] == "Truee":
    with st.expander("matches"):
        st.dataframe(matches)
    
    with st.expander("lista_mazzi"):
        st.dataframe(lista_mazzi[1:])

    st.write("Heatmap con duelli fatti, non in utilizzo fin quando non ci saranno più dati:")
    heatmap_duelli(matches)

    

################################
# PAGINA: "Aggiungi un duello"
if pagina_selezionata == "➕ Aggiungi un duello":

    matches = load_the_spreadsheet("matches")
    lista_mazzi = load_the_spreadsheet("mazzi")
    tournaments = load_the_spreadsheet("tournaments")

    with st.form(key = 'insert_match'):
        c1, c2  = st.columns((1, 1))
        with c1: 
            deck_1 = st.selectbox("Mazzo 1: ", lista_mazzi["deck_name"])
        with c2: 
            deck_2 = st.selectbox("Mazzo 2: ", lista_mazzi["deck_name"])
        c1, c2 = st.columns([1, 1])
        with c1:
            outcome = st.radio("Vincitore: ", options = ["1", "2"])
        with c2:
            tournament = st.selectbox("Torneo: ", options = tournaments["tournament_name"].unique())
        button_insert_match = st.form_submit_button("Inserisci il duello a sistema")

    if not button_insert_match:
        immagini_yugioh = {
              "yugi"    : "https://vignette.wikia.nocookie.net/p__/images/d/d5/YugiRender.png/revision/latest?cb=20200128002036&path-prefix=protagonist" 
            , "slifer"  : "https://th.bing.com/th/id/R.a43e318bc53e873acb6668a784d5b091?rik=L0JSbZGRKFhzzA&pid=ImgRaw&r=0&sres=1&sresct=1"
            , "ra"      : "https://th.bing.com/th/id/R.5d3205801a7d642ee718bef53bfdfdea?rik=BFbCta6LS3i5FA&riu=http%3a%2f%2forig09.deviantart.net%2fa09d%2ff%2f2016%2f065%2f7%2fe%2fwinged_dragon_of_ra___full_artwork_by_xrosm-d9u37b6.png&ehk=Ec3SeR1YD2DNZcpz20J781rK%2fHEPyqi60Qf2W00lvRw%3d&risl=&pid=ImgRaw&r=0"
            , "obelisk" : "https://th.bing.com/th/id/OIP.Uo4eYtROaa28MMKHMrFrgQHaHa?pid=ImgDet&rs=1"
            , "prev.met": "https://external-content.duckduckgo.com/iu/?u=http%3A%2F%2Fi275.photobucket.com%2Falbums%2Fjj295%2Fwilson911%2FWeatherReportMRL-EN-C.jpg&f=1&nofb=1"
            , "sold.pie": "https://vignette.wikia.nocookie.net/yugioh/images/f/fa/GiantSoldierofStone-TF04-JP-VG.jpg/revision/latest?cb=20130115210040&path-prefix=it"
            , "exodia"  : "https://orig00.deviantart.net/e245/f/2012/364/9/b/exodia_the_forbidden_one_by_alanmac95-d5grylr.png"
            , "mag.ner" : "https://images-wixmp-ed30a86b8c4ca887773594c2.wixmp.com/f/06cb28af-a15c-45d3-b1b6-fcbc1910e0c3/dberd1j-e363f2b7-e201-4e31-b6dd-ea75cfe0e4cc.png?token=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ1cm46YXBwOiIsImlzcyI6InVybjphcHA6Iiwib2JqIjpbW3sicGF0aCI6IlwvZlwvMDZjYjI4YWYtYTE1Yy00NWQzLWIxYjYtZmNiYzE5MTBlMGMzXC9kYmVyZDFqLWUzNjNmMmI3LWUyMDEtNGUzMS1iNmRkLWVhNzVjZmUwZTRjYy5wbmcifV1dLCJhdWQiOlsidXJuOnNlcnZpY2U6ZmlsZS5kb3dubG9hZCJdfQ.JxG1f74TXzHH23bTwTb2hnzMbjXgHfnEtjcWy918iyI"
            , "mag.ner2": "https://i.pinimg.com/originals/8c/35/f3/8c35f3b9c684859284240416b86f2569.png"
            , "kuriboh" : "https://external-content.duckduckgo.com/iu/?u=https%3A%2F%2F4.bp.blogspot.com%2F-0B5hoixAQO8%2FUukam4xT6LI%2FAAAAAAAABV0%2Fw6sLOKcoYHU%2Fw1200-h630-p-k-no-nu%2FWinged%2BKuriboh%2B.png&f=1&nofb=1"
            , "mos.res" : "http://4.bp.blogspot.com/-RuSjO8dQcXc/TcCXLJYAfdI/AAAAAAAAA80/lkxq0z536dQ/s1600/MonsterReborn.png"
            , "cyb.drag": "https://external-content.duckduckgo.com/iu/?u=http%3A%2F%2Forig07.deviantart.net%2F8e9b%2Ff%2F2012%2F051%2F6%2F6%2Fcyber_dragon_render_by_moonmanxo-d4qfk75.png&f=1&nofb=1"
            , "cyb.dra2": "https://external-content.duckduckgo.com/iu/?u=https%3A%2F%2F2.bp.blogspot.com%2F-o-k2v5lysEY%2FUn5tYpaTUlI%2FAAAAAAAAATQ%2Fi4XMvGMtaRk%2Fs1600%2FCyber%2BTwin%2BDragon.png&f=1&nofb=1"
            , "whi.dra.": "https://external-content.duckduckgo.com/iu/?u=http%3A%2F%2F2.bp.blogspot.com%2F-62vgvvFQB3g%2FUopWcotTXWI%2FAAAAAAAAAtA%2FNe21d28M1Jg%2Fs1600%2FBlue%2BEyes%2BWhite%2BDragon%2BAlternate%2B3.png&f=1&nofb=1"
            , "wh.dra.2": "https://external-content.duckduckgo.com/iu/?u=https%3A%2F%2Fimages-wixmp-ed30a86b8c4ca887773594c2.wixmp.com%2Fintermediary%2Ff%2F06cb28af-a15c-45d3-b1b6-fcbc1910e0c3%2Fdajib0k-fb4ca87f-66c4-4aaf-9afe-97761db37741.png%2Fv1%2Ffill%2Fw_1023%2Ch_630%2Cstrp%2Fblue_eyes_alternative_white_dragon_render_by_carlos123321_dajib0k-fullview.png&f=1&nofb=1"
            # , "": ""
            # , "": ""
            # , "": ""
            # , "": ""
            # , "": ""
        
        }
        immagine_pescata = random.sample(range(1, len(immagini_yugioh)), k = 1)[0]
        st.image(list(immagini_yugioh.values())[immagine_pescata])

    if button_insert_match:
        matches, lista_mazzi, tournaments = download_data()
        outcome = insert_match2(matches, deck_1, deck_2, outcome, tournament, lista_mazzi)
        if outcome == True:
            st.success("Duello inserito correttamente a sistema")



################################
# PAGINA: "Classifiche"
if pagina_selezionata == "🏆 Classifiche":

    st.markdown("## 🏆 Classifica deck")
    classifica = lista_mazzi[1:].copy()
    classifica = classifica.astype({"elo": int})
    classifica.columns = ["# Cat.", "Cat.", "Nome deck", "Elo", "Vinte", "Perse", "Percentuale", "Duellante", "Note"]
    classifica.sort_values(by = ['Elo'], inplace=True, ascending=False)
    classifica = classifica.reset_index()
    output = ""
    posizione = 1
    for deck in classifica["Nome deck"]:
        if posizione == 1: output = output + "🥇 "
        if posizione == 2: output = output + "🥈 "
        if posizione == 3: output = output + "🥉 "
        if posizione == len(classifica): output = output + "🥄 "
        output = output + f"**{posizione}** - {deck} - {classifica['Elo'][posizione-1]}  \n"
        posizione += 1
    st.markdown(output)

    lista_distribuzione = lista_mazzi[["deck_name","elo","deck_category","owner"]]
    plot_distribuzione_mazzi(lista_distribuzione[1:])



################################
# PAGINA: "🔍 Confronta Mazzi"
if pagina_selezionata == "🔍 Confronta mazzi":

    with st.form(key = 'confronta_mazzi'):
        st.subheader("Seleziona due mazzi da confrontare")
        c1, c2  = st.columns((1, 1))
        with c1: 
            deck_1 = st.selectbox("Mazzo 1: ", lista_mazzi["deck_name"])
        with c2: 
            deck_2 = st.selectbox("Mazzo 2: ", lista_mazzi["deck_name"])
        button_confronta_mazzi = st.form_submit_button("Confronta mazzi")

    if button_confronta_mazzi:
        statistiche_duelli(deck_1, deck_2, matches)
        print_duelli(filter_matches(matches, deck_1, deck_2))



################################
# PAGINA: "✨ Highlights serata"
if pagina_selezionata == "✨ Highlights serata":
    st.markdown("## Highlights della serata✨")
    
    with st.form(key = 'highlights serata'):
        lista_date = matches["date"].drop_duplicates()[::-1]     
        data_selezionata = st.multiselect("Seleziona data:", options=lista_date)
        button_highlights = st.form_submit_button("Highlights ✨")

    if button_highlights:
        matches_serata = filter_matches(matches, date = data_selezionata)
        if data_selezionata==[]:
            st.warning("Selezionare almeno un giorno per avere informazioni su una singola serata.")

        ## Creazione delle statistiche della serata
        duelli_serata       = []
        vittorie_serata     = []
        elo_before_serata   = []
        elo_after_serata    = []
        delta_elo_serata    = []
        posizione_classifica_before = []
        posizione_classifica_after  = []
        delta_posizione_classifica  = []
        for index, row in lista_mazzi.iterrows():
            deck_name = row['deck_name']
            duelli_mazzo = 0
            vittorie_mazzo = 0
            elo_before_mazzo = 0
            elo_after_mazzo = 0
            for index, row_match in matches_serata.iterrows():
                if deck_name == row_match['deck_name']:
                    duelli_mazzo += 1
                    if row_match['win_flag'] == 1:
                        vittorie_mazzo += 1
                    if elo_before_mazzo == 0:
                        elo_before_mazzo = row_match['elo_before']
                    elo_after_mazzo = row_match['elo_after']
            duelli_serata.append(duelli_mazzo)
            vittorie_serata.append(vittorie_mazzo)
            if duelli_mazzo == 0: elo_before_serata.append(row['elo'])
            else: elo_before_serata.append(elo_before_mazzo)
            if duelli_mazzo == 0: elo_after_serata.append(row['elo'])
            else: elo_after_serata.append(elo_after_mazzo)
            delta_elo_serata.append(elo_after_mazzo - elo_before_mazzo)
        lista_mazzi['duelli_serata']        = duelli_serata
        lista_mazzi['vittorie_serata']      = vittorie_serata
        lista_mazzi['elo_before_serata']    = elo_before_serata
        lista_mazzi['elo_after_serata']     = elo_after_serata
        lista_mazzi['delta_elo_serata']     = delta_elo_serata

        for index, row_deck in lista_mazzi.iterrows():
            deck_name       = row_deck['deck_name']
            deck_elo_before = row_deck['elo_before_serata']
            deck_elo_after  = row_deck['elo_after_serata']
            posizione_mazzo_before  = 1
            posizione_mazzo_after   = 1
            for index, row_classifica in lista_mazzi.iterrows():
                if deck_name == '': continue # no need to compute for the empty row
                if (row_classifica['elo_before_serata'] == '') or (deck_elo_before == ''):
                    posizione_mazzo_before  += 1
                    posizione_mazzo_after   += 1
                    continue
                if (row_classifica['deck_name'] != deck_name) and (row_classifica['elo_before_serata'] >= int(deck_elo_before)):
                    posizione_mazzo_before += 1
                if (row_classifica['deck_name'] != deck_name) and (row_classifica['elo_after_serata'] >= int(deck_elo_after)):
                    posizione_mazzo_after += 1
            posizione_classifica_before.append(posizione_mazzo_before - 1)
            posizione_classifica_after.append(posizione_mazzo_after - 1)
            delta_posizione_classifica.append(posizione_mazzo_after - posizione_mazzo_before)

        lista_mazzi['posizione_classifica_before']  = posizione_classifica_before
        lista_mazzi['posizione_classifica_after']   = posizione_classifica_after
        lista_mazzi['delta_posizione_classifica']   = delta_posizione_classifica

        st.markdown("")
        st.markdown(f"Numero di duelli nella serata: **{sum(lista_mazzi['duelli_serata'])/2}**")

        # TOP della serata
        st.markdown("### 😎 Top deck della serata")

        ## Mazzo con più duelli
        max_duelli = lista_mazzi[lista_mazzi['duelli_serata'] == max(lista_mazzi['duelli_serata'])]
        output = ""
        if len(max_duelli) > 1: output = output + "Mazzi con più duelli:  \n"
        else: output = output + "Mazzo con più duelli:  \n"
        output = output + output_info_mazzo_serata(max_duelli)
        st.markdown(output, unsafe_allow_html=True)

        ## Mazzo con più punti ELO
        max_elo = lista_mazzi[lista_mazzi['delta_elo_serata'] == max(lista_mazzi['delta_elo_serata'])]
        output = ""
        if len(max_elo) > 1: output = output + "Mazzi che hanno guadagnato più punti ELO:  \n"
        else: output = output + "Mazzo che ha guadagnato più punti ELO:  \n"
        output = output + output_info_mazzo_serata(max_elo)
        st.markdown(output, unsafe_allow_html=True)

        st.markdown("---")
        # WORST della serata
        st.markdown("### 😪 Peggiori deck della serata")

        ## Mazzo con meno punti ELO
        min_elo = lista_mazzi[lista_mazzi['delta_elo_serata'] == min(lista_mazzi['delta_elo_serata'])]
        output = ""
        if len(min_elo) > 1: output = output + "Mazzi che hanno perso più punti ELO:  \n"
        else: output = output + "Mazzo che ha perso più punti ELO:  \n"
        output = output + output_info_mazzo_serata(min_elo)
        st.markdown(output, unsafe_allow_html=True)

        st.markdown("---")
        # Delta elo serata per proprietario deck
        st.markdown("### 👤 Delta ELO per proprietario deck")
        pivot_serata = pd.pivot_table(
            data = lista_mazzi[lista_mazzi['duelli_serata'] != 0], 
            values = ['delta_elo_serata', 'duelli_serata', 'vittorie_serata'], 
            index = 'owner', 
            aggfunc='sum').reset_index("owner")
        pivot_serata = pivot_serata.sort_values(by = 'delta_elo_serata', ascending=False)
        output = ''
        for index, row in pivot_serata.iterrows():
            if row['owner'] == "": continue
            else:
                delta = round(row['delta_elo_serata'], 1)
                duelli = row['duelli_serata']
                percentuale = int( row['vittorie_serata'] / row['duelli_serata'] * 100 )
                output = output + f" ⬩ **{row['owner']}**: "
                if delta > 0: output = output + f"<font color={verde_elo}>+{delta}</font> punti con {duelli} duelli ({percentuale}%)"
                elif delta < 0: output = output + f"<font color={rosso_elo}>{delta}</font> punti con {duelli} duelli ({percentuale}%)"
                else: output = output + f"+0 punti con {duelli} duelli ({percentuale}%)"
            output = output + "  \n"
        st.markdown(output, unsafe_allow_html=True)


        st.markdown("---")
        # Sezione di Maggiori dettagli
        st.markdown("### ℹ Maggiori dettagli della serata")

        with st.expander("🔍 Dettaglio per tutti i mazzi:"):
            lista_mazzi_serata = lista_mazzi[lista_mazzi['duelli_serata'] > 0]
            lista_mazzi_serata = lista_mazzi_serata.sort_values(by=['duelli_serata'], ascending=False)
            output = ""
            output = output + output_info_mazzo_serata(lista_mazzi_serata)
            st.markdown(output, unsafe_allow_html=True)


        # # Classifica con DELTA
        classifica = lista_mazzi[1:].copy()
        classifica = classifica.astype({"elo": int})
        classifica = classifica.astype({"elo_before_serata": int})
        classifica = classifica.astype({"elo_after_serata": int})

        classifica.sort_values(by = ['posizione_classifica_after'], inplace=True, ascending=True)
        classifica = classifica.reset_index()
        output = ""
        for index, row in classifica.iterrows():
            posizione_classifica_before = row['posizione_classifica_before']
            posizione_classifica_after = row['posizione_classifica_after']
            delta_posizione_classifica = row['delta_posizione_classifica']
            if posizione_classifica_after == 1: output = output + "🥇 "
            if posizione_classifica_after == 2: output = output + "🥈 "
            if posizione_classifica_after == 3: output = output + "🥉 "
            if posizione_classifica_after == len(classifica): output = output + "🥄 "
            output = output + f"**{posizione_classifica_after}** - {row['deck_name']} - {row['elo_after_serata']} "
            if delta_posizione_classifica < 0: output = output + f"(<font color={verde_elo}> ▲ {- delta_posizione_classifica} </font>) "
            if delta_posizione_classifica > 0: output = output + f"(<font color={rosso_elo}> ▼ {- delta_posizione_classifica} </font>) "
            output = output + "  \n"
        with st.expander("🏆 Classifica aggiornata dopo la serata:"):
            st.markdown(output, unsafe_allow_html=True)

        
         ## Lista duelli serata
        with st.expander("💥 Lista dei duelli della serata:"):
            print_duelli(matches_serata)



################################
# PAGINA: "🏅 Torneo"
if pagina_selezionata == "🏅 Torneo":

    tournaments = load_the_spreadsheet("tournaments")

    with st.form(key = "creazione_torneo"):
        st.subheader("Crea un torneo")
        nome_torneo = st.text_input("Nome del torneo")
        st.markdown("---")
        mazzi_torneo = {}
        for owner in lista_mazzi["owner"].unique():
            if owner == "": continue
            mazzi_da_selezionare = [""]
            mazzi_da_selezionare.extend(list(lista_mazzi.loc[lista_mazzi["owner"] == owner, "deck_name"]))
            mazzi_torneo[owner] = st.selectbox(owner, mazzi_da_selezionare)
        button_creazione_torneo = st.form_submit_button("Crea torneo")

    if button_creazione_torneo: 
        if nome_torneo in list(tournaments["tournament_name"]): 
            st.error("Nome torneo già esistente")
        else:
            st.success("Torneo creato")
            st.subheader(nome_torneo)

            deck_partecipanti = []
            for i, owner in enumerate(mazzi_torneo):
                deck = mazzi_torneo[owner]
                deck_partecipanti.append(deck)
                if deck == "": continue
                riga_torneo = [nome_torneo, "", "", deck, get_deck_elo(deck, lista_mazzi), owner]
                tournaments.loc[len(tournaments)] = riga_torneo
            spread.df_to_sheet(tournaments, sheet = "tournaments", index = False)
            elo_0 = get_deck_elo(deck_partecipanti[0], lista_mazzi)
            elo_1 = get_deck_elo(deck_partecipanti[1], lista_mazzi)
            elo_2 = get_deck_elo(deck_partecipanti[2], lista_mazzi)
            elo_3 = get_deck_elo(deck_partecipanti[3], lista_mazzi)
            w0 = int(round(probabilità_vittoria_torneo_a_eliminazione(elo_0,elo_1,elo_2,elo_3),2)*100)
            w1 = int(round(probabilità_vittoria_torneo_a_eliminazione(elo_1,elo_0,elo_2,elo_3),2)*100)
            w2 = int(round(probabilità_vittoria_torneo_a_eliminazione(elo_2,elo_3,elo_0,elo_1),2)*100)
            w3 = int(round(probabilità_vittoria_torneo_a_eliminazione(elo_3,elo_2,elo_0,elo_1),2)*100)
            st.markdown(f"Vittoria del deck _{deck_partecipanti[0]}_ ({elo_0}): **{w0}%**")
            st.markdown(f"Vittoria del deck _{deck_partecipanti[1]}_ ({elo_1}): **{w1}%**")
            st.markdown(f"Vittoria del deck _{deck_partecipanti[2]}_ ({elo_2}): **{w2}%**")
            st.markdown(f"Vittoria del deck _{deck_partecipanti[3]}_ ({elo_3}): **{w3}%**")


    st.subheader("Probabilità vittoria")
    with st.form(key = "probabilità_inizio_torneo"):
        st.markdown("Calcola la probabilità di vittoria ad inizio torneo \n _'Torneo ad eliminazione con 4 giocatori'_")
        deck_partecipanti = st.multiselect("Seleziona i partecipanti: ", options=lista_mazzi["deck_name"])
        button_probabilità = st.form_submit_button("Calcola probabilità")

    if button_probabilità:
        elo_0 = get_deck_elo(deck_partecipanti[0], lista_mazzi)
        elo_1 = get_deck_elo(deck_partecipanti[1], lista_mazzi)
        elo_2 = get_deck_elo(deck_partecipanti[2], lista_mazzi)
        elo_3 = get_deck_elo(deck_partecipanti[3], lista_mazzi)
        print(f"0: {elo_0}")
        print(f"1: {elo_1}")
        print(f"2: {elo_2}")
        print(f"3: {elo_3}")
        w0 = int(round(probabilità_vittoria_torneo_a_eliminazione(elo_0,elo_1,elo_2,elo_3),2)*100)
        w1 = int(round(probabilità_vittoria_torneo_a_eliminazione(elo_1,elo_0,elo_2,elo_3),2)*100)
        w2 = int(round(probabilità_vittoria_torneo_a_eliminazione(elo_2,elo_3,elo_0,elo_1),2)*100)
        w3 = int(round(probabilità_vittoria_torneo_a_eliminazione(elo_3,elo_2,elo_0,elo_1),2)*100)
        st.markdown(f"Vittoria del deck _{deck_partecipanti[0]}_ ({elo_0}): **{w0}%**")
        st.markdown(f"Vittoria del deck _{deck_partecipanti[1]}_ ({elo_1}): **{w1}%**")
        st.markdown(f"Vittoria del deck _{deck_partecipanti[2]}_ ({elo_2}): **{w2}%**")
        st.markdown(f"Vittoria del deck _{deck_partecipanti[3]}_ ({elo_3}): **{w3}%**")






################################
# PAGINA: "📈 Statistiche mazzo"
if pagina_selezionata == "📈 Statistiche mazzo":

    with st.form(key = 'statistiche_mazzo'):
        st.subheader("Seleziona il mazzo di cui avere le statistiche")
        st.write("Lasciare vuoto per avere statistiche per ogni mazzo")
        deck_list = st.multiselect("Mazzo: ", lista_mazzi["deck_name"])
        button_statistiche_mazzo = st.form_submit_button("Ottieni le statistiche")

    if button_statistiche_mazzo:
        if len(deck_list) != 0:
            if len(deck_list) > 1:
                # grafico con andamento ELO di più deck
                ELO_plot_multiple_altair(deck_list, matches)
                # Statistiche duelli a coppie di deck 
                coppie_deck = list(itertools.combinations(deck_list, 2))
                # for coppia in coppie_deck:
                #     with st.expander(coppia[0] + " 💥 " + coppia[1]):
                #         statistiche_duelli(coppia[0], coppia[1], matches)
            for deck_name in deck_list:
                st.markdown("## *" + deck_name + "*")
                ELO_plot(get_deck_matches(matches, deck_name))
                statistiche_mazzo(deck_name, get_deck_matches(matches, deck_name))
                st.markdown("---")
        else:
            ELO_plot_multiple_altair(lista_mazzi["deck_name"], matches)
            for deck in lista_mazzi["deck_name"]:
                if deck != "":
                    ELO_plot(get_deck_matches(matches, deck))
                    expander_stats = st.expander(f"Statistiche del deck *{deck}* 👉")
                    with expander_stats:
                        statistiche_mazzo(deck, get_deck_matches(matches, deck))
                    st.markdown("---")
                    


################################
# PAGINA: "Info ELO"
if pagina_selezionata == "📝 Info ELO":

    st.markdown("## ELO-system")
    st.markdown("Fonte: 🌍 [link](https://metinmediamath.wordpress.com/2013/11/27/how-to-calculate-the-elo-rating-including-example/)")

    st.latex(r'''
        \text{Expected score player 1} = E_1 = \frac{R_1}{(R_1+R_2)}
        ''')
    st.markdown("where: ")

    st.latex(r'''
        R_n = 10^{r_n/400}
    ''')
    st.latex(r'''
        r_n: \text{score of player}\  n
    ''')

    st.markdown("After the match is finished, the actual score is set:")
    st.latex(r'''
        S_1 = 1\ \text{if player 1 wins}, 0.5\ \text{if draw}, 0\ \text{if player 2 wins} 
    ''')
    st.latex(r'''
        S_2 = 0\ \text{if player 1 wins}, 0.5\ \text{if draw}, 1\ \text{if player 2 wins} 
    ''')

    st.markdown("In the last step, putting all together, for each player the updated Elo-rating is computed:")
    st.latex(r'''
        r^{'}_n=r_n+K(S_n-E_n)
    ''')



################################
# PAGINA: "Cardmarket"
if pagina_selezionata == "🛒 Cardmarket":

    with st.form(key = 'cardmarket_seller_carte'):
        st.subheader("Seleziona venditori")

        Extimate_Cards = st.checkbox("Extimate-cards")
        Jinzo81 = st.checkbox("Jinzo81")
        Jlter94 = st.checkbox("Jolter94")
        KalosGames = st.checkbox("KalosGames")
        TCGEmpire = st.checkbox("TCGEmpire")
        Zuzu_fantasia = st.checkbox("Zuzu-Fantasia")
        CardsMania = st.checkbox('CardsMania')
        Goatinho = st.checkbox("goatinho")
        ChronikTM = st.checkbox("ChronikTM")
        Galactus_roma = st.checkbox("galactus-roma")
        Lop_vi = st.checkbox("lop-vi")
        Fbgame = st.checkbox("Fbgame")
        Blastercards = st.checkbox("Blastercards")
        Angeli_e_draghi = st.checkbox("Angeli_e_draghi")

        carta_input = st.text_input("Carta da cercare:")

        button_cardmarket = st.form_submit_button("Ottieni prezzi di vendita")

    if button_cardmarket:
        lista_seller = []
        if Extimate_Cards:
            lista_seller.append("Extimate-cards")
        if Jinzo81:
            lista_seller.append("Jinzo81")
        if Jlter94:
            lista_seller.append("Jolter94")
        if KalosGames:
            lista_seller.append("KalosGames")
        if TCGEmpire:
            lista_seller.append("TCGEmpire")
        if Zuzu_fantasia:
            lista_seller.append("Zuzu-Fantasia")
        if CardsMania:
            lista_seller.append('CardsMania')
        if Goatinho:
            lista_seller.append("goatinho")
        if ChronikTM:
            lista_seller.append("ChronikTM")
        if Galactus_roma:
            lista_seller.append("galactus-roma")
        if Lop_vi:
            lista_seller.append("lop-vi")
        if Fbgame:
            lista_seller.append("Fbgame")
        if Blastercards:
            lista_seller.append("Blastercards")
        if Angeli_e_draghi:
            lista_seller.append("Angeli-e-Draghi")

        carta = carta_input.replace(' ', '+')

        with st.spinner('Recuperando i prezzi da CardMarket...'):

            # Print card name and image
            get_image_from_api(carta_input)

            for index, venditore in enumerate(lista_seller):
                url = "https://www.cardmarket.com/it/YuGiOh/Users/" + venditore + '/Offers/Singles?name=' + carta
                page = requests.get(url)
                content = html.fromstring(page.content)
                prezzo_minore = 99999
                nome_carta = ""
                for i in range(1,21):
                    xpath = "/html/body/main/section/div[3]/div[2]/div[" + str(i) + "]/div[5]/div[1]/div/div/span"
                    xpath_nome = "/html/body/main/section/div[3]/div[2]/div[" + str(i) + "]/div[4]/div/div[1]/a"
                    xpath_condizione = "/html/body/main/section/div[3]/div[2]/div[" + str(i) + "]/div[4]/div/div[2]/div/div[1]/a[2]/span"
                    xpath_disponibilita = "/html/body/main/section/div[3]/div[2]/div[" + str(i) + "]/div[5]/div[2]/span"
                    
                    try:
                        prezzo_str = content.xpath(xpath)
                        prezzo_str = prezzo_str[0].text[:-2]
                        prezzo = float(prezzo_str.replace(',','.'))
                        if prezzo < prezzo_minore: 
                            nome_riga = content.xpath(xpath_nome)[0].text
                            if nome_carta == "":
                                nome_carta = nome_riga
                                prezzo_minore = prezzo
                                condizione_carta = content.xpath(xpath_condizione)[0].text
                                disponibilita = content.xpath(xpath_disponibilita)[0].text
                            elif nome_riga == nome_carta:
                                prezzo_minore = prezzo
                                condizione_carta = content.xpath(xpath_condizione)[0].text
                                disponibilita = content.xpath(xpath_disponibilita)[0].text
                    except:
                        continue
                if prezzo_minore != 99999:
                    if condizione_carta in ("PO", "PL"): condizione_carta = '<font color=Red>'    + condizione_carta + '</font>'
                    if condizione_carta in ("LP", "GD"): condizione_carta = '<font color=Orange>' + condizione_carta + '</font>'
                    if condizione_carta in ("EX", "NM", "MT"): condizione_carta = '<font color=Green>' + condizione_carta + '</font>'
                    output = f'{venditore}: **{prezzo_minore}** € - '
                    output = output + f'*{nome_carta}* - {condizione_carta} - '
                    output = output + f'qta: {disponibilita} - 🌍 [link]({url})'
                    st.markdown(output, unsafe_allow_html=True)
                else:
                    st.write(f"{venditore}: -")









# if True:

#     data_selezionata = "12/02/2022"
#     matches_serata = filter_matches(matches, date = [data_selezionata])

#     duelli_serata       = []
#     vittorie_serata     = []
#     elo_before_serata   = []
#     elo_after_serata    = []
#     delta_elo_serata    = []
#     posizione_classifica_before = []
#     posizione_classifica_after  = []
#     delta_posizione_classifica  = []
#     for index, row in lista_mazzi.iterrows():
#         deck_name = row['deck_name']
#         duelli_mazzo = 0
#         vittorie_mazzo = 0
#         elo_before_mazzo = 0
#         elo_after_mazzo = 0
#         for index, row_match in matches_serata.iterrows():
#             if deck_name == row_match['deck_name']:
#                 duelli_mazzo += 1
#                 if row_match['win_flag'] == 1:
#                     vittorie_mazzo += 1
#                 if elo_before_mazzo == 0:
#                     elo_before_mazzo = row_match['elo_before']
#                 elo_after_mazzo = row_match['elo_after']
#         duelli_serata.append(duelli_mazzo)
#         vittorie_serata.append(vittorie_mazzo)
#         if duelli_mazzo == 0: elo_before_serata.append(row['elo'])
#         else: elo_before_serata.append(elo_before_mazzo)
#         if duelli_mazzo == 0: elo_after_serata.append(row['elo'])
#         else: elo_after_serata.append(elo_after_mazzo)
#         delta_elo_serata.append(elo_after_mazzo - elo_before_mazzo)
#     lista_mazzi['duelli_serata']        = duelli_serata
#     lista_mazzi['vittorie_serata']      = vittorie_serata
#     lista_mazzi['elo_before_serata']    = elo_before_serata
#     lista_mazzi['elo_after_serata']     = elo_after_serata
#     lista_mazzi['delta_elo_serata']     = delta_elo_serata

#     for index, row_deck in lista_mazzi.iterrows():
#         deck_name       = row_deck['deck_name']
#         deck_elo_before = row_deck['elo_before_serata']
#         deck_elo_after  = row_deck['elo_after_serata']
#         posizione_mazzo_before  = 1
#         posizione_mazzo_after   = 1
#         for index, row_classifica in lista_mazzi.iterrows():
#             if deck_name == '': continue # no need to compute for the empty row
#             if (row_classifica['elo_before_serata'] == '') or (deck_elo_before == ''):
#                 posizione_mazzo_before  += 1
#                 posizione_mazzo_after   += 1
#                 continue
#             if (row_classifica['deck_name'] != deck_name) and (row_classifica['elo_before_serata'] >= int(deck_elo_before)):
#                 posizione_mazzo_before += 1
#             if (row_classifica['deck_name'] != deck_name) and (row_classifica['elo_after_serata'] >= int(deck_elo_after)):
#                 posizione_mazzo_after += 1
#         posizione_classifica_before.append(posizione_mazzo_before - 1)
#         posizione_classifica_after.append(posizione_mazzo_after - 1)
#         delta_posizione_classifica.append(posizione_mazzo_after - posizione_mazzo_before)

#     lista_mazzi['posizione_classifica_before']  = posizione_classifica_before
#     lista_mazzi['posizione_classifica_after']   = posizione_classifica_after
#     lista_mazzi['delta_posizione_classifica']   = delta_posizione_classifica


#     # # Classifica con DELTA
#     classifica = lista_mazzi[1:].copy()
#     classifica = classifica.astype({"elo": int})
#     classifica = classifica.astype({"elo_before_serata": int})
#     classifica = classifica.astype({"elo_after_serata": int})

#     classifica.sort_values(by = ['posizione_classifica_after'], inplace=True, ascending=True)
#     classifica = classifica.reset_index()
#     output = ""
#     for index, row in classifica.iterrows():
#         posizione_classifica_before = row['posizione_classifica_before']
#         posizione_classifica_after = row['posizione_classifica_after']
#         delta_posizione_classifica = row['delta_posizione_classifica']
#         if posizione_classifica_after == 1: output = output + "🥇 "
#         if posizione_classifica_after == 2: output = output + "🥈 "
#         if posizione_classifica_after == 3: output = output + "🥉 "
#         if posizione_classifica_after == len(classifica): output = output + "🥄 "
#         output = output + f"**{posizione_classifica_after}** - {row['deck_name']} - {row['elo_after_serata']} "
#         if delta_posizione_classifica < 0: output = output + f"(<font color=verde_elo> ▲ {- delta_posizione_classifica} </font>) "
#         if delta_posizione_classifica > 0: output = output + f"(<font color=Red> ▼ {- delta_posizione_classifica} </font>) "
#         output = output + "  \n"
#     with st.expander("Classifica aggiornata dopo la serata:"):
#         st.markdown(output, unsafe_allow_html=True)





