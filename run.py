# run.py
from app import create_app
from app.config import Config
from app.services.graph_service import save_graph_visualization

app = create_app(Config)

if __name__ == '__main__':
    save_graph_visualization()

    app.run(debug=True)


# Example to run:
"""
   a. Test the `/analyze` endpoint:
   ```bash
   curl -X POST http://127.0.0.1:5000/analyze \
        -H "Content-Type: application/json" \
        -d '{"query": "What are the top 5 customers by total order amount?"}'
   ```

   b. Test the `/stream` endpoint:
   ```bash
   curl -X POST http://127.0.0.1:5000/stream \
        -H "Content-Type: application/json" \
        -d '{"query": "What are the top 5 customers by total order amount?"}'
"""

