from functions import *

matches = st.session_state['matches']
lista_mazzi = st.session_state['lista_mazzi']
tournaments = st.session_state['tournaments']

lista_duellanti = lista_mazzi["owner"].copy().drop_duplicates()

################################
# PAGINA: ""
st.markdown("## Statistiche del duellante")

with st.form(key = 'stat_duellante'):
    duellante_selezionato = st.multiselect("Seleziona duellante:", options=lista_duellanti)
    button_duellante = st.form_submit_button("Statistiche")


if button_duellante:
    st.write(f"Ciao {duellante_selezionato[0]}")

    


    
