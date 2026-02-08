# Brazilian E-commerce Data Analysis

## 🗂️ Project Overview
This project exploraty data analysis of the Brazilian Ecommerce dataset using Python.

This goal is to explore an ecommerce dataset to understand sales performance, customer behavior, and key business metrics.

## 🛒 Dataset
Source: Olist
Name: Brazilian E-commerce Public Dataset

## 🧹 Data cleaning and preparation
The dataset was prepared by:
  - Connecting with database SQLite
  - Loading all tables into dataframes by pandas
  - Converting data columns to datatime format
  - Removing invalid values and duplicates
  - Checking for negative prices or freight values
  - Merging all tables into a clean dataframe
  - Assigning one category per order to avoid duplication
  - Creating new columns: revenue, delivery_time, month, year

## 🔍 Exploraty Analysis
The analysis includes:
  - Total revenue
  - Top 10 product categories
  - Top 10 states by revenue
  - Average delivery time (days)
  - Monthly KPIs: number of orders, total revenue, MoM % change, YoY % change
  - Seasonality: average revenue per month across years
  - RFM: recency, frequency, monetary
  - RFM scoring and customer segmentation: VIP, Loyal, New, Sleeping, Potential  

## 📊 Visualizations 
This project includes multiple visualizations:
  - Monthly revenue bar chart
  - Revenue seasonality by month
  - Revenue by RFM segment
  - Delivery time distrubution histogram
### Note: All chart are saved as images and included in the repository for reference

## 💡 Key Insight
  - Top product categories: Beauty, Watches, Home & Living.
  - Highest revenue states: SP, RJ, MG.
  - Average delivery time: ~12 days.
  - Orders and revenue show steady growth with peaks in Nov–Dec (seasonality).
  - VIP and loyal customers generate the majority of revenue.
    
## 🛠️ Technologies Used
  - Python
  - Pandas
  - Matplotlib


