fig.add_bar(
    x=summary_df["Project"],
    y=summary_df["OK"],
    name="OK",
    marker_color="#7DCEA0"   # soft green
)

fig.add_bar(
    x=summary_df["Project"],
    y=summary_df["Running with issues"],
    name="Running with issues",
    marker_color="#F5B041"   # soft orange
)

fig.add_bar(
    x=summary_df["Project"],
    y=summary_df["Pending Release"],
    name="Pending Release",
    marker_color="#5DADE2"   # soft blue
)

fig.add_bar(
    x=summary_df["Project"],
    y=summary_df["Down"],
    name="Down",
    marker_color="#E59898"   # soft red
)
