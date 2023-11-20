from functions import *

# matches = st.session_state['matches']
# lista_mazzi = st.session_state['lista_mazzi']
# tournaments = st.session_state['tournaments']

lista_mazzi = pd.read_csv(st.secrets["ghseet_url_lista_mazzi"])
lista_mazzi = lista_mazzi[pd.isna(lista_mazzi["deck_name"]) == False].sort_values(by="elo", ascending=False)
lista_mazzi["Vittorie torneo"] = lista_mazzi["Vittorie torneo"].astype(int)
matches = pd.read_csv(st.secrets["gsheet_url_matches"])

################################
# PAGINA: "📈 Statistiche mazzo"
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
            statistiche_mazzo(deck_name, get_deck_matches(matches, deck_name), lista_mazzi)
            st.markdown("---")
    else:
        ELO_plot_multiple_altair(lista_mazzi["deck_name"], matches)
        for deck in lista_mazzi["deck_name"]:
            if deck != "":
                ELO_plot(get_deck_matches(matches, deck))
                expander_stats = st.expander(f"Statistiche del deck *{deck}* 👉")
                with expander_stats:
                    statistiche_mazzo(deck, get_deck_matches(matches, deck), lista_mazzi)
                st.markdown("---")