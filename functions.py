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
import itertools
import random

# Create a Google authentication connection object
scope = ["https://www.googleapis.com/auth/spreadsheets", 
         "https://www.googleapis.com/auth/drive"]

credentials = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"], scopes = scope )
client = Client(scope=scope, creds=credentials)
spreadsheetname = "Copy of ELO db" 
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



def telegram_send_image(img_url, bot_id, chat_id):
    url_req = "https://api.telegram.org/bot"+bot_id+"/sendPhoto?chat_id="+chat_id+"&photo="+img_url
    requests.get(url_req)
    return True



def telegram_send_sticker(sticker_ID, bot_id, chat_id):
    url_req = "https://api.telegram.org/bot"+bot_id+"/sendSticker?chat_id="+chat_id+"&sticker="+sticker_ID
    requests.get(url_req)
    return True
 


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
                output = output + f'<font color={st.session_state["verde_elo"]}>' + deck_name1 + '</font>'
                output = output + " - "
                output = output + f'<font color={st.session_state["rosso_elo"]}>' + deck_name2 + '</font>  \n'
            else:
                output = output + f'<font color={st.session_state["rosso_elo"]}>' + deck_name1 + '</font>'
                output = output + " - "
                output = output + f'<font color={st.session_state["verde_elo"]}>' + deck_name2 + '</font>  \n'

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
        if int(row['delta_elo_serata']) > 0: output = output + f"<font color={st.session_state['verde_elo']}>+"
        elif int(row['delta_elo_serata']) < 0: output = output + f"<font color={st.session_state['rosso_elo']}>"
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
        deck_matches.loc[deck_matches.index[i], 'opponent_name'] = opponent_row.loc[opponent_row.index[0], 'deck_name']
        deck_matches.loc[deck_matches.index[i], 'opponent_elo_before'] = opponent_row.loc[opponent_row.index[0], 'elo_before']
        deck_matches.loc[deck_matches.index[i], 'opponent_elo_after'] = opponent_row.loc[opponent_row.index[0], 'elo_after']
        i += 1
    
    return deck_matches



