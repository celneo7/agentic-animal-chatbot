import React, {useState, useEffect} from "react";
import './styles/Chat.css';

function Chat() {
  const [messages, setMessages] = useState([{'agent': 'deciding_agent', 'answer': 'Decision: answer.\nJustification & next action: The provided documents contain detailed information about cat claws, including their structure, function, and how they are used. Therefore, I can answer the question directly.', 'tools': {'name': 'info'}}
])
  const [loading, setLoading] = useState(false)
  
  
  const sendMessage = async (question) => {
    setLoading(true);
    setMessages(prev => [...prev, {agent: 'user', answer: `${question}`}]);

    const es = new EventSource(`http://localhost:5000/chat?question=${encodeURIComponent(question)}`);

    es.onmessage = (e) => {
      const data = JSON.parse(e.data);
      if (data.agent === 'done'){
        es.close();
        setLoading(false);
        return;
      }
    
      let new_msg = {
        agent: data.agent,
        answer: data.answer,
        tools: data.tools,
      }


      setMessages(prev => [...prev, new_msg])

    
      es.onerror = (error) => {
          console.error('SSE Error:', error);
          es.close();
          setLoading(false);
      };
    
    }
    
  };

  const formatSources = (toolValue) => {
  if (!toolValue) return [];
  // Split by "Document [Number]:"
  const parts = toolValue.split(/Document \d+:/g).filter(Boolean);
  return parts.map((text, index) => ({
    id: index + 1,
    content: text.trim()
  }));
};

  

  return (
  <div className="chat-container">
    <div className="chat-window">
      <div className="messages-list">
        {/*display each message*/}
        {messages.map((msg, idx) => (
          <div key={idx} className={`message-card ${msg.agent}`}>
            <div className="message-header">
              <span className="agent-badge">{msg.agent.replace('_', ' ')}</span>
            </div>
            
            <div className="message-content">
              {msg.answer}
            </div>

            {/*display tools used if exists*/}
            {msg.tools && Object.entries(msg.tools).length > 0 && (
              <div className="tools-section">
                {Object.entries(msg.tools).map(([toolKey, toolValue]) => (
                  <div key={toolKey} className="tool-pill">
                    <div className="source-header">Tool Used: {toolKey}</div>
                    {formatSources(toolValue).map((doc) => (
                      <details key={doc.id} className="document-accordion">
                        <summary className="document-summary">
                          <span className="doc-index">Doc {doc.id}</span>
                          <span className="doc-preview">{doc.content.substring(0, 50)}...</span>
                        </summary>
                        <div className="document-content">
                          {doc.content}
                        </div>
                      </details>
                    ))}
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}


        {loading && (
          <div className="loading-indicator">
            <div className="dot-typing"></div>
            <span>Next Agent is thinking...</span>
          </div>
        )}
      </div>
    </div>

    <div className="input-area">
      <input
        className="chat-input"
        placeholder="Ask a question about any animal..."
        type="text"
        onKeyDown={(e) => {
          if (e.key === 'Enter' && e.target.value.trim()) {
            sendMessage(e.target.value);
            e.target.value = '';
          }
        }}
      />
    </div>
  </div>
);

  // return (
  //   <div className="chat-interface">
  //     <div className="chat-window">


  //       <div className="messages">
          
  //         {messages.map((msg, idx) => (
  //           <div key={idx} className={`message ${msg.agent}`}>
  //             <div className="agent-label">{msg.agent}</div>
  //             <div className="content">{msg.answer}</div>
              
  //             {msg.tools && Object.entries(msg.tools).map(([toolKey, toolValue]) => (
  //               <div key={toolKey} className="tool-container">
  //                 <div className="tool-name">
  //                   <strong>Source ({toolKey}):</strong>
  //                 </div>
  //                 <div className="tool-answer">
  //                   {toolValue}
  //                 </div>
  //               </div>
  //             ))}
  //           </div>
  //         ))}
  //       </div>


  //     </div>
      
  //     {loading && <div className="loading">Processing...</div>}
      
  //     <input 
  //       type="text" 
  //       onKeyPress={(e) => {
  //         //if (e.key === 'Enter') sendMessage(e.target.value);
  //       }}
  //     />
  //   </div>
  // );


}

export default Chat;
