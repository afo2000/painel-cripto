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
    try:
        ids = ','.join(MOEDAS.keys())
       url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids}&vs_currencies=brl&x_cg_demo_api_key=1"

        response = requests.get(url)
        st.write(f"🔍 Status da API: {response.status_code}")
        data = response.json() if response.status_code == 200 else {}
        st.write("📦 Retorno da API:", data)
        return data
    except Exception as e:
        st.error(f"Erro ao obter preços: {e}")
        return {}

@st.cache_data(ttl=60)
def historico(moeda):
    try:
        url = f"https://api.coingecko.com/api/v3/coins/{moeda}/market_chart?vs_currency=brl&days=1"
        r = requests.get(url)
        st.write(f"📊 Status histórico {moeda}: {r.status_code}")
        r_json = r.json()
        if 'prices' not in r_json:
            return pd.DataFrame(columns=['timestamp', 'preco'])
        preco = pd.DataFrame(r_json['prices'], columns=['timestamp', 'preco'])
        preco['timestamp'] = pd.to_datetime(preco['timestamp'], unit='ms')
        return preco
    except Exception as e:
        st.error(f"Erro ao obter histórico de {moeda}: {e}")
        return pd.DataFrame(columns=['timestamp', 'preco'])

def gerar_dica(dados, nome):
    if dados.empty:
        return "⚠️ Sem dados suficientes para análise."
    ultimos = dados['preco'].tail(20)
    variacao = ultimos.pct_change().mean() * 100
    if variacao > 0.15:
        mensagem = f"🟢 Oportunidade de compra em {nome}: tendência de alta."
        enviar_alerta_whatsapp(mensagem)
        return mensagem
    elif variacao < -0.15:
        mensagem = f"🔴 Oportunidade de venda em {nome}: tendência de queda."
        enviar_alerta_whatsapp(mensagem)
        return mensagem
    else:
        return f"🟡 {nome}: mercado lateral. Sem sinal claro."

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

    if chave not in dados:
        st.warning(f"❌ Dados não encontrados para {nome}. Pulei esta moeda.")
        continue

    preco_atual = dados[chave]['brl']
    col1, col2 = st.columns([2, 1])

    with col1:
        st.metric("Preço Atual", f"R${preco_atual:,.2f}")
        graf = historico(chave)
        if graf.empty:
            st.warning("Sem dados para exibir gráfico.")
        else:
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
