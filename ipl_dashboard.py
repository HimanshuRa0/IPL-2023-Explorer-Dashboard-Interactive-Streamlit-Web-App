import streamlit as st
import pandas as pd
import plotly.express as px

# Page config
st.set_page_config(page_title="IPL 2023 Team Explorer", layout="wide")

# Load auction data
df = pd.read_csv("iplauction2023.csv")
df.columns = df.columns.str.strip()
df.rename(columns={
    'name': 'Player',
    'franchise': 'Team',
    'final price (in lacs)': 'Price'
}, inplace=True)
df["Team"] = df["Team"].astype(str).str.strip().replace("nan", "Unsold").fillna("Unsold")
df["Price"] = pd.to_numeric(df["Price"], errors='coerce')

# Load stats dataset
stats_df = pd.read_csv("IPL_Stats.csv")
stats_df.columns = stats_df.columns.str.strip().str.lower()
stats_df.rename(columns={
    "player name": "Player Name",
    "runs": "Runs",
    "total runs": "Runs",
    "runs scored": "Runs",
    "wickets": "Wickets",
    "total wickets": "Wickets",
    "wickets taken": "Wickets"
}, inplace=True)

if "Runs" not in stats_df.columns:
    stats_df["Runs"] = 0
if "Wickets" not in stats_df.columns:
    stats_df["Wickets"] = 0

stats_df["Player Name"] = stats_df["Player Name"].astype(str).str.strip()

# Title
st.title("🏏 IPL 2023 Team Explorer - Interactive Dashboard")

# 🔍 Search Player by Name
st.subheader("🔍 Search Player by Name")
search_player = st.text_input("Type the name of a player to search:")

if search_player:
    search_results = df[df["Player"].str.contains(search_player, case=False, na=False)]
    if not search_results.empty:
        search_display = search_results[["Player", "Team", "Price"]].rename(columns={
            "Player": "Player Name", "Price": "Price (in Lacs)"
        }).sort_values(by="Price (in Lacs)", ascending=False).reset_index(drop=True)
        search_display.index = search_display.index + 1
        st.write(f"Search Results for **{search_player}**:")
        st.dataframe(search_display, use_container_width=True)
    else:
        st.warning("Player not found in the auction data.")

    # Stats search
    st.subheader(f"📊 Career Stats for {search_player.title()}")
    player_stats = stats_df[stats_df["Player Name"].str.lower().str.contains(search_player.lower())]
    if not player_stats.empty:
        filtered_stats = player_stats.dropna(axis=1, how='all')
        if not filtered_stats.empty:
            st.dataframe(filtered_stats.T.rename(columns={filtered_stats.index[0]: "Stats"}), use_container_width=True)
        else:
            st.info("No valid stats available for display.")
    else:
        st.info("Stats not found in the local dataset.")

# 🔽 Team Selector
team_selected = st.selectbox("🔽 Select a Team:", sorted(df["Team"].unique()))
team_df = df[df["Team"] == team_selected]

# 🎚️ Role & Nationality Filters
if "Role" in df.columns and "Nationality" in df.columns:
    st.subheader("🎚️ Filter Players")
    role_options = df["Role"].dropna().unique()
    nationality_options = df["Nationality"].dropna().unique()

    selected_roles = st.multiselect("📌 Filter by Role", sorted(role_options))
    selected_nationalities = st.multiselect("🌎 Filter by Nationality", sorted(nationality_options))

    if selected_roles:
        team_df = team_df[team_df["Role"].isin(selected_roles)]
    if selected_nationalities:
        team_df = team_df[team_df["Nationality"].isin(selected_nationalities)]

# 👉 Side-by-side layout: Player table + Business Report Card
left_col, right_col = st.columns([0.65, 0.35])

with left_col:
    st.subheader(f"👥 Players Bought by {team_selected}")
    df_display = team_df[["Player", "Price"]].rename(columns={
        "Player": "Player Name", "Price": "Price (in Lacs)"
    }).sort_values(by="Price (in Lacs)", ascending=False, na_position='last').reset_index(drop=True)
    df_display.index = df_display.index + 1
    st.dataframe(df_display)

