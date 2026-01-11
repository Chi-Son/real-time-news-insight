import React, { useState, useEffect } from "react";
import { theme } from "../styles/theme";
import Header from "../components/Header";
import NewsCard from "../components/NewsCard";
import RankingBox from "../components/RankingBox";
import Footer from "../components/Footer";

type Topic = {
  topic_id: number;
  name: string;
};

type Entity = {
  entity_id: number;
  text: string;
};

type NewsItem = {
  id: number;
  title: string;
  published_at: string;
  source?: string;
  url: string;
  sentiment?: string;
  topics: Topic[];
  entities: Entity[];
};

const Home: React.FC = () => {
  const [keyword, setKeyword] = useState("");
  const [newsList, setNewsList] = useState<NewsItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 5;

  // Fetch latest articles from API
  useEffect(() => {
    const fetchArticles = async () => {
      try {
        const res = await fetch(
          "http://localhost:8001/api/articles/latest?limit=30"
        );
        const data = await res.json();
        setNewsList(data.articles || []);
      } catch (err) {
        console.error("Failed to fetch latest articles", err);
      } finally {
        setLoading(false);
      }
    };

    fetchArticles();
  }, []);

  // Calculate pagination
  const totalPages = Math.ceil(newsList.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const currentNews = newsList.slice(startIndex, endIndex);

  const handlePageChange = (page: number) => {
    setCurrentPage(page);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };



  return (
    <div
      style={{
        minHeight: "100vh",
        background: `linear-gradient(135deg, ${theme.colors.background} 0%, #faf8f3 100%)`,
        color: theme.colors.text,
        fontFamily: theme.fonts.body,
      }}
    >
      <Header keyword={keyword} setKeyword={setKeyword} />

      <main
        style={{
          maxWidth: "1400px",
          margin: "0 auto",
          padding: "40px 20px",
        }}
      >
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "1fr 350px",
            gap: "40px",
            alignItems: "start",
          }}
        >
          {/* News Feed - Left */}
          <div>
            <div
              style={{
                marginBottom: "32px",
                paddingBottom: "20px",
                borderBottom: `3px solid ${theme.colors.text}`,
              }}
            >
              <h2
                style={{
                  margin: 0,
                  fontSize: "32px",
                  fontWeight: 800,
                  letterSpacing: "-1px",
                }}
              >
                Tin mới nhất
              </h2>
              <p
                style={{
                  margin: "10px 0 0 0",
                  fontSize: "15px",
                  opacity: 0.7,
                  fontWeight: 500,
                }}
              >

              </p>
            </div>

            {loading ? (
              <div
                style={{
                  display: "flex",
                  justifyContent: "center",
                  alignItems: "center",
                  minHeight: "400px",
                }}
              >
                <div
                  style={{
                    fontSize: "16px",
                    opacity: 0.6,
                    animation: "pulse 1.5s ease-in-out infinite",
                  }}
                >
                  Loading articles...
                </div>
              </div>
            ) : newsList.length === 0 ? (
              <div
                style={{
                  textAlign: "center",
                  padding: "60px 20px",
                  opacity: 0.6,
                }}
              >
                <p>No articles available</p>
              </div>
            ) : (
              <>
                <div style={{ display: "flex", flexDirection: "column", gap: "0" }}>
                  {currentNews.map((news) => (
                    <NewsCard key={news.id} {...news} />
                  ))}
                </div>

                {/* Pagination */}
                {totalPages > 1 && (
                  <div
                    style={{
                      display: "flex",
                      justifyContent: "center",
                      alignItems: "center",
                      gap: "8px",
                      marginTop: "40px",
                      padding: "20px",
                    }}
                  >
                    <button
                      onClick={() => handlePageChange(currentPage - 1)}
                      disabled={currentPage === 1}
                      style={{
                        padding: "10px 16px",
                        fontSize: "14px",
                        fontWeight: 600,
                        border: `2px solid ${theme.colors.text}`,
                        borderRadius: "8px",
                        background: currentPage === 1 ? "rgba(0,0,0,0.1)" : "white",
                        color: theme.colors.text,
                        cursor: currentPage === 1 ? "not-allowed" : "pointer",
                        opacity: currentPage === 1 ? 0.4 : 1,
                        transition: "all 0.2s ease",
                      }}
                    >
                      ← Previous
                    </button>

                    <div style={{ display: "flex", gap: "6px" }}>
                      {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => {
                        // Show first page, last page, current page, and pages around current
                        const showPage =
                          page === 1 ||
                          page === totalPages ||
                          (page >= currentPage - 1 && page <= currentPage + 1);

                        const showEllipsis =
                          (page === currentPage - 2 && currentPage > 3) ||
                          (page === currentPage + 2 && currentPage < totalPages - 2);

                        if (showEllipsis) {
                          return (
                            <span
                              key={page}
                              style={{
                                padding: "10px 8px",
                                fontSize: "14px",
                                color: theme.colors.text,
                                opacity: 0.5,
                              }}
                            >
                              ...
                            </span>
                          );
                        }

                        if (!showPage) return null;

                        return (
                          <button
                            key={page}
                            onClick={() => handlePageChange(page)}
                            style={{
                              padding: "10px 16px",
                              fontSize: "14px",
                              fontWeight: 600,
                              border: `2px solid ${theme.colors.text}`,
                              borderRadius: "8px",
                              background: page === currentPage ? theme.colors.text : "white",
                              color: page === currentPage ? "white" : theme.colors.text,
                              cursor: "pointer",
                              transition: "all 0.2s ease",
                              minWidth: "44px",
                            }}
                            onMouseEnter={(e) => {
                              if (page !== currentPage) {
                                e.currentTarget.style.background = "rgba(0,0,0,0.05)";
                                e.currentTarget.style.transform = "translateY(-2px)";
                              }
                            }}
                            onMouseLeave={(e) => {
                              if (page !== currentPage) {
                                e.currentTarget.style.background = "white";
                                e.currentTarget.style.transform = "translateY(0)";
                              }
                            }}
                          >
                            {page}
                          </button>
                        );
                      })}
                    </div>

                    <button
                      onClick={() => handlePageChange(currentPage + 1)}
                      disabled={currentPage === totalPages}
                      style={{
                        padding: "10px 16px",
                        fontSize: "14px",
                        fontWeight: 600,
                        border: `2px solid ${theme.colors.text}`,
                        borderRadius: "8px",
                        background: currentPage === totalPages ? "rgba(0,0,0,0.1)" : "white",
                        color: theme.colors.text,
                        cursor: currentPage === totalPages ? "not-allowed" : "pointer",
                        opacity: currentPage === totalPages ? 0.4 : 1,
                        transition: "all 0.2s ease",
                      }}
                    >
                      Next →
                    </button>
                  </div>
                )}
              </>
            )}
          </div>

          {/* Sidebar - Right */}
          <div style={{ position: "sticky", top: "20px" }}>
            <RankingBox />
          </div>
        </div>
      </main>

      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 0.6; }
          50% { opacity: 0.8; }
        }
        @media (max-width: 1024px) {
          main > div {
            grid-template-columns: 1fr;
          }
          div[style*="position: sticky"] {
            position: static;
          }
        }
      `}</style>

      <Footer />
    </div>
  );
};

export default Home;
