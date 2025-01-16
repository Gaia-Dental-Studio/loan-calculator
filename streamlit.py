import pandas as pd
import streamlit as st
import numpy as np
from model import LoanCalculator
import requests
from datetime import date

st.title('Loan Calculator')


type = st.radio('Select the type of loan', ('By Loan Term', 'By Repayment Amount'))




with st.container(border=True):
    st.markdown("### Loan Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        loan_amount = st.number_input('Loan Amount', min_value=0, value=150000)
        interest_rate = st.number_input('Annual Interest Rate (%)', min_value=0.0, value=5.5, step=0.25)
        
        
        loan_term = None
        repayment_amount = None
        
        if type == 'By Loan Term':
            loan_term = st.number_input('Loan Term (years)', min_value=0, value=30)
        else:
            repayment_amount = st.number_input('Repayment Amount', min_value=0, value=800)
        
        
    
    with col2:
        compound_period = st.selectbox('Compound Period', ['Monthly'])
        payment_frequency = st.selectbox('Payment Frequency', ['weekly', 'fortnightly', 'monthly'], index=2)
        first_payment_date = st.date_input('First Payment Date', value=pd.to_datetime('2025-01-01'))
        
    sliced_period = st.number_input('Get amortization after specific year', min_value=0, value=0)
    sliced_date = None
    
    if sliced_period > 0:
        
        # calculate sliced date by taking the first payment date and adding the sliced period in years
        sliced_date = first_payment_date + pd.DateOffset(years=sliced_period)
        sliced_date = sliced_date.strftime('%Y-%m-%d')
        
    else:
        sliced_date = first_payment_date
        sliced_date = sliced_date.strftime('%Y-%m-%d')
        
    
    
    
# with st.container(border=True):
#     st.markdown("### Interest Rate Configuration")
    
    
#     interest_type = st.selectbox('Interest Type', ['Fixed', 'Variable'])
    
#     if interest_type == 'Variable':
 
#         col1, col2 = st.columns(2)
        
#         with col1:
            
#             years_rate_remains_fixed = st.number_input('Years Rate Remains Fixed', min_value=0, value=1)
#             interest_rate_cap = st.number_input('Interest Rate Cap (%)', min_value=0, value=12)
#             interest_rate_minimum = st.number_input('Interest Rate Minimum (%)', min_value=0, value=4)
            
#         with col2:
#             periods_between_adjustments = st.number_input('Periods Between Adjustments (Months)', min_value=0, value=12)
#             estimated_adjustments = st.number_input('Estimated Adjustments (%)', min_value=0.0, value=0.25, step=0.25)
            

with st.container(border=True):
    st.markdown("### Interest Rate Configuration (Table Mode)")
    
    interest_type = st.selectbox('Interest Type', ['Fixed', 'Variable'], key='interest-table')
    
    if interest_type == 'Variable':
        
        interest_table = pd.DataFrame(columns=['Interest Rate', 'Length Period before next Adjustment'], data=[[interest_rate, 12]]*1)
        
        interest_table = st.data_editor(interest_table, hide_index=True, num_rows="dynamic")
        
        # drop rows with NaN values
        interest_table = interest_table.dropna()
        
        interest_table_dict = interest_table.to_dict()
        
        # print(interest_table.to_dict())

            
with st.container(border=True):
    
    st.markdown("### Extra Repayment / Drawdown Adjustments")
    
    # create empty dataframe with 2 columns of Event Date and Adjustment Amount with 5 empty rows 
    adjustment_df = pd.DataFrame(columns=['Event Date', 'Adjustment Amount'], data=[[date(2025, 1, 1), 0]]*1)
    
    
    adjustment_df = st.data_editor(
                    adjustment_df,
                    column_config={
                        "Event Date": st.column_config.DateColumn(
                            "Event Date",
                            # min_value=adjustment_df(1900, 1, 1),
                            # max_value=adjustment_df(2030, 1, 1),
                            format="DD.MM.YYYY",
                            step=1,
                        ),
                    },
                    hide_index=True,
                    num_rows="dynamic")
    
    
    
    adjustment_df['Event Date'] = pd.to_datetime(adjustment_df['Event Date'])
    adjustment_df['Event Date'] = adjustment_df['Event Date'].dt.strftime('%Y-%m-%d')
    
    if (adjustment_df['Adjustment Amount'] == 0).all():
        adjustment_df = None 
        
    # loan_term_mode = st.selectbox('Loan Term Mode', ['fixed', 'adjusted'], index=1)
    loan_term_mode = 'adjusted'
    
    # loan_term_mode = 'adjusted'
    
    # st.write(adjustment_df)
    
            
# if st.button('Calculate'):     
#     if interest_type == 'Fixed':
#         calculator = LoanCalculator(interest_rate)

#         # Generate the amortization schedule
#         schedule_df = calculator.calculate_amortization_schedule(
#             loan_amount,
#             loan_term,  # 15 years
#             first_payment_date
#         )
        
#     elif interest_type == 'Variable':
#         calculator = LoanCalculator(interest_rate, interest_rate_cap, interest_rate_minimum)

#         # Generate the amortization schedule
#         schedule_df = calculator.calculate_amortization_schedule(
#             loan_amount,
#             loan_term,  # 15 years
#             first_payment_date,
#             years_rate_remains_fixed,  
#             periods_between_adjustments,  # Adjust every 6 months
#             estimated_adjustments  # Adjust by 0.5% per adjustment period
#         )

#     st.dataframe(schedule_df)
    
#     fig = calculator.amortization_plot(schedule_df)
    
#     st.plotly_chart(fig)
    
    
if st.button('Calculate'):
    api_url = "http://localhost:5000/calculate_amortization_schedule"  # Flask app URL

    # Convert date to string
    first_payment_date_str = first_payment_date.strftime('%Y-%m-%d')  # Convert to "YYYY-MM-DD" format

    if interest_type == 'Fixed':
        payload = {
            "loan_amount": loan_amount,
            "loan_term": loan_term,  # 15 years
            "repayment_amount": repayment_amount,
            "first_payment_date": first_payment_date_str,
            "interest_type": "Fixed",
            "interest_rate": interest_rate,
            "adjustment_df": adjustment_df.to_dict(orient='records') if adjustment_df is not None else None,
            "sliced_date": sliced_date,
            "loan_term_mode": loan_term_mode,
            "payment_frequency": payment_frequency,
            'interest_table': None,
            'type': type
        }
    elif interest_type == 'Variable':
        payload = {
            "loan_amount": loan_amount,
            "loan_term": loan_term,  # 15 years
            "repayment_amount": repayment_amount,
            "first_payment_date": first_payment_date_str,
            "interest_type": "Variable",
            "interest_rate": interest_rate,
            # "interest_rate_cap": interest_rate_cap,
            # "interest_rate_minimum": interest_rate_minimum,
            # "years_rate_remains_fixed": years_rate_remains_fixed,
            # "periods_between_adjustments": periods_between_adjustments,
            # "estimated_adjustments": estimated_adjustments,
            "adjustment_df": adjustment_df.to_dict(orient='records') if adjustment_df is not None else None,
            "sliced_date": sliced_date,
            "loan_term_mode": loan_term_mode,
            "payment_frequency": payment_frequency,
            'interest_table': interest_table_dict,
            'type': type
        }
        
    # print(payload)

    # Send POST request to Flask API
    response = requests.post(api_url, json=payload)
    
    # print("PRINT THIS")
    # print(response.json())

    response_data = response.json()
    # st.write(response_data)
    response_df = pd.DataFrame(response_data['schedule_df'])
    response_df_sliced = pd.DataFrame(response_data['sliced_schedule_df'])
    
    st.dataframe(response_df, column_order = ('No.', 'Period', 'Balance', 'Balance Adjustment', 'Interest Rate', 'Interest Due', 'Principal Paid', 'Payment Due', 'Year', 'Remark'), hide_index=True)
    
    
    fig = LoanCalculator(interest_rate).amortization_plot(response_df)
    
    fig_loan_balance = LoanCalculator(interest_rate).loan_balance_plot(response_df)
    
    
    st.plotly_chart(fig)
    
    st.plotly_chart(fig_loan_balance)
    
    st.divider()
    
    st.markdown("### Sliced Amortization Schedule")
    
    st.dataframe(response_df_sliced)
    
    fig2 = LoanCalculator(interest_rate).amortization_plot(response_df_sliced)
    
    fig2_loan_balance = LoanCalculator(interest_rate).loan_balance_plot(response_df_sliced)
    
    
    st.plotly_chart(fig2)
    

    st.plotly_chart(fig2_loan_balance)

    # if response.status_code == 200:
    #     # Parse JSON response
    #     schedule_df = pd.DataFrame(response.json())
    #     st.write(schedule_df)
    # else:
    #     st.error(f"Error: {response.json().get('error', 'Unknown error')}")