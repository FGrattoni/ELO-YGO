from functions import *

################################
# PAGINA: "Cardmarket"

with st.form(key = 'cardmarket_seller_carte'):
    st.subheader("Seleziona venditori")

    Extimate_Cards = st.checkbox("Extimate-cards")
    Jinzo81 = st.checkbox("Jinzo81")
    Jlter94 = st.checkbox("Jolter94")
    KalosGames = st.checkbox("KalosGames")
    TCGEmpire = st.checkbox("TCGEmpire")
    Zuzu_fantasia = st.checkbox("Zuzu-Fantasia")
    CardsMania = st.checkbox('CardsMania')
    Goatinho = st.checkbox("goatinho")
    ChronikTM = st.checkbox("ChronikTM")
    Galactus_roma = st.checkbox("galactus-roma")
    Lop_vi = st.checkbox("lop-vi")
    Fbgame = st.checkbox("Fbgame")
    Blastercards = st.checkbox("Blastercards")
    Angeli_e_draghi = st.checkbox("Angeli_e_draghi")

    carta_input = st.text_input("Carta da cercare:")

    button_cardmarket = st.form_submit_button("Ottieni prezzi di vendita")

if button_cardmarket:
    lista_seller = []
    if Extimate_Cards:
        lista_seller.append("Extimate-cards")
    if Jinzo81:
        lista_seller.append("Jinzo81")
    if Jlter94:
        lista_seller.append("Jolter94")
    if KalosGames:
        lista_seller.append("KalosGames")
    if TCGEmpire:
        lista_seller.append("TCGEmpire")
    if Zuzu_fantasia:
        lista_seller.append("Zuzu-Fantasia")
    if CardsMania:
        lista_seller.append('CardsMania')
    if Goatinho:
        lista_seller.append("goatinho")
    if ChronikTM:
        lista_seller.append("ChronikTM")
    if Galactus_roma:
        lista_seller.append("galactus-roma")
    if Lop_vi:
        lista_seller.append("lop-vi")
    if Fbgame:
        lista_seller.append("Fbgame")
    if Blastercards:
        lista_seller.append("Blastercards")
    if Angeli_e_draghi:
        lista_seller.append("Angeli-e-Draghi")

    carta = carta_input.replace(' ', '+')

    with st.spinner('Recuperando i prezzi da CardMarket...'):

        # Print card name and image
        get_image_from_api(carta_input)

        for index, venditore in enumerate(lista_seller):
            url = "https://www.cardmarket.com/it/YuGiOh/Users/" + venditore + '/Offers/Singles?name=' + carta
            page = requests.get(url)
            content = html.fromstring(page.content)
            prezzo_minore = 99999
            nome_carta = ""
            for i in range(1,21):
                xpath = "/html/body/main/section/div[3]/div[2]/div[" + str(i) + "]/div[5]/div[1]/div/div/span"
                xpath_nome = "/html/body/main/section/div[3]/div[2]/div[" + str(i) + "]/div[4]/div/div[1]/a"
                xpath_condizione = "/html/body/main/section/div[3]/div[2]/div[" + str(i) + "]/div[4]/div/div[2]/div/div[1]/a[2]/span"
                xpath_disponibilita = "/html/body/main/section/div[3]/div[2]/div[" + str(i) + "]/div[5]/div[2]/span"
                
                try:
                    prezzo_str = content.xpath(xpath)
                    prezzo_str = prezzo_str[0].text[:-2]
                    prezzo = float(prezzo_str.replace(',','.'))
                    if prezzo < prezzo_minore: 
                        nome_riga = content.xpath(xpath_nome)[0].text
                        if nome_carta == "":
                            nome_carta = nome_riga
                            prezzo_minore = prezzo
                            condizione_carta = content.xpath(xpath_condizione)[0].text
                            disponibilita = content.xpath(xpath_disponibilita)[0].text
                        elif nome_riga == nome_carta:
                            prezzo_minore = prezzo
                            condizione_carta = content.xpath(xpath_condizione)[0].text
                            disponibilita = content.xpath(xpath_disponibilita)[0].text
                except:
                    continue
            if prezzo_minore != 99999:
                if condizione_carta in ("PO", "PL"): condizione_carta = '<font color=Red>'    + condizione_carta + '</font>'
                if condizione_carta in ("LP", "GD"): condizione_carta = '<font color=Orange>' + condizione_carta + '</font>'
                if condizione_carta in ("EX", "NM", "MT"): condizione_carta = '<font color=Green>' + condizione_carta + '</font>'
                output = f'{venditore}: **{prezzo_minore}** € - '
                output = output + f'*{nome_carta}* - {condizione_carta} - '
                output = output + f'qta: {disponibilita} - 🌍 [link]({url})'
                st.markdown(output, unsafe_allow_html=True)
            else:
                st.write(f"{venditore}: -")