import streamlit as st  #st import
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

#EMACrossover and RSI are two independent signals, a Crossover is a signal to trade and the rsi is a signal of a trend reversal, combined, these two signals work well with each other. the volume check is also independant as a signal but only serves to check the reliability of te other signals

st.title("EMA Crossover Trading Strategy")  # st title


#default values
SEMA=9
LEMA=21
tail= 10

#streamlit operations
#-----------------------------------------------------------------------------------------------------#
with st.sidebar:                                                                                      # this puts the below on the side bar as opposed to on teh main page which i like, you could also j use x=st.sidebar.input... using with st.sidebar it applies to all so its easier 
    ticker= st.text_input("Stock Ticker:", "AAPL").upper()                                            #
    days= st.number_input("Number of days:", min_value=10, max_value=200, value=70) # st inputs       #
    Show_RSI= st.checkbox("Show RSI")
    expand_adsets= st.checkbox("Advanced Settings")                                                   #
                                                                                                      #
if expand_adsets:                                                                                     #
    with st.sidebar:                                                                                  #
        SEMA=st.number_input("Short EMA span (hours):", min_value=1, max_value=200, value=SEMA)       # these will cause a bug if u dont provide a default value like up there bc the MA are only set when the box is ticked so when its not they wont be set
        LEMA=st.number_input("Long EMA span(hours):", min_value=1, max_value=200, value=LEMA)         # value=x is setting a default value
        tail=st.number_input("Last periods shown in table", min_value=1, max_value=200, value=tail)   #
#-----------------------------------------------------------------------------------------------------#


#data download
apple = yf.download(ticker, interval="1h", period="200d")                                          
data = apple[["Close"]].copy()


#creation of MA, position, and volume check
#-----------------------------------------------------------------------#
data["short_EMA"]=data.ewm(span=SEMA, adjust=False).mean()              #  create a column for a short ma and a long one,basically we want to compare them, if the long is higher than the short you should go long and vice versa
data["long_EMA"]=data.Close.ewm(span=LEMA, adjust=False).mean()         #  btw, the MAs are set in hours since the download intervals are set in hours so this is a 9/21 open market hour split
                                                                        #
data.dropna(inplace=True)                                               #
                                                                        #
data["position"]=np.where(data["short_EMA"] > data["long_EMA"], 1, -1)  #  here we make a column that decides if we go long (1) or short(-1)
data["Crossover"]=data["position"].diff(periods=1)                      #
data["Crossover"] = data["Crossover"].replace({2: "Buy", -2: "Sell"})   #
buy_signals=data[data["Crossover"]=="Buy"]                              #  When short EMA crosses above long EMA
sell_signals=data[data["Crossover"]=="Sell"]                            #  When long EMA crosses above short EMA
                                                                        # 
data["Volume"] = apple["Volume"]                                        #  Volume refers to the total number of shares traded during a given time period, we dont have to create the column, its included automatically
data["Vol_MA"] = data["Volume"].rolling(15, min_periods=1).mean()       #  low volume makes the data less reliable (in teh way a low sample size would skew results), so we calculate the moving average of teh volume and we want the current to be above it.
data["Valid_Signal"] = data["Volume"] >= data["Vol_MA"]                 #  if true then signal is trustworthy, if false its less reliable
#-----------------------------------------------------------------------#


#RSI related
#---------------------------------------------------------------------#  RSI measures the speed and change of price movements, it ranges between 0-100, above 70 indicates that the stock is overbought meaning it may be priced too high and could be due for a price pullback below 30 suggest the asset is "oversold," meaning it may be priced too low and could be due for a price increase
if Show_RSI:                                                          #  here its to make it so that the RSI will only be shown when the box is checked 
    data["delta"]=data["Close"].diff(1)                               #  finds the diffs
    data["gain"] = np.where(data["delta"] > 0, data["delta"], 0)      #  if the diffs are positive then its a gain, this isolates the gains
    data["loss"] = np.where(data["delta"] < 0, -data["delta"], 0)     #  if the diffs are negative its a loss, this isolates the loss, notice we make data.delta negative to obtain the absolute value
    avg_gain = data["gain"].rolling(window=14, min_periods=1).mean()  #  we find the moving average of the gains of the past 14 periods
    avg_loss = data["loss"].rolling(window=14, min_periods=1).mean()  #  same but for loss, maye we can change 14 periods to something else
    RS = np.where(avg_loss == 0, 0, avg_gain / avg_loss)              #  we do it this way to avoid ever dividing by 0 in case avg_loss is 0
    RSI=100-(100/(1+RS))                                              #
    data["RSI"]=RSI                                                   #
