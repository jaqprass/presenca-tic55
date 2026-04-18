import streamlit as st
import requests

from views import professor, residente, registro_presenca

# -----------------------------
# CONFIG
# -----------------------------
st.set_page_config(layout="wide")
API_URL = "http://127.0.0.1:8000"

# -----------------------------
# SESSION STATE
# -----------------------------
if "carregando" not in st.session_state:
    st.session_state.carregando = False

if "email_submetido" not in st.session_state:
    st.session_state.email_submetido = ""

if "pin_submetido" not in st.session_state:
    st.session_state.pin_submetido = ""

if "acao" not in st.session_state:
    st.session_state.acao = None  # "entrar" | "registrar"

if "pagina" not in st.session_state:
    st.session_state.pagina = "login"

if "role" not in st.session_state:
    st.session_state.role = None

if "dashboard_data" not in st.session_state:
    st.session_state.dashboard_data = None

# -----------------------------
# TELA DE REGISTRO (rota separada)
# -----------------------------
if st.session_state.pagina == "registro":
    registro_presenca.render(API_URL, st.session_state.email_submetido)
    st.stop()

# -----------------------------
# HEADER
# -----------------------------
st.title("Controle de Frequência")
st.subheader("Programa Residência em TIC 55: Apoio à Recuperação do Rio Grande do Sul - Turma 2 • Porto Alegre - RS")

st.markdown(
"""
📌 **Regras de Faltas (Edital – item 6.1.8)**

- Na segunda falta não justificada o residente receberá uma advertência  
- Na terceira falta não justificada o residente será excluído do programa  
- Na sexta falta (justificada ou não), o residente será excluído do programa  
"""
)

# -----------------------------
# INPUT
# -----------------------------
email = st.text_input("Digite seu email").strip()
pin = st.text_input("PIN de acesso", max_chars=4, placeholder="Ex: A3K9").strip().upper()

# -----------------------------
# BOTÕES
# -----------------------------
eh_professor_logado = st.session_state.role == "professor"
eh_coordenador_logado = st.session_state.role == "coordenador"

if eh_professor_logado:
    col_entrar, col_registrar = st.columns([1, 1], gap="small")
else:
    col_entrar = st.columns(1)[0]

with col_entrar:
    btn_entrar = st.button("Entrar", disabled=st.session_state.carregando, use_container_width=True)

btn_registrar = False
if eh_professor_logado:
    with col_registrar:
        btn_registrar = st.button(
            "Registrar presenças",
            disabled=st.session_state.carregando,
            use_container_width=True,
        )

if btn_entrar:
    if not pin:
        st.error("Informe o PIN de acesso.")
        st.stop()
    st.session_state.carregando = True
    st.session_state.acao = "entrar"
    st.session_state.email_submetido = email
    st.session_state.pin_submetido = pin
    st.rerun()

if btn_registrar:
    if not pin:
        st.error("Informe o PIN de acesso.")
        st.stop()
    st.session_state.carregando = True
    st.session_state.acao = "registrar"
    st.session_state.email_submetido = email
    st.session_state.pin_submetido = pin
    st.rerun()

# -----------------------------
# CARREGAMENTO
# -----------------------------
if st.session_state.carregando:
    erro = None

    with st.spinner("Carregando dados..."):
        email_atual = st.session_state.email_submetido
        pin_atual = st.session_state.pin_submetido

        role_response = requests.post(
            f"{API_URL}/auth/login",
            params={"email": email_atual, "pin": pin_atual},
        )

        if role_response.status_code != 200:
            erro = "Erro ao validar usuário"
        else:
            role_data = role_response.json()

            if "error" in role_data:
                erro = role_data["error"]
            else:
                role = role_data["role"]
                st.session_state.role = role

                if st.session_state.acao == "registrar":
                    if role != "professor":
                        erro = "Apenas professores podem registrar presenças."
                    else:
                        st.session_state.pagina = "registro"
                elif role == "resident":
                    st.session_state.dashboard_data = requests.get(
                        f"{API_URL}/attendance/by-email",
                        params={"email": email_atual},
                    ).json()
                elif role in ("professor", "coordenador"):
                    st.session_state.dashboard_data = requests.get(
                        f"{API_URL}/dashboard"
                    ).json()

    st.session_state.carregando = False

    if erro:
        st.error(erro)
        st.stop()

    st.rerun()

# -----------------------------
# DASHBOARD (após login)
# -----------------------------
if st.session_state.dashboard_data is not None:
    if st.session_state.role == "resident":
        residente.render_data(st.session_state.dashboard_data)
    elif st.session_state.role in ("professor", "coordenador"):
        professor.render_data(st.session_state.dashboard_data)
