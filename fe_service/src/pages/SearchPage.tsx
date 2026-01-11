import React, { useEffect, useState } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import Header from "../components/Header";
import { theme } from "../styles/theme";

type SearchResult =
  | {
    result_type: "topic";
    topic_id: number;
    name: string;
    short_description?: string;
  }
  | {
    result_type: "entity";
    entity_id: number;
    entity_type: string;
    text: string;
  };

const SearchPage: React.FC = () => {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const query = params.get("q") || "";

  const [keyword, setKeyword] = useState(query);
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!query) return;

    setLoading(true);

    fetch(
      `http://localhost:8001/api/search/?q=${encodeURIComponent(query)}`
    )
      .then((res) => res.json())
      .then((data) => setResults(data.results || []))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [query]);

  return (
    <div
      style={{
        minHeight: "100vh",
        background: `linear-gradient(135deg, ${theme.colors.background} 0%, #faf8f3 100%)`,
        color: theme.colors.text,
      }}
    >
      <Header keyword={keyword} setKeyword={setKeyword} />

      <main style={{ maxWidth: 1000, margin: "0 auto", padding: "48px 20px" }}>
        <h2
          style={{
            marginBottom: 32,
            fontSize: "32px",
            fontWeight: 800,
            letterSpacing: "-1px",
            borderBottom: "3px solid rgba(0,0,0,0.15)",
            paddingBottom: "16px",
          }}
        >
          🔍 Kết quả tìm kiếm cho: <span style={{ color: "#4527a0" }}>"{query}"</span>
        </h2>

        {loading ? (
          <div
            style={{
              display: "flex",
              justifyContent: "center",
              alignItems: "center",
              minHeight: "300px",
            }}
          >
            <div
              style={{
                fontSize: "18px",
                opacity: 0.6,
                animation: "pulse 1.5s ease-in-out infinite",
              }}
            >
              Đang tìm kiếm...
            </div>
          </div>
        ) : results.length === 0 ? (
          <div
            style={{
              textAlign: "center",
              padding: "80px 20px",
              background: "rgba(255,255,255,0.5)",
              borderRadius: "16px",
              border: "2px dashed rgba(0,0,0,0.1)",
            }}
          >
            <p style={{ fontSize: "18px", opacity: 0.6, margin: 0 }}>
              Không có kết quả phù hợp.
            </p>
          </div>
        ) : (
          results.map((item, idx) => (
            <div
              key={idx}
              onClick={() => {
                if (item.result_type === "topic") {
                  navigate(`/topics/${item.topic_id}`);
                } else {
                  navigate(`/entities/${item.entity_id}`);
                }
              }}
              style={{
                padding: "24px 28px",
                borderRadius: 12,
                background: "rgba(255,255,255,0.6)",
                border: "2px solid rgba(0,0,0,0.1)",
                marginBottom: 20,
                cursor: "pointer",
                transition: "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
                boxShadow: "0 2px 8px rgba(0,0,0,0.05)",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = "rgba(255,255,255,0.9)";
                e.currentTarget.style.transform = "translateY(-4px)";
                e.currentTarget.style.boxShadow = "0 8px 24px rgba(0,0,0,0.12)";
                e.currentTarget.style.borderColor = "#4527a0";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = "rgba(255,255,255,0.6)";
                e.currentTarget.style.transform = "translateY(0)";
                e.currentTarget.style.boxShadow = "0 2px 8px rgba(0,0,0,0.05)";
                e.currentTarget.style.borderColor = "rgba(0,0,0,0.1)";
              }}
            >
              {item.result_type === "topic" ? (
                <>
                  <h3
                    style={{
                      margin: "0 0 8px 0",
                      fontSize: "22px",
                      fontWeight: 700,
                      color: "#4527a0",
                    }}
                  >
                    {item.name}
                  </h3>
                  {item.short_description && (
                    <p style={{ opacity: 0.75, margin: 0, lineHeight: "1.6" }}>
                      {item.short_description}
                    </p>
                  )}
                  <span
                    style={{
                      display: "inline-block",
                      marginTop: "12px",
                      padding: "4px 12px",
                      background: "rgba(69, 39, 160, 0.12)",
                      color: "#4527a0",
                      borderRadius: "6px",
                      fontSize: "11px",
                      fontWeight: 700,
                      textTransform: "uppercase",
                      letterSpacing: "0.5px",
                    }}
                  >
                    Topic
                  </span>
                </>
              ) : (
                <>
                  <h3
                    style={{
                      margin: "0 0 8px 0",
                      fontSize: "22px",
                      fontWeight: 700,
                      color: "#1976d2",
                    }}
                  >
                    {item.text}
                  </h3>
                  <p style={{ opacity: 0.75, margin: 0 }}>
                    Thực thể ({item.entity_type})
                  </p>
                  <span
                    style={{
                      display: "inline-block",
                      marginTop: "12px",
                      padding: "4px 12px",
                      background: "rgba(25, 118, 210, 0.12)",
                      color: "#1976d2",
                      borderRadius: "6px",
                      fontSize: "11px",
                      fontWeight: 700,
                      textTransform: "uppercase",
                      letterSpacing: "0.5px",
                    }}
                  >
                    Entity
                  </span>
                </>
              )}
            </div>
          ))
        )}
      </main>

      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 0.6; }
          50% { opacity: 0.8; }
        }
      `}</style>
    </div>
  );
};

export default SearchPage;
