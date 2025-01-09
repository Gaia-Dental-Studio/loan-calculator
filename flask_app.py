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
        loan_term = data['loan_term']
        first_payment_date = data['first_payment_date']
        interest_type = data['interest_type']
        adjustment_df = data['adjustment_df']
        sliced_date = data['sliced_date']
        sliced_date = pd.to_datetime(sliced_date) if sliced_date is not None else None
        loan_term_mode = data['loan_term_mode']
        
        if adjustment_df is not None:
            adjustment_df = pd.DataFrame(adjustment_df)
            
            adjustment_df['Event Date'] = pd.to_datetime(adjustment_df['Event Date'])

        if interest_type == 'Fixed':
            interest_rate = data['interest_rate']
            calculator = LoanCalculator(interest_rate)
            schedule_df = calculator.calculate_amortization_schedule(
                loan_amount,
                loan_term,
                first_payment_date,
                adjustment_df=adjustment_df,
                loan_term_mode=loan_term_mode
            )
        elif interest_type == 'Variable':
            interest_rate = data['interest_rate']
            interest_rate_cap = data['interest_rate_cap']
            interest_rate_minimum = data['interest_rate_minimum']
            years_rate_remains_fixed = data['years_rate_remains_fixed']
            periods_between_adjustments = data['periods_between_adjustments']
            estimated_adjustments = data['estimated_adjustments']

            calculator = LoanCalculator(
                interest_rate,
                interest_rate_cap,
                interest_rate_minimum
            )
            schedule_df = calculator.calculate_amortization_schedule(
                loan_amount,
                loan_term,
                first_payment_date,
                years_rate_remains_fixed,
                periods_between_adjustments,
                estimated_adjustments,
                adjustment_df,
                loan_term_mode
            )
        else:
            return jsonify({'error': 'Invalid interest type specified'}), 400
        
        # slice the schedule_df post sliced_date
        schedule_df['Period'] = pd.to_datetime(schedule_df['Period'])
        print("MANAGED TO GET HERE")
        
        
        sliced_schedule_df = schedule_df[schedule_df['Period'] >= sliced_date] if sliced_date is not None else schedule_df
        
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
