#!/usr/bin/env python3

# Import Library
import pandas as pd
import numpy as np
import streamlit as st
import matplotlib.pyplot as plt
import altair as alt
import string 
from datetime import timedelta, datetime

# Import Data
df = pd.read_csv("test_data.csv")

# Set-up Data Type
df.Date = pd.to_datetime(df.Date)
df["Order Time"] = pd.to_datetime(df["Order Time"])
df["Serve Time"] = pd.to_datetime(df["Serve Time"])
df["Kitchen Staff"] = df["Kitchen Staff"].astype("int64")
df["Drinks Staff"] = df["Drinks Staff"].astype("int64")

# สร้างตัวแปรใหม่
df["Diff_Minute"] = (df["Serve Time"] - df["Order Time"]) / pd.Timedelta(minutes=1) # สร้าง Diff_Minute เพื่อระบุระยะเวลาการทำอาหาร
df["Month"] = df["Order Time"].dt.month_name().str.slice(stop=3)                    # สร้าง Month เพื่อระบุเดือนของวันนั้น ๆ 
df.rename(columns={"Day Of Week": "Week"}, inplace=True)                            # เปลี่ยนชื่อตัวแปรเพื่อให้ง่ายต่อการเข้าถึง

Month = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", 
        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
Week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
dict_time = {"Month":Month, "Week":Week}

food_menu = ["Cheese Burger", "Classic Burger", "Supreme Burger","Veggie Burger"]
drink_menu = ["Chocolate Milkshake", "Coffee", "Coke", "Soda", "Strawberry Milkshake", "Tea", "Water"]

# Select ตัวแปรที่เกี่ยวข้องเท่านั้น
food_drink_df = df.reindex(columns=["Date", "Week", "Month", "Menu", "Price", "Category", "Kitchen Staff", "Drinks Staff", "Hour", "Minute", "Diff_Minute"])

# Highest Header
st.markdown('<h1  style="text-align:center;"><font size="36"> Dashboard </font></h1>', unsafe_allow_html=True)

# Setting Filter
with st.sidebar:
    st.title("⚙️ Filters")
    max_date = df.Date.max().date()
    min_date = df.Date.min().date()

    start_date = st.date_input("Start date", min_date, min_value=df.Date.min().date(), max_value=max_date)
    start_date = pd.to_datetime(start_date)
    end_date = st.date_input("End date", max_date, min_value=df.Date.min().date(), max_value=max_date)
    end_date = pd.to_datetime(end_date)

    select_time = st.selectbox("Select Time",
                              ({"Date", "Week", "Month"}),)
    
    categories = st.selectbox("Select Categories", ["Food", "Drink"])
    

# 1. ในช่วงที่มีลูกค้าจำนวนมาก เกิดปัญหาหรือไม่
# 2. การวางจำนวนพนักงานของผมมีประสิทธิภาพมากน้อยเพียงใด
# แสดงข้อมูล Time Series ของ Standard_Order_Volume and Standard_Diff_Minute
# Standard_Order_Volume
    # Standard_Order_Volume > 0 -> ช่วงเวลาที่มีคนมาก
    # Standard_Order_Volume <= 0 -> ช่วงเวลาที่มีคนน้อย
# Standard_Diff_Minute
    # Standard_Diff_Minute > 0 -> ใช้เวลาในการทำอาหารมาก
    # Standard_Diff_Minute <= 0 -> ใช้เวลาในการทำอาหารน้อย

# แสดงปริมาณรวม Order แต่ละ time (select_time)
col01, col02 = st.columns([0.2,0.8])
with col01:
    menu = st.selectbox("Select Menu", food_menu) if categories == "Food" else st.selectbox("Select Menu", drink_menu)
    order_quantity = st.radio("Select Order Quantity", ["All", "High Volume", "Low Volume"])
order_volume_time = pd.DataFrame(food_drink_df.loc[(food_drink_df["Date"] >= start_date) & 
                                                   (food_drink_df["Date"] <= end_date)].groupby([select_time])["Week"].count())
