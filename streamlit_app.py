# streamlit_app.py
# import streamlit as st
# import pandas as pd
# import requests
# import folium
# from streamlit_folium import folium_static
# from geopy.distance import geodesic

import streamlit as st
import pandas as pd
import requests
import plotly.express as px

def check_dependencies():
    dependencies = {
        # 'folium': False,
        'plotly': False,
        'geopy': False
    }
    
    # try:
    #     # import folium
    #     # from streamlit_folium import folium_static
    #     # dependencies['folium'] = True
    # except ImportError:
    #     pass
        
    try:
        import plotly.express as px
        dependencies['plotly'] = True
    except ImportError:
        pass
        
    return dependencies

deps = check_dependencies()

# Title and description
st.title("🌽 Taita Taveta Food Donation Network")
st.subheader("Connecting Agricultural Surplus with Communities in Need")

# Load data
@st.cache_data
def load_data():
    df = pd.read_csv('corn_data.csv')
    df['Acreage'] = df['Acreage'].fillna(df['Acreage'].median())
    df['Fertilizer amount'] = df['Fertilizer amount'].fillna(df['Fertilizer amount'].median())
    df['Yield_per_acre'] = df['Yield'] / df['Acreage']
    df['Surplus_score'] = df['Yield'] - (df['Household size'] * 50)
    return df

df = load_data()

# Display surplus farmers
st.header("Farmers with Surplus Crops")
st.write(f"Found {len(df[df['Surplus_score'] > 0])} farmers with surplus crops")

# Map visualization using Plotly
st.subheader("Surplus Locations")
fig = px.scatter_mapbox(
    df[df['Surplus_score'] > 0],
    lat="Latitude",
    lon="Longitude",
    size="Surplus_score",
    color="Surplus_score",
    hover_name="Farmer",
    hover_data=["Yield", "Household size"],
    zoom=9,
    height=600
)
fig.update_layout(mapbox_style="open-street-map")
fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
st.plotly_chart(fig)

# # Title and description
# st.title("🌽 Taita Taveta Food Donation Network")
# st.subheader("Connecting Agricultural Surplus with Communities in Need")
# st.markdown("""
# This platform helps achieve **UN SDG 2: Zero Hunger** by:
# - Identifying farmers with surplus crops
# - Connecting them with food banks and needy communities
# - Optimizing distribution routes to reduce waste
# """)

# # Load data
# @st.cache_data
# def load_data():
#     df = pd.read_csv('corn_data.csv')
#     df['Acreage'] = df['Acreage'].fillna(df['Acreage'].median())
#     df['Fertilizer amount'] = df['Fertilizer amount'].fillna(df['Fertilizer amount'].median())
#     df['Yield_per_acre'] = df['Yield'] / df['Acreage']
#     df['Surplus_score'] = df['Yield'] - (df['Household size'] * 50)
#     return df

# df = load_data()

# Sidebar filters
st.sidebar.header("Filters")
min_surplus = st.sidebar.slider("Minimum Surplus (kg)", 0, 500, 100)
education_filter = st.sidebar.multiselect("Education Level", df['Education'].unique())

# Filter data
filtered_df = df[df['Surplus_score'] >= min_surplus]
if education_filter:
    filtered_df = filtered_df[filtered_df['Education'].isin(education_filter)]

# # Display surplus farmers
# st.header("Farmers with Surplus Crops")
# st.write(f"Found {len(filtered_df)} farmers with surplus crops")

# # Map visualization
# st.subheader("Surplus Locations")
# m = folium.Map(location=[-3.45, 38.35], zoom_start=10)
# for _, row in filtered_df.iterrows():
#     folium.Marker(
#         [row['Latitude'], row['Longitude']],
#         popup=f"{row['Farmer']}: {row['Surplus_score']:.0f}kg surplus",
#         tooltip=f"Yield: {row['Yield']}kg"
#     ).add_to(m)
# folium_static(m)

# Donation matching
st.header("💝 Make a Donation")
col1, col2 = st.columns(2)

with col1:
    st.subheader("Farmers Available")
    selected_farmer = st.selectbox("Select a farmer", filtered_df['Farmer'].unique())
    farmer_data = filtered_df[filtered_df['Farmer'] == selected_farmer].iloc[0]
    st.write(f"**Yield:** {farmer_data['Yield']}kg")
    st.write(f"**Household Need:** {farmer_data['Household size'] * 50}kg")
    st.write(f"**Available Surplus:** {farmer_data['Surplus_score']:.0f}kg")

with col2:
    st.subheader("Donation Details")
    donation_amount = st.number_input("Amount to donate (kg)", 0, int(farmer_data['Surplus_score']), 10)
    recipient_type = st.selectbox("Recipient Type", ["Food Bank", "School", "Orphanage", "Community Center"])
    if st.button("Schedule Donation"):
        st.success(f"🎉 Scheduled donation of {donation_amount}kg from {selected_farmer} to {recipient_type}")

# Yield prediction tool
st.header("📈 Yield Prediction")
with st.form("prediction_form"):
    col1, col2 = st.columns(2)
    with col1:
        acreage = st.number_input("Acreage", 0.1, 10.0, 1.0)
        fertilizer = st.number_input("Fertilizer Amount (kg)", 0, 500, 50)
    with col2:
        laborers = st.number_input("Number of Laborers", 1, 10, 2)
        household_size = st.number_input("Household Size", 1, 10, 4)
    
    if st.form_submit_button("Predict Yield"):
        response = requests.post("http://localhost:5000/predict_yield", json={
            'acreage': acreage,
            'fertilizer': fertilizer,
            'laborers': laborers,
            'household_size': household_size
        })
        prediction = response.json()['predicted_yield']
        st.metric("Predicted Yield", f"{prediction:.0f} kg")
        surplus = prediction - (household_size * 50)
        st.metric("Potential Surplus", f"{surplus:.0f} kg", delta_color="inverse" if surplus < 0 else "normal")

# About section
st.markdown("---")
st.subheader("About This Project")
st.write("""
This system helps reduce food waste and hunger in Taita Taveta County by:
1. Identifying farmers with surplus crops using AI analysis
2. Connecting them with organizations that can distribute food to those in need
3. Optimizing logistics to ensure efficient delivery
4. Predicting future yields to plan ahead

By leveraging agricultural data, we can make meaningful progress toward **Zero Hunger**.
""")
