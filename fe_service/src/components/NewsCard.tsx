import React from "react";
import { theme } from "../styles/theme";

type Topic = {
  topic_id: number;
  name: string;
};

type Entity = {
  entity_id: number;
  text: string;
};

type NewsCardProps = {
  title: string;
  published_at: string;
  source?: string;
  url: string;
  sentiment?: string;
  topics?: Topic[];
  entities?: Entity[];
};

const sentimentColor = (s?: string) => {
  if (s === "POS") return "#2e7d32";
  if (s === "NEG") return "#c62828";
  return "#616161";
};

const formatTime = (iso: string) =>
  new Date(iso).toLocaleString("vi-VN", {
    hour: "2-digit",
    minute: "2-digit",
    day: "2-digit",
    month: "2-digit",
  });

const NewsCard: React.FC<NewsCardProps> = ({
  title,
  published_at,
  source,
  url,
  sentiment,
  topics = [],
  entities = [],
}) => {
  return (
    <article
      onClick={() => window.open(url, "_blank")}
      style={{
        padding: "24px 28px",
        borderLeft: `5px solid ${sentimentColor(sentiment)}`,
        borderBottom: "1px solid rgba(0,0,0,0.08)",
        cursor: "pointer",
        fontFamily: theme.fonts.body,
        transition: "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
        background: "rgba(255,255,255,0.4)",
        borderRadius: "0",
        position: "relative",
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.background = "rgba(255,255,255,0.85)";
        e.currentTarget.style.transform = "translateX(8px)";
        e.currentTarget.style.boxShadow = "0 4px 16px rgba(0,0,0,0.08)";
        e.currentTarget.style.borderLeftWidth = "6px";
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.background = "rgba(255,255,255,0.4)";
        e.currentTarget.style.transform = "translateX(0)";
        e.currentTarget.style.boxShadow = "none";
        e.currentTarget.style.borderLeftWidth = "5px";
      }}
    >
      {/* Title */}
      <h3
        style={{
          margin: "0 0 14px 0",
          fontSize: "21px",
          fontWeight: 700,
          lineHeight: "1.45",
          color: theme.colors.text,
          letterSpacing: "-0.3px",
        }}
      >
        {title}
      </h3>

      {/* Meta row */}
      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
          alignItems: "center",
          gap: "8px",
          marginBottom: "12px",
          fontSize: "12px",
        }}
      >
        {/* Topics */}
        {topics.map((t: Topic) => (
          <span
            key={t.topic_id}
            style={{
              padding: "6px 12px",
              borderRadius: "6px",
              background: "rgba(69, 39, 160, 0.12)",
              color: "#4527a0",
              fontWeight: 700,
              fontSize: "11px",
              textTransform: "uppercase",
              letterSpacing: "0.5px",
              border: "1px solid rgba(69, 39, 160, 0.2)",
            }}
          >
            {t.name}
          </span>
        ))}

        {/* Sentiment */}
        {sentiment && (
          <span
            style={{
              padding: "6px 12px",
              borderRadius: "6px",
              background: sentimentColor(sentiment),
              color: "white",
              fontWeight: 700,
              fontSize: "11px",
              textTransform: "uppercase",
              letterSpacing: "0.5px",
              boxShadow: "0 2px 4px rgba(0,0,0,0.15)",
            }}
          >
            {sentiment}
          </span>
        )}
      </div>

      {/* Entities */}
      {entities.length > 0 && (
        <div
          style={{
            fontSize: "12px",
            opacity: 0.8,
            marginBottom: "14px",
            display: "flex",
            flexWrap: "wrap",
            gap: "8px",
          }}
        >
          {entities.slice(0, 3).map((e: Entity) => (
            <span
              key={e.entity_id}
              style={{
                background: "rgba(0,0,0,0.06)",
                padding: "4px 10px",
                borderRadius: "5px",
                fontWeight: 500,
                border: "1px solid rgba(0,0,0,0.08)",
              }}
            >
              {e.text}
            </span>
          ))}
        </div>
      )}

      {/* Meta row: source + date */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginTop: "12px",
          fontSize: "12px",
          opacity: 0.65,
          paddingTop: "12px",
          borderTop: "1px solid rgba(0,0,0,0.08)",
        }}
      >
        <span style={{ fontWeight: 500 }}>{source || "Unknown source"}</span>
        <span>{formatTime(published_at)}</span>
      </div>
    </article>
  );
};

export default NewsCard;
