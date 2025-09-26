import mysql
import streamlit as st
import pandas as pd
import pymysql
import requests
from sqlalchemy import create_engine


# Function to establish a MySQL connection
def get_connection():
    return pymysql.connect(
        host="localhost",
        user="root",
        password="1234",   # Replace with your MySQL password
        database="cricbuzz"
    )

# Function to execute a query and return results as a DataFrame
def execute_query(query):
    conn = get_connection()
    df = pd.read_sql(query, conn)
    conn.close()
    return df

st.markdown(
    """
    <style>
    /* Sidebar background with gradient and shadow for 3D effect */
    [data-testid="stSidebar"] {
        background: linear-gradient(145deg, #667eea, #764ba2);
        border-radius: 15px;
        box-shadow: 8px 8px 20px #d1d1d1, -8px -8px 20px #ffffff;
        padding: 20px;
        color: #111111;
    }

    /* Sidebar title */
    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3 {
        color: #ffffff;
        font-weight: 700;
    }

    /* Sidebar radio buttons styling */
    [data-testid="stSidebar"] .stRadio > label {
        color: #111111;
        font-size: 20sspx;
        padding: 8px 10px;
        border-radius: 10px;
        transition: all 0.3s ease;
    }

    /* Sidebar tips */
    [data-testid="stSidebar"] p {
        color: #ffffff;
        font-size: 14px;
    }

    /* Horizontal separators */
    [data-testid="stSidebar"] hr {
        border-color: #ffffff;
    }

    /* Content cards styling */
    .card {
        background: linear-gradient(145deg, #ffffff, #f0f0f0);
        border-radius: 15px;
        padding: 20px;
        margin: 10px;
        box-shadow: 5px 5px 15px #d1d1d1, -5px -5px 15px #ffffff;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- Sidebar Menu ---
with st.sidebar:
    st.markdown("## 🏏 Cricbuzz LiveStats")
    st.markdown("---")
    # st.sidebar.markdown(
    #     '<p style="font-size:20px; font-weight:bold;">📌 Choose a Page</p>',
    #     unsafe_allow_html=True
    # )

    menu_items = {

        "📄 Match Details": "Match Details",
        "⏱️ Live Scores": "Live Scores",
        "🎯 Player Stats": "Player Stats",
        "📊 SQL Analytics": "SQL Analytics",
        "🛠️ CRUD Operations": "CRUD Operations"
    }

    page = st.radio(
        "**📌 Choose a page:**",
        options=list(menu_items.values()),
        format_func=lambda x: [k for k,v in menu_items.items() if v==x][0]
    )

    st.markdown("---")

##############################################################################################################################
if page == "Match Details":
    st.title("📊 Cricbuzz LiveStats")
    st.subheader("🎯 Completed Match Details")

    # Fetch matches from MySQL
    df_matches = execute_query("SELECT * FROM live_matches")
    if df_matches.empty:
        st.warning("⚠️ No live matches available in database.")
    else:
        # Create match label for dropdown
        df_matches["match_label"] = (
            df_matches["team1"] + " vs " + df_matches["team2"] +
            " - " + df_matches["match_desc"] +
            " (" + df_matches["match_format"] + ")"
        )

    selected_match = st.selectbox("Select a match:", df_matches["match_label"])

    # Get row for selected match
    match_info = df_matches[df_matches["match_label"] == selected_match].iloc[0].to_dict()

    # Display match details
    st.markdown(f"### 🏏 {match_info['team1']} vs {match_info['team2']}")
    st.write(f"📄 Match: {match_info['match_desc']}")
    st.write(f"🏆 Format: {match_info['match_format']}")
    st.write(f"📍 Venue: {match_info['venue']}")
    st.write(f"📌 Status: {match_info['status']}")

    st.info(
        f"📊 Series: {match_info['series_name']} ({match_info['series_id']})\n"
        f"🆔 Match ID: {match_info['match_id']}"
    )
    # Placeholder: scores (you can join with score table later if needed)
    st.markdown("### 📈 Teams")
    col1, col2 = st.columns(2)
    col1.metric("Team 1", match_info["team1"])
    col2.metric("Team 2", match_info["team2"])

elif page == "Live Scores":
    st.title("📊 Cricbuzz LiveStats")
    st.subheader("🎯 Live Scores")

    url = "https://cricbuzz-cricket.p.rapidapi.com/matches/v1/live"

    headers = {
        "x-rapidapi-key": "5b6ada5745mshc0f89b85e6f1b9dp1b0883jsn683a7c4c9efe",
        "x-rapidapi-host": "cricbuzz-cricket.p.rapidapi.com"
    }


    @st.cache_data(ttl=60)
    def get_live_matches():
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to fetch data: {response.status_code}")
            return {}

    data = get_live_matches()

    if "typeMatches" in data and data["typeMatches"]:
        matches_list = []

        for type_match in data["typeMatches"]:
            match_type = type_match.get("matchType", "Unknown")
            for series in type_match.get("seriesMatches", []):
                series_info = series.get("seriesAdWrapper", {})
                series_name = series_info.get("seriesName", "Unknown Series")
                for match in series_info.get("matches", []):
                    match_info = match.get("matchInfo", {})
                    match_score = match.get("matchScore", {})

                    team1 = match_info.get("team1", {}).get("teamName", "Team 1")
                    team2 = match_info.get("team2", {}).get("teamName", "Team 2")
                    status = match_info.get("status", "N/A")
                    match_desc = match_info.get("matchDesc", "")
                    match_format = match_info.get("matchFormat", "")
                    venue = match_info.get("venueInfo", {}).get("ground", "")
                    city = match_info.get("venueInfo", {}).get("city", "")

                    team1_runs = team1_wkts = team1_overs = "-"
                    team2_runs = team2_wkts = team2_overs = "-"

                    if match_score.get("team1Score") and match_score["team1Score"].get("inngs1"):
                        t1 = match_score["team1Score"]["inngs1"]
                        team1_runs, team1_wkts, team1_overs = t1.get("runs","-"), t1.get("wickets","-"), t1.get("overs","-")
                    if match_score.get("team2Score") and match_score["team2Score"].get("inngs1"):
                        t2 = match_score["team2Score"]["inngs1"]
                        team2_runs, team2_wkts, team2_overs = t2.get("runs","-"), t2.get("wickets","-"), t2.get("overs","-")

                    matches_list.append({
                        "Match Type": match_type,
                        "Series": series_name,
                        "Match": match_desc,
                        "Format": match_format,
                        "Venue": venue,
                        "City": city,
                        "Team 1": team1,
                        "Team 1 Score": f"{team1_runs}/{team1_wkts} ({team1_overs})",
                        "Team 2": team2,
                        "Team 2 Score": f"{team2_runs}/{team2_wkts} ({team2_overs})",
                        "Status": status
                    })

        df_matches = pd.DataFrame(matches_list)

        if not df_matches.empty:
            # Sidebar filter
            match_types = df_matches["Match Type"].unique()
            selected_type = st.sidebar.selectbox("Filter by Match Type", match_types)
            filtered_df = df_matches[df_matches["Match Type"] == selected_type]

            # Display matches
            for idx, row in filtered_df.iterrows():
                st.markdown(f"### 🏏 {row['Team 1']} vs {row['Team 2']}")
                st.write(f"**Series:** {row['Series']}")
                st.write(f"**Match:** {row['Match']} | **Format:** {row['Format']}")
                st.write(f"**Venue:** {row['Venue']}, {row['City']}")
                st.write(f"**Status:** {row['Status']}")
                col1, col2 = st.columns(2)
                col1.metric(row["Team 1"], row["Team 1 Score"])
                col2.metric(row["Team 2"], row["Team 2 Score"])
                st.markdown("---")
        else:
            st.warning("⚠️ No live matches available.")
    else:
        st.warning("⚠️ No live matches data found.")

#################################################################################################################################################################

elif page == "Player Stats":
    st.title("📊 Cricbuzz LiveStats")
    st.subheader("🎯 Player Stats Page")
    import streamlit as st
    import pandas as pd
    import streamlit as st
    import pandas as pd
    import mysql.connector

    import streamlit as st
    import pandas as pd
    import mysql.connector


    # -------------------
    # MySQL Connection
    # -------------------
    def get_connection():
        return mysql.connector.connect(
            host="localhost",
            user="root",
            password="1234",  # 🔹 change if needed
            database="cricbuzz"
        )


    # -------------------
    # Fetch Data from MySQL
    # -------------------
    def fetch_mostruns_data():
        conn = get_connection()
        query = "SELECT Batter, M, I, R, Avg, MatchType, Team FROM mostruns_batsmans"
        df = pd.read_sql(query, conn)
        conn.close()
        return df


    # -------------------
    # Streamlit Page Setup
    # -------------------
    st.set_page_config(page_title="Cricket Analytics Dashboard", layout="wide")

    # Create Tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["🏏 Most Runs (Test)", "📊 ICC Top Batters 2025", "🥎 Top Bowling Stats", "🏏 ODI format", "🏏 Test format", "🏏 T20 format"])

    # -------------------
    # Tab 1: Most Runs
    # -------------------
    with tab1:
        st.title("🏏 Most Runs by Batsmen (Test Format)")
        st.markdown("### Data fetched from MySQL table: `mostruns_batsmans`")

        # Fetch data
        df = fetch_mostruns_data()

        # Filters
        col1, col2 = st.columns([2, 2])
        team_filter = col1.selectbox("Select Team", ["All"] + sorted(df["Team"].unique().tolist()))
        search_player = col2.text_input("🔍 Search Player by Name").strip()

        if team_filter != "All":
            df = df[df["Team"] == team_filter]

        if search_player:
            df = df[df["Batter"].str.contains(search_player, case=False, na=False)]

        # Show dataframe
        st.dataframe(df, use_container_width=True)

        # Summary
        st.markdown("### 📊 Summary")
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Players", len(df))
        col2.metric("Total Runs", int(df["R"].sum()) if not df.empty else 0)
        col3.metric("Highest Avg", round(df["Avg"].max(), 2) if not df.empty else 0)

    # -------------------
    # Tab 2: ICC Top Batters 2025
    # -------------------
    with tab2:
        # JSON Data (without faceImageId)
        data = {
            'rank': [
                {'id': '8019', 'rank': '1', 'name': 'Joe Root', 'country': 'England', 'rating': '908', 'points': '908',
                 'lastUpdatedOn': '2025-09-22', 'trend': 'Flat', 'countryId': '9'},
                {'id': '12201', 'rank': '2', 'name': 'Harry Brook', 'country': 'England', 'rating': '868',
                 'points': '868',
                 'lastUpdatedOn': '2025-09-22', 'trend': 'Flat', 'countryId': '9'},
                {'id': '6326', 'rank': '3', 'name': 'Kane Williamson', 'country': 'New Zealand', 'rating': '850',
                 'points': '850', 'lastUpdatedOn': '2025-09-22', 'trend': 'Flat', 'countryId': '13'},
                {'id': '2250', 'rank': '4', 'name': 'Steven Smith', 'country': 'Australia', 'rating': '816',
                 'points': '816', 'lastUpdatedOn': '2025-09-22', 'trend': 'Flat', 'countryId': '4'},
                {'id': '13940', 'rank': '5', 'name': 'Yashasvi Jaiswal', 'country': 'India', 'rating': '792',
                 'points': '792', 'lastUpdatedOn': '2025-09-22', 'trend': 'Flat', 'countryId': '2'},
                {'id': '8583', 'rank': '6', 'name': 'Temba Bavuma', 'country': 'South Africa', 'rating': '790',
                 'points': '790', 'lastUpdatedOn': '2025-09-22', 'trend': 'Flat', 'countryId': '11'},
                {'id': '10940', 'rank': '7', 'name': 'Kamindu Mendis', 'country': 'Sri Lanka', 'rating': '781',
                 'points': '781', 'lastUpdatedOn': '2025-09-22', 'trend': 'Flat', 'countryId': '5'},
                {'id': '10744', 'rank': '8', 'name': 'Rishabh Pant', 'country': 'India', 'rating': '768',
                 'points': '768',
                 'lastUpdatedOn': '2025-09-22', 'trend': 'Flat', 'countryId': '2'},
                {'id': '10713', 'rank': '9', 'name': 'Daryl Mitchell', 'country': 'New Zealand', 'rating': '748',
                 'points': '748', 'lastUpdatedOn': '2025-09-22', 'trend': 'Flat', 'countryId': '13'},
                {'id': '8502', 'rank': '10', 'name': 'Ben Duckett', 'country': 'England', 'rating': '747',
                 'points': '747',
                 'lastUpdatedOn': '2025-09-22', 'trend': 'Flat', 'countryId': '9'},
                {'id': '8497', 'rank': '11', 'name': 'Travis Head', 'country': 'Australia', 'rating': '740',
                 'points': '740', 'lastUpdatedOn': '2025-09-22', 'trend': 'Flat', 'countryId': '4'},
                {'id': '9812', 'rank': '12', 'name': 'Saud Shakeel', 'country': 'Pakistan', 'rating': '739',
                 'points': '739', 'lastUpdatedOn': '2025-09-22', 'trend': 'Flat', 'countryId': '3'},
                {'id': '11808', 'rank': '13', 'name': 'Shubman Gill', 'country': 'India', 'rating': '725',
                 'points': '725',
                 'lastUpdatedOn': '2025-09-22', 'trend': 'Flat', 'countryId': '2'},
                {'id': '6245', 'rank': '14', 'name': 'Dinesh Chandimal', 'country': 'Sri Lanka', 'rating': '717',
                 'points': '717', 'lastUpdatedOn': '2025-09-22', 'trend': 'Flat', 'countryId': '5'},
                {'id': '9582', 'rank': '15', 'name': 'Aiden Markram', 'country': 'South Africa', 'rating': '709',
                 'points': '709', 'lastUpdatedOn': '2025-09-22', 'trend': 'Flat', 'countryId': '11'}
            ]
        }

        # Country codes for flags
        country_codes = {
            "England": "gb-eng",
            "Australia": "au",
            "India": "in",
            "Pakistan": "pk",
            "South Africa": "za",
            "New Zealand": "nz",
            "Sri Lanka": "lk"
        }

        # Convert to DataFrame
        df_icc = pd.DataFrame(data['rank'])
        df_icc['rank'] = df_icc['rank'].astype(int)
        df_icc['rating'] = df_icc['rating'].astype(int)
        df_icc['points'] = df_icc['points'].astype(int)

        st.title("🏏 ICC Top Batters 2025")

        # Display players in cards (without images)
        cols_per_row = 3
        for i in range(0, len(df_icc), cols_per_row):
            cols = st.columns(cols_per_row)
            for j, col in enumerate(cols):
                idx = i + j
                if idx >= len(df_icc):
                    break
                player = df_icc.iloc[idx]
                country_flag_code = country_codes.get(player['country'], "unknown")
                flag_url = f"https://flagcdn.com/w40/{country_flag_code}.png"  # 40px width flag
                with col:
                    st.markdown(f"**{player['rank']}. {player['name']}**")
                    st.markdown(f"![flag]({flag_url}) {player['country']}")
                    st.markdown(f"⭐ Rating: {player['rating']} | Trend: {player['trend']}")

    with tab3:
        # Fetch Data from MySQL
        # --------------------------
        def fetch_top_bowling():
            conn = get_connection()
            query = "SELECT * FROM top_bowling"
            df = pd.read_sql(query, conn)
            conn.close()
            return df

        # --------------------------
        # Streamlit UI
        # --------------------------
        import streamlit as st

        st.set_page_config(page_title="🥎 Top Bowling Stats", layout="wide")
        st.title("🥎 Top Bowling Stats")

        # Fetch data
        df = fetch_top_bowling()

        # Search bar for filtering by player name
        search_query = st.text_input("Search Player")

        if search_query:
            df = df[df['Player'].str.contains(search_query, case=False, na=False)]

        # Display DataFrame
        st.dataframe(df.style.format({
            'Overs': "{:.1f}",
            'Avg': "{:.2f}"
        }))


    def get_connection():
        return mysql.connector.connect(
            host="localhost",
            user="root",
            password="1234",  # 🔹 change if needed
            database="cricbuzz"
        )
    with tab4:
            # Fetch Data from MySQL
            # --------------------------
        def fetch_odi_format():
            conn = get_connection()
            query = "SELECT * FROM cricbuzz.odi_format;"
            df = pd.read_sql(query, conn)
            conn.close()
            return df

        st.set_page_config(page_title="🏏 ODI format", layout="wide")
        st.title("🏏 ODI format")
        df = fetch_odi_format()

        st.dataframe(df.style.format({
            'Overs': "{:.1f}",
            'Avg': "{:.2f}"
        }))
    with tab5:
            # Fetch Data from MySQL
            # --------------------------
        def fetch_test_format():
            conn = get_connection()
            query = "SELECT * FROM cricbuzz.test_format;"
            df = pd.read_sql(query, conn)
            conn.close()
            return df

        st.set_page_config(page_title="🏏 Test format", layout="wide")
        st.title("🏏 Test format")
        df = fetch_test_format()

        st.dataframe(df.style.format({
            'Overs': "{:.1f}",
            'Avg': "{:.2f}"
        }))
    with tab6:
            # Fetch Data from MySQL
            # --------------------------
        def fetch_t20_format():
            conn = get_connection()
            query = "SELECT * FROM cricbuzz.t20_formats;"
            df = pd.read_sql(query, conn)
            conn.close()
            return df

        st.set_page_config(page_title="🏏 T20 format", layout="wide")
        st.title("🏏 T20 format")
        df = fetch_t20_format()

        st.dataframe(df.style.format({
            'Overs': "{:.1f}",
            'Avg': "{:.2f}"
        }))
###################################################################################################################################
elif page == "SQL Analytics":
    st.title("📊 Cricket SQL Analytics")
    st.subheader("🎯 SQL Analytics Page")
    import streamlit as st
    import pandas as pd
    import mysql.connector
    from io import StringIO


    # Database connection
    def get_connection():
        return mysql.connector.connect(
            host="localhost",
            user="root",
            password="1234",
            database="cricbuzz"
        )

#---------------------------------------------------------------------------------------------------------------------------------------------------------------
    # SQL queries list
#---------------------------------------------------------------------------------------------------------------------------------------------------------------
    queries = {
        "1. Find all players who represent India": "SELECT * FROM cricbuzz.india_players;",
        "2. All cricket matches that were played in the last Few days": "SELECT * FROM cricbuzz.recent_matches;",
        "3. Top 10 highest run scorers in ODI cricket": "SELECT * FROM cricbuzz.top10_scorer;",
        "4. Cricket venues with seating Capacity > 30,000": "SELECT * FROM cricbuzz.venues_info WHERE REPLACE(capacity, ',', '') + 0 > 30000;",
        "5. Show team name and total number of wins":"""SELECT team1, team2, status FROM cricbuzz.live_matches WHERE status LIKE '%won by%';""",
        "6. Role and count of players for each role.": "SELECT * FROM cricbuzz.playingrole;",
        "7. Highest individual batting score in all formats(Test, ODI, T20)": "SELECT * FROM cricbuzz.player_highest_scores;",
        "8. Cricket Series in 2024": "SELECT * FROM cricbuzz.cric_series_2024;",
        "9. All-rounder players who have scored more than 1000 runs & taken more than 50 wickets": "SELECT * FROM cricbuzz.allrounder_players;",
        "10. Get details of the last 20 completed matches": "SELECT * FROM cricbuzz.last_20_matches;",
        "11. Compare each player's performance across different cricket formats":"""SELECT 'Test' AS  format, Player, Country, Matches, Runs, Avg FROM cricbuzz.test_format UNION ALL SELECT 'ODI' AS format, Player,  Country, Matches, Runs, Avg FROM cricbuzz.odi_format UNION ALL SELECT 'T20' AS format, Player, Country, Matches, Runs, Avg FROM cricbuzz.t20_formats;""",
        "12. International team's performance when playing at home versus playing away":"SELECT * FROM cricbuzz.home_vs_away;",
        "13. Identify batting partnerships where two consecutive batsmen": "SELECT innings_id, player1, player2, combined_runs FROM cricbuzz.batting_partnership WHERE combined_runs >= 100;",
        "14. Bowling performance at different venues":"SELECT * FROM cricbuzz.bowler_venue_stats;",
        "15. Close matches":"SELECT * FROM cricbuzz.close_matches;",
        "16. Batting Performance changes over different years. For matches since 2020":"""SELECT Player, MAX(Country) AS Country,  -- In case of duplicates with same player name SUM(Mat) AS Total_Matches, SUM(Runs) AS Total_Runs,  -- Runs scored per year
    SUM(CASE WHEN Played_Year = 2020 THEN Runs ELSE 0 END) AS Runs_2020,
    SUM(CASE WHEN Played_Year = 2021 THEN Runs ELSE 0 END) AS Runs_2021,
    SUM(CASE WHEN Played_Year = 2022 THEN Runs ELSE 0 END) AS Runs_2022,
    SUM(CASE WHEN Played_Year = 2023 THEN Runs ELSE 0 END) AS Runs_2023,
    SUM(CASE WHEN Played_Year = 2024 THEN Runs ELSE 0 END) AS Runs_2024,
    ROUND(SUM(Runs) / SUM(Mat), 2) AS Avg_Runs_per_Match
FROM (
    SELECT * 
    FROM consist_players
    WHERE Played_Year IN (2020, 2021, 2022, 2023, 2024)
      AND Mat >= 5
) AS filtered
GROUP BY 
    Player
ORDER BY 
    Avg_Runs_per_Match DESC;""",
        "17.  Toss decision, choosing to Bat first (or) Bowl first": """SELECT
        COUNT(*) AS total_matches,
        SUM(CASE WHEN winning_margin LIKE '%runs%' THEN 1 ELSE 0 END) AS Bat_first_winning_count,
        SUM(CASE WHEN winning_margin LIKE '%wkts%' THEN 1 ELSE 0 END) AS Bowl_first_winning_count,
        ROUND(SUM(CASE WHEN winning_margin LIKE '%runs%' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS Bat_first_win_percentage,
        ROUND(SUM(CASE WHEN winning_margin LIKE '%wkts%' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS Bowl_first_win_percentage FROM cricbuzz.winning_perc;""",
        "18. Most Economical Bowlers":"""
        SELECT 'ODI' AS format, player, matches, overs, runs, wkts, economy
        FROM cricbuzz.most_economy_odi_bowler
        UNION ALL
        SELECT 'T20' AS format, player, matches, overs, runs, wkts, economy
        FROM cricbuzz.most_economical_bowler;
        """,
        "19.Which batsmen are most consistent in their scoring": """SELECT 
    Player,
    MAX(CASE WHEN Played_Year = 2022 THEN Runs END) AS Runs_2022,
    MAX(CASE WHEN Played_Year = 2023 THEN Runs END) AS Runs_2023,
    MAX(CASE WHEN Played_Year = 2024 THEN Runs END) AS Runs_2024,
    ROUND(AVG(Avg), 2) AS Avg
FROM 
    cricbuzz.consist_players
WHERE 
    Played_Year IN (2022, 2023, 2024)
GROUP BY 
    Player
HAVING 
    COUNT(DISTINCT Played_Year) >= 3
ORDER BY 
    Player;
    """,
        "20. Player has played in different cricket formats":"""
SELECT 'Test' AS format, Player, Matches, Runs, Avg
FROM cricbuzz.test_format
UNION ALL
SELECT 'ODI' AS format, Player, Matches, Runs, Avg
FROM cricbuzz.odi_format
UNION ALL
SELECT 'T20' AS format, Player, Matches, Runs, Avg
FROM cricbuzz.t20_formats;

""",
        "21. Combine their batting, bowling & Fielding performance":"""SELECT
    Player,
    Format,
    Runs_Scored,
    Batting_Avg,
    Strike_Rate,
    Wickets_Taken,
    Bowling_Avg,
    Economy_Rate,
    -- Calculate points dynamically
    ((Runs_Scored * 0.01) + (Batting_Avg * 0.5) + (Strike_Rate * 0.3)) AS Batting_Points,
    ((Wickets_Taken * 2) + ((50 - Bowling_Avg) * 0.5) + ((6 - Economy_Rate) * 2)) AS Bowling_Points,
    (Catches + Stumpings) AS Fielding_Points,
    (((Runs_Scored * 0.01) + (Batting_Avg * 0.5) + (Strike_Rate * 0.3)) +
     ((Wickets_Taken * 2) + ((50 - Bowling_Avg) * 0.5) + ((6 - Economy_Rate) * 2)) +
     (Catches + Stumpings)) AS Total_Score,
    -- Rank players within each format
    RANK() OVER (PARTITION BY Format ORDER BY
        (((Runs_Scored * 0.01) + (Batting_Avg * 0.5) + (Strike_Rate * 0.3)) +
         ((Wickets_Taken * 2) + ((50 - Bowling_Avg) * 0.5) + ((6 - Economy_Rate) * 2)) +
         (Catches + Stumpings)) DESC
    ) AS Format_Rank
FROM
    cricbuzz.player_performance_allformats
ORDER BY
    Format,
    Format_Rank;""",
        "22. Head-to-Head match prediction analysis between teams.":"SELECT * FROM cricbuzz.head_to_head;",
        "23. player form and momentum":"SELECT * FROM cricbuzz.player_form_batting_perf;",
        "24. Successful batting partnerships":"SELECT * FROM cricbuzz.partnership;",
        "25. Perform a time-series analysis of player performance evolution":"SELECT * FROM cricbuzz.player_quarterly_performance;"
    }

    def fetch_data(query):
        conn = get_connection()
        df = pd.read_sql(query, conn)
        conn.close()
        return df

#------------------------------------------------------------------------------------------------------
    # Streamlit page config
    st.set_page_config(page_title="Cricket SQL Analytics", layout="wide")
    st.markdown("### 🏏 Database Query Questions")

    # Query selection box
    selected_query_name = st.selectbox("Select a question to analyze:", list(queries.keys()))
    selected_query = queries[selected_query_name]

    # Show the SQL query
    st.subheader("SQL Query")
    st.code(selected_query, language='sql')

    # Execute button
    if st.button("🚀 Execute Query"):
        try:
            conn = get_connection()
            df = pd.read_sql(selected_query, conn)
            conn.close()

            st.success("Query executed successfully!")
            st.subheader("Query Results")
            st.dataframe(df)

            if selected_query_name == "8. Cricket Series in 2024":
                st.markdown(f"**Number of matches Planned:** {len(df)}")

            if selected_query_name == "5. Show team name and total number of wins":
                st.markdown(f"**Total number of matches:** {len(df)}")

        #if st.button("Execute Query"):
            if selected_query_name == "18. Most Economical Bowlers":
                # Fetch ODI & T20 separately
                # Split into separate DataFrames by format
                odi_df = df[df['format'] == 'ODI'].drop(columns=['format'])
                t20_df = df[df['format'] == 'T20'].drop(columns=['format'])

                # Display using tabs
                tab1, tab2 = st.tabs(["ODI", "T20"])

                with tab1:
                    st.subheader("ODI Most Economical Bowlers")
                    st.dataframe(odi_df)

                with tab2:
                    st.subheader("T20 Most Economical Bowlers")
                    st.dataframe(t20_df)



            if selected_query_name == "19.Which batsmen are most consistent in their scoring":
                player = df[df['Avg'] == df['Avg'].max()]
                st.subheader("Player with Highest Avg (Higher value = scores fluctuate a lot → less consistent.):")
                st.write(player)
                std_dev = df['Avg'].std()
                st.write("Standard Deviation of Avg: ", round(std_dev, 2))
            if selected_query_name == "19.Which batsmen are most consistent in their scoring":
                player = df[df['Avg'] == df['Avg'].min()]
                st.subheader("Player with Lowest Avg (Lower value = scores are closer to the average → more consistent.):")
                st.write(player)

            if selected_query_name == "20. Player has played in different cricket formats":
                tabs = st.tabs(["Test", "ODI", "T20"])
                for tab_name, tab in zip(["Test", "ODI", "T20"], tabs):
                    with tab:
                        st.dataframe(df[df['format'] == tab_name])


            def get_close_matches(data):
                return data[
                    ((data['margin_type'] == 'runs') & (data['margin_value'] < 50)) |
                    ((data['margin_type'] == 'wkts') & (data['margin_value'] < 5))
                    ]

            if selected_query_name == "15. Close matches":
                close_matches_df = get_close_matches(df)

                st.markdown("### 🏏 Close Matches Summary")
                st.markdown(f"**Total Number of close matches:** {len(close_matches_df)}")

                st.dataframe(close_matches_df, use_container_width=True)

            if selected_query_name == "11. Compare each player's performance across different cricket formats":
                tabs = st.tabs(["Test", "ODI", "T20"])
                for tab_name, tab in zip(["Test", "ODI", "T20"], tabs):
                    with tab:
                        st.dataframe(df[df['format'] == tab_name])

            user = 'root'
            password = '1234'
            host = 'localhost'
            port = '3306'
            database = 'cricbuzz'

            conn_str = f"mysql+mysqlconnector://{user}:{password}@{host}:{port}/{database}"
            engine = create_engine(conn_str)

            if selected_query_name == "25. Perform a time-series analysis of player performance evolution":
                query = """
                SELECT player_name, career_phase
                FROM player_quarterly_performance
                GROUP BY player_name, career_phase;
                """
                #career_df = pd.read_sql(query, conn)
                df = pd.read_sql(query, engine)
                # Display in Streamlit
                st.subheader("Players Career Phase")
                st.dataframe(df)

                phase_counts = df['career_phase'].value_counts().reset_index()
                phase_counts.columns = ['Career Phase', 'Number of Players']
                st.subheader("Number of Players per Career Phase")
                st.bar_chart(phase_counts.set_index('Career Phase'))

            if selected_query_name == "23. player form and momentum":
                query = """
                    SELECT
                        player_name,
                        form_category
                    FROM
                        cricbuzz.player_form_batting_perf;
                """
                # Using pandas to read SQL query into a DataFrame
                df = pd.read_sql(query, engine)
                st.subheader("Player form & performances")
                # Display the data in Streamlit
                st.dataframe(df)

            if selected_query_name == "14. Bowling performance at different venues":
                query = """
                    SELECT bowler_name, matches_played, average_economy_rate, total_wickets FROM cricbuzz.bowler_venue_stats ORDER BY average_economy_rate ASC LIMIT 2;"""
                # Using pandas to read SQL query into a DataFrame
                df = pd.read_sql(query, engine)
                st.subheader("Best economy rate")
                # Display the data in Streamlit
                st.dataframe(df)


            # Download as CSV
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Download Results as CSV",
                data=csv,
                file_name=f"{selected_query_name.replace(' ', '_')}.csv",
                mime="text/csv"
            )

        except Exception as e:
            st.error(f"Error executing query: {e}")

####################################################################################################################
elif page == "CRUD Operations":
    st.title("📊 Cricbuzz LiveStats")
    st.subheader("CRUD Operations Page")

    import mysql.connector
    from mysql.connector import Error


    # --- MySQL Connection ---
    def get_connection():
        return mysql.connector.connect(
            host="localhost",  # replace with your host
            user="root",  # replace with your username
            password="1234",  # replace with your password
            database="cricbuzz"  # replace with your database
        )


    # Create table if it doesn't exist
    def create_table():
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS players (
                    id VARCHAR(20) PRIMARY KEY,
                    name VARCHAR(100),
                    matches INT,
                    runs INT,
                    average FLOAT
                )
            """)
            conn.commit()
            cursor.close()
            conn.close()
        except Error as e:
            st.error(f"Error creating table: {e}")


    create_table()

    # --- CRUD Operations ---
    st.write("Select an operation and manage player records.")

    operation = st.selectbox("Select Operation", ["CREATE", "READ", "UPDATE", "DELETE"])

    # CREATE
    if operation == "CREATE":
        st.subheader("Add New Player")
        player_id = st.text_input("Player ID")
        name = st.text_input("Player Name")
        matches = st.number_input("Matches Played", min_value=0, step=1)
        runs = st.number_input("Runs Scored", min_value=0, step=1)
        average = st.number_input("Batting Average", min_value=0.0, step=0.1)

        if st.button("Add Player"):
            if player_id.strip() == "" or name.strip() == "":
                st.warning("Player ID and Name are required!")
            else:
                try:
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO players (id, name, matches, runs, average)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (player_id, name, matches, runs, average))
                    conn.commit()
                    st.success(f"Player {name} added successfully!")
                    cursor.close()
                    conn.close()
                except Error as e:
                    st.error(f"Error: {e}")

    # READ
    elif operation == "READ":
        st.subheader("View Player Records")
        try:
            conn = get_connection()
            df = pd.read_sql("SELECT * FROM players", conn)
            st.dataframe(df)
            conn.close()
        except Error as e:
            st.error(f"Error: {e}")

    # UPDATE
    elif operation == "UPDATE":
        st.subheader("Update Player")
        try:
            conn = get_connection()
            df = pd.read_sql("SELECT id, name FROM players", conn)
            conn.close()
            player_to_update = st.selectbox("Select Player to Update", df['id'] + " - " + df['name'])
            player_id = player_to_update.split(" - ")[0]

            name = st.text_input("Player Name")
            matches = st.number_input("Matches Played", min_value=0, step=1)
            runs = st.number_input("Runs Scored", min_value=0, step=1)
            average = st.number_input("Batting Average", min_value=0.0, step=0.1)

            if st.button("Update Player"):
                try:
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute("""
                        UPDATE players
                        SET name=%s, matches=%s, runs=%s, average=%s
                        WHERE id=%s
                    """, (name, matches, runs, average, player_id))
                    conn.commit()
                    st.success(f"Player {player_id} updated successfully!")
                    cursor.close()
                    conn.close()
                except Error as e:
                    st.error(f"Error: {e}")
        except Error as e:
            st.error(f"Error fetching players: {e}")

    # DELETE
    elif operation == "DELETE":
        st.subheader("Delete Player")
        try:
            conn = get_connection()
            df = pd.read_sql("SELECT id, name FROM players", conn)
            conn.close()
            player_to_delete = st.selectbox("Select Player to Delete", df['id'] + " - " + df['name'])
            player_id = player_to_delete.split(" - ")[0]

            if st.button("Delete Player"):
                try:
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM players WHERE id=%s", (player_id,))
                    conn.commit()
                    st.success(f"Player {player_id} deleted successfully!")
                    cursor.close()
                    conn.close()
                except Error as e:
                    st.error(f"Error: {e}")
        except Error as e:
            st.error(f"Error fetching players: {e}")