def eventi_duello_messaggi(deck1, deck2, outcome, elo_deck1, elo_after_1, elo_deck2, elo_after_2, lista_mazzi, bot_id, chat_id, matches):
    """ Funzione che manda un messaggio, appena dopo le informazioni del duello.
    Possono essere mandati sticker, con sent_telegram_sticker(), oppure messaggi.
    """
    if outcome == "1":
        vincitore = lista_mazzi.loc[lista_mazzi["deck_name"] == deck1, "owner"].iloc[0]
        mazzo_vincitore = deck1
        perdente = lista_mazzi.loc[lista_mazzi["deck_name"] == deck2, "owner"].iloc[0]
        mazzo_perdente = deck2
    else: 
        vincitore = lista_mazzi.loc[lista_mazzi["deck_name"] == deck2, "owner"].iloc[0]
        mazzo_vincitore = deck2
        perdente = lista_mazzi.loc[lista_mazzi["deck_name"] == deck1, "owner"].iloc[0]
        mazzo_perdente = deck1
            
    ## STICKER SCONFITTE CONSECUTIVE
    # "Stop, he's already dead!"

    filtered_matches_deck1_inverso = get_deck_matches(matches, deck1).sort_values("match_key", ascending = False)
    sconfitte_consecutive_deck1 = 0
    stop_sconfitte = 0
    for index, row in filtered_matches_deck1_inverso.iterrows():
        if (row["win_flag"] == 0) and (stop_sconfitte == 0): 
            sconfitte_consecutive_deck1 += 1
        else: stop_sconfitte = 1
    if sconfitte_consecutive_deck1 > 5 and sconfitte_consecutive_deck1 % 2 == 0:
        telegram_send_message(f"Questa è stata la {sconfitte_consecutive_deck1}^ sconfitta consecutiva per {deck1} 😭", bot_id, chat_id)
        telegram_send_sticker("https://i.postimg.cc/sXQ1y1Lr/Stop-hes-already-dead.webp", bot_id, chat_id)

    filtered_matches_deck2_inverso = get_deck_matches(matches, deck2).sort_values("match_key", ascending = False)
    sconfitte_consecutive_deck2 = 0
    stop_sconfitte = 0
    for index, row in filtered_matches_deck2_inverso.iterrows():
        if (row["win_flag"] == 0) and (stop_sconfitte == 0): 
            sconfitte_consecutive_deck2 += 1
        else: stop_sconfitte = 1
    if sconfitte_consecutive_deck2 > 5 and sconfitte_consecutive_deck2 % 2 == 0:
        telegram_send_message(f"Questa è stata la {sconfitte_consecutive_deck2}^ sconfitta consecutiva per <br>{deck2}</br> 😭", bot_id, chat_id)
        telegram_send_sticker("https://i.postimg.cc/sXQ1y1Lr/Stop-hes-already-dead.webp", bot_id, chat_id)

    # # # # # #

    print(f"sconfitte_consecutive_deck1: {sconfitte_consecutive_deck1}")

    num = random.random()
    print(f"num: {num}")
    if num < 0.05:
        telegram_send_message("SEGNA BELTRA, SEGNA! 📝", bot_id, chat_id)

    if vincitore == "Gabro":
        if num < 0.1: 
            telegram_send_message("BOM BAM GABRO! 💥", bot_id, chat_id) # 

    if mazzo_vincitore == "Nubiano":
        telegram_send_image("https://i.imgur.com/XWBvmX6.gif", bot_id, chat_id)

    elif  (mazzo_vincitore == "Obelisk") and (perdente == "Gabro"):
        telegram_send_sticker("https://i.postimg.cc/wTZ17CRg/Gabro-obelisk.webp", bot_id, chat_id)

    elif mazzo_vincitore == "Skull servant":
        if num < 0.1: 
            telegram_send_sticker("https://i.postimg.cc/PJQNtvXP/Ok-Skull-Servant-2912951370-1.webp", bot_id, chat_id) # Skull servant OK
        elif num < 0.2: 
            telegram_send_sticker("https://i.postimg.cc/MHWGHZrH/0bc50f6a0db89d9356c2fc7b998758f9f3ba2fa2-3055657206.webp", bot_id, chat_id) # 
        elif num < 0.3:
            telegram_send_sticker("https://i.postimg.cc/hthfVj47/d7572f62f9c31ee95187aa4e8a0e1df8-367954919-1.webp", bot_id, chat_id) # 
        elif num < 0.4:
            telegram_send_sticker("https://i.postimg.cc/2y2SZpPw/king-of-the-skull-servants-render-by-alanmac95-dceu7qn-pre-2387621854.webp", bot_id, chat_id) # 
        elif num < 0.5:
            telegram_send_sticker("https://i.postimg.cc/4NfKNPrP/Skull-servant.webp", bot_id, chat_id) # 
        elif num < 0.6:
            telegram_send_sticker("https://i.postimg.cc/8PZ7FWGS/Skull-servant-lightning.webp", bot_id, chat_id) # 
        elif num < 0.7:
            telegram_send_sticker("https://i.postimg.cc/rmGmqRj7/Skull-Servant-LOB-EN-C-3222265127.webp", bot_id, chat_id) # 
        elif num < 0.78:
            telegram_send_sticker("https://i.postimg.cc/HkkVQC1R/fgratt5-King-of-an-army-of-skeletons-art-by-Mucha-stained-glass-242a8f52-a4c4-4ff5-9d6d-f21ccfe6b6c2.webp", bot_id, chat_id) # 
        elif num < 0.85:
            telegram_send_sticker("https://i.postimg.cc/65w7pvj9/FGratt6-anime-skeleton-vector-art-inspired-by-Kano-Hogai-ukiyo-35c12af1-9455-49ce-922d-f79ad7442161.webp", bot_id, chat_id) # 
        elif num < 0.94:
            telegram_send_sticker("https://i.postimg.cc/y60gKPTQ/FGratt6-octrender-8k-hyperreal-skeleton-king-with-Dripping-glos-3f284b55-5086-42dc-a3a8-2e29a3ac74fd.webp", bot_id, chat_id) # 
        elif num < 0.999:
            telegram_send_sticker("https://i.postimg.cc/br0sRyJc/fgratt8-King-of-skeletons-on-a-mountains-of-skulls-playing-card-732470d5-f5ce-433e-ba13-9226d60c7592.webp", bot_id, chat_id) 
        
    elif mazzo_vincitore == "Dinosauro":
        if num < 0.1: 
            telegram_send_sticker("https://i.postimg.cc/Y90bS0Sq/IMG-20211225-WA0004.webp", bot_id, chat_id) # 

    if (deck1 == "Slifer" and deck2 == "Obelisk") or (deck1 == "Obelisk" and deck2 == "Slifer"):
        if num < 0.125: 
            telegram_send_sticker("https://i.postimg.cc/RFMxVVvq/Slifer-vs-Obelisk-1.webp", bot_id, chat_id) # 
        elif num < 0.25: 
            telegram_send_sticker("https://i.postimg.cc/5NGJqVSk/Slifer-vs-Obelisk-2.webp", bot_id, chat_id) # 
        elif num < 0.375:
            telegram_send_sticker("https://i.postimg.cc/Kc0xjLkb/Slifer-vs-Obelisk-3.webp", bot_id, chat_id) # 
        elif num < 0.5:
            telegram_send_sticker("https://i.postimg.cc/ncMZDzBD/Slifer-vs-Obelisk-4.webp", bot_id, chat_id) # 
        elif num < 0.625:
            telegram_send_sticker("https://i.postimg.cc/sghrTNnf/Slifer-vs-Obelisk-5.webp", bot_id, chat_id) # 
        elif num < 0.75:
            telegram_send_sticker("https://i.postimg.cc/8CdVSrQq/Slifer-vs-Obelisk-6.webp", bot_id, chat_id) # 
        elif num < 0.875:
            telegram_send_sticker("https://i.postimg.cc/7Lrydnc3/Slifer-vs-Obelisk-7.webp", bot_id, chat_id) # 
        else:
            telegram_send_sticker("https://i.postimg.cc/tJvjcQQJ/Slifer-vs-Obelisk-8.webp", bot_id, chat_id) # 

    elif mazzo_vincitore == "Slifer": 
        if num < 0.125: 
            telegram_send_sticker("https://i.postimg.cc/ZqvQ9bZJ/Slifer-1.webp", bot_id, chat_id) # 
        elif num < 0.25: 
            telegram_send_sticker("https://i.postimg.cc/qq4DZ2K7/Slifer-2.webp", bot_id, chat_id) # 
        elif num < 0.375:
            telegram_send_sticker("https://i.postimg.cc/W3Mfn5hK/Slifer-3.webp", bot_id, chat_id) # 
        elif num < 0.5:
            telegram_send_sticker("https://i.postimg.cc/pTN6zwXz/Slifer-4.webp", bot_id, chat_id) # 

    elif mazzo_vincitore == "Obelisk": 
        if num < 0.125: 
            telegram_send_sticker("https://i.postimg.cc/KY46gd36/Obelisk.webp", bot_id, chat_id) # 
        elif num < 0.25: 
            telegram_send_sticker("https://i.postimg.cc/L8yd5H5k/Obelisk-2.webp", bot_id, chat_id) # 
        elif num < 0.375:
            telegram_send_sticker("https://i.postimg.cc/dVQPJ7st/Obelisk-1.webp", bot_id, chat_id) # 

    elif mazzo_vincitore == "Dinowrestler": 
        if num < 0.1: 
            telegram_send_sticker("https://i.postimg.cc/xTD9VTNc/Dinowrestler-1.webp", bot_id, chat_id) # 
        elif num < 0.2: 
            telegram_send_sticker("https://i.postimg.cc/NGrQnrM3/Dinowrestler-1-1.webp", bot_id, chat_id) # 
        elif num < 0.3:
            telegram_send_sticker("https://i.postimg.cc/4N6sfkpw/Dinowrestler-2.webp", bot_id, chat_id) # 
        elif num < 0.4:
            telegram_send_sticker("https://i.postimg.cc/T3TGh79x/Dinowrestler-3.webp", bot_id, chat_id) # 
        elif num < 0.5:
            telegram_send_sticker("https://i.postimg.cc/RFWv4WTn/Dinowrestler-4.webp", bot_id, chat_id) # 

    elif (deck1 == "Drago bianco" and deck2 == "Potere del Mago Nero") or (deck1 == "Potere del Mago Nero" and deck2 == "Drago bianco"):
        if num < 0.2: 
            telegram_send_sticker("https://i.postimg.cc/NGTwDqCY/Mago-Nero-VS-Drago-Bianco-1.webp", bot_id, chat_id) # 
        elif num < 0.4: 
            telegram_send_sticker("https://i.postimg.cc/xCNVBW0v/Mago-Nero-VS-Drago-Bianco-1-1.webp", bot_id, chat_id) # 
        elif num < 0.6:
            telegram_send_sticker("https://i.postimg.cc/VNVcGYcs/Mago-Nero-VS-Drago-Bianco-2.webp", bot_id, chat_id) # 
        elif num < 0.8:
            telegram_send_sticker("https://i.postimg.cc/d3McF41z/Mago-Nero-VS-Drago-Bianco-3.webp", bot_id, chat_id) # 
        elif num < 0.9999:
            telegram_send_sticker("https://i.postimg.cc/6qdJpn4T/Mago-Nero-VS-Drago-Bianco-5.webp", bot_id, chat_id) # 

    elif mazzo_vincitore == "Drago bianco": 
        if num < 0.1: 
            telegram_send_sticker("https://i.postimg.cc/bJ4pJq6V/Drago-Bianco-1.webp", bot_id, chat_id) # 
        elif num < 0.2: 
            telegram_send_sticker("https://i.postimg.cc/hvxgQN6D/Drago-Bianco-2.webp", bot_id, chat_id) # 
        elif num < 0.3:
            telegram_send_sticker("https://i.postimg.cc/8PH9X1R8/Drago-Bianco-3.webp", bot_id, chat_id) # 
        elif num < 0.4:
            telegram_send_sticker("https://i.postimg.cc/RZZ8jjdW/Drago-Bianco-4.webp", bot_id, chat_id) # 
        elif num < 0.5:
            telegram_send_sticker("https://i.postimg.cc/cJsq4vdL/Drago-Bianco-5.webp", bot_id, chat_id) # 
        elif num < 0.6:
            telegram_send_sticker("https://i.postimg.cc/s2KkB329/Drago-Bianco-6.webp", bot_id, chat_id) # 

    elif mazzo_vincitore == "Potere del Mago Nero": 
        if num < 0.1: 
            telegram_send_sticker("https://i.postimg.cc/8C5Sm79n/Mago-Nero.webp", bot_id, chat_id) # 
        elif num < 0.2: 
            telegram_send_sticker("https://i.postimg.cc/BZ2dD5tn/Mago-Nero-2.webp", bot_id, chat_id) # 
        elif num < 0.3:
            telegram_send_sticker("https://i.postimg.cc/3J7zZyDC/Mago-Nero-2.webp", bot_id, chat_id) # 
        elif num < 0.4:
            telegram_send_sticker("https://i.postimg.cc/sgKzWY6h/Mago-Nero-1.webp", bot_id, chat_id) # 

    elif mazzo_vincitore == "Jinzo-Terror": 
        if num < 0.1: 
            telegram_send_sticker("https://i.postimg.cc/L4r843w4/Jinzo-1.webp", bot_id, chat_id) # 
        elif num < 0.2: 
            telegram_send_sticker("https://i.postimg.cc/sXXt7bQF/Jinzo-1-1.webp", bot_id, chat_id) # 
        elif num < 0.3:
            telegram_send_sticker("https://i.postimg.cc/T15FHmJC/Jinzo-2.webp", bot_id, chat_id) # 
        elif num < 0.4:
            telegram_send_sticker("https://i.postimg.cc/KcKYyH9s/Jinzo-3.webp", bot_id, chat_id) # 

    elif mazzo_vincitore == "Karakuri": 
        if num < 0.1:
            telegram_send_sticker("https://i.postimg.cc/fLr1K5mV/Karakuri-1-1.webp", bot_id, chat_id) # 
        elif num < 0.2: 
            telegram_send_sticker("https://i.postimg.cc/YC72YqtJ/Karakuri-2.webp", bot_id, chat_id) # 
        elif num < 0.3:
            telegram_send_sticker("https://i.postimg.cc/hPTPX7RL/Karakuri-2-1.webp", bot_id, chat_id) # 
        elif num < 0.4:
            telegram_send_sticker("https://i.postimg.cc/Qdq8bGtV/Karakuri-3.webp", bot_id, chat_id) # 
        elif num < 0.5:
            telegram_send_sticker("https://i.postimg.cc/W4b2YWF8/Karakuri-4.webp", bot_id, chat_id) # 
        elif num < 0.6:
            telegram_send_sticker("https://i.postimg.cc/Jh6RfNjL/Karakuri-5.webp", bot_id, chat_id) # 
        elif num < 0.7:
            telegram_send_sticker("https://i.postimg.cc/6qxggqbK/Karakuri-6.webp", bot_id, chat_id) # 
        elif num < 0.8:
            telegram_send_sticker("https://i.postimg.cc/Y0NZH7TW/Karakuri-7.webp", bot_id, chat_id) # 
        elif num < 0.9:
            telegram_send_sticker("https://i.postimg.cc/3WMVMRL7/Karakuri-1.webp", bot_id, chat_id) # 

    elif mazzo_vincitore == "Montgomery Burn": 
        if num < 0.1:
            telegram_send_sticker("https://i.postimg.cc/rFk2Yn74/Montgomery-Burns.webp", bot_id, chat_id) # 
        elif num < 0.2:
            telegram_send_sticker("https://i.postimg.cc/PJVMwrpZ/Montgomery-Burns-1.webp", bot_id, chat_id) # 
        elif num < 0.3:
            telegram_send_sticker("https://i.postimg.cc/GtmQts2d/Montgomery-Burns-2.webp", bot_id, chat_id) # 
        elif num < 0.4:
            telegram_send_sticker("https://i.postimg.cc/bYmgMLCJ/Montgomery-Burns-3.webp", bot_id, chat_id) # 

    elif mazzo_vincitore == "Samurai EVO": 
        if num < 0.15:
            telegram_send_sticker("https://i.postimg.cc/Zqg1PVrC/Sei-Samurai-1.webp", bot_id, chat_id) # 
        elif num < 0.3:
            telegram_send_sticker("https://i.postimg.cc/9M7sLZp1/Sei-Samurai-2.webp", bot_id, chat_id) # 

    elif mazzo_vincitore == "Predaplant": 
        if num < 0.15:
            telegram_send_sticker("https://i.postimg.cc/SQZH63dx/Predaplant.webp", bot_id, chat_id) # 
        elif num < 0.3:
            telegram_send_sticker("https://i.postimg.cc/Rhb8vJhH/Predaplant-2.webp", bot_id, chat_id) # 
        elif num < 0.4:
            telegram_send_sticker("https://i.postimg.cc/WbhCX8Y6/Predaplant-1.webp", bot_id, chat_id) # 

    return True