order_volume_time.rename(columns={"Week":"order_volume"},inplace=True)
order_volume_time["Standard_Order_Volume"] = (order_volume_time.values - order_volume_time.values.mean())/order_volume_time.values.std()
order_volume_time["Order_Quantity"] = ["High Volume" if i > 0 else "Low Volume" for i in list(order_volume_time["Standard_Order_Volume"])]
order_volume_time.reset_index(inplace=True)
if select_time != "Date":
    order_volume_time[select_time] = pd.Categorical(order_volume_time[select_time], categories=dict_time[select_time], ordered=True)
order_volume_time.sort_values(by = select_time,ascending=True, inplace=True)

# แสดงปริมาณค่า Mean ของ Diff_Minute, Kitchen Staff แต่ละ menu
menu_volume = pd.DataFrame(food_drink_df.loc[(food_drink_df["Date"] >= start_date) & 
                                               (food_drink_df["Date"] <= end_date) & 
                                               (food_drink_df["Menu"] == menu)].groupby([select_time])[["Diff_Minute","Kitchen Staff"]].mean())
# ทำให้อยู่ในช่วงเดียวกันเพื่อง่ายต่อการวิเคราะห์ในกราฟเดียวกัน
# ใช้ข้อมูลจาก menu ที่เป็น select box เพื่อนำมาพิจาณาแต่ละ Menu ได้ง่าย
menu_volume["Standard_Diff_Minute"] = (menu_volume.Diff_Minute - menu_volume.Diff_Minute.mean())/menu_volume.Diff_Minute.std()
menu_volume["Standard_Kitchen_Staff"] = (menu_volume["Kitchen Staff"] - menu_volume["Kitchen Staff"].mean())/menu_volume["Kitchen Staff"].std()
menu_volume.reset_index(inplace=True)


# รวม order_volume_time กับ menu_volume ให้เป็น column เดียวกันเพื่อนำมาเปรียบเทียบ
order_time = order_volume_time.assign(Diff_Minute = menu_volume["Diff_Minute"],Standard_Diff_Minute = menu_volume["Standard_Diff_Minute"], Kitchen_Staff = menu_volume["Kitchen Staff"],Standard_Kitchen_Staff = menu_volume["Standard_Kitchen_Staff"])
if order_quantity != "All": 
    order_time = order_time.loc[order_time["Order_Quantity"] == order_quantity]
with col02:
    st.subheader(f"Comparison of Standard Time Difference, Kitchen Staff, and {menu} Order Volume ")
    st.line_chart(order_time,
                x=select_time, 
                y=["Standard_Order_Volume", "Standard_Diff_Minute", "Standard_Kitchen_Staff"],
                color=["#FFCF9D", "#BFECFF", "#8174A0"])


col1_1, col1_2 = st.columns([0.5,0.5])
with col1_1:
    st.subheader(f"Comparison of Time Difference, Kitchen Staff in {menu} Order")
    st.line_chart(order_time,
                x=select_time, 
                y=["Diff_Minute", "Kitchen_Staff"],
                color=["#FFCF9D", "#BFECFF"])

with col1_2:
    st.subheader(f"{menu} Order Volume Line")
    st.line_chart(order_time,
                x=select_time, 
                y=["order_volume"],
                color=["#8174A0"])

# 3. ไม่ทราบถึงความพึงพอใจในอาหารแต่ละ Menu ของลูกค้า → เพื่อที่จะสามารถสร้างโปรโมชั่นที่สามารถดึงดูดลูกค้าได้เพิ่มมากขึ้น
# แสดงปริมาณรวม Order แต่ละ Menu
food_drink_volume = pd.DataFrame(food_drink_df.loc[(food_drink_df["Category"] == "drink") | 
                                                   (food_drink_df["Category"] == "food")].groupby(["Menu"])["Week"].count())
food_drink_volume.rename(columns={"Week":"order_volume"},inplace=True)
food_drink_volume["Standard_Order_Volume"] = (food_drink_volume["order_volume"]-(food_drink_volume["order_volume"].mean()))/(food_drink_volume["order_volume"].std())
food_drink_volume = food_drink_volume.sort_values("order_volume", ascending=False)
food_drink_volume.reset_index(inplace=True)

