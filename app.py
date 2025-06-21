from flask import Flask, request, jsonify, render_template, make_response, redirect, url_for
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, decode_token
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
import datetime
import google.generativeai as genai
import os  # For environment variables
from dotenv import load_dotenv

app = Flask(__name__)

# Configuration
load_dotenv()
app.config['MONGO_URI'] = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/finance_tracker')
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'your_jwt_secret_key')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

# Initialize Gemini (only if API key is available)
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-pro')
else:
    print("Warning: GEMINI_API_KEY not found. Gemini functionality will be disabled.")
    model = None

# Extensions
mongo = PyMongo(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

# Collections
users_collection = mongo.db.users
expenses_collection = mongo.db.expenses
budgets_collection = mongo.db.budgets
goals_collection = mongo.db.goals

@app.route('/')
def home():
    # Redirect to the dashboard  
    return redirect(url_for('dashboard'))

# Removed the /login route

@app.route('/logout')
def logout():
    response = make_response(redirect(url_for('home')))
    response.delete_cookie('access_token', path='/')
    return response

@app.route('/dashboard')
@jwt_required()
def dashboard():
    user_id = get_jwt_identity()
    user = users_collection.find_one({"_id": ObjectId(user_id)})
    expenses = expenses_collection.find({"user": ObjectId(user_id)})
    expenses_list = list(expenses)

    total_income = user.get('income', 0)
    total_expenses = sum(exp.get('amount', 0) for exp in expenses_list)
    current_balance = total_income - total_expenses

    # Get recent transactions (last 5 as an example)
    recent_transactions = sorted(expenses_list, key=lambda x: x.get('date', datetime.datetime.now()), reverse=True)[:5]
    recent_transactions_formatted = [{
        "type": exp.get('title', 'Unknown'),
        "amount": exp.get('amount', 0),
        "date": exp.get('date', datetime.datetime.now()).strftime('%Y-%m-%d')
    } for exp in recent_transactions]

    # Fetch budgets summary
    budgets = budgets_collection.find({"user": ObjectId(user_id)})
    budgets_summary = []
    for budget in budgets:
        spent = sum(exp.get('amount', 0) for exp in expenses_list if exp.get('title', '').lower() == budget.get('category', '').lower())
        budgets_summary.append({
            "category": budget.get('category', 'Unknown'),
            "budget": budget.get('amount', 0),
            "spent": spent,
            "progress": (spent / budget.get('amount', 1)) * 100 if budget.get('amount', 1) > 0 else 0
        })

    # Fetch financial goals
    financial_goals = list(goals_collection.find({"user": ObjectId(user_id)}))

    return render_template('dashboard.html',
                           user=user,
                           total_income=total_income,
                           total_expenses=total_expenses,
                           current_balance=current_balance,
                           recent_transactions=recent_transactions_formatted,
                           budgets_summary=budgets_summary,
                           financial_goals=financial_goals)

# --- Budgets ---

@app.route('/budgets', methods=['GET'])
@jwt_required()
def view_budgets():
    user_id = get_jwt_identity()
    budgets = budgets_collection.find({"user": ObjectId(user_id)})
    budgets_list = [{
        "id": str(budget["_id"]),
        "category": budget["category"],
        "amount": budget["amount"]
    } for budget in budgets]
    return render_template('budgets.html', budgets=budgets_list)

@app.route('/budgets/create', methods=['GET'])
@jwt_required()
def create_budget_page():
    return render_template('create_budget.html')

@app.route('/budgets/create', methods=['POST'])
@jwt_required()
def create_budget():
    data = request.get_json()
    user_id = get_jwt_identity()
    budget = {
        "user": ObjectId(user_id),
        "category": data['category'],
        "amount": float(data['amount'])
    }
    try:
        budgets_collection.insert_one(budget)
        return jsonify({"message": "Budget created successfully!"}), 201
    except Exception as e:
        return jsonify({"message": f"Failed to create budget: {str(e)}"}), 500

@app.route('/budgets/delete/<budget_id>', methods=['POST'])
@jwt_required()
def delete_budget(budget_id):
    user_id = get_jwt_identity()
    try:
        result = budgets_collection.delete_one({"_id": ObjectId(budget_id), "user": ObjectId(user_id)})
        if result.deleted_count > 0:
            return jsonify({"message": "Budget deleted successfully!"}), 200
        else:
            return jsonify({"message": "Budget not found or you don't have permission to delete it."}), 404
    except Exception as e:
        return jsonify({"message": f"Failed to delete budget: {str(e)}"}), 500

# --- Financial Goals ---

@app.route('/goals', methods=['GET'])
@jwt_required()
def view_goals():
    user_id = get_jwt_identity()
    goals = goals_collection.find({"user": ObjectId(user_id)})
    goals_list = [{
        "id": str(goal["_id"]),
        "title": goal["title"],
        "target_amount": goal["target_amount"],
        "current_amount": goal["current_amount"]
    } for goal in goals]
    return render_template('goals.html', goals=goals_list)

@app.route('/goals/create', methods=['GET'])
@jwt_required()
def create_goal_page():
    return render_template('create_goal.html')

@app.route('/goals/create', methods=['POST'])
@jwt_required()
def create_goal():
    data = request.get_json()
    user_id = get_jwt_identity()
    goal = {
        "user": ObjectId(user_id),
        "title": data['title'],
        "target_amount": float(data['target_amount']),
        "current_amount": float(data.get('current_amount', 0))
    }
    try:
        goals_collection.insert_one(goal)
        return jsonify({"message": "Financial goal created successfully!"}), 201
    except Exception as e:
        return jsonify({"message": f"Failed to create financial goal: {str(e)}"}), 500

@app.route('/goals/update/<goal_id>', methods=['POST'])
@jwt_required()
def update_goal(goal_id):
    data = request.get_json()
    user_id = get_jwt_identity()
    try:
        result = goals_collection.update_one(
            {"_id": ObjectId(goal_id), "user": ObjectId(user_id)},
            {"$set": {"current_amount": float(data['current_amount'])}},
        )
        if result.modified_count > 0:
            return jsonify({"message": "Financial goal updated successfully!"}), 200
        else:
            return jsonify({"message": "Financial goal not found or you don't have permission to update it."}), 404
    except Exception as e:
        return jsonify({"message": f"Failed to update financial goal: {str(e)}"}), 500

@app.route('/goals/delete/<goal_id>', methods=['POST'])
@jwt_required()
def delete_goal(goal_id):
    user_id = get_jwt_identity()
    try:
        result = goals_collection.delete_one({"_id": ObjectId(goal_id), "user": ObjectId(user_id)})
        if result.deleted_count > 0:
            return jsonify({"message": "Financial goal deleted successfully!"}), 200
        else:
            return jsonify({"message": "Financial goal not found or you don't have permission to delete it."}), 404
    except Exception as e:
        return jsonify({"message": f"Failed to delete financial goal: {str(e)}"}), 500

# --- Spending Prediction ---

@app.route('/prediction')
@jwt_required()
def spending_prediction():
    user_id = get_jwt_identity()
    user = users_collection.find_one({"_id": ObjectId(user_id)})
    expenses = expenses_collection.find({"user": ObjectId(user_id)})
    expenses_list = list(expenses)
    now = datetime.datetime.now()
    last_month = now.replace(day=1) - datetime.timedelta(days=1)
    three_months_ago = now - datetime.timedelta(days=90)

    last_month_expenses = [exp['amount'] for exp in expenses_list if exp['date'].year == last_month.year and exp['date'].month == last_month.month]
    expenses_last_three_months = [exp['amount'] for exp in expenses_list if exp['date'] >= three_months_ago]

    average_spending = sum(expenses_last_three_months) / (len(expenses_last_three_months) or 1) if expenses_last_three_months else 0

    category_spending = {}
    for exp in expenses_list:
        category = exp.get('title', 'Other').lower() # Using lowercase for consistency
        category_spending[category] = category_spending.get(category, 0) + exp.get('amount', 0)

    top_category = max(category_spending, key=category_spending.get) if category_spending else "N/A"
    transaction_count = len(expenses_list)
    savings_rate = user.get('savings_rate', 0)

    user_data = {
        "last_month_spending": sum(last_month_expenses),
        "average_spending": average_spending,
        "top_category": top_category.capitalize(),
        "transaction_count": transaction_count,
        "savings_rate": savings_rate
    }
    return jsonify(user_data), 200

# --- Spending Prediction using Gemini ---
@app.route('/predict/spending', methods=['POST'])
@jwt_required()
def predict_spending():
    if not model:
        return jsonify({"message": "Gemini AI not configured. Please provide a valid GEMINI_API_KEY."}), 500

    data = request.get_json()
    user_id = get_jwt_identity()

    try:
        prompt = data.get("prompt", "").strip()
        if not prompt:
            return jsonify({"message": "Please provide a valid prompt for prediction."}), 400

        full_prompt = f"You are a financial assistant. Based on the user's message:\n\n{prompt}\n\nGive financial advice or predict upcoming spending behavior."

        response = model.generate_content(full_prompt)
        generated_text = response.text if hasattr(response, 'text') else str(response)

        return jsonify({
            "message": "Prediction generated successfully.",
            "prediction": generated_text
        }), 200
    except Exception as e:
        return jsonify({"message": f"Failed to generate prediction: {str(e)}"}), 500

# --- Error Handlers ---
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

# --- Run the Flask App ---
if __name__ == '__main__':
    app.run(debug=True)