def eventi_duello_statistiche(deck1, deck2, outcome, elo_deck1, elo_after_1, elo_deck2, elo_after_2, bot_id, chat_id, matches, 
                              rank_deck1_pre, rank_deck2_pre, rank_deck1_post, rank_deck2_post):
    """Funzione che crea una stringa con tutte le statistiche del duello.
    """
    output = ""

    filtered_matches = get_deck_matches(matches, deck1)
    filtered_matches = filtered_matches[filtered_matches["opponent_name"]==deck2]

    num_duelli = len(filtered_matches)
    num_vittorie_deck1 = sum(filtered_matches["win_flag"])
    perc_vittorie_deck_1_round = int(round(num_vittorie_deck1 / num_duelli * 10, 0))
    output += "\n"
    for i in range(perc_vittorie_deck_1_round):
        output += "▰"
    for i in range(10 - perc_vittorie_deck_1_round):
        output += "▱"
    output += f" ({num_duelli})"   

    if num_duelli%5 == 0:
        output += f"\n\nQuesto è stato il {num_duelli}° duello tra i due deck."
    
    # Statistiche del deck1
    stats_deck1 = ""
        
    filtered_matches_deck1_inverso = get_deck_matches(matches, deck1).sort_values("match_key", ascending = False)

    vittorie_consecutive_deck1 = 0
    sconfitte_consecutive_deck1 = 0
    stop_vittorie = 0
    stop_sconfitte = 0
    for index, row in filtered_matches_deck1_inverso.iterrows():
        if (row["win_flag"] == 1) and (stop_vittorie == 0): 
            vittorie_consecutive_deck1 += 1
        else: stop_vittorie = 1

        if (row["win_flag"] == 0) and (stop_sconfitte == 0): 
            sconfitte_consecutive_deck1 += 1
        else: stop_sconfitte = 1

    if vittorie_consecutive_deck1 % 2 == 0 and vittorie_consecutive_deck1 > 3: 
        stats_deck1 += f"{vittorie_consecutive_deck1}^ vittoria consecutiva contro tutti i deck"
    if sconfitte_consecutive_deck1 % 2 == 0 and sconfitte_consecutive_deck1 > 3: 
        stats_deck1 += f"{sconfitte_consecutive_deck1}^ sconfitta consecutiva contro tutti i deck"
        if sconfitte_consecutive_deck1 > 5:
            telegram_send_message(f"Questa è stata la {sconfitte_consecutive_deck1}^ sconfitta consecutiva per {deck1} 😭", bot_id, chat_id)
            telegram_send_sticker("https://i.postimg.cc/sXQ1y1Lr/Stop-hes-already-dead.webp", bot_id, chat_id)

    delta_posizioni = rank_deck1_post - rank_deck1_pre
    if delta_posizioni < 0:
        if stats_deck1 == "": 
            stats_deck1 += f"▲ {abs(delta_posizioni)} posizioni guadagnate in classifica"
        else: 
            stats_deck1 += f"\n▲ {abs(delta_posizioni)} posizioni guadagnate in classifica"
    elif delta_posizioni > 0: 
        if stats_deck1 == "": 
            stats_deck1 += f"▼ {abs(delta_posizioni)} posizioni perse in classifica"
        else: 
            stats_deck1 += f"\n▼ {abs(delta_posizioni)} posizioni perse in classifica"

    if stats_deck1 != "": 
        output += f"\n\n<b>{deck1}</b>\n"+stats_deck1
    # # # # # # # # # # # # 

    # Statistiche del deck2
    stats_deck2 = ""
        
    filtered_matches_deck2_inverso = get_deck_matches(matches, deck2).sort_values("match_key", ascending = False)

    vittorie_consecutive_deck2 = 0
    sconfitte_consecutive_deck2 = 0
    stop_vittorie = 0
    stop_sconfitte = 0
    for index, row in filtered_matches_deck2_inverso.iterrows():
        if (row["win_flag"] == 1) and (stop_vittorie == 0): 
            vittorie_consecutive_deck2 += 1
        else: stop_vittorie = 1

        if (row["win_flag"] == 0) and (stop_sconfitte == 0): 
            sconfitte_consecutive_deck2 += 1
        else: stop_sconfitte = 1

    if vittorie_consecutive_deck2 % 2 == 0 and vittorie_consecutive_deck2 > 3: 
        stats_deck2 += f"{vittorie_consecutive_deck2}^ vittoria consecutiva contro tutti i deck"
    if sconfitte_consecutive_deck2 % 2 == 0 and sconfitte_consecutive_deck2 > 3: 
        stats_deck2 += f"{sconfitte_consecutive_deck2}^ sconfitta consecutiva contro tutti i deck"
        # if sconfitte_consecutive_deck2 > 5:
        #     telegram_send_message(f"Questa è stata la {sconfitte_consecutive_deck2}^ sconfitta consecutiva per {deck2} 😭", bot_id, chat_id)
        #     telegram_send_sticker("https://i.postimg.cc/sXQ1y1Lr/Stop-hes-already-dead.webp", bot_id, chat_id)
    
    delta_posizioni = rank_deck2_post - rank_deck2_pre
    if delta_posizioni < 0:
        if stats_deck2 == "": 
            stats_deck2 += f"▲ {abs(delta_posizioni)} posizioni guadagnate in classifica"
        else: 
            stats_deck2 += f"\n▲ {abs(delta_posizioni)} posizioni guadagnate in classifica"
    elif delta_posizioni > 0: 
        if stats_deck2 == "": 
            stats_deck2 += f"▼ {abs(delta_posizioni)} posizioni perse in classifica"
        else: 
            stats_deck2 += f"\n▼ {abs(delta_posizioni)} posizioni perse in classifica"

    print(f"STATS DECK: {stats_deck2}")

    if stats_deck2 != "": 
        output += f"\n\n<b>{deck2}</b>\n"+stats_deck2
    # # # # # # # # # # # # 
    
    return output



