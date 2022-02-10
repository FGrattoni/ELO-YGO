#from functools import cache
#from json import load
#from os import write
#from altair.vegalite.v4.api import concat
#from numpy import concatenate
#from pandas.core.frame import DataFrame
#from pyarrow import ListValue
from unittest import result
from PIL.Image import TRANSPOSE
# from black import out
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
from lxml import html
import json
import itertools
import random
import cardmarket
#from gsheetsdb import connect


# Telegram options
chat_id = st.secrets["telegram"]['chat_id']
bot_id = st.secrets["telegram"]['bot_id']



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



def get_deck_matches(matches, deck):
    """ get a dataframe of the matches (with elo changes linked to them) for a single deck 
    Add the opponent for each match and a few of his statistics. 
    - - - - - - -
    USED IN:
     - plots functions
     - statistics functions """

    # # Extract deck data
    deck_matches = matches[matches['deck_name'] == deck].reset_index()

    # # Add opponent statistics
    # add empty columns
    deck_matches['opponent_name'] = range(0, len(deck_matches))
    deck_matches['opponent_elo_before'] = range(0, len(deck_matches))
    deck_matches['opponent_elo_after'] = range(0, len(deck_matches))
    i = 0
    for id_match in deck_matches['id_match']:
        #opponent_row = matches[matches['id_match'] == id_match and matches['deck_name'] != deck]
        opponent_row = matches.query('id_match == @id_match and deck_name != @deck').reset_index()
        deck_matches['opponent_name'].iloc[i]       = opponent_row['deck_name'].iloc[0]
        deck_matches['opponent_elo_before'].iloc[i] = opponent_row['elo_before'].iloc[0]
        deck_matches['opponent_elo_after'].iloc[i]  = opponent_row['elo_after'].iloc[0]
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
    storico_duelli(deck1, deck2, matches)
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



# DOWNLOAD THE DATA
def download_data():
    matches = load_the_spreadsheet("matches")
    lista_mazzi = load_the_spreadsheet("mazzi")
    tournaments = load_the_spreadsheet("tournaments")

    return matches, lista_mazzi, tournaments

matches, lista_mazzi, tournaments = download_data()



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
                         "📈 Statistiche mazzo",
                         "📝 Info ELO",
                         "🛒 Cardmarket"])




################################
# PAGINA: "Debug"
if st.secrets["debug"]['debug_offline'] == "True":
    with st.expander("matches"):
        st.dataframe(matches)
    
    with st.expander("lista_mazzi"):
        st.dataframe(lista_mazzi[1:])

    with st.expander("lista_seller"):
        st.dataframe(load_the_spreadsheet("CardMarket_seller"))
    


################################
# PAGINA: "Aggiungi un duello"
if pagina_selezionata == "➕ Aggiungi un duello":

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
            tournament = st.selectbox("Torneo: ", options = tournaments["tournament_name"])
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
        storico_duelli(deck_1, deck_2, matches)



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

    lista_seller = load_the_spreadsheet("CardMarket_seller")

    if 'seller_selezionati' in locals():
        st.write(seller_selezionati)
    else:
        seller_selezionati = [0] * len(lista_seller)

    with st.form(key = 'cardmarket_seller_carte'):
        st.subheader("Seleziona venditori")

        for index, seller in enumerate(lista_seller["Seller"]):
            seller_selezionati[index] = st.checkbox(seller)

        carta_input = st.text_input("Carta da cercare (inserire più carte separate da virgola per cercare più carte contemporaneamente):")

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



