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

    def calculate_amortization_schedule_by_loan_term(self, loan_amount, loan_term, first_payment_date,
                                                     adjustment_df=None, loan_term_mode="fixed", 
                                                     payment_frequency="monthly", interest_type="Fixed",
                                                     variable_interest_configuration=None):
        # Validate payment frequency
        valid_frequencies = {"monthly": 12, "weekly": 52, "fortnightly": 26}
        if payment_frequency not in valid_frequencies: 
            raise ValueError(f"Invalid payment frequency. Choose from {list(valid_frequencies.keys())}.")

        # Validate variable interest configuration
        if interest_type == "Variable" and not variable_interest_configuration:
            raise ValueError("Variable interest configuration must be provided for 'Variable' interest type.")

        # Determine the number of periods per year
        periods_per_year = valid_frequencies[payment_frequency]

        # Convert first payment date to datetime
        first_payment_date = pd.to_datetime(first_payment_date)

        # Initialize variables
        total_periods = loan_term * periods_per_year
        remaining_balance = loan_amount
        current_interest_rate = self.annual_interest_rate

        # Prepare adjustments
        if adjustment_df is not None:
            adjustment_df = self.process_adjustments(adjustment_df)

        # Initialize variable interest configuration tracking
        if interest_type == "Variable":
            interest_rate_schedule = variable_interest_configuration["Interest Rate"]
            length_period_schedule = variable_interest_configuration["Length Period before next Adjustment"]
            current_stage = 0
            periods_remaining_in_stage = length_period_schedule.get(str(current_stage), float("inf"))
            current_interest_rate = interest_rate_schedule.get(str(current_stage), self.annual_interest_rate)

        # Calculate initial payment
        period_interest_rate = (current_interest_rate / 100) / periods_per_year
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
                                                        pv=remaining_balance).round()))
                
                print("Remaining Period", remaining_periods)
                
                total_periods = period + remaining_periods - 1

            # Adjust interest rate if variable
            if interest_type == "Variable":
                if periods_remaining_in_stage <= 0:
                    current_stage += 1
                    current_interest_rate = interest_rate_schedule.get(str(current_stage), current_interest_rate)
                    periods_remaining_in_stage = length_period_schedule.get(str(current_stage), float("inf"))

                periods_remaining_in_stage -= 1
                period_interest_rate = current_interest_rate / 100 / periods_per_year

            # Calculate PMT for this period
            if loan_term_mode == "fixed" or (adjustment_df is None or adjustment_df.empty):
                pmt = npf.pmt(rate=period_interest_rate, nper=total_periods - period + 1, pv=-remaining_balance)
            else:
                pmt = npf.pmt(rate=period_interest_rate, nper=total_periods - period + 1, pv=-remaining_balance)
                initial_payment = pmt

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

        # Convert schedule to DataFrame
        schedule_df = pd.DataFrame(schedule)
        return schedule_df

    def calculate_amortization_schedule_by_repayment_amount(self, loan_amount, repayment_amount, first_payment_date,
                                                            adjustment_df=None, loan_term_mode="adjusted", 
                                                            payment_frequency="monthly", interest_type="Fixed",
                                                            variable_interest_configuration=None):
        # Validate payment frequency
        valid_frequencies = {"monthly": 12, "weekly": 52, "fortnightly": 26}
        if payment_frequency not in valid_frequencies:
            raise ValueError(f"Invalid payment frequency. Choose from {list(valid_frequencies.keys())}.")

        # Validate variable interest configuration
        if interest_type == "Variable" and not variable_interest_configuration:
            raise ValueError("Variable interest configuration must be provided for 'Variable' interest type.")

        # Determine the number of periods per year
        periods_per_year = valid_frequencies[payment_frequency]

        # Convert first payment date to datetime
        first_payment_date = pd.to_datetime(first_payment_date)

        # Initialize variables
        period_interest_rate = (self.annual_interest_rate / 100) / periods_per_year
        try:
            total_periods = int(npf.nper(rate=period_interest_rate, pmt=-repayment_amount, pv=loan_amount).round())
        except ValueError as e:
            raise ValueError(f"Invalid repayment amount: {e}")

        remaining_balance = loan_amount
        current_interest_rate = self.annual_interest_rate

        # Prepare adjustments
        if adjustment_df is not None:
            adjustment_df = self.process_adjustments(adjustment_df)

        # Initialize variable interest configuration tracking
        if interest_type == "Variable":
            interest_rate_schedule = variable_interest_configuration["Interest Rate"]
            length_period_schedule = variable_interest_configuration["Length Period before next Adjustment"]
            current_stage = 0
            periods_remaining_in_stage = length_period_schedule.get(str(current_stage), float("inf"))
            current_interest_rate = interest_rate_schedule.get(str(current_stage), self.annual_interest_rate)

        # Create an empty list to hold schedule data
        schedule = []
        
        print("do we get here", total_periods)

        for period in range(1, total_periods + 1):
            
           
            
            # Generate the correct period date
            if payment_frequency == "monthly":
                current_date = first_payment_date + pd.DateOffset(months=period - 1)
            else:
                current_date = first_payment_date + timedelta(days=(365 // periods_per_year) * (period - 1))

            # Check for balance adjustment
            if adjustment_df is not None:
                adjustments = adjustment_df[
                    (adjustment_df['Event Date'] > (current_date - timedelta(days=(365 // periods_per_year)))) &
                    (adjustment_df['Event Date'] <= current_date)
                ]
                balance_adjustment = adjustments['Adjustment Amount'].sum() if not adjustments.empty else 0
            else:
                balance_adjustment = 0

            # Apply adjustments and recalculate loan term if necessary
            remaining_balance += balance_adjustment

            if loan_term_mode == "adjusted" and adjustment_df is not None and not adjustment_df.empty and balance_adjustment != 0:
                try:
                    remaining_periods = max(1, int(npf.nper(rate=period_interest_rate, 
                                                            pmt=-repayment_amount, 
                                                            pv=remaining_balance).round()))
                except ValueError:
                    raise ValueError(f"Adjustment caused invalid remaining balance: {remaining_balance}")
                total_periods = period + remaining_periods - 1

            # Adjust interest rate if variable
            if interest_type == "Variable":
                if periods_remaining_in_stage <= 0:
                    current_stage += 1
                    current_interest_rate = interest_rate_schedule.get(str(current_stage), current_interest_rate)
                    periods_remaining_in_stage = length_period_schedule.get(str(current_stage), float("inf"))

                periods_remaining_in_stage -= 1
                period_interest_rate = current_interest_rate / 100 / periods_per_year

            # Calculate interest due and principal paid
            interest_due = remaining_balance * period_interest_rate
            principal_paid = repayment_amount - interest_due

            # Handle final period adjustments
            if remaining_balance - principal_paid <= 0:
                principal_paid = remaining_balance
                repayment_amount = principal_paid + interest_due
                remaining_balance = 0

            # Update remaining balance
            remaining_balance -= principal_paid

            # Append data to schedule
            remark = "original" if period <= total_periods else "extension"
            schedule.append({
                "No.": period,
                "Period": current_date.strftime("%Y-%m-%d"),
                "Year": current_date.year,
                "Interest Rate": round(current_interest_rate, 2),
                "Interest Due": round(interest_due, 2),
                "Principal Paid": round(principal_paid, 2),
                "Payment Due": round(repayment_amount, 2),
                "Balance Adjustment": round(balance_adjustment, 2),
                "Balance": round(max(0, remaining_balance), 2),
                "Remark": remark
            })

            # Debug logging
            print(f"Period: {period}, Remaining Balance: {remaining_balance}, PMT: {repayment_amount}, Total Periods: {total_periods}")

            # Stop the loop if balance is fully paid off
            if remaining_balance <= 0:
                break

        # Convert schedule to DataFrame
        schedule_df = pd.DataFrame(schedule)

        

        # Check for empty schedule
        if schedule_df.empty:
            raise ValueError("Amortization schedule generation failed; the schedule is empty.")
        
        

        return schedule_df


    def calculate_amortization(self, type, **kwargs):
        if type == "By Loan Term":
            
            # print("Managed to get here lad")
            
            return self.calculate_amortization_schedule_by_loan_term(**kwargs)
        elif type == "By Repayment Amount":
            # print("Managed to get here lads")
            return self.calculate_amortization_schedule_by_repayment_amount(**kwargs)
        else:
            raise ValueError("Invalid type. Choose 'By Loan Term' or 'By Repayment Amount'.")


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

 