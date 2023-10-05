from functions import *

################################
# PAGINA: "Info ELO"

st.markdown("## ELO-system")
st.markdown("Fonte: 🌍 [link](https://metinmediamath.wordpress.com/2013/11/27/how-to-calculate-the-elo-rating-including-example/)")

st.latex(r'''
    \text{Expected score player 1} = E_1 = \frac{R_1}{(R_1+R_2)}
    ''')
st.markdown("where: ")

st.latex(r'''
    R_n = 10^{r_n/400}
''')
st.latex(r'''
    r_n: \text{score of player}\  n
''')

st.markdown("After the match is finished, the actual score is set:")
st.latex(r'''
    S_1 = 1\ \text{if player 1 wins}, 0.5\ \text{if draw}, 0\ \text{if player 2 wins} 
''')
st.latex(r'''
    S_2 = 0\ \text{if player 1 wins}, 0.5\ \text{if draw}, 1\ \text{if player 2 wins} 
''')

st.markdown("In the last step, putting all together, for each player the updated Elo-rating is computed:")
st.latex(r'''
    r^{'}_n=r_n+K(S_n-E_n)
''')