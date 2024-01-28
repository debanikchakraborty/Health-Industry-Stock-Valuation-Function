
# -*- coding: utf-8 -*-
"""
Created on Fri Dec  9 01:40:07 2022

@author: deban
"""
#Importing necessary libraries
import yfinance as yf
from datetime import datetime
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
#TickerList=['UNH','JNJ','PFE','CVS','RDY','DHR','RMD','WST'] #Some tickers from health industry

#Creating a function for multiple valuation of a ticker from health industry
#Give ticker and Tickers List(industry peers) as inputs

def HealthStock_Valuation(ticker, TickersList):
    
    #Procuring required Data from yfinance  
    yf_data = yf.Ticker(ticker)
    bf=yf_data.info #ticker's info
    Market_Price=bf['currentPrice'] 
    shares_outstanding = bf['sharesOutstanding'] 
    EPS=bf['trailingEps'] 
    
    #Present Year from datatime
    present_year = datetime.now().year
    years = 4 #As it is convenient for the model [Cannot be given as an input of the function as only 4 years 
    #income statement data is available, which is a limitation to historical net income growth rate calcualtion]
    
    #ticker's cashflow
    cf = yf_data.cashflow
    
    #Checking if necessary cf rows exists
    CF_columns = ['Net Borrowings','Total Cash From Operating Activities', 'Capital Expenditures']
    for col in CF_columns:
          try:
              cf.loc[col]
          except:cf.loc[col,:] = np.nan
    
    #Calculating current year Free Cash Flow to Equity
    cur_fcf= (cf.loc['Total Cash From Operating Activities'].iloc[0] + cf.loc['Capital Expenditures'].iloc[0] + cf.loc['Net Borrowings'].iloc[0])
    
    #Assumptions :
    #1)Industry(Tickers list) average Net Income Growth rate as Growth rate of FCFE of the ticker for next 3 years
    #2)And industry(Ticker list) average sustainable growth rate as the perpetual rate after 3 years
    #3)CAPM of the ticker as the Expected rate of return of the ticker as discounting rate
    
    #Getting all necessary industry data 
    ind_net_inc_growth=[] #List for saving net income growth rate of each Tickers 
    industry_growth = 0.0 #Manually adding sustanable growth rate of each Tickers
    rel_Val_df=pd.DataFrame() #Relative Valuation DataFrame
    
    for tic in TickersList: #Looping through the tickers from Tickers List
        #Calling each tickers yf data to get info and income statement
        data=yf.Ticker(tic) 
        info_data=data.info
        inc=data.financials
        
        #Creating two columns-EPS and Price keeping tickers as rows in Relative Valuation DF
        rel_Val_df.loc[tic,'EPS'] = info_data['trailingEps']
        rel_Val_df['Price']= info_data['currentPrice']
        
        #Checking if required row exist in Income Statements of the tickers
        Inc_columns = ['Net Income']
        for col in Inc_columns:
              try:
                  inc.loc[col]
              except:inc.loc[col,:] = np.nan
        
        #creating net income dataframe for each ticker to calculate net income growth rate 
        netinc= pd.DataFrame()
        #Looping through the net income row of 4 years(current and previous 3 years) of each ticker
        for i in range(years):
            netinc.loc[present_year-i, 'NI']= inc.loc['Net Income'].iloc[i]
        
        #Reindexing the year to set the rows of dataframe in ascending order of years[column]
        netinc=netinc.reset_index()
        netinc= netinc.rename(columns={'index':'Year'}) 
        netinc= netinc.sort_values(by=['Year'], ascending=True) 
        netinc['growth_rate']=netinc.NI.pct_change() #Calculating the growth of net income for each ticker
        netinc_growth=netinc.growth_rate.mean() #Calculating average net income growth for each ticker
        ind_net_inc_growth.append(netinc_growth) #Saving the average net income growth of each ticker in the list
        dividend_payout= info_data['trailingAnnualDividendRate']/info_data['trailingEps'] #Calculating each ticker payoutratio
        ROE=info_data['returnOnEquity'] #Each ticker ROE
        retention_ratio=(1- dividend_payout) 
        industry_growth += ROE*retention_ratio #Adding the sustainable growth rates of each ticker
    
    #Averaging the average net income growth rate of all tickers
    NI_growth= np.average(ind_net_inc_growth)
    
    #Averaging the sum of industry sustainable growths
    average_industry_growth= industry_growth/len(TickersList)
    
    g=average_industry_growth #Our industry sustainable growth rate
    
    #Creating a list to save current FCFE and calculate 3 years forcasted FCFE
    df=[cur_fcf]
    
    #looping through each item in df list to calculate next year forcasted FCFE
    for i in range(years-1): #(years-1) as 1 item is already added in the list(total item will be 4)
         lf=df[i]*(1+NI_growth)
         df.append(lf)
    
    #Saving the list as a column in Future FCFE dataframe [current year and next 3 years]
    future_fcf=pd.DataFrame(df, columns= ['Forcasted_FCF'])
    
    #Generating a column for respective years in the same way as above from a list
    future_time=[]
    for i in range(years): #years as 4 years will be added
        future= present_year+i
        future_time.append(future)
    
    future_fcf['Years']=future_time
    
    #Plotting the data in Future FCFE DF in bar charts
    future_fcf.plot(x="Years", y="Forcasted_FCF", kind="bar",figsize=(10, 9))
    plt.title('Current and Forcasted Free Cash flow to Equity')
    plt.show()
    
    future_fcf=future_fcf.set_index('Years') #Setting years as index in Future FCFE DF
    
    #CAPM Calculation of the Stock:  
    #Calculating Market Return and variance(S&P 500 index) and ticker returns
    hf=yf.Ticker('^GSPC').history('10y', interval='1d').Close.pct_change()
    marketreturn_variance=hf.var()
    jf=yf_data.history('10y', interval='1d').Close.pct_change()
    #Creating Return DataFrame to save ticker and Market Returns
    ret_df=pd.DataFrame()
    ret_df['Stock_Return']=hf
    ret_df['Market_Return']=jf
    ret_df=ret_df.dropna()
    #Calculating Covariance of Stock(ticker) and Market Returns
    covMX=ret_df.cov()
    cov=covMX.loc['Stock_Return', 'Market_Return']
    beta=cov/marketreturn_variance #Calcualting Beta
    rf= yf.Ticker('^TNX').history('10y').Close.iloc[-1]/100  #10year TBonds rate as risk free rate
    rm=hf.mean()*252 #Expectation of Market Returns over last 10 years(annually)   
    CAPM=rf+(rm-rf)*beta #The CAPM
    
    #Printing growth rates and CAPM
    print('Industry Net Income growth rate',NI_growth)
    print('CAPM', CAPM)
    print('Industry Sustainable growth rate', g)
    
    print('\n')
    
    #Creating a list to save discounting factors for 4 years[current and next 3 years]
    discounting_factor=[]
    #Looping through years to calcualte discounting factors
    for i in range(years): 
        baal=1/((1+CAPM)**i)
        discounting_factor.append(baal)
    #Saving the list as a column in Future FCFE DF
    future_fcf['Discounting_Factor']= discounting_factor
    future_fcf['Present_Value']= future_fcf.Forcasted_FCF*future_fcf.Discounting_Factor #Calculation of PVs for 4 years
    future_fcf = future_fcf.drop(present_year, axis=0) #Dropping the row of current year as we dont need it
    sum_of_equity_PVvalue=future_fcf['Present_Value'].sum() #Sum of Present value of forcasted 3 year free cash flows to equity
    
    #calculation of the terminal value={4th year Forcasted FCFE/(CAPM-sustainable growth rate)}
    terminal_value=future_fcf['Forcasted_FCF'].iloc[-1]*(1+NI_growth)/(CAPM-g)
    
    #Present Value of Terminal Value
    PV_terminal_value= terminal_value/(1+CAPM)**years
    
    #Firm value as summation of PV of 3 years forcasted FCFE and PV of terminal value
    Firm_Value= PV_terminal_value+sum_of_equity_PVvalue
    
    print ('Current Market Price', Market_Price)
    print('Firm Value', Firm_Value)
    
    Stock_Value=Firm_Value/shares_outstanding #Intrinsic Stock price as per FCFE Valuation
    
    print('FCFE Valuation Stock Price of', ticker, Stock_Value)
    
    #Finding whether the ticker is overvalued or undervalued than market price, as per FCFE Valuation Stock Price
    if Market_Price > Stock_Value:
        print('Relative to Free Cash Flow Firm Value', ticker, 'is overvalued')
    else:
        print('Relative to Free Cash Flow Firm Value', ticker, 'is undervalued')
        
    print('\n')
    
    #Adding a Column for PE in Relative Valuation DF
    rel_Val_df['PE'] = rel_Val_df['Price'] / rel_Val_df['EPS']
    industry_PE=rel_Val_df['PE'].mean() #Finding Industry PE by averaging (Industry multiplier)
    print('industryPE Ratio', industry_PE) 
    
    imp_prcPE= EPS*industry_PE #Calculating intrinsic stock price as per industry PE
    print('Intrinsic Stock Price as per Industry PE Ratio', imp_prcPE)
    
    #Finding whether the ticker is overvalued or undervalued than market price, as per intrinsic stock price by industry PE
    if Market_Price > imp_prcPE:
        print('Relative to Industry', ticker, 'is overvalued')
    else:
        print('Relative to Industry', ticker, 'is undervalued')
        
    #Plotting the price comparisons
    x = ['FCFE Price','Industry P/E Price','Market Price']
    y = [Stock_Value,imp_prcPE, Market_Price]
    color= ['red', 'blue', 'green']
    plt.bar(x, y, color=color)
    plt.title('Comparison of Prices')
    plt.show()