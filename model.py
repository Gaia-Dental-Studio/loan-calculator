import pandas as pd
import numpy_financial as npf
from datetime import datetime, timedelta
import plotly.graph_objects as go


class LoanCalculator:
    def __init__(self, annual_interest_rate, interest_rate_cap=12, interest_rate_minimum=4):
        self.annual_interest_rate = annual_interest_rate  # Initial interest rate (APR)
        self.interest_rate_cap = interest_rate_cap  # Maximum interest rate cap
        self.interest_rate_minimum = interest_rate_minimum  # Minimum interest rate cap

    def calculate_amortization_schedule(self, loan_amount, loan_term, first_payment_date,
                                        years_rate_remains_fixed=1, periods_between_adjustments=12,
                                        estimated_adjustments=0):
        # Convert first payment date to datetime
        first_payment_date = pd.to_datetime(first_payment_date)

        # Initialize variables
        total_periods = loan_term * 12
        remaining_balance = loan_amount
        current_interest_rate = self.annual_interest_rate
        adjustment_start_period = (years_rate_remains_fixed * 12) - 12 

        # Create an empty list to hold schedule data
        schedule = []

        for period in range(1, total_periods + 1):
            # Calculate monthly interest rate (APR-based)
            monthly_interest_rate = current_interest_rate / 12 / 100

            # Calculate PMT for this period
            pmt = npf.pmt(rate=monthly_interest_rate, nper=total_periods - period + 1, pv=-remaining_balance)

            # Calculate interest due and principal paid
            interest_due = remaining_balance * monthly_interest_rate
            principal_paid = pmt - interest_due

            # Update remaining balance
            remaining_balance -= principal_paid

            # Append data to schedule
            schedule.append({
                "No.": period,
                "Period": (first_payment_date + pd.DateOffset(months=period - 1)).strftime("%Y-%m-%d"),
                "Year": (first_payment_date + pd.DateOffset(months=period - 1)).year,
                "Interest Rate": current_interest_rate,
                "Interest Due": round(interest_due,2),
                "Principal Paid": round(principal_paid,2),
                "Payment Due": round(pmt,2),
                "Balance": round(max(0, remaining_balance),2),  # Avoid negative balances
            })

            # Adjust interest rate after the fixed period
            if period > adjustment_start_period and (period - adjustment_start_period) % periods_between_adjustments == 0:
                current_interest_rate += estimated_adjustments
                current_interest_rate = max(self.interest_rate_minimum, min(self.interest_rate_cap, current_interest_rate))

        # Convert schedule to DataFrame
        schedule_df = pd.DataFrame(schedule)
        return schedule_df
    
    
    def amortization_plot(self, schedule_df):
        # Create stacked bar chart using Plotly
        fig = go.Figure()
        
                # Add interest due stacked above principal paid
        fig.add_trace(go.Bar(
            x=schedule_df["Period"],
            y=schedule_df["Interest Due"],
            name="Interest Due",
            marker_color="#7201a8"
        ))

        # Add principal paid as the base bar
        fig.add_trace(go.Bar(
            x=schedule_df["Period"],
            y=schedule_df["Principal Paid"],
            name="Principal Paid",
            marker_color="#ed7953"
        ))



        # Update layout
        fig.update_layout(
            title="Amortization Schedule",
            xaxis_title="Months",
            yaxis_title="Amount ($)",
            barmode="stack",
            legend=dict(title="Components"),
            xaxis=dict(tickformat="%b-%Y")
        )

        return fig