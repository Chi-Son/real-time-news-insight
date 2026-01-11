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
        padding: "16px 20px",
        borderBottom: "1px solid rgba(0,0,0,0.12)",
        cursor: "pointer",
        fontFamily: theme.fonts.body,
        transition: "background 0.15s",
      }}
      onMouseEnter={(e) =>
        (e.currentTarget.style.background = "rgba(0,0,0,0.03)")
      }
      onMouseLeave={(e) =>
        (e.currentTarget.style.background = "transparent")
      }
    >
      {/* Title */}
      <h3 style={{ margin: "0 0 8px 0", fontSize: "18px" }}>{title}</h3>

      {/* Meta row */}
      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
          alignItems: "center",
          gap: "8px",
          marginBottom: "6px",
          fontSize: "13px",
        }}
      >
        {/* Topics */}
        {topics.map((t: Topic) => (
          <span
            key={t.topic_id}
            style={{
              padding: "2px 8px",
              borderRadius: "12px",
              background: "#ede7f6",
              color: "#4527a0",
              fontWeight: 500,
            }}
          >
            #{t.name}
          </span>
        ))}

        {/* Sentiment */}
        {sentiment && (
          <span
            style={{
              padding: "2px 8px",
              borderRadius: "12px",
              background: sentimentColor(sentiment),
              color: "white",
              fontWeight: 600,
            }}
          >
            {sentiment}
          </span>
        )}

        {/* Time */}
        <span style={{ opacity: 0.6 }}>{formatTime(published_at)}</span>
      </div>

      {/* Entities */}
      {entities.length > 0 && (
        <div
          style={{
            fontSize: "13px",
            opacity: 0.85,
            marginBottom: "6px",
          }}
        >
          {entities.slice(0, 3).map((e: Entity) => (
            <span key={e.entity_id} style={{ marginRight: "8px" }}>
              {e.text}
            </span>
          ))}
        </div>
      )}

      {/* Source */}
      {source && (
        <div style={{ fontSize: "12px", opacity: 0.6 }}>Nguồn: {source}</div>
      )}
    </article>
  );
};

export default NewsCard;
