from functions import *
#from functools import cache
#from json import load
#from os import write
#from altair.vegalite.v4.api import concat
#from numpy import concatenate
#from pandas.core.frame import DataFrame
#from pyarrow import ListValue
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
#from gsheetsdb import connect


# Telegram options
chat_id = st.secrets["telegram"]['chat_id']
bot_id = st.secrets["telegram"]['bot_id']

st.session_state['verde_elo'] = "#00CC00"
st.session_state['rosso_elo'] = "Red"


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





# DOWNLOAD THE DATA
@st.experimental_memo
def download_data():
    matches = load_the_spreadsheet("matches")
    lista_mazzi = load_the_spreadsheet("mazzi")
    tournaments = load_the_spreadsheet("tournaments")

    return matches, lista_mazzi, tournaments

matches, lista_mazzi, tournaments = download_data()

st.session_state['matches'] = matches
st.session_state['lista_mazzi'] = lista_mazzi
st.session_state['tournaments'] = tournaments








### APP ########################

#st.markdown("# YGO ELO app")
st.image("./YGMEME_title.jpg")

################################
# SEZIONE: "Debug"
if st.secrets["debug"]['debug_offline'] == "True":
    with st.expander("matches"):
        st.dataframe(matches)
    
    with st.expander("lista_mazzi"):
        st.dataframe(lista_mazzi[1:])
    


################################
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





# SIDEBAR
st.write( "[🔗 Link to Google Sheets](" + spread.url + ")" )

