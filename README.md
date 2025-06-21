
# Personal Finance Tracker

A web-based personal finance tracker built with Flask, MongoDB, JWT authentication, and Gemini AI for smart spending predictions and advice. This app enables users to manage budgets, track expenses, set financial goals, and get AI-powered financial insights.

---

## Features

- **User Authentication:** Secure login/logout with JWT tokens.
- **Dashboard:** Overview of current balance, recent transactions, budgets, and financial goals.
- **Expense Tracking:** Add, view, and analyze expenses.
- **Budget Management:** Create, view, and delete category-wise budgets.
- **Financial Goals:** Set, update, and delete savings or investment goals.
- **Spending Prediction:** AI-powered predictions and advice via Gemini API.
- **Data Security:** Uses bcrypt for password hashing and JWT for secure authentication.
- **RESTful API:** JSON endpoints for all major CRUD operations.
- **Responsive UI:** Renders with Flask templates (`dashboard.html`, `budgets.html`, etc.).

---

## Getting Started

### Prerequisites

- Python 3.8+
- MongoDB (local or Atlas)
- [Gemini API key](https://aistudio.google.com/app/apikey)
- [pipenv](https://pipenv.pypa.io/en/latest/) or `pip`

### Installation

1. **Clone the repository:**
   ```sh
   git clone https://github.com/beingaditya18/Personal-Fianance-Tracker.git
   cd Personal-Fianance-Tracker
   ```

2. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**

   Create a `.env` file in the root directory:
   ```
   MONGO_URI=mongodb://localhost:27017/finance_tracker
   JWT_SECRET_KEY=your_jwt_secret_key
   GEMINI_API_KEY=your_gemini_api_key
   ```

4. **Start MongoDB:**
   - Locally: `mongod`
   - Or use a MongoDB Atlas URI

5. **Run the app:**
   ```sh
   python app.py
   ```
   The app will be available at [http://127.0.0.1:5000/](http://127.0.0.1:5000/)

---

## API Endpoints

### Authentication & User
- `/logout` : Log out user (clears JWT cookie)

### Dashboard
- `/dashboard` : Main dashboard (requires login)

### Budgets
- `GET /budgets` : View budgets
- `POST /budgets/create` : Create a new budget (JSON)
- `POST /budgets/delete/<budget_id>` : Delete a budget

### Financial Goals
- `GET /goals` : View financial goals
- `POST /goals/create` : Create a new goal (JSON)
- `POST /goals/update/<goal_id>` : Update goal's current amount
- `POST /goals/delete/<goal_id>` : Delete a goal

### Spending Prediction
- `GET /prediction` : Get data summary for predictions
- `POST /predict/spending` : Get AI-powered advice/prediction (JSON: `{ "prompt": "..." }`)

---

## AI-Powered Predictions

To use Gemini-based financial advice, ensure your `GEMINI_API_KEY` is set in `.env`.
Send a POST request to `/predict/spending` with your question or message in the `prompt` field.

Example:
```json
{
  "prompt": "How can I reduce my monthly dining expenses?"
}
```

---

## Project Structure

```
app.py
templates/
    dashboard.html
    budgets.html
    goals.html
    create_budget.html
    create_goal.html
    404.html
    500.html
static/
    (CSS, JS, assets)
requirements.txt
.env.example
README.md
```

---

## Environment Variables

- `MONGO_URI`: MongoDB connection string
- `JWT_SECRET_KEY`: Secret key for JWT token encoding/decoding
- `GEMINI_API_KEY`: API key for Gemini AI (Google Generative AI)

---

## Contributing

Pull requests are welcome! Please open issues for bugs and feature requests.

---

## License

MIT License

---

## Author

[beingaditya18](https://github.com/beingaditya18)
