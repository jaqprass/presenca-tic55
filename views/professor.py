import streamlit as st


def render_data(data: list) -> None:
    if not data:
        st.warning("Nenhum dado encontrado")
        return

    # agrupar por professor
    professores = {}

    for team in data:
        prof = team.get("professor", "Sem professor")

        if prof not in professores:
            professores[prof] = []

        professores[prof].append(team)

    st.markdown(
        "**Legenda:** ✅ presenças · 🟠 faltas justificadas · 🔴 faltas não justificadas"
    )

    cols = st.columns(2)

    for i, (professor, teams) in enumerate(professores.items()):

        col = cols[i % 2]

        with col:
            st.markdown(f"## {professor}")

            for team in teams:
                st.markdown(f"### {team['team']}")

                for r in team["residents"]:
                    advertencia = (
                        " &nbsp;<span style='"
                        "background-color:#ef4444;"
                        "color:#fff;"
                        "font-size:0.75rem;"
                        "font-weight:bold;"
                        "padding:2px 7px;"
                        "border-radius:4px;"
                        "vertical-align:middle;"
                        "'>⚠️ ADVERTÊNCIA</span>"
                        if r["nao_justificadas"] >= 2 else ""
                    )

                    st.markdown(
                        f"""
                        <div style="
                            background-color:#eef2f7;
                            color:#111827;
                            padding:12px;
                            border-radius:10px;
                            margin-bottom:8px;
                            border:1px solid #cbd5e1;
                        ">
                            <b style="color:#0f172a;">{r['name']}</b><br>
                            ✅ {r['presencas']} | 🟠 {r['justificadas']} | 🔴 {r['nao_justificadas']}{advertencia}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