def telegram_duello_message(deck1, deck2, outcome, elo_deck1, elo_after_1, elo_deck2, elo_after_2, 
                            bot_id, chat_id, matches, rank_deck1_pre, rank_deck2_pre, rank_deck1_post, rank_deck2_post, emoji_flag=True):
    outcome_1, outcome_2, pointer = (" - ", " - ", "")
    if emoji_flag:
        outcome_1 = " ✅ - ❌ "
        outcome_2 = " ❌ - ✅ "
    else: 
        pointer = "⯈"

    message = ""
    if outcome == "1":
        message = pointer + "<b> " + deck1 + "</b>" + outcome_1 + deck2 + "\n"
        message = message + str(elo_after_1) + " (▲ " + str(round(elo_after_1- elo_deck1, 1)) + ") - " + str(elo_after_2) + " (▼ " + str(round(elo_after_2 - elo_deck2, 1)) + ")" 
    else: 
        message = deck1 + outcome_2 + pointer + "<b> " + deck2 + "</b>" + "\n" 
        message = message + str(elo_after_1) + " (▼ " + str(round(elo_after_1- elo_deck1, 1)) + ") - " + str(elo_after_2) + " (▲ " + str(round(elo_after_2 - elo_deck2, 1)) + ")" 

    message += eventi_duello_statistiche(deck1, deck2, outcome, elo_deck1, elo_after_1, elo_deck2, elo_after_2, bot_id, chat_id, matches, 
                                         rank_deck1_pre, rank_deck2_pre, rank_deck1_post, rank_deck2_post)
    
    return message
