from functions import *

matches = st.session_state['matches']
lista_mazzi = st.session_state['lista_mazzi']
tournaments = st.session_state['tournaments']
print(lista_mazzi)
################################
# PAGINA: "Classifiche"
st.markdown("## 🏆 Classifica deck")
classifica = lista_mazzi.iloc[1:,0:11].copy()
classifica = classifica.astype({"elo": int})
classifica.columns = ["# Cat.", "Cat.", "Nome deck", "Elo", "Vinte", "Perse", "Percentuale", "Duellante", "Note", "Vittorie torneo", "Esclusione classifica"]
classifica = classifica[classifica["Esclusione classifica"] != "escluso"]
classifica.sort_values(by = ['Elo'], inplace=True, ascending=False)
classifica = classifica.reset_index()
output = ""
posizione = 1
for deck in classifica["Nome deck"]:
    if posizione == 1: output = output + "🥇 "
    if posizione == 2: output = output + "🥈 "
    if posizione == 3: output = output + "🥉 "
    if posizione == len(classifica): output = output + "🥄 "
    output = output + f"**{posizione}** - {deck} - {classifica['Elo'][posizione-1]} "
    if classifica['Vittorie torneo'][posizione-1] > 0:
        output = output + f" {classifica['Vittorie torneo'][posizione-1]*'🏆'}  \n"
    else:
        output = output + f" \n"

    posizione += 1
st.markdown(output)

st.markdown("### Distribuzione ELO")
lista_distribuzione = lista_mazzi[["deck_name","elo","deck_category","owner"]]
plot_distribuzione_mazzi(lista_distribuzione[1:])




st.markdown("### Numero di duelli")
plot_numero_duelli_mazzi(classifica, matches)



