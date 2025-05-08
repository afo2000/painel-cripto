import streamlit as st
import requests
import pandas as pd
import time
import os
from twilio.rest import Client

st.set_page_config(page_title="Painel Cripto", layout="wide")
st.title("📈 Painel Cripto – BTC, ETH e Mais")

MOEDAS = {
    "bitcoin": "Bitcoin",
    "ethereum": "Ethereum",
    "binancecoin": "Binance Coin",
    "solana": "Solana",
    "cardano": "Cardano"
}

# Dados do Twilio atualizados
ACCOUNT_SID = 'AC4dfcac3404262d6aef40880ca2e890d4'
AUTH_TOKEN = '6651d0a3e28ec73ffcc091dc7ce449b2'
NUMERO_DESTINO = 'whatsapp:+5521986539352'
NUMERO_TWILIO = 'whatsapp:+14155238886'

def enviar_alerta_whatsapp(mensagem):
    try:
        client = Client(ACCOUNT_SID, AUTH_TOKEN)
        message = client.messages.create(
            body=mensagem,
            from_=NUMERO_TWILIO,
            to=NUMERO_DESTINO
        )
        st.success("🔔 Alerta enviado via WhatsApp")
    except Exception as e:
        st.error(f"Erro ao enviar alerta: {e}")

@st.cache_data(ttl=60)
def obter_precos():
    ids = ','.join(MOEDAS.keys())
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids}&vs_currencies=brl"
    return requests.get(url).json()

@st.cache_data(ttl=60)
def historico(moeda):
    url = f"https://api.coingecko.com/api/v3/coins/{moeda}/market_chart?vs_currency=brl&days=1"
    r = requests.get(url).json()
    preco = pd.DataFrame(r['prices'], columns=['timestamp', 'preco'])
    preco['timestamp'] = pd.to_datetime(preco['timestamp'], unit='ms')
    return preco

def gerar_dica(dados, nome):
    ultimos = dados['preco'].tail(20)
    variacao = ultimos.pct_change().mean() * 100
    if variacao > 0.1:
        mensagem = f"🔼 {nome}: Tendência de alta. Possível entrada curta."
        enviar_alerta_whatsapp(mensagem)
        return mensagem
    elif variacao < -0.1:
        mensagem = f"🔽 {nome}: Tendência de queda. Evite entradas."
        enviar_alerta_whatsapp(mensagem)
        return mensagem
    else:
        return f"⏸️ {nome}: Lateralizado. Aguarde confirmação."

def simular_compra(nome, preco):
    registro = pd.DataFrame([[nome, preco, pd.Timestamp.now()]], columns=['Moeda', 'Preço', 'Data'])
    if os.path.exists("operacoes.csv"):
        registro.to_csv("operacoes.csv", mode='a', index=False, header=False)
    else:
        registro.to_csv("operacoes.csv", index=False)
    st.success(f"Compra simulada de {nome} a R${preco:,.2f}")

dados = obter_precos()

for chave, nome in MOEDAS.items():
    st.subheader(f"{nome} ({chave.upper()[:3]})")
    preco_atual = dados[chave]['brl']
    col1, col2 = st.columns([2, 1])

    with col1:
        st.metric("Preço Atual", f"R${preco_atual:,.2f}")
        graf = historico(chave)
        st.line_chart(graf.rename(columns={"timestamp": "Data", "preco": nome}).set_index("Data"))
        st.info(gerar_dica(graf, nome))

    with col2:
        if st.button(f"Simular Compra de {nome}", key=chave):
            simular_compra(nome, preco_atual)
        st.markdown("---")

if os.path.exists("operacoes.csv"):
    st.subheader("📄 Histórico de Simulações")
    operacoes = pd.read_csv("operacoes.csv")
    st.dataframe(operacoes[::-1])
