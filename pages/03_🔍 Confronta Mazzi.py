from functions import *

################################
# PAGINA: "🔍 Confronta Mazzi"

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
