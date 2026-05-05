import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Fleet Status Report", layout="wide")
st.title("📊 BEHR Fleet Status")


def normalize_status(value):
    if pd.isna(value) or str(value).strip() == "":
        return "Unknown"

    s = str(value).strip().lower()

    if s in ["ok", "running", "healthy", "online"]:
        return "OK"
    if "pending release" in s:
        return "Pending Release"
    if "down" in s or "offline" in s:
        return "Down"
    if "issue" in s or "warning" in s:
        return "Running with issues"

    return "Other"


def clean_dataframe(df):
    for col in df.columns:
        df[col] = df[col].apply(
            lambda x: str(int(x))
            if isinstance(x, float) and x.is_integer()
            else x
        )
    return df


def enhance_dataframe(df):
    df = df.copy()

    # STATUS COLORS
    if "Status" in df.columns:
        def color_status(val):
            txt = str(val)
            s = txt.lower()

            if s in ["ok", "running", "healthy", "online"]:
                color = "#7DCEA0"
            elif "issue" in s or "warning" in s:
                color = "#F5B041"
            elif "pending release" in s:
                color = "#85C1E9"
            elif "down" in s or "offline" in s:
                color = "#E59898"
            else:
                color = "white"

            return f'<span style="color:{color}; font-weight:bold;">{txt}</span>'

        df["Status"] = df["Status"].apply(color_status)

    # CLICKABLE LINKS
    for col in ["OTE", "Extra", "Tracking"]:
        if col in df.columns:
            df[col] = df[col].apply(
                lambda x: f'<a href="{x}" target="_blank">🔗 Open</a>'
                if str(x).startswith("http")
                else x
            )

    return df


def load_workbook(uploaded_file):
    xls = pd.ExcelFile(uploaded_file)
    project_rows = []
    project_details = {}

    for sheet in xls.sheet_names:
        try:
            df = pd.read_excel(uploaded_file, sheet_name=sheet)

            df.columns = [str(c).strip() for c in df.columns]
            df = df.loc[:, ~df.columns.str.contains("^Unnamed", case=False)]

            status_col = next((c for c in df.columns if "status" in c.lower()), None)
            if status_col is None:
                continue

            df = df.fillna("")
            df = clean_dataframe(df)

            normalized = df[status_col].apply(normalize_status)
            counts = normalized.value_counts()

            project_rows.append({
                "Project": sheet,
                "Fleet Size": len(df),
                "OK": counts.get("OK", 0),
                "Running with issues": counts.get("Running with issues", 0),
                "Pending Release": counts.get("Pending Release", 0),
                "Down": counts.get("Down", 0),
            })

            project_details[sheet] = df

        except Exception as e:
            st.warning(f"Skipped sheet '{sheet}' due to error: {e}")

    if not project_rows:
        st.error("No valid sheets found.")
        st.stop()

    summary_df = pd.DataFrame(project_rows).sort_values("Fleet Size", ascending=False)
    return summary_df, project_details


uploaded = st.file_uploader("Upload Weekly Service Report Excel", type=["xlsx", "xls"])

if uploaded:

    summary_df, project_details = load_workbook(uploaded)

    # ----- GRAPH -----
    fig = go.Figure()

    fig.add_bar(x=summary_df["Project"], y=summary_df["OK"], name="OK", marker_color="#7DCEA0")
    fig.add_bar(x=summary_df["Project"], y=summary_df["Running with issues"], name="Running with issues", marker_color="#F5B041")
    fig.add_bar(x=summary_df["Project"], y=summary_df["Pending Release"], name="Pending Release", marker_color="#85C1E9")
    fig.add_bar(x=summary_df["Project"], y=summary_df["Down"], name="Down", marker_color="#E59898")

    fig.update_layout(
        barmode="stack",
        xaxis_title="<b>Project</b>",
        yaxis_title="<b># Robots</b>",
        height=550,
        xaxis_tickangle=-45
    )

    fig.update_xaxes(tickfont=dict(size=14, family="Arial Black"))
    st.plotly_chart(fig, use_container_width=True)

    # ----- PROJECT SELECTION -----
    search = st.text_input("Search project")
    projects = [p for p in summary_df["Project"] if search.lower() in p.lower()]

    if not projects:
        st.warning("No project found")
        st.stop()

    selected_project = st.selectbox("Select project", projects)

    detail_df = enhance_dataframe(project_details[selected_project])

    row = summary_df[summary_df["Project"] == selected_project].iloc[0]

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Fleet Size", int(row["Fleet Size"]))
    c2.metric("OK", int(row["OK"]))
    c3.metric("Issues", int(row["Running with issues"]))
    c4.metric("Pending", int(row["Pending Release"]))
    c5.metric("Down", int(row["Down"]))

    # ----- TABLE -----
    html_table = detail_df.to_html(escape=False, index=False)

    st.markdown(
        f"""
        <style>
        table {{
            border-collapse: collapse;
            width: 100%;
            font-size: 16px;
        }}
        th {{
            background-color: #1f2c3a;
            color: white;
            padding: 8px;
            text-align: left;
        }}
        td {{
            padding: 8px;
            border-bottom: 1px solid #444;
            vertical-align: top;
            white-space: pre-wrap;
        }}
        tr:hover {{
            background-color: #2c3e50;
        }}
        </style>

        <div style="overflow-x:auto; height:700px;">
            {html_table}
        </div>
        """,
        unsafe_allow_html=True
    )

else:
    st.info("Upload your Excel file to generate the dashboard.")
