# README.md
# Advanced SQL Agent API

This Flask-based API provides Advanced SQL query analysis and visualization services using LangChain and LangGraph.



![image](https://github.com/user-attachments/assets/cef48c8b-2129-4c27-b0c4-8bfd22e045ef)

## Prerequisites
- Ensure you have Python 3.9 or higher installed
- Make sure all required dependencies are installed

## Steps to Run the Application

1. Open a terminal or command prompt

2. Navigate to your project root directory:
   ```
   cd path/to/your/project
   ```

3. Activate your virtual environment (if you're using one):
   - On Windows:
     ```
     venv\Scripts\activate
     ```
   - On macOS and Linux:
     ```
     source venv/bin/activate
     ```

4. Set the Flask application environment variable:
   - On Windows:
     ```
     set FLASK_APP=run.py
     ```
   - On macOS and Linux:
     ```
     export FLASK_APP=run.py
     ```

5. (Optional) Enable debug mode for development:
   - On Windows:
     ```
     set FLASK_DEBUG=1
     ```
   - On macOS and Linux:
     ```
     export FLASK_DEBUG=1
     ```

6. Start the Flask development server:
   ```
   flask run
   ```

7. You should see output similar to:
   ```
   * Serving Flask app "run.py"
   * Environment: development
   * Debug mode: on
   * Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)
   ```

## Testing the API

Once the server is running, you can test the `/analyze` endpoint using curl or any API testing tool:

```bash
curl -X POST -H "Content-Type: application/json" -d '{"query":"What are the top 5 customers by total order amount?"}' http://localhost:5000/analyze
```

Or using Python with the requests library:

```python
import requests
import json

url = "http://localhost:5000/analyze"
payload = {"query": "What are the top 5 customers by total order amount?"}
headers = {"Content-Type": "application/json"}

response = requests.post(url, data=json.dumps(payload), headers=headers)

print(response.status_code)
print(json.dumps(response.json(), indent=2))
```

## Troubleshooting

If you encounter any issues:
1. Check the console output for error messages.
2. Verify that all required environment variables are set correctly in your `.env` file.
3. Ensure that your database is properly configured and accessible.
4. If using SQLite, make sure the database file exists and has the correct permissions.

Remember to stop the Flask server (Ctrl+C) when you're done testing.

## Setup

1. Clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Copy `.env.example` to `.env` and fill in your configuration details
6. Run the application: `python run.py`

## API Endpoints

- POST /analyze: Analyze a SQL query
  - Request body: JSON object with a "query" field
  - Response: JSON object with analysis results

## Running Tests

Run tests using: `python -m unittest discover tests`

## Contributing

Please read CONTRIBUTING.md for details on our code of conduct and the process for submitting pull requests.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
