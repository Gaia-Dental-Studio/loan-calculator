from flask import Flask, request, jsonify
from model import LoanCalculator
import pandas as pd

app = Flask(__name__)

@app.route('/calculate_amortization_schedule', methods=['POST'])
def calculate_amortization_schedule():
    try:
        # Get the JSON data from the request
        data = request.json

        # Extract variables from the request
        loan_amount = data['loan_amount']
        loan_term = data.get('loan_term', None)
        repayment_amount = data.get('repayment_amount', None)
        first_payment_date = data['first_payment_date']
        interest_type = data['interest_type']
        adjustment_df = data.get('adjustment_df', None)
        sliced_date = pd.to_datetime(data.get('sliced_date')) if data.get('sliced_date') else None
        loan_term_mode = data['loan_term_mode']
        payment_frequency = data['payment_frequency']
        type = data['type']
        interest_table = data.get('interest_table', None)
        
        print(interest_table)
        
        # print(repayment_amount)

        # Process adjustment_df if provided
        if adjustment_df:
            adjustment_df = pd.DataFrame(adjustment_df)
            if not {'Event Date', 'Adjustment Amount'}.issubset(adjustment_df.columns):
                raise ValueError("Adjustment DataFrame must contain 'Event Date' and 'Adjustment Amount'.")
            adjustment_df['Event Date'] = pd.to_datetime(adjustment_df['Event Date'])

        # Initialize LoanCalculator and calculate schedule
        calculator = LoanCalculator(annual_interest_rate=data['interest_rate'])

        if type == "By Loan Term":
            schedule_df = calculator.calculate_amortization(
                type=type,
                loan_amount=loan_amount,
                # repayment_amount=repayment_amount,
                loan_term=loan_term,
                first_payment_date=first_payment_date,
                adjustment_df=adjustment_df,
                loan_term_mode=loan_term_mode,
                payment_frequency=payment_frequency,
                interest_type=interest_type,
                variable_interest_configuration=interest_table
            )
            
        else:
            # print("this supposed to run")
            
            schedule_df = calculator.calculate_amortization(
                type=type,
                loan_amount=loan_amount,
                repayment_amount=repayment_amount,
                # loan_term=loan_term,
                first_payment_date=first_payment_date,
                adjustment_df=adjustment_df,
                loan_term_mode=loan_term_mode,
                payment_frequency=payment_frequency,
                interest_type=interest_type,
                variable_interest_configuration=interest_table
            )
        
        

        # Filter by sliced_date if applicable
        schedule_df['Period'] = pd.to_datetime(schedule_df['Period'])
        if sliced_date:
            sliced_schedule_df = schedule_df[schedule_df['Period'] >= sliced_date]
        else:
            sliced_schedule_df = schedule_df

        # Format dates for JSON output
        schedule_df['Period'] = schedule_df['Period'].dt.strftime('%d-%m-%Y')
        sliced_schedule_df['Period'] = sliced_schedule_df['Period'].dt.strftime('%d-%m-%Y')

        # Convert DataFrames to JSON and return as a response
        return jsonify({
            'schedule_df': schedule_df.to_dict(orient='records'),
            'sliced_schedule_df': sliced_schedule_df.to_dict(orient='records')
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
