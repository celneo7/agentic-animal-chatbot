from flask import Flask
import sys
sys.path.insert(1, 'C:/Users/Celeste/Documents/Data Science/1-project/agentic-animal-chatbot/')
from agents.main import agent_workflow


app = Flask(__name__)

@app.route("/data")
def get_data():
    agent_workflow
    return


if __name__ == '__main__':
    app.run(debug=True)