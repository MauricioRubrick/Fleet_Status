import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from openpyxl import load_workbook
from io import BytesIO

st.set_page_config(page_title="Fleet Status Report", layout="wide")
st.title("📊 Fleet Status by Project")


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


# 🔥 Extract hyperlinks from Excel properly
def extract_links(ws):
    links = {}
    for row in ws.iter_rows():
        for cell in row:
            if cell.hyperlink:
                links[(cell.row - 1, cell.column - 1)] = cell.hyperlink.target
    return links


def load_workbook_with_links(uploaded_file):
    wb = load_workbook(BytesIO(uploaded_file.read()), data_only=True)

    project_rows = []
    project_details = {}

    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]

        data = list(ws.values)
        if not data or len(data) < 2:
            continue

        df = pd.DataFrame(data[1:], columns=[str(c).strip() for c in data[0]])
        df = df.loc[:, ~df.columns.str.contains("^Unnamed", case=False)]
        df = df.fillna("")
        df = clean_dataframe(df)

        links = extract_links(ws)

        # Inject hyperlinks
        for col_name in ["OTE", "Extra", "Tracking"]:
            if col_name in df.columns:
                col_idx = df.columns.get_loc(col_name)
                for i in range(len(df)):
                    link = links.get((i + 1, col_idx))
                    if link:
                        df.iloc[i, col_idx] = f'<a href="{link}" target="_blank">🔗 Open</a>'

        # Status normalization
        status_col = next((c for c in df.columns if "status" in c.lower()), None)
        if not status_col:
            continue

        normalized = df[status_col].apply(normalize_status)
        counts = normalized.value_counts()

        project_rows.append({
            "Project": sheet_name,
            "Fleet Size": len(df),
            "OK": counts.get("OK", 0),
            "Running with issues": counts.get("Running with issues", 0),
            "Pending Release": counts.get("Pending Release", 0),
            "Down": counts.get("Down", 0),
        })

        # Status color formatting
        def format_status(val):
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

            return f'<span style="color:{color}; font-weight:bold; font-size:20px;">{txt}</span>'

        df[status_col] = df[status_col].apply(format_status)

        project_details[sheet_name] = df

    summary_df = pd.DataFrame(project_rows).sort_values("Fleet Size", ascending=False)
    return summary_df, project_details


uploaded = st.file_uploader("Upload Excel", type=["xlsx", "xls"])

if uploaded:

    summary_df, project_details = load_workbook_with_links(uploaded)

    # -------- GRAPH --------
    fig = go.Figure()

    fig.add_bar(x=summary_df["Project"], y=summary_df["OK"], name="OK", marker_color="#7DCEA0")
    fig.add_bar(x=summary_df["Project"], y=summary_df["Running with issues"], name="Issues", marker_color="#F5B041")
    fig.add_bar(x=summary_df["Project"], y=summary_df["Pending Release"], name="Pending", marker_color="#85C1E9")
    fig.add_bar(x=summary_df["Project"], y=summary_df["Down"], name="Down", marker_color="#E59898")

    fig.update_layout(barmode="stack", height=550)
    st.plotly_chart(fig, use_container_width=True)

    # -------- SELECT --------
    project = st.selectbox("Select project", summary_df["Project"])
    df = project_details[project]

    # -------- TABLE --------
    html_table = df.to_html(index=False, escape=False)

    st.markdown(
        f"""
        <style>
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 16px;
        }}
        th, td {{
            padding: 10px;
            border-bottom: 1px solid #333;
            vertical-align: top;
        }}
        td {{
            white-space: normal;
            word-break: break-word;
        }}
        </style>

        {html_table}
        """,
        unsafe_allow_html=True
    )

else:
    st.info("Upload your Excel file")