# แสดงปริมาณรวม Order แต่ละ Menu ที่เป็น Categories
fd_volume = pd.DataFrame(food_drink_df.loc[food_drink_df["Category"] == categories.lower()].groupby(["Menu"])["Week"].count())
fd_volume.rename(columns={"Week":"order_volume"},inplace=True)
fd_volume["Standard_Order_Volume"] = (fd_volume["order_volume"]-(fd_volume["order_volume"].mean()))/(fd_volume["order_volume"].std())
fd_volume = fd_volume.sort_values("order_volume", ascending=False)
fd_volume.reset_index(inplace=True)

col3_1, col3_2 = st.columns([0.7,0.3])
# แสดงข้อมูลที่ Standard ของทุกเมนู แล้วนำมาเทียบกัน ว่าควรตัดเมนูไหนออก (ตัดเมนูที่มีค่าติดลบออก)
with col3_1:
    st.subheader("Standard All Menu Volume Chart")
    fdv_color = alt.when(Standard_Order_Volume=food_drink_volume["Standard_Order_Volume"].min()).then(alt.value("#FF8A8A")).otherwise(alt.value("#CCE0AC"))
    food_drink_volume_ = alt.Chart(food_drink_volume).mark_bar().encode(
        x='Standard_Order_Volume',
        y=alt.X("Menu", sort=None), color=fdv_color).properties(height=500)
    
    st.altair_chart(food_drink_volume_, use_container_width=True)
# แสดงข้อมูลที่ Standard ของ Menu ตาม Select Box (Categories) แล้วนำมาเทียบกัน ว่าควรตัดเมนูไหนออก (ตัดเมนูที่มีค่าติดลบออก)
with col3_2:
    st.subheader(f"Standard {categories} Volume Chart ")
    fd_color = alt.when(Standard_Order_Volume=fd_volume["Standard_Order_Volume"].min()).then(alt.value("#FF8A8A")).otherwise(alt.value("#CCE0AC"))
    fd_ = alt.Chart(fd_volume).mark_bar().encode(x=alt.X("Menu", sort=None),
                                                 y='Standard_Order_Volume', color = fd_color).properties(height=500)
    st.altair_chart(fd_, use_container_width=True)



# 4. มีพนักงานอยู่บางกลุ่มที่เสนอให้ผมลด Menu ที่ไม่จำเป็นออกเพื่อการจัดการที่ง่ายขึ้น
# พิจารณาจากรายได้ที่ได้
money = pd.DataFrame(food_drink_df.groupby("Menu")["Price"].sum())
money.rename(columns={"Price":"Amount"},inplace=True)
money.reset_index(inplace=True)
money = money.sort_values("Amount", ascending=False)

money_c = pd.DataFrame(food_drink_df.loc[food_drink_df["Category"] == categories.lower()].groupby("Menu")["Price"].sum())
money_c.rename(columns={"Price":"Amount"},inplace=True)
money_c.reset_index(inplace=True)
money_c = money_c.sort_values("Amount", ascending=False)

col4_1, col4_2 = st.columns([0.7,0.3])
with col4_1:
    st.subheader(f"All Menu Amount Chart")
    money_color = alt.when(Amount=money["Amount"].min()).then(alt.value("#FFDDAE")).otherwise(alt.value("#D4F6FF"))
    money_a = alt.Chart(money).mark_bar().encode(
        x='Amount',
        y=alt.X("Menu", sort=None), color=money_color
    ).properties(height=500)
    
    st.altair_chart(money_a, use_container_width=True)

with col4_2:
    st.subheader(f"{categories} Amount Chart")
    money_c_color = alt.when(Amount=money_c["Amount"].min()).then(alt.value("#FFDDAE")).otherwise(alt.value("#D4F6FF"))
    money_c_a = alt.Chart(money_c).mark_bar().encode(
        x=alt.X("Menu", sort=None), color=money_c_color,
        y='Amount'
    ).properties(height=500)
    
    st.altair_chart(money_c_a, use_container_width=True)