#---------------------------------------------------------------------#



#graph related
#-----------------------------------------------------------------------------------------------------------------------------#
plt.style.use("dark_background")                                                                                              #
fig, ax=plt.subplots(figsize=(12, 8))                                                                                         #
if Show_RSI:                                                                                                                  #  secondary y axis for RSI
    ax2=ax.twinx()                                                                                                            #
ax.grid(True, linestyle="dotted", linewidth=0.5, alpha=0.2, color="white")                                                    #
period=data.index.max() - pd.Timedelta(days=days)                                                                             #  this makes it so that i see only the last 30 days on the graph
ax.plot(data.loc[period:, "Close"], label='Close Price', color='green', alpha=0.7)                                            #  to plot the actual stock price in case u want to
ax.plot(data.loc[period:].index, data.loc[period:, "short_EMA"], label="Short EMA", color="red")                              #  plot long and short EMAs
ax.plot(data.loc[period:].index, data.loc[period:, "long_EMA"], label="Long EMA", color="blue")                               #
                                                                                                                              #
ax.scatter(buy_signals.loc[period:].index, buy_signals.loc[period:, "short_EMA"],                                             #  this gives an up arrow to signal a buy on graph
           marker="^", color="green", s=150, label="Buy Signal", alpha=0.8, zorder=4, edgecolor="white")                      #  i added z order bc it puts the signals above other lines, just better
ax.scatter(sell_signals.loc[period:].index, sell_signals.loc[period:, "short_EMA"],                                           #  this gives an down arrow to signal a sell on graph
           marker="v", color="red", s=150, label="Sell Signal", alpha=0.8, zorder=4, edgecolor="white")                       #
ax.set_ylabel("Price", fontsize=14, fontweight="bold")                                                                        #
                                                                                                                              # 
if Show_RSI:                                                                                                                  #  all the secondary graph shit we have to do in condition obviously in case rsi is turned off 
    ax2.plot(data.loc[period:].index, data.loc[period:, "RSI"], label="RSI", color="purple", linestyle="dashed", alpha=0.4)   #  this graphs the RSI o, the secondary y axis
    ax2.axhline(70, color="white", linestyle="dotted", alpha=0.5, label="Overbought (70)")                                    #  this creates a line on the 70 mark of secondary y axis, cool technique
    ax2.axhline(30, color="white", linestyle="dotted", alpha=0.5, label="Oversold (30)")                                      #  same but for 30
    ax2.legend(loc="upper right")                                                                                             #
    ax2.set_ylabel("RSI", fontsize=14, fontweight="bold")                                                                     # didnt have this in the OG but it j anotates the y axis
    ax2.grid(False)                                                                                                           #  to remove the grid of second graph, looks weird otherwise
                                                                                                                              #
ax.set_title(ticker, fontsize=16, fontweight="bold")                                                                          #
ax.legend(loc="upper left")                                                                                                   #
st.pyplot(fig)                                                                                                                #  here it replaces the plt.show() ig it does the same but in the app
                                                                                                                              #
st.write("### Trading Data Table")                                                                                            #  here the more ### you put, the larger the smaller teh text will appear 
st.dataframe(data.loc[:, ["Close", "Crossover", "Valid_Signal", "Volume"]].tail(tail))                                        #  same here, it replaces the print command for the website
#-----------------------------------------------------------------------------------------------------------------------------#

#streamlit run "C:\Users\eliot\OneDrive\Desktop\travail\UCL\ALGO\streamlit_SMG_app\SMG_sl.py"