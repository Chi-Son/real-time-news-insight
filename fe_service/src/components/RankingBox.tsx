import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
interface Topic {
  topic_id: string;
  topic_name: string;
  score: number;
}

interface RankingApiResponse {
  data: Topic[];
  updated_at: number;
}

interface WebSocketData {
  type: string;
  data: Topic[];
  updated_at: number;
}

const RankingBox: React.FC = () => {
  const [topics, setTopics] = useState<Topic[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("http://localhost:8001/api/topics/ranking?limit=20")
      .then((res) => res.json())
      .then((data: RankingApiResponse) => setTopics(data.data))
      .catch((err) => console.error("Failed to fetch ranking", err))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    const ws = new WebSocket("ws://0.0.0.0:8000/ws/topics");

    ws.onmessage = (event) => {
      try {
        const msg: WebSocketData = JSON.parse(event.data);
        if (msg.type === "topic_score_update") {
          setTopics(msg.data.slice(0, 20));
        }
      } catch (err) {
        console.error("WebSocket parse error", err);
      }
    };

    ws.onerror = (err) => console.error("WebSocket error", err);
    return () => ws.close();
  }, []);

  return (
    <div
      style={{
        background: "rgba(255, 255, 255, 0.6)",
        border: "3px solid rgba(0, 0, 0, 0.12)",
        borderRadius: "16px",
        padding: "28px",
        fontFamily: "inherit",
        color: "#2F2F2F",
        boxShadow: "0 4px 20px rgba(0,0,0,0.08)",
        transition: "all 0.3s ease",
      }}
    >
      <h2
        style={{
          fontSize: "22px",
          fontWeight: 800,
          textAlign: "center",
          borderBottom: "3px solid rgba(0, 0, 0, 0.15)",
          paddingBottom: "18px",
          marginBottom: "24px",
          margin: "0 0 24px 0",
          letterSpacing: "-0.5px",
        }}
      >
        🔥 Trending Topics
      </h2>

      {loading ? (
        <p
          style={{
            textAlign: "center",
            opacity: 0.6,
            fontSize: "14px",
            margin: 0,
          }}
        >
          Loading ranking...
        </p>
      ) : topics.length === 0 ? (
        <p
          style={{
            textAlign: "center",
            opacity: 0.6,
            fontSize: "14px",
            margin: 0,
          }}
        >
          No active topics in last 24h
        </p>
      ) : (
        <div
          style={{
            overflowY: "auto",
            maxHeight: "520px",
          }}
        >
          <table
            style={{
              width: "100%",
              borderCollapse: "collapse",
            }}
          >
            <thead>
              <tr
                style={{
                  background: "rgba(0, 0, 0, 0.05)",
                  position: "sticky",
                  top: 0,
                }}
              >
                <th
                  style={{
                    textAlign: "left",
                    padding: "10px 8px",
                    borderBottom: "1px solid rgba(0, 0, 0, 0.1)",
                    width: "30px",
                    fontWeight: 600,
                    fontSize: "12px",
                  }}
                >
                  #
                </th>
                <th
                  style={{
                    textAlign: "left",
                    padding: "10px 8px",
                    borderBottom: "1px solid rgba(0, 0, 0, 0.1)",
                    fontWeight: 600,
                    fontSize: "12px",
                  }}
                >
                  Topic
                </th>
                <th
                  style={{
                    textAlign: "right",
                    padding: "10px 8px",
                    borderBottom: "1px solid rgba(0, 0, 0, 0.1)",
                    width: "60px",
                    fontWeight: 600,
                    fontSize: "12px",
                  }}
                >
                  Score
                </th>
              </tr>
            </thead>
            <tbody>
              {topics.map((topic, index) => (
                <tr
                  key={topic.topic_id}
                  style={{
                    transition: "all 0.25s cubic-bezier(0.4, 0, 0.2, 1)",
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.background = "rgba(69, 39, 160, 0.1)";
                    e.currentTarget.style.transform = "scale(1.02)";
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.background = "transparent";
                    e.currentTarget.style.transform = "scale(1)";
                  }}
                >
                  <td
                    style={{
                      padding: "14px 10px",
                      borderBottom: "1px solid rgba(0, 0, 0, 0.06)",
                      fontWeight: 800,
                      fontSize: "15px",
                      color: index < 3 ? "#d32f2f" : "#2F2F2F",
                    }}
                  >
                    {index + 1}
                  </td>
                  <td
                    style={{
                      padding: "14px 10px",
                      borderBottom: "1px solid rgba(0, 0, 0, 0.06)",
                      whiteSpace: "nowrap",
                      overflow: "hidden",
                      textOverflow: "ellipsis",
                      maxWidth: "120px",
                    }}
                  >
                    <Link
                      to={`/topics/${topic.topic_id}`}
                      style={{
                        textDecoration: "none",
                        color: "#4527a0",
                        fontWeight: 700,
                        cursor: "pointer",
                        transition: "all 0.2s ease",
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.textDecoration = "underline";
                        e.currentTarget.style.color = "#311b92";
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.textDecoration = "none";
                        e.currentTarget.style.color = "#4527a0";
                      }}
                    >
                      {topic.topic_name}
                    </Link>
                  </td>
                  <td
                    style={{
                      padding: "14px 10px",
                      borderBottom: "1px solid rgba(0, 0, 0, 0.06)",
                      fontFamily: "'Courier New', monospace",
                      textAlign: "right",
                      fontWeight: 600,
                      fontSize: "14px",
                      color: "#1976d2",
                    }}
                  >
                    {topic.score.toFixed(1)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default RankingBox;
