from functions import *

# matches = st.session_state['matches']
# lista_mazzi = st.session_state['lista_mazzi']
# tournaments = st.session_state['tournaments']

lista_mazzi = pd.read_csv(st.secrets["ghseet_url_lista_mazzi"])
lista_mazzi = lista_mazzi[pd.isna(lista_mazzi["deck_name"]) == False].sort_values(by="elo", ascending=False)
lista_mazzi["Vittorie torneo"] = lista_mazzi["Vittorie torneo"].astype(int)
matches = pd.read_csv(st.secrets["gsheet_url_matches"])


################################
# PAGINA: "🔍 Confronta Mazzi"

with st.form(key = 'confronta_mazzi'):
    st.subheader("Seleziona due mazzi da confrontare")
    c1, c2  = st.columns((1, 1))
    with c1: 
        deck_1 = st.selectbox("Mazzo 1: ", lista_mazzi["deck_name"], index=None, placeholder="Seleziona deck...")
    with c2: 
        deck_2 = st.selectbox("Mazzo 2: ", lista_mazzi["deck_name"], index=None, placeholder="Seleziona deck...")
    button_confronta_mazzi = st.form_submit_button("Confronta mazzi")

if button_confronta_mazzi:
    statistiche_duelli(deck_1, deck_2, matches)
    print_duelli(filter_matches(matches, deck_1, deck_2))
    plot_duelli_tra_due_mazzi(matches, deck_1, deck_2)
