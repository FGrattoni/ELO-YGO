from functions import *

################################
# PAGINA: "✨ Highlights serata"
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