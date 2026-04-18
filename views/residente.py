import streamlit as st


def render_data(data: list) -> None:
    if not data:
        st.warning("Nenhum registro encontrado")
        return

    # RESUMO
    faltas = [x for x in data if x["status"].lower() != "presente"]

    total_faltas = len(faltas)

    faltas_justificadas = len([
        x for x in faltas if x["justification"] is not None
    ])

    faltas_nao_justificadas = len([
        x for x in faltas if x["justification"] is None
    ])

    col1, col2, col3 = st.columns(3)

    col1.metric("Total de faltas", total_faltas)
    col2.metric("Faltas justificadas", faltas_justificadas)
    col3.metric("Faltas não justificadas", faltas_nao_justificadas)

    st.divider()

    # LISTA
    for item in data:
        status = item["status"].lower()

        if status == "presente":
            bg = "#4CAF50"
        elif status == "justificada":
            bg = "#FF9800"
        else:
            bg = "#F44336"

        st.markdown(
            f"""
            <div style="
                background-color:{bg};
                padding:16px;
                margin:10px 0;
                border-radius:12px;
                color:white;
            ">
                <b>{item['session']}</b><br>
                📅 {item['date']}<br>
                Status: {item['status']}
            </div>
            """,
            unsafe_allow_html=True,
        )
