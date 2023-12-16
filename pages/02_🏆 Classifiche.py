from functions import *

# lista_mazzi = st.session_state['lista_mazzi']

lista_mazzi = pd.read_csv(st.secrets["ghseet_url_lista_mazzi"])
lista_mazzi = lista_mazzi[pd.isna(lista_mazzi["deck_name"]) == False].sort_values(by="elo", ascending=False)
lista_mazzi["Vittorie torneo"] = lista_mazzi["Vittorie torneo"].astype(int)
# st.dataframe(lista_mazzi)

# tournaments = st.session_state['tournaments']
# print(lista_mazzi)

################################
# PAGINA: "Classifiche"
st.markdown("## 🏆 Classifica deck")
classifica = lista_mazzi.iloc[:,0:11].copy()
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



# matches = st.session_state['matches']
# st.dataframe(matches)
matches2 = pd.read_csv(st.secrets["gsheet_url_matches"])

st.markdown("### Numero di duelli")
plot_numero_duelli_mazzi(classifica, matches2)



