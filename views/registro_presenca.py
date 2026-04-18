from concurrent.futures import ThreadPoolExecutor

import requests
import streamlit as st


_STATUS_LABEL = {
    "presente": "✅ Presente",
    "falta": "🔴 Falta sem justificativa",
    "justificada": "🟠 Falta com justificativa",
}


def _label_para_status(statuses: list, nome: str) -> int:
    """Retorna o id do AttendanceStatus pelo nome (case-insensitive)."""
    for s in statuses:
        if s["name"].lower() == nome.lower():
            return s["id"]
    return None


def render(api_url: str, email_professor: str) -> None:
    st.title("Registrar Presenças")

    if st.button("← Voltar"):
        st.session_state.pagina = "login"
        st.session_state.dashboard_data = None
        st.session_state.carregando = True
        st.session_state.acao = "entrar"
        st.rerun()

    st.divider()

    # -------------------------------------------------------
    # Carregar dados necessários (em paralelo)
    # -------------------------------------------------------
    with st.spinner("Carregando sessões e times..."):
        with ThreadPoolExecutor(max_workers=3) as executor:
            f_sessoes = executor.submit(lambda: requests.get(f"{api_url}/sessions").json())
            f_teams = executor.submit(
                lambda: requests.get(
                    f"{api_url}/teams/by-professor", params={"email": email_professor}
                ).json()
            )
            f_statuses = executor.submit(lambda: requests.get(f"{api_url}/attendance-status").json())

        sessoes_resp = f_sessoes.result()
        teams_resp = f_teams.result()
        statuses = f_statuses.result()

    if "error" in (teams_resp if isinstance(teams_resp, dict) else {}):
        st.error(teams_resp["error"])
        return

    if not sessoes_resp:
        st.warning("Nenhuma sessão cadastrada.")
        return

    if not teams_resp:
        st.warning("Nenhum time vinculado a este professor.")
        return

    # -------------------------------------------------------
    # Seleção de sessão e time
    # -------------------------------------------------------
    col1, col2 = st.columns(2)

    with col1:
        sessao_opcoes = {
            f"{s['description']} ({s['date']})": s["id"] for s in sessoes_resp
        }
        sessao_label = st.selectbox("Sessão", list(sessao_opcoes.keys()))
        sessao_id = sessao_opcoes[sessao_label]

    with col2:
        time_opcoes = {t["name"]: t for t in teams_resp}
        time_label = st.selectbox("Time", list(time_opcoes.keys()))
        time_selecionado = time_opcoes[time_label]

    residentes = time_selecionado["residents"]

    if not residentes:
        st.warning("Este time não possui residentes cadastrados.")
        return

    # -------------------------------------------------------
    # Lista de residentes com seleção de status
    # -------------------------------------------------------
    st.divider()
    st.markdown("### Marque a presença de cada residente")

    opcoes_status = list(_STATUS_LABEL.values())
    selecoes = {}

    for r in residentes:
        selecoes[r["id"]] = st.radio(
            label=f"**{r['name']}**",
            options=opcoes_status,
            horizontal=True,
            key=f"status_{r['id']}",
        )

    # -------------------------------------------------------
    # Salvar
    # -------------------------------------------------------
    st.divider()

    if st.button("💾 Salvar presenças", type="primary"):
        label_para_nome = {v: k for k, v in _STATUS_LABEL.items()}

        erros = []
        with st.spinner("Salvando..."):
            for residente_id, label in selecoes.items():
                nome_status = label_para_nome[label]
                status_id = _label_para_status(statuses, nome_status)

                if status_id is None:
                    erros.append(f"Status '{nome_status}' não encontrado no banco.")
                    continue

                resp = requests.post(
                    f"{api_url}/attendance",
                    params={
                        "resident_id": residente_id,
                        "session_id": sessao_id,
                        "status_id": status_id,
                    },
                )

                if resp.status_code != 200:
                    erros.append(f"Erro ao salvar residente {residente_id}.")

        if erros:
            for e in erros:
                st.error(e)
        else:
            st.success("Presenças registradas com sucesso!")
            # Limpa as seleções para permitir novo registro
            for r in residentes:
                if f"status_{r['id']}" in st.session_state:
                    del st.session_state[f"status_{r['id']}"]
            st.rerun()
