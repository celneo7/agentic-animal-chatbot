from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
sys.path.insert(1, 'C:/Users/Celeste/Documents/Data Science/1-project/agentic-animal-chatbot/')
from agents.main import agent_workflow


app = Flask(__name__)
CORS(app)

@app.route("/chat", methods= ["POST"])
def get_answer():
    response = request.json
    user_message = response['message']
    
    answer = agent_workflow

    return


if __name__ == '__main__':
    app.run(debug=True)