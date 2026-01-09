from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
import sys
sys.path.insert(1, 'C:/Users/Celeste/Documents/Data Science/1-project/agentic-animal-chatbot/')
from agents.main import agent_workflow
import json

app = Flask(__name__)
CORS(app)

@app.route("/chat", methods= ["POST"])
def stream():
    question = request.json.get('question')

    def get_answer():
        for event in agent_workflow.stream({'question': question}, stream_mode='updates'):
            for node, update in event.items():

                if 'messages' not in update:
                    continue

                response = update['messages']
                
                res_json = {'agent': str(node), 'answer': '', 'count': 0 }

                for msg in response:
                    m_type = getattr(msg, 'type', '')

                    if m_type == 'tool': #ToolMessage
                        t_name = getattr(msg, 'name', 'tool')
                        t_content = getattr(msg, 'content', '')
                        
                        res_json["count"] += 1
                        res_json[f'tool{res_json["count"] + 1}'] = (t_name, t_content)
                        
                    elif m_type == 'ai': # AIMessage
                        m_content = getattr(msg, 'content', '')
                        if isinstance(m_content, str):
                            res_json['answer'] = m_content   
            yield f"data: {json.dumps(res_json)}\n\n"
        yield f"data: {json.dumps({'agent': 'done'})}\n\n"

    return Response(
        stream_with_context(get_answer()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no'
        }
    )

if __name__ == '__main__':
    app.run(debug=True)