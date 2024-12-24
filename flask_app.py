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

        if interest_type == 'Fixed':
            interest_rate = data['interest_rate']
            calculator = LoanCalculator(interest_rate)
            schedule_df = calculator.calculate_amortization_schedule(
                loan_amount,
                loan_term,
                first_payment_date
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
                estimated_adjustments
            )
        else:
            return jsonify({'error': 'Invalid interest type specified'}), 400

        # Convert DataFrame to JSON and return as a response
        return jsonify(schedule_df.to_dict(orient='records'))

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
