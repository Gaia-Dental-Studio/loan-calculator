import pandas as pd
import streamlit as st
import numpy as np
from model import LoanCalculator
import requests

st.title('Loan Calculator')


with st.container(border=True):
    st.markdown("### Loan Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        loan_amount = st.number_input('Loan Amount', min_value=0, value=150000)
        interest_rate = st.number_input('Annual Interest Rate (%)', min_value=0.0, value=5.5, step=0.25)
        loan_term = st.number_input('Loan Term (years)', min_value=0, value=30)
    
    with col2:
        compound_period = st.selectbox('Compound Period', ['Monthly'])
        payment_frequency = st.selectbox('Payment Frequency', ['Monthly'])
        first_payment_date = st.date_input('First Payment Date', value=pd.to_datetime('2025-01-01'))
        
    
with st.container(border=True):
    st.markdown("### Interest Rate Configuration")
    
    
    interest_type = st.selectbox('Interest Type', ['Fixed', 'Variable'])
    
    if interest_type == 'Variable':
 
        col1, col2 = st.columns(2)
        
        with col1:
            
            years_rate_remains_fixed = st.number_input('Years Rate Remains Fixed', min_value=0, value=1)
            interest_rate_cap = st.number_input('Interest Rate Cap (%)', min_value=0, value=12)
            interest_rate_minimum = st.number_input('Interest Rate Minimum (%)', min_value=0, value=4)
            
        with col2:
            periods_between_adjustments = st.number_input('Periods Between Adjustments (Months)', min_value=0, value=12)
            estimated_adjustments = st.number_input('Estimated Adjustments (%)', min_value=0.0, value=0.25, step=0.25)
            
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
            "first_payment_date": first_payment_date_str,
            "interest_type": "Fixed",
            "interest_rate": interest_rate
        }
    elif interest_type == 'Variable':
        payload = {
            "loan_amount": loan_amount,
            "loan_term": loan_term,  # 15 years
            "first_payment_date": first_payment_date_str,
            "interest_type": "Variable",
            "interest_rate": interest_rate,
            "interest_rate_cap": interest_rate_cap,
            "interest_rate_minimum": interest_rate_minimum,
            "years_rate_remains_fixed": years_rate_remains_fixed,
            "periods_between_adjustments": periods_between_adjustments,
            "estimated_adjustments": estimated_adjustments
        }

    # Send POST request to Flask API
    response = requests.post(api_url, json=payload)

    response_df = pd.DataFrame(response.json())
    
    st.dataframe(response_df)
    
    fig = LoanCalculator(interest_rate).amortization_plot(response_df)
    
    st.plotly_chart(fig)
    

    # if response.status_code == 200:
    #     # Parse JSON response
    #     schedule_df = pd.DataFrame(response.json())
    #     st.write(schedule_df)
    # else:
    #     st.error(f"Error: {response.json().get('error', 'Unknown error')}")