with right_col:
    st.subheader("📊 Business Report Card")
    business_df = pd.merge(team_df, stats_df, left_on="Player", right_on="Player Name", how="left")
    business_df["Runs"] = business_df["Runs"].fillna(0)
    business_df["Wickets"] = business_df["Wickets"].fillna(0)
    business_df["Price"] = business_df["Price"].replace(0, 1)
    business_df["ROI"] = (business_df["Runs"] + 20 * business_df["Wickets"]) / business_df["Price"]

    total_spent = business_df["Price"].sum()
    avg_price = business_df["Price"].mean()
    top_player = business_df.sort_values(by="ROI", ascending=False).iloc[0]

    st.metric("💰 Total Spent", f"₹{total_spent:,.0f} L")
    st.metric("🏅 Top Performer", top_player['Player'])
    st.metric("🎯 Avg Price per Player", f"₹{avg_price:,.0f} L")

# 💸 Cheapest & Costliest Player
if not team_df.empty and team_df["Price"].notna().sum() > 0:
    cheapest = team_df.sort_values(by="Price").iloc[0]
    costliest = team_df.sort_values(by="Price", ascending=False).iloc[0]
    st.success(f"💸 Most Expensive: **{costliest['Player']}** – ₹{costliest['Price']:,} L")
    st.warning(f"🧾 Cheapest: **{cheapest['Player']}** – ₹{cheapest['Price']:,} L")

# 📈 Player Price Bar Chart
if not team_df.empty and team_df["Price"].notna().sum() > 0:
    bar_fig = px.bar(
        team_df.sort_values(by="Price", ascending=False),
        x="Player", y="Price", color="Player",
        title=f"{team_selected} Player Prices",
        labels={"Player": "Player Name", "Price": "Price (in Lacs)"}
    )
    st.plotly_chart(bar_fig, use_container_width=True)

# 🥧 Player Price Distribution Pie
if not team_df.empty and team_df["Price"].notna().sum() > 0:
    pie_fig = px.pie(
        team_df,
        names="Player", values="Price",
        title=f"{team_selected} - Price Distribution",
        labels={"Player": "Player Name", "Price": "Price (in Lacs)"}
    )
    st.plotly_chart(pie_fig, use_container_width=True)

# 📊 Role Breakdown
if "Role" in df.columns and not team_df.empty:
    st.subheader(f"📊 {team_selected} - Role Distribution")
    role_breakdown = team_df["Role"].value_counts().reset_index()
    role_breakdown.columns = ["Role", "Count"]
    role_fig = px.pie(role_breakdown, names="Role", values="Count", title=f"{team_selected} - Player Roles")
    st.plotly_chart(role_fig, use_container_width=True)

# 💎 Top N Highest Paid Players
st.subheader("💎 Top N Most Expensive Players")
top_n = st.slider("Select number of top-paid players to display:", 1, 20, 5)
top_paid = df[df["Price"].notna()].sort_values(by="Price", ascending=False).head(top_n)
top_paid_display = top_paid[["Player", "Team", "Price"]].reset_index(drop=True)
top_paid_display.index = top_paid_display.index + 1
st.dataframe(top_paid_display, use_container_width=True)

# ⚔️ Compare Two Players
st.subheader("⚔️ Compare Two Players")
player_list = sorted(stats_df["Player Name"].unique())
player_1 = st.selectbox("Select First Player", player_list, key="p1")
player_2 = st.selectbox("Select Second Player", player_list, key="p2")
compare_df = stats_df[stats_df["Player Name"].isin([player_1, player_2])].set_index("Player Name").T
compare_df = compare_df.dropna(how='all')
if not compare_df.empty:
    st.dataframe(compare_df, use_container_width=True)
else:
    st.info("Comparison data not available.")

# 💰 Total Spend by Team
st.subheader("💰 Total Spend by Each Team (in ₹ Crores)")
team_spend = df[df["Team"] != "Unsold"].groupby("Team")["Price"].sum().sort_values(ascending=False).reset_index()
team_spend["Price"] = team_spend["Price"] / 100
spend_fig = px.bar(
    team_spend, x="Team", y="Price", color="Team",
    title="Team-wise Total Spending (in ₹ Crores)",
    labels={"Price": "Total Spend (in Crores)"}
)
st.plotly_chart(spend_fig, use_container_width=True)

# 📥 Download CSV
if not df_display.empty:
    st.subheader("📥 Download Team Data")
    csv = df_display.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download CSV of Selected Team",
        data=csv,
        file_name=f"{team_selected}_players.csv",
        mime="text/csv"
    )