#  ❌ - ✅



def insert_match2(matches, deck1, deck2, outcome, tournament, lista_mazzi, bot_id, chat_id):

    if deck1 == deck2: 
        st.error("Errore. Mazzo 1 e Mazzo 2 combaciano.")
        return False

    ws = sh.worksheet("matches")

    date = str(datetime.now().strftime("%d/%m/%Y"))
    time = str(datetime.now().strftime("%H:%M"))

    id_match = max(matches["id_match"]) + 1

    elo_deck1 = get_deck_elo(deck1, lista_mazzi)
    elo_deck2 = get_deck_elo(deck2, lista_mazzi)

    rank_deck1_pre = get_deck_rank(deck1, lista_mazzi.iloc[1:])
    rank_deck2_pre = get_deck_rank(deck2, lista_mazzi.iloc[1:])

    if outcome=="1": win_flag_1 = 1
    else: win_flag_1 = 0

    elo_after_1 = elo_calculation(elo_deck1, elo_deck2, win_flag_1)

    data_list_1 = {
        "match_key": [10*id_match+1],
        "id_match": id_match,
        "deck_pos": [1], #fixed
        "date": [date],
        "time": [time],
        "deck_name": [deck1],
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
        "deck_name": [deck2],
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
    
    rank_deck1_post = get_deck_rank(deck1, lista_mazzi.iloc[1:])
    rank_deck2_post = get_deck_rank(deck2, lista_mazzi.iloc[1:])


    # Invio messaggio con duello eseguito:
    telegram_send_message(
        telegram_duello_message(
            deck1, deck2, outcome, 
            elo_deck1, elo_after_1, 
            elo_deck2, elo_after_2,  
            bot_id, chat_id, matches, 
            rank_deck1_pre, rank_deck2_pre, 
            rank_deck1_post, rank_deck2_post,
            emoji_flag=True), 
        bot_id, chat_id)

    eventi_duello_messaggi(deck1, deck2, outcome, elo_deck1, elo_after_1, elo_deck2, elo_after_2, lista_mazzi, bot_id, chat_id, matches)
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



def plot_numero_duelli_mazzi(classifica, matches): 
    """ Altair barplot to plot the number of duels for each deck"""
    # numero_duelli = pd.DataFrame(matches.groupby(["deck_name"])["deck_name"].count())
    # print(numero_duelli)
    # print(type(numero_duelli))

    lista_duelli_mazzo = []
    for mazzo in classifica["Nome deck"]:
        duelli_mazzo = matches[matches["deck_name"] == mazzo]["match_key"].count()       
        print(f"{mazzo}: {duelli_mazzo};")
        lista_duelli_mazzo.append(duelli_mazzo)
    classifica["numero_duelli"] = lista_duelli_mazzo

    numero_duelli = alt.Chart(classifica, height = 900).mark_bar().encode(
        alt.X("numero_duelli:Q", title="Numero duelli"),
        alt.Y('Nome deck', title="Deck"),
        color = alt.Color(
             'numero_duelli',
             legend=None)
        #color="Cat."
    )
    text = numero_duelli.mark_text(
        align='left',
        baseline='middle',
        dx=3  # Nudges text to right so it doesn't appear on top of the bar
    ).encode(
        text='numero_duelli:Q',
        color = "numero_duelli"
    )

    # (numero_duelli + text).properties(height=900)
    st.altair_chart(numero_duelli + text)
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



def statistiche_mazzo(deck_name, deck_matches, mazzi):
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



def get_deck_rank(deck_name, lista_mazzi):
    lista_mazzi_ordered = lista_mazzi.sort_values(by="elo", ascending=False).reset_index()
    rank = lista_mazzi_ordered[lista_mazzi_ordered["deck_name"] == deck_name].index.tolist()[0] + 1
    return rank

