import streamlit as st
import pandas as pd
import plotly.graph_objects as go

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


def load_workbook(uploaded_file):
    xls = pd.ExcelFile(uploaded_file)
    project_rows = []
    project_details = {}

    for sheet in xls.sheet_names:
        try:
            df = pd.read_excel(uploaded_file, sheet_name=sheet)

            df.columns = [str(c).strip() for c in df.columns]
            df = df.loc[:, ~df.columns.str.contains("^Unnamed", case=False)]

            status_col = None
            for col in df.columns:
                if "status" in col.lower():
                    status_col = col
                    break

            if status_col is None:
                continue

            df = df.fillna("")

            normalized_status = df[status_col].apply(normalize_status)
            counts = normalized_status.value_counts()
            fleet_size = len(df)

            row = {
                "Project": sheet,
                "Fleet Size": fleet_size,
                "OK": int(counts.get("OK", 0)),
                "Running with issues": int(
                    counts.get("Running with issues", 0)
                ),
                "Pending Release": int(
                    counts.get("Pending Release", 0)
                ),
                "Down": int(counts.get("Down", 0)),
                "Other": int(counts.get("Other", 0)),
                "Unknown": int(counts.get("Unknown", 0)),
            }

            project_rows.append(row)
            project_details[sheet] = df

        except Exception as e:
            st.warning(f"Skipped sheet '{sheet}' due to error: {e}")

    if not project_rows:
        st.error("No valid sheets found.")
        st.stop()

    summary_df = pd.DataFrame(project_rows).sort_values(
        "Fleet Size", ascending=False
    )

    return summary_df, project_details


def style_status(val):
    text = str(val).strip().lower()

    if text in ["ok", "running", "healthy", "online"]:
        return "color:#7FB3D5; font-weight:bold;"

    if "issue" in text or "warning" in text:
        return "color:#F5B041; font-weight:bold;"

    if "pending release" in text:
        return "color:#5DADE2; font-weight:bold;"

    if "down" in text or "offline" in text:
        return "color:#E59898; font-weight:bold;"

    return "font-weight:bold;"


uploaded = st.file_uploader(
    "Upload Weekly Service Report Excel",
    type=["xlsx", "xls"]
)

if uploaded:
    summary_df, project_details = load_workbook(uploaded)

    fig = go.Figure()

    # Softer colors (same family, lower contrast)
    fig.add_bar(
        x=summary_df["Project"],
        y=summary_df["OK"],
        name="OK",
        marker_color="#7FB3D5"
    )

    fig.add_bar(
        x=summary_df["Project"],
        y=summary_df["Running with issues"],
        name="Running with issues",
        marker_color="#F5B041"
    )

    fig.add_bar(
        x=summary_df["Project"],
        y=summary_df["Pending Release"],
        name="Pending Release",
        marker_color="#5DADE2"
    )

    fig.add_bar(
        x=summary_df["Project"],
        y=summary_df["Down"],
        name="Down",
        marker_color="#E59898"
    )

    fig.update_layout(
        barmode="stack",
        title="Fleet Status by Project",
        xaxis_title="Project",
        yaxis_title="# Robots",
        height=550,
        xaxis_tickangle=-45,
        hovermode="x unified"
    )

    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Project Summary")

    selected_project = st.selectbox(
        "Select a project",
        summary_df["Project"].tolist()
    )

    detail_df = project_details[selected_project].copy().fillna("")
    row = summary_df[summary_df["Project"] == selected_project].iloc[0]

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Fleet Size", int(row["Fleet Size"]))
    c2.metric("OK", int(row["OK"]))
    c3.metric("Issues", int(row["Running with issues"]))
    c4.metric("Pending", int(row["Pending Release"]))
    c5.metric("Down", int(row["Down"]))

    st.markdown(
        """
        <style>
        .dataframe td {
            white-space: pre-wrap !important;
            word-wrap: break-word !important;
            overflow-wrap: break-word !important;
            vertical-align: top !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    if "Status" in detail_df.columns:
        styled_df = detail_df.style.map(
            style_status,
            subset=["Status"]
        )

        st.dataframe(
            styled_df,
            use_container_width=True,
            height=700,
            row_height=120
        )
    else:
        st.dataframe(
            detail_df,
            use_container_width=True,
            height=700,
            row_height=120
        )

else:
    st.info("Upload your Excel file to generate the fleet status dashboard.")
