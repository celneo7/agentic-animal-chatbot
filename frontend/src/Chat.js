import React, {useState, useEffect} from "react";
import './styles/Chat.css';

function Chat() {
  //const [messages, setMessages] = useState([{'agent': 'deciding_agent', 'answer': 'Decision: answer.\nJustification & next action: The provided documents contain detailed information about cat claws, including their structure, function, and how they are used. Therefore, I can answer the question directly.', 'tools': {}}, {'agent': 'rag_agent', 'answer': '', 'tools': {'retriever_tool': 'Document 1:\n\n### Claws\n\nCats have protractible and retractable claws. In their normal, relaxed position, the claws are sheathed with the skin and fur around the paw\'s toe pads. This keeps the claws sharp by preventing wear from contact with the ground and allows for the silent stalking of prey. The claws on the forefeet are typically sharper than those on the hindfeet. Cats can voluntarily extend their claws, such as in hunting, fighting, climbing, kneading, or for extra traction on soft surfaces. Cats shed the outside layer of their claw sheaths when scratching rough surfaces.\n\nMost cats have five claws on their front paws and four on their rear paws. The dewclaw is proximal to the other claws. More proximally is a protrusion which appears to be a sixth "finger". This special feature of the front paws on the inside of the wrists has no function in normal walking but is thought to be an antiskidding device used while jumping. Some cat breeds are prone to having extra digits ("polydactyly").\n\n\nDocument 2:\n# Cat\n\nCatus domesticus Erxleben, 1777 F. angorensis Gmelin, 1788 F. vulgaris Fischer, 1829\n\nThe cat (Felis catus), also called domestic cat and house cat, is a small carnivorous mammal. It is an obligate carnivore, requiring a predominantly meat-based diet. Its retractable claws are adapted to killing small prey species such as mice and rats. It has a strong, flexible body, quick reflexes, and sharp teeth, and its night vision and sense of smell are well developed. It is a social species, but a solitary hunter and a crepuscular predator. Cat communication includes meowing, purring, trilling, hissing, growling, grunting, and body language. It can hear sounds too faint or too high in frequency for human ears, such as those made by small mammals. It secretes and perceives pheromones. Cat intelligence is evident in its ability to adapt, learn through observation, and solve problems. Female domestic cats can have kittens from spring to late autumn in temperate zones and throughout the year in equatorial regions, with litter sizes often ranging from two to five kittens.\n\nThe domestic cat is the only domesticated species of the family Felidae. Advances in archaeology and genetics have shown that the domestication of the cat started in the Near East around 7500 BCE. Today, the domestic cat occurs across the globe and is valued by humans for companionship and its ability to kill vermin. It is commonly kept as a pet, working cat, and pedigreed cat shown at cat fancy events. Out of the estimated 600 million domestic cats worldwide, 400 million reside in Asia, including 58 million in China. The United States leads in cat ownership with 73.8 million cats, followed by the United Kingdom with approximately 10.9 million cats. It also ranges freely as a feral cat, avoiding human contact. Pet abandonment contributes to increasing of the global feral cat population, which has driven the decline of bird, mammal, and reptile species. Population control includes spaying and neutering.\n\n\nDocument 3:\n\n### Skeleton\n\nCats have seven cervical vertebrae (as do most mammals); 13 thoracic vertebrae (humans have 12); seven lumbar vertebrae (humans have five); three sacral vertebrae (as do most mammals, but humans have five); and a variable number of caudal vertebrae in the tail (humans have only three to five vestigial caudal vertebrae, fused into an internal coccyx).: 11 The extra lumbar and thoracic vertebrae account for the cat\'s spinal mobility and flexibility. Attached to the spine are 13 ribs, the shoulder, and the pelvis.: 16 Unlike human arms, cat forelimbs are attached to the shoulder by free-floating clavicle bones which allow them to pass their body through any space into which they can fit their head.\n'}}])
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(false)
  const [inputValue, setInputValue] = useState("");

  const isLanding = messages.length === 0;

  const sendMessage = async (question) => {
    setMessages(prev => [...prev, {agent: 'user', answer: `${question}`}]);

    const es = new EventSource(`http://localhost:5000/chat?question=${encodeURIComponent(question)}`);

    setInputValue("");
    setLoading(true);

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
    {!isLanding && <div className="chat-window">
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
    </div>}

    <div className="input-wrapper">
        <div className="input-container">
          <input
            className="chat-input"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="Type your question..."
            onKeyPress={(e) => e.key === 'Enter' && sendMessage(inputValue)}
          />
          <button className="send-btn" onClick={() => sendMessage(inputValue)}>
            Send
          </button>
        </div>
        {isLanding && (
          <div className="suggestions">
            <button onClick={() => sendMessage("Tell me about elephants")}>🐘 About Elephants</button>
            <button onClick={() => sendMessage("How do cat claws work?")}>🐱 Cat Claws</button>
          </div>
        )}
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
