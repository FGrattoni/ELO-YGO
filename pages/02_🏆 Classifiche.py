from functions import *

matches = st.session_state['matches']
lista_mazzi = st.session_state['lista_mazzi']
tournaments = st.session_state['tournaments']

################################
# PAGINA: "Classifiche"
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

st.write(classifica)

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

    st.write(classifica)
    st.write(classifica["Cat."])

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
plot_numero_duelli_mazzi(classifica, matches)



