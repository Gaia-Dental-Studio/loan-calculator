import pandas as pd
import numpy_financial as npf
from datetime import datetime, timedelta
import plotly.graph_objects as go

class LoanCalculator:
    def __init__(self, annual_interest_rate, interest_rate_cap=12, interest_rate_minimum=4):
        self.annual_interest_rate = annual_interest_rate  # Initial interest rate (APR)
        self.interest_rate_cap = interest_rate_cap  # Maximum interest rate cap
        self.interest_rate_minimum = interest_rate_minimum  # Minimum interest rate cap

    def process_adjustments(self, adjustment_df):
        """
        Process and validate repayment/drawdown adjustments.
        
        adjustment_df: DataFrame with columns ['Event Date', 'Adjustment Amount']
        """
        if not all(col in adjustment_df.columns for col in ['Event Date', 'Adjustment Amount']):
            raise ValueError("Adjustment DataFrame must contain 'Event Date' and 'Adjustment Amount' columns.")

        # Convert Event Date to datetime
        adjustment_df['Event Date'] = pd.to_datetime(adjustment_df['Event Date'])
        
        # Sort by Event Date
        adjustment_df = adjustment_df.sort_values(by='Event Date')
        return adjustment_df

    def calculate_amortization_schedule(self, loan_amount, loan_term, first_payment_date,
                                        years_rate_remains_fixed=1, periods_between_adjustments=12,
                                        estimated_adjustments=0, adjustment_df=None, 
                                        loan_term_mode="fixed", payment_frequency="monthly"):
        # Validate payment frequency
        valid_frequencies = {"monthly": 12, "weekly": 52, "fortnightly": 26}
        if payment_frequency not in valid_frequencies:
            raise ValueError(f"Invalid payment frequency. Choose from {list(valid_frequencies.keys())}.")

        # Determine the number of periods per year
        periods_per_year = valid_frequencies[payment_frequency]

        # Convert first payment date to datetime
        first_payment_date = pd.to_datetime(first_payment_date)

        # Initialize variables
        total_periods = loan_term * periods_per_year
        remaining_balance = loan_amount
        current_interest_rate = self.annual_interest_rate
        adjustment_start_period = (years_rate_remains_fixed * periods_per_year) - periods_per_year

        # Prepare adjustments
        if adjustment_df is not None:
            adjustment_df = self.process_adjustments(adjustment_df)

        # Calculate initial payment
        period_interest_rate = (self.annual_interest_rate / 100) / periods_per_year
        initial_payment = npf.pmt(rate=period_interest_rate, nper=total_periods, pv=-loan_amount)

        # Create an empty list to hold schedule data
        schedule = []

        for period in range(1, total_periods + 1):
            # Generate the correct period date
            if payment_frequency == "monthly":
                current_date = first_payment_date + pd.DateOffset(months=period - 1)
            else:
                current_date = first_payment_date + timedelta(days=(365 // periods_per_year) * (period - 1))

            # Check for balance adjustment
            if adjustment_df is not None:
                adjustments = adjustment_df[(adjustment_df['Event Date'] > (current_date - timedelta(days=(365 // periods_per_year)))) &
                                             (adjustment_df['Event Date'] <= current_date)]
                balance_adjustment = adjustments['Adjustment Amount'].sum() if not adjustments.empty else 0
            else:
                balance_adjustment = 0

            # Apply adjustments and recalculate loan term if necessary
            remaining_balance += balance_adjustment

            if loan_term_mode == "adjusted" and adjustment_df is not None and not adjustment_df.empty and balance_adjustment != 0:
                remaining_periods = max(1, int(npf.nper(rate=period_interest_rate, 
                                                        pmt=-initial_payment, 
                                                        pv=-remaining_balance).round()))
                total_periods = period + remaining_periods - 1

            # Calculate PMT for this period
            if loan_term_mode == "fixed" or (adjustment_df is None or adjustment_df.empty):
                pmt = npf.pmt(rate=period_interest_rate, nper=total_periods - period + 1, pv=-remaining_balance)
            else:
                pmt = initial_payment

            # Calculate interest due and principal paid
            interest_due = remaining_balance * period_interest_rate
            principal_paid = pmt - interest_due

            # Handle final period adjustments
            if remaining_balance - principal_paid <= 0:
                principal_paid = remaining_balance
                pmt = principal_paid + interest_due
                remaining_balance = 0

            # Update remaining balance
            remaining_balance -= principal_paid

            # Append data to schedule
            remark = "original" if period <= loan_term * periods_per_year else "extension"
            schedule.append({
                "No.": period,
                "Period": current_date.strftime("%Y-%m-%d"),
                "Year": current_date.year,
                "Interest Rate": round(current_interest_rate, 2),
                "Interest Due": round(interest_due, 2),
                "Principal Paid": round(principal_paid, 2),
                "Payment Due": round(pmt, 2),
                "Balance Adjustment": round(balance_adjustment, 2),
                "Balance": round(max(0, remaining_balance), 2),
                "Remark": remark
            })

            # Stop the loop if balance is fully paid off
            if remaining_balance <= 0:
                break

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
            xaxis_title="Periods",
            yaxis_title="Amount ($)",
            barmode="stack",
            legend=dict(title="Components"),
            xaxis=dict(tickformat="%b-%Y")
        )

        return fig
