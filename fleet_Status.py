# --- FIXED TABLE RENDER ---
detail_df = detail_df.copy()

# STATUS styling (bigger + colored)
if "Status" in detail_df.columns:
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

        return f'<span style="color:{color}; font-weight:bold; font-size:18px;">{txt}</span>'

    detail_df["Status"] = detail_df["Status"].apply(format_status)


# CLICKABLE LINKS (keep original text)
for col in ["OTE", "Extra", "Tracking"]:
    if col in detail_df.columns:
        detail_df[col] = detail_df[col].apply(
            lambda x: f'<a href="{x}" target="_blank">{x}</a>'
            if isinstance(x, str) and x.startswith("http")
            else x
        )


# Convert to HTML properly
html_table = detail_df.to_html(index=False, escape=False)

# Render with correct structure + CSS
st.markdown(
    f"""
    <div style="overflow-x:auto; height:700px;">
        <style>
            table {{
                width: 100%;
                border-collapse: collapse;
                font-size: 15px;
            }}
            th {{
                padding: 8px;
                text-align: left;
                border-bottom: 2px solid #555;
            }}
            td {{
                padding: 8px;
                border-bottom: 1px solid #333;
                vertical-align: top;
                white-space: pre-wrap;
            }}
        </style>
        {html_table}
    </div>
    """,
    unsafe_allow_html=True
)
