import ReactDOM from "react-dom";
import React from "react";
import { useState } from "react";
import axios from "axios";

import "../public/assets/style.scss";

interface Message {
    text: string;
    sentAt: number;
    sender: string;
}

const App = (): JSX.Element => {
    const [textInput, setTextInput] = useState("");
    const [messages, setMessages] = useState<Message[]>([]);
    const [responses, setResponses] = useState<Message[]>([]);
    const [isExpecting, setIsExpecting] = useState(false);

    const isInputEmpty = textInput.trim().length === 0;
    const sendMsg = () => {
        const msg = {
            text: textInput,
            sentAt: Date.now(),
            sender: "me",
        };
        setMessages([...messages, msg]);
        setTextInput("");
        setIsExpecting(true);

        axios
            .post("/lizzie", msg)
            .then((response) => {
                setIsExpecting(false);
                const respMsg: Message = {
                    ...response.data,
                    sentAt: Date.now(),
                };
                setResponses([...responses, respMsg]);
            })
            .catch((error) => {
                console.error("Failed to fetch response");
                console.error(error);
            });
        // Mock response for now
        // const mockResp = {
        //     text: textInput,
        //     sentAt: Date.now(),
        //     sender: "alzbeta",
        // };
        // setResponses([...responses, mockResp]);
    };

    const orderedMsgs = messages
        .concat(responses)
        .sort((a, b) => a.sentAt - b.sentAt);

    return (
        <div className="app">
            <div className="top">
                {orderedMsgs.map((m, idx) => (
                    <div
                        key={idx}
                        className={`msg${
                            m.sender === "me" ? "" : " odAlzbety"
                        }`}
                    >
                        <span>{m.text}</span>
                    </div>
                ))}
            </div>
            <div className="bottom">
                <div>
                    <textarea
                        onChange={(e) => setTextInput(e.target.value)}
                        value={textInput}
                    ></textarea>
                </div>
                <div>
                    <span
                        onClick={sendMsg}
                        className={`button${isInputEmpty ? " disabled" : ""}`}
                    >
                        <a>🦝</a>
                    </span>
                </div>
            </div>
        </div>
    );
};

ReactDOM.render(
    <React.StrictMode>
        <App />
    </React.StrictMode>,
    document.getElementById("root")
);
