import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { theme } from "../styles/theme";

type CrisisAlert = {
    topic_id: string;
    topic_name: string;
    crisis_score: number;
    level: "severe" | "warning";
    level_text: string;
    negative_percentage: number;
    total_articles: number;
    z_score: number;
};

const CrisisAlertBox: React.FC = () => {
    const [alerts, setAlerts] = useState<CrisisAlert[]>([]);
    const [isConnected, setIsConnected] = useState(false);
    const navigate = useNavigate();

    useEffect(() => {
        const ws = new WebSocket("ws://localhost:8000/ws/crisis");

        ws.onopen = () => {
            console.log("Crisis WebSocket connected");
            setIsConnected(true);
        };

        ws.onmessage = (event) => {
            try {
                const message = JSON.parse(event.data);
                if (message.type === "crisis_alert" && message.data) {
                    setAlerts(message.data);
                    console.log(`Received ${message.data.length} crisis alerts via WebSocket`);
                }
            } catch (err) {
                console.error("Failed to parse crisis message", err);
            }
        };

        ws.onerror = (error) => {
            console.error("Crisis WebSocket error:", error);
            setIsConnected(false);
        };

        ws.onclose = () => {
            console.log("Crisis WebSocket disconnected");
            setIsConnected(false);
        };

        return () => {
            ws.close();
        };
    }, []);

    const getLevelColor = (level: string) => {
        switch (level) {
            case "severe":
                return "#dc2626"; // red-600
            case "warning":
                return "#ea580c"; // orange-600
            default:
                return "#f59e0b"; // amber-500
        }
    };

    const getLevelBgColor = (level: string) => {
        switch (level) {
            case "severe":
                return "#fee2e2"; // red-100
            case "warning":
                return "#ffedd5"; // orange-100
            default:
                return "#fef3c7"; // amber-100
        }
    };

    return (
        <div
            style={{
                background: "white",
                borderRadius: "16px",
                padding: "24px",
                boxShadow: "0 4px 20px rgba(0,0,0,0.08)",
                border: `3px solid ${theme.colors.text}`,
                marginBottom: "24px",
            }}
        >
            <div
                style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "12px",
                    marginBottom: "20px",
                    paddingBottom: "16px",
                    borderBottom: `2px solid ${theme.colors.text}`,
                }}
            >
                <span style={{ fontSize: "24px" }}>🚨</span>
                <h3
                    style={{
                        margin: 0,
                        fontSize: "20px",
                        fontWeight: 800,
                        letterSpacing: "-0.5px",
                    }}
                >
                    Cảnh báo khủng hoảng
                </h3>
                {isConnected && (
                    <div
                        style={{
                            width: "8px",
                            height: "8px",
                            borderRadius: "50%",
                            background: "#10b981",
                            marginLeft: "auto",
                            animation: "pulse 2s ease-in-out infinite",
                        }}
                    />
                )}
            </div>

            {alerts.length === 0 ? (
                <div
                    style={{
                        textAlign: "center",
                        padding: "40px 20px",
                        opacity: 0.5,
                    }}
                >
                    <p style={{ margin: 0, fontSize: "14px", fontWeight: 500 }}>
                        {isConnected ? "Không có cảnh báo khủng hoảng" : "Đang kết nối..."}
                    </p>
                </div>
            ) : (
                <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
                    {alerts.slice(0, 5).map((alert) => (
                        <div
                            key={alert.topic_id}
                            onClick={() => navigate(`/topic/${alert.topic_id}`)}
                            style={{
                                padding: "16px",
                                borderRadius: "12px",
                                background: getLevelBgColor(alert.level),
                                border: `2px solid ${getLevelColor(alert.level)}`,
                                cursor: "pointer",
                                transition: "all 0.2s ease",
                            }}
                            onMouseEnter={(e) => {
                                e.currentTarget.style.transform = "translateX(4px)";
                                e.currentTarget.style.boxShadow = "0 4px 12px rgba(0,0,0,0.1)";
                            }}
                            onMouseLeave={(e) => {
                                e.currentTarget.style.transform = "translateX(0)";
                                e.currentTarget.style.boxShadow = "none";
                            }}
                        >
                            <div
                                style={{
                                    display: "flex",
                                    alignItems: "center",
                                    justifyContent: "space-between",
                                    marginBottom: "8px",
                                }}
                            >
                                <span
                                    style={{
                                        fontSize: "11px",
                                        fontWeight: 700,
                                        color: getLevelColor(alert.level),
                                        textTransform: "uppercase",
                                        letterSpacing: "0.5px",
                                    }}
                                >
                                    {alert.level_text}
                                </span>
                                <span
                                    style={{
                                        fontSize: "16px",
                                        fontWeight: 800,
                                        color: getLevelColor(alert.level),
                                    }}
                                >
                                    {alert.crisis_score}
                                </span>
                            </div>

                            <h4
                                style={{
                                    margin: "0 0 8px 0",
                                    fontSize: "15px",
                                    fontWeight: 700,
                                    color: theme.colors.text,
                                    lineHeight: "1.4",
                                }}
                            >
                                {alert.topic_name}
                            </h4>

                            <div
                                style={{
                                    display: "flex",
                                    gap: "16px",
                                    fontSize: "12px",
                                    color: "rgba(0,0,0,0.6)",
                                    fontWeight: 600,
                                }}
                            >
                                <span>
                                    📰 {alert.total_articles} bài
                                </span>
                                <span>
                                    😡 {alert.negative_percentage}% tiêu cực
                                </span>
                                <span>
                                    📈 Z-score: {alert.z_score}
                                </span>
                            </div>
                        </div>
                    ))}
                </div>
            )}

            <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }
      `}</style>
        </div>
    );
};

export default CrisisAlertBox;
