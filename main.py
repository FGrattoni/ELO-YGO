#from functools import cache
#from json import load
#from os import write
#from altair.vegalite.v4.api import concat
#from numpy import concatenate
#from pandas.core.frame import DataFrame
#from pyarrow import ListValue
from unittest import result
from PIL.Image import TRANSPOSE
from black import out
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
#from gsheetsdb import connect


# Telegram options
chat_id = st.secrets["telegram"]['chat_id']
bot_id = st.secrets["telegram"]['bot_id']



# Streamlit CONFIGURATION settings
About = "App per l'inserimento dei duelli, la gestione del database dei duelli e il calcolo del punteggio ELO"

st.set_page_config( 
    page_title='YGO ELO', 
    page_icon = "🃏", 
    layout = 'centered', 
    initial_sidebar_state = 'collapsed'#,
    #menu_items = {
    #    "About": [About]
    #}
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

        st.image("https://storage.googleapis.com/ygoprodeck.com/pics_small/" + str(id_card) +".jpg")

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










### APP ########################

st.markdown("# YGO ELO app")

# SIDEBAR
st.sidebar.write( "[🔗 Link to Google Sheets](" + spread.url + ")" )
## Indice:
pagina_selezionata = st.sidebar.radio("Menu:", 
                     options = [
                         "Aggiungi un duello", 
                         "Classifiche",
                         "Confronta mazzi",
                         "Statistiche mazzo 📈",
                         "Info",
                         "Cardmarket"])




################################
# PAGINA: "Aggiungi un duello"

if pagina_selezionata == "Aggiungi un duello":

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

    if button_insert_match:
        matches, lista_mazzi, tournaments = download_data()
        outcome = insert_match2(matches, deck_1, deck_2, outcome, tournament, lista_mazzi)
        if outcome == True:
            st.success("Duello inserito correttamente a sistema")

################################
# PAGINA: "Classifiche"
if pagina_selezionata == "Classifiche":

    classifica = lista_mazzi.copy()
    classifica = classifica.astype({"elo": int})
    #classifica['percentage'] = classifica['percentage'].apply(lambda x: round(x * 100, 1) ).astype('string') + " %"
    classifica.columns = ["# Cat.", "Cat.", "Nome deck", "Elo", "Vinte", "Perse", "Percentuale", "Duellante", "Note"]
    classifica.style.bar()
    st.write(classifica[["Cat.", "Nome deck", "Elo", "Vinte", "Perse", "Percentuale", "Duellante", "Note"]])



################################
# PAGINA: "Confronta Mazzi"
if pagina_selezionata == "Confronta mazzi":

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
# PAGINA: "Statistiche mazzo 📈"
if pagina_selezionata == "Statistiche mazzo 📈":

    with st.form(key = 'statistiche_mazzo'):
        st.subheader("Seleziona il mazzo di cui avere le statistiche")
        st.write("Lasciare vuoto per avere i grafici per ogni mazzo")
        deck_list = st.multiselect("Mazzo: ", lista_mazzi["deck_name"])
        button_statistiche_mazzo = st.form_submit_button("Ottieni le statistiche")

    if button_statistiche_mazzo:
        if deck_list[0] != "":
            for deck_name in deck_list:
                st.markdown("## *" + deck_name + "*")
                ELO_plot(get_deck_matches(matches, deck_name))
                statistiche_mazzo(deck_name, get_deck_matches(matches, deck_name))
                st.markdown("---")
        else: 
            for deck in lista_mazzi["deck_name"]:
                if deck != "":
                    ELO_plot(get_deck_matches(matches, deck))
                    expander_stats = st.expander(f"Statistiche del deck *{deck}* 👉")
                    with expander_stats:
                        statistiche_mazzo(deck, get_deck_matches(matches, deck))
                    st.markdown("---")
                    


################################
# PAGINA: "Info"
if pagina_selezionata == "Info":

    matches, lista_mazzi, tournaments = download_data()

    Mazzi = st.expander("Mazzi 👉")
    with Mazzi:
        lista_mazzi_info = lista_mazzi.copy()
        lista_mazzi_info.set_index('owner', inplace=True)
        st.write(lista_mazzi_info[["deck_name","deck_category"]])

    Duelli = st.expander("Duelli 👉")
    with Duelli:
        st.write(matches)

    prova_colored_markdown = '<p style="color:Green;"> ▲ Testo </p>'
    st.markdown(prova_colored_markdown, unsafe_allow_html=True)

    prova_colored_markdown = '<p style="color:Red;"> ▼ Testo </p>'
    st.markdown(prova_colored_markdown, unsafe_allow_html=True)







################################
# PAGINA: "Cardmarket"
if pagina_selezionata == "Cardmarket":

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