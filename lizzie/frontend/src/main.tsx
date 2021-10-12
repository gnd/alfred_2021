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
    const [engine, setEngine] = useState("davinci");
    const [temperature, setTemperature] = useState(90);
    const [respLength, setRespLength] = useState(200);

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

        const req = {
            ...msg,
            engine: engine,
            max_tokens: respLength,
            temperature: temperature,
        };

        axios
            .post("/lizzie", req)
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
                    <div className="slidecontainer">
                        <label>temperature</label>
                        <input
                            type="range"
                            min="0"
                            max="100"
                            value={temperature}
                            className="slider"
                            onChange={(e) =>
                                setTemperature(Number(e.target.value))
                            }
                        />
                    </div>
                    <div>
                        <label>engine</label>
                        <select
                            onChange={(e) => setEngine(e.target.value)}
                            defaultValue="davinci"
                        >
                            <option value="ada">Ada</option>
                            <option value="babbage">Babbage</option>
                            <option value="curie">Curie</option>
                            <option value="curie-instruct-beta">
                                Curie Instruct Beta
                            </option>
                            <option value="davinci">Davinci</option>
                            <option value="davinci-instruct-beta">
                                Davinci Instruct Beta
                            </option>
                        </select>
                    </div>
                    <div className="slidecontainer">
                        <label>words {respLength}</label>
                        <input
                            type="range"
                            min="20"
                            max="2000"
                            value={respLength}
                            className="slider"
                            onChange={(e) =>
                                setRespLength(Number(e.target.value))
                            }
                        />
                    </div>
                </div>
                <div>
                    <div>
                        <textarea
                            onChange={(e) => setTextInput(e.target.value)}
                            value={textInput}
                        ></textarea>
                    </div>
                    <div>
                        <span
                            onClick={sendMsg}
                            className={`button${
                                isInputEmpty ? " disabled" : ""
                            }`}
                        >
                            <a>🦝</a>
                        </span>
                    </div>
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
