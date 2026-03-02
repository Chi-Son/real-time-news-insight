import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { theme } from "../styles/theme";
import Header from "../components/Header";
import NewsCard from "../components/NewsCard";
import Footer from "../components/Footer";

type Topic = {
  topic_id: number;
  name: string;
  short_description?: string;
};

type NewsItem = {
  id: number;
  title: string;
  published_at: string;
  source?: string;
  url: string;
  sentiment?: string;
};

type DailyHistory = {
  date: string;
  count: number;
  sentiment: {
    positive: SentimentDistribution;
    negative: SentimentDistribution;
    neutral: SentimentDistribution;
  };
  z_score: number;
  spike: number;
};

type TrendAnalysis = {
  count_now: number;
  weighted_mean: number;
  weighted_std: number;
  z_score: number;
};

type SentimentDistribution = {
  count: number;
  percentage: number;
};

type SentimentToday = {
  total_articles: number;
  distribution: {
    positive: SentimentDistribution;
    negative: SentimentDistribution;
    neutral: SentimentDistribution;
  };
  crisis_score: number;
};

const TopicPage: React.FC = () => {
  const { topicId } = useParams<{ topicId: string }>();

  const [topic, setTopic] = useState<Topic | null>(null);
  const [articles24h, setArticles24h] = useState<NewsItem[]>([]);
  const [articlesHistory, setArticlesHistory] = useState<NewsItem[]>([]);
  const [dailyHistory, setDailyHistory] = useState<DailyHistory[]>([]);
  const [trendAnalysis, setTrendAnalysis] = useState<TrendAnalysis | null>(null);
  const [sentimentToday, setSentimentToday] = useState<SentimentToday | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [keyword, setKeyword] = useState("");
  const [currentPage24h, setCurrentPage24h] = useState(1);
  const [currentPageHistory, setCurrentPageHistory] = useState(1);
  const [selectedDay, setSelectedDay] = useState<DailyHistory | null>(null);
  const itemsPerPage = 5;

  useEffect(() => {
    const fetchTopicArticles = async () => {
      try {
        const res = await fetch(
          `http://localhost:8001/api/topics/${topicId}`
        );
        const data = await res.json();

        setTopic(data.topic);
        setArticles24h(data.articles_24h || []);
        setArticlesHistory(data.articles_history || []);
        setDailyHistory(data.daily_history || []);
        setTrendAnalysis(data.trend_analysis || null);
        setSentimentToday(data.sentiment_today || null);
      } catch (err) {
        console.error("Failed to fetch topic articles", err);
      } finally {
        setLoading(false);
      }
    };

    fetchTopicArticles();
  }, [topicId]);

  // Pagination for 24h articles
  const totalPages24h = Math.ceil(articles24h.length / itemsPerPage);
  const startIndex24h = (currentPage24h - 1) * itemsPerPage;
  const endIndex24h = startIndex24h + itemsPerPage;
  const current24hNews = articles24h.slice(startIndex24h, endIndex24h);

  // Pagination for history articles
  const totalPagesHistory = Math.ceil(articlesHistory.length / itemsPerPage);
  const startIndexHistory = (currentPageHistory - 1) * itemsPerPage;
  const endIndexHistory = startIndexHistory + itemsPerPage;
  const currentHistoryNews = articlesHistory.slice(startIndexHistory, endIndexHistory);

  const handlePageChange24h = (page: number) => {
    setCurrentPage24h(page);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const handlePageChangeHistory = (page: number) => {
    setCurrentPageHistory(page);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  // Helper function để xác định xu hướng
  const getTrendInfo = (zScore: number) => {
    if (zScore > 2) {
      return {
        label: "🔥 Xu hướng tăng mạnh",
        color: "#d32f2f",
        bgColor: "#ffebee",
        description: "Số lượng bài viết tăng đột biến so với 7 ngày trước"
      };
    } else if (zScore < -2) {
      return {
        label: "❄️ Xu hướng giảm mạnh",
        color: "#1976d2",
        bgColor: "#e3f2fd",
        description: "Số lượng bài viết giảm đáng kể so với 7 ngày trước"
      };
    } else {
      return {
        label: "📊 Xu hướng bình thường",
        color: "#388e3c",
        bgColor: "#e8f5e9",
        description: "Số lượng bài viết ổn định so với 7 ngày trước"
      };
    }
  };

  // Helper function để xác định mức độ khủng hoảng
  const getCrisisInfo = (crisisScore: number) => {
    if (crisisScore >= 2.5) {
      return {
        label: "🚨 KHỦNG HOẢNG NGHIÊM TRỌNG",
        color: "#b71c1c",
        bgColor: "#ffcdd2",
        description: "Bùng phát tin tức tiêu cực mạnh - Cần theo dõi sát"
      };
    } else if (crisisScore >= 1.5) {
      return {
        label: "⚠️ Cảnh báo khủng hoảng",
        color: "#e65100",
        bgColor: "#ffe0b2",
        description: "Xu hướng tiêu cực đáng lo ngại"
      };
    } else if (crisisScore >= 0.8) {
      return {
        label: "⚡ Bùng phát nhưng chưa nghiêm trọng",
        color: "#f57c00",
        bgColor: "#fff3e0",
        description: "Tăng đột biến nhưng cảm xúc hỗn hợp"
      };
    } else {
      return {
        label: "✅ Bình thường",
        color: "#2e7d32",
        bgColor: "#e8f5e9",
        description: "Không có dấu hiệu khủng hoảng"
      };
    }
  };

  // Helper function để tính crisis score cho ngày cụ thể
  const calculateDayCrisisScore = (day: DailyHistory) => {
    const negativeRatio = day.sentiment.negative.percentage / 100.0;
    return day.z_score * negativeRatio;
  };

  const renderPagination = (
    currentPage: number,
    totalPages: number,
    handlePageChange: (page: number) => void
  ) => {
    if (totalPages <= 1) return null;

    return (
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
    );
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
          display: "flex",
          justifyContent: "center",
          alignItems: "flex-start",
          padding: "48px 20px",
        }}
      >
        <div
          style={{
            maxWidth: "1200px",
            width: "100%",
            display: "flex",
            justifyContent: "center",
          }}
        >
          {/* Cột nội dung chính */}
          <div style={{ flex: "1 1 900px", minWidth: "320px" }}>
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
                    fontSize: "18px",
                    opacity: 0.6,
                    animation: "pulse 1.5s ease-in-out infinite",
                  }}
                >
                  Đang tải dữ liệu chủ đề...
                </div>
              </div>
            ) : !topic ? (
              <div
                style={{
                  textAlign: "center",
                  padding: "80px 20px",
                  opacity: 0.6,
                }}
              >
                <p style={{ fontSize: "18px" }}>Không tìm thấy chủ đề.</p>
              </div>
            ) : (
              <>
                {/* Header Topic */}
                <div
                  style={{
                    marginBottom: "40px",
                    padding: "32px",
                    background: "rgba(255,255,255,0.6)",
                    borderRadius: "16px",
                    border: "3px solid rgba(0,0,0,0.1)",
                    boxShadow: "0 4px 20px rgba(0,0,0,0.08)",
                  }}
                >
                  <h1
                    style={{
                      margin: "0 0 16px 0",
                      fontSize: "36px",
                      fontWeight: 800,
                      letterSpacing: "-1px",
                      color: "#4527a0",
                    }}
                  >
                    {topic.name}
                  </h1>

                  {topic.short_description && (
                    <p
                      style={{
                        opacity: 0.8,
                        fontSize: "16px",
                        lineHeight: "1.6",
                        margin: 0,
                      }}
                    >
                      {topic.short_description}
                    </p>
                  )}
                </div>

                {/* Trend Analysis Card */}
                {trendAnalysis && (
                  <div
                    style={{
                      marginBottom: "40px",
                      padding: "32px",
                      background: "rgba(255,255,255,0.8)",
                      borderRadius: "16px",
                      border: "3px solid rgba(0,0,0,0.1)",
                      boxShadow: "0 4px 20px rgba(0,0,0,0.08)",
                    }}
                  >
                    {/* Trend Alert Badge */}
                    <div
                      style={{
                        display: "inline-block",
                        padding: "12px 24px",
                        borderRadius: "12px",
                        background: getTrendInfo(trendAnalysis.z_score).bgColor,
                        color: getTrendInfo(trendAnalysis.z_score).color,
                        fontWeight: 700,
                        fontSize: "18px",
                        marginBottom: "20px",
                        border: `2px solid ${getTrendInfo(trendAnalysis.z_score).color}`,
                      }}
                    >
                      {getTrendInfo(trendAnalysis.z_score).label}
                    </div>

                    <p
                      style={{
                        fontSize: "14px",
                        opacity: 0.7,
                        marginBottom: "24px",
                      }}
                    >
                      {getTrendInfo(trendAnalysis.z_score).description}
                    </p>

                    {/* Stats Grid */}
                    <div
                      style={{
                        display: "grid",
                        gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
                        gap: "16px",
                        marginBottom: "32px",
                      }}
                    >
                      <div
                        style={{
                          padding: "20px",
                          background: "rgba(255,255,255,0.6)",
                          borderRadius: "12px",
                          border: "2px solid rgba(0,0,0,0.08)",
                        }}
                      >
                        <div style={{ fontSize: "14px", opacity: 0.6, marginBottom: "8px" }}>
                          Hôm nay
                        </div>
                        <div style={{ fontSize: "32px", fontWeight: 800, color: "#4527a0" }}>
                          {trendAnalysis.count_now}
                        </div>
                        <div style={{ fontSize: "12px", opacity: 0.5 }}>bài viết</div>
                      </div>

                      <div
                        style={{
                          padding: "20px",
                          background: "rgba(255,255,255,0.6)",
                          borderRadius: "12px",
                          border: "2px solid rgba(0,0,0,0.08)",
                        }}
                      >
                        <div style={{ fontSize: "14px", opacity: 0.6, marginBottom: "8px" }}>
                          Trung bình 7 ngày
                        </div>
                        <div style={{ fontSize: "32px", fontWeight: 800, color: "#666" }}>
                          {trendAnalysis.weighted_mean}
                        </div>
                        <div style={{ fontSize: "12px", opacity: 0.5 }}>bài viết/ngày</div>
                      </div>

                      <div
                        style={{
                          padding: "20px",
                          background: "rgba(255,255,255,0.6)",
                          borderRadius: "12px",
                          border: "2px solid rgba(0,0,0,0.08)",
                        }}
                      >
                        <div style={{ fontSize: "14px", opacity: 0.6, marginBottom: "8px" }}>
                          Z-Score
                        </div>
                        <div
                          style={{
                            fontSize: "32px",
                            fontWeight: 800,
                            color: getTrendInfo(trendAnalysis.z_score).color,
                          }}
                        >
                          {trendAnalysis.z_score > 0 ? "+" : ""}
                          {trendAnalysis.z_score}
                        </div>
                        <div style={{ fontSize: "12px", opacity: 0.5 }}>độ lệch chuẩn</div>
                      </div>
                    </div>

                    {/* 7-Day Chart */}
                    <div>
                      <h4
                        style={{
                          fontSize: "16px",
                          fontWeight: 700,
                          marginBottom: "16px",
                          opacity: 0.8,
                        }}
                      >
                        📈 Lịch sử 7 ngày (cùng khung giờ)
                      </h4>

                      <div
                        style={{
                          display: "flex",
                          alignItems: "flex-end",
                          gap: "12px",
                          padding: "20px",
                          background: "rgba(255,255,255,0.4)",
                          borderRadius: "12px",
                          minHeight: "200px",
                        }}
                      >
                        {dailyHistory.map((day, index) => {
                          const maxCount = Math.max(...dailyHistory.map((d) => d.count), trendAnalysis.count_now);
                          const heightPercent = (day.count / maxCount) * 100;
                          const isToday = index === dailyHistory.length - 1;

                          return (
                            <div
                              key={day.date}
                              onClick={() => setSelectedDay(day)}
                              style={{
                                flex: 1,
                                display: "flex",
                                flexDirection: "column",
                                alignItems: "center",
                                gap: "8px",
                                cursor: "pointer",
                                transition: "transform 0.2s ease",
                              }}
                              onMouseEnter={(e) => {
                                e.currentTarget.style.transform = "scale(1.05)";
                              }}
                              onMouseLeave={(e) => {
                                e.currentTarget.style.transform = "scale(1)";
                              }}
                            >
                              <div
                                style={{
                                  fontSize: "14px",
                                  fontWeight: 700,
                                  color: isToday ? "#4527a0" : "#666",
                                }}
                              >
                                {day.count}
                              </div>
                              <div
                                style={{
                                  width: "100%",
                                  height: `${Math.max(heightPercent, 5)}%`,
                                  minHeight: "20px",
                                  background: isToday
                                    ? "linear-gradient(180deg, #4527a0 0%, #7b1fa2 100%)"
                                    : "linear-gradient(180deg, #9e9e9e 0%, #757575 100%)",
                                  borderRadius: "8px 8px 0 0",
                                  transition: "all 0.3s ease",
                                  boxShadow: "0 2px 8px rgba(0,0,0,0.1)",
                                }}
                              />
                              <div
                                style={{
                                  fontSize: "11px",
                                  opacity: 0.6,
                                  textAlign: "center",
                                  fontWeight: isToday ? 700 : 400,
                                }}
                              >
                                {new Date(day.date).toLocaleDateString("vi-VN", {
                                  month: "numeric",
                                  day: "numeric",
                                })}
                              </div>
                            </div>
                          );
                        })}

                        {/* Today's bar */}
                        <div
                          style={{
                            flex: 1,
                            display: "flex",
                            flexDirection: "column",
                            alignItems: "center",
                            gap: "8px",
                          }}
                        >
                          <div
                            style={{
                              fontSize: "14px",
                              fontWeight: 700,
                              color: "#d32f2f",
                            }}
                          >
                            {trendAnalysis.count_now}
                          </div>
                          <div
                            style={{
                              width: "100%",
                              height: `${Math.max((trendAnalysis.count_now / Math.max(...dailyHistory.map((d) => d.count), trendAnalysis.count_now)) * 100, 5)}%`,
                              minHeight: "20px",
                              background: "linear-gradient(180deg, #d32f2f 0%, #c62828 100%)",
                              borderRadius: "8px 8px 0 0",
                              transition: "all 0.3s ease",
                              boxShadow: "0 4px 12px rgba(211,47,47,0.3)",
                              animation: "pulse-bar 2s ease-in-out infinite",
                            }}
                          />
                          <div
                            style={{
                              fontSize: "11px",
                              fontWeight: 700,
                              color: "#d32f2f",
                              textAlign: "center",
                            }}
                          >
                            Hôm nay
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Sentiment & Crisis Analysis Card */}
                {sentimentToday && trendAnalysis && (
                  <div
                    style={{
                      marginBottom: "40px",
                      padding: "32px",
                      background: "rgba(255,255,255,0.8)",
                      borderRadius: "16px",
                      border: "3px solid rgba(0,0,0,0.1)",
                      boxShadow: "0 4px 20px rgba(0,0,0,0.08)",
                    }}
                  >
                    <h3
                      style={{
                        fontSize: "20px",
                        fontWeight: 700,
                        marginBottom: "24px",
                        opacity: 0.9,
                      }}
                    >
                      💭 Phân tích cảm xúc hôm nay
                    </h3>

                    {/* Crisis Score Badge */}
                    <div
                      style={{
                        display: "inline-block",
                        padding: "12px 24px",
                        borderRadius: "12px",
                        background: getCrisisInfo(sentimentToday.crisis_score).bgColor,
                        color: getCrisisInfo(sentimentToday.crisis_score).color,
                        fontWeight: 700,
                        fontSize: "16px",
                        marginBottom: "16px",
                        border: `2px solid ${getCrisisInfo(sentimentToday.crisis_score).color}`,
                      }}
                    >
                      {getCrisisInfo(sentimentToday.crisis_score).label}
                    </div>

                    <p
                      style={{
                        fontSize: "14px",
                        opacity: 0.7,
                        marginBottom: "24px",
                      }}
                    >
                      {getCrisisInfo(sentimentToday.crisis_score).description}
                    </p>

                    <div
                      style={{
                        display: "grid",
                        gridTemplateColumns: "1fr 1fr",
                        gap: "24px",
                        marginBottom: "24px",
                      }}
                    >
                      {/* Crisis Score */}
                      <div
                        style={{
                          padding: "20px",
                          background: "rgba(255,255,255,0.6)",
                          borderRadius: "12px",
                          border: "2px solid rgba(0,0,0,0.08)",
                        }}
                      >
                        <div style={{ fontSize: "14px", opacity: 0.6, marginBottom: "8px" }}>
                          Crisis Score
                        </div>
                        <div
                          style={{
                            fontSize: "36px",
                            fontWeight: 800,
                            color: getCrisisInfo(sentimentToday.crisis_score).color,
                          }}
                        >
                          {sentimentToday.crisis_score}
                        </div>
                        <div style={{ fontSize: "12px", opacity: 0.5, marginTop: "4px" }}>
                          = Z-score ({trendAnalysis.z_score}) × Tỉ lệ tiêu cực (
                          {sentimentToday.distribution.negative.percentage}%)
                        </div>
                      </div>

                      {/* Total Articles */}
                      <div
                        style={{
                          padding: "20px",
                          background: "rgba(255,255,255,0.6)",
                          borderRadius: "12px",
                          border: "2px solid rgba(0,0,0,0.08)",
                        }}
                      >
                        <div style={{ fontSize: "14px", opacity: 0.6, marginBottom: "8px" }}>
                          Tổng bài phân tích
                        </div>
                        <div style={{ fontSize: "36px", fontWeight: 800, color: "#4527a0" }}>
                          {sentimentToday.total_articles}
                        </div>
                        <div style={{ fontSize: "12px", opacity: 0.5, marginTop: "4px" }}>
                          bài viết hôm nay
                        </div>
                      </div>
                    </div>

                    {/* Sentiment Distribution */}
                    <div>
                      <h4
                        style={{
                          fontSize: "16px",
                          fontWeight: 700,
                          marginBottom: "16px",
                          opacity: 0.8,
                        }}
                      >
                        📊 Phân bố cảm xúc
                      </h4>

                      <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
                        {/* Positive */}
                        <div>
                          <div
                            style={{
                              display: "flex",
                              justifyContent: "space-between",
                              marginBottom: "8px",
                              fontSize: "14px",
                            }}
                          >
                            <span style={{ fontWeight: 600, color: "#2e7d32" }}>
                              😊 Tích cực
                            </span>
                            <span style={{ fontWeight: 700 }}>
                              {sentimentToday.distribution.positive.count} bài (
                              {sentimentToday.distribution.positive.percentage}%)
                            </span>
                          </div>
                          <div
                            style={{
                              width: "100%",
                              height: "24px",
                              background: "#e8f5e9",
                              borderRadius: "12px",
                              overflow: "hidden",
                            }}
                          >
                            <div
                              style={{
                                width: `${sentimentToday.distribution.positive.percentage}%`,
                                height: "100%",
                                background: "linear-gradient(90deg, #66bb6a 0%, #43a047 100%)",
                                transition: "width 0.5s ease",
                              }}
                            />
                          </div>
                        </div>

                        {/* Neutral */}
                        <div>
                          <div
                            style={{
                              display: "flex",
                              justifyContent: "space-between",
                              marginBottom: "8px",
                              fontSize: "14px",
                            }}
                          >
                            <span style={{ fontWeight: 600, color: "#757575" }}>
                              😐 Trung lập
                            </span>
                            <span style={{ fontWeight: 700 }}>
                              {sentimentToday.distribution.neutral.count} bài (
                              {sentimentToday.distribution.neutral.percentage}%)
                            </span>
                          </div>
                          <div
                            style={{
                              width: "100%",
                              height: "24px",
                              background: "#f5f5f5",
                              borderRadius: "12px",
                              overflow: "hidden",
                            }}
                          >
                            <div
                              style={{
                                width: `${sentimentToday.distribution.neutral.percentage}%`,
                                height: "100%",
                                background: "linear-gradient(90deg, #bdbdbd 0%, #9e9e9e 100%)",
                                transition: "width 0.5s ease",
                              }}
                            />
                          </div>
                        </div>

                        {/* Negative */}
                        <div>
                          <div
                            style={{
                              display: "flex",
                              justifyContent: "space-between",
                              marginBottom: "8px",
                              fontSize: "14px",
                            }}
                          >
                            <span style={{ fontWeight: 600, color: "#c62828" }}>
                              😞 Tiêu cực
                            </span>
                            <span style={{ fontWeight: 700 }}>
                              {sentimentToday.distribution.negative.count} bài (
                              {sentimentToday.distribution.negative.percentage}%)
                            </span>
                          </div>
                          <div
                            style={{
                              width: "100%",
                              height: "24px",
                              background: "#ffebee",
                              borderRadius: "12px",
                              overflow: "hidden",
                            }}
                          >
                            <div
                              style={{
                                width: `${sentimentToday.distribution.negative.percentage}%`,
                                height: "100%",
                                background: "linear-gradient(90deg, #ef5350 0%, #d32f2f 100%)",
                                transition: "width 0.5s ease",
                              }}
                            />
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Day Detail Modal */}
                {selectedDay && (
                  <div
                    onClick={() => setSelectedDay(null)}
                    style={{
                      position: "fixed",
                      top: 0,
                      left: 0,
                      right: 0,
                      bottom: 0,
                      background: "rgba(0,0,0,0.5)",
                      display: "flex",
                      justifyContent: "center",
                      alignItems: "center",
                      zIndex: 1000,
                      padding: "20px",
                    }}
                  >
                    <div
                      onClick={(e) => e.stopPropagation()}
                      style={{
                        background: "white",
                        borderRadius: "16px",
                        padding: "32px",
                        maxWidth: "600px",
                        width: "100%",
                        maxHeight: "80vh",
                        overflowY: "auto",
                        boxShadow: "0 8px 32px rgba(0,0,0,0.2)",
                      }}
                    >
                      {/* Header */}
                      <div
                        style={{
                          display: "flex",
                          justifyContent: "space-between",
                          alignItems: "center",
                          marginBottom: "24px",
                          paddingBottom: "16px",
                          borderBottom: "2px solid rgba(0,0,0,0.1)",
                        }}
                      >
                        <h3
                          style={{
                            margin: 0,
                            fontSize: "24px",
                            fontWeight: 800,
                            color: "#4527a0",
                          }}
                        >
                          📅 {new Date(selectedDay.date).toLocaleDateString("vi-VN", {
                            weekday: "long",
                            year: "numeric",
                            month: "long",
                            day: "numeric",
                          })}
                        </h3>
                        <button
                          onClick={() => setSelectedDay(null)}
                          style={{
                            background: "none",
                            border: "none",
                            fontSize: "24px",
                            cursor: "pointer",
                            padding: "8px",
                            opacity: 0.6,
                            transition: "opacity 0.2s",
                          }}
                          onMouseEnter={(e) => (e.currentTarget.style.opacity = "1")}
                          onMouseLeave={(e) => (e.currentTarget.style.opacity = "0.6")}
                        >
                          ✕
                        </button>
                      </div>

                      {/* Stats Grid */}
                      <div
                        style={{
                          display: "grid",
                          gridTemplateColumns: "repeat(2, 1fr)",
                          gap: "16px",
                          marginBottom: "24px",
                        }}
                      >
                        <div
                          style={{
                            padding: "20px",
                            background: "rgba(69, 39, 160, 0.1)",
                            borderRadius: "12px",
                            border: "2px solid rgba(69, 39, 160, 0.2)",
                          }}
                        >
                          <div style={{ fontSize: "14px", opacity: 0.6, marginBottom: "8px" }}>
                            Số lượng bài
                          </div>
                          <div style={{ fontSize: "32px", fontWeight: 800, color: "#4527a0" }}>
                            {selectedDay.count}
                          </div>
                        </div>

                        <div
                          style={{
                            padding: "20px",
                            background: "rgba(0,0,0,0.05)",
                            borderRadius: "12px",
                            border: "2px solid rgba(0,0,0,0.1)",
                          }}
                        >
                          <div style={{ fontSize: "14px", opacity: 0.6, marginBottom: "8px" }}>
                            Z-Score
                          </div>
                          <div
                            style={{
                              fontSize: "32px",
                              fontWeight: 800,
                              color: getTrendInfo(selectedDay.z_score).color,
                            }}
                          >
                            {selectedDay.z_score > 0 ? "+" : ""}
                            {selectedDay.z_score}
                          </div>
                        </div>

                        <div
                          style={{
                            padding: "20px",
                            background: "rgba(0,0,0,0.05)",
                            borderRadius: "12px",
                            border: "2px solid rgba(0,0,0,0.1)",
                          }}
                        >
                          <div style={{ fontSize: "14px", opacity: 0.6, marginBottom: "8px" }}>
                            Spike
                          </div>
                          <div
                            style={{
                              fontSize: "32px",
                              fontWeight: 800,
                              color: selectedDay.spike > 0 ? "#d32f2f" : "#1976d2",
                            }}
                          >
                            {selectedDay.spike > 0 ? "+" : ""}
                            {selectedDay.spike}%
                          </div>
                        </div>

                        <div
                          style={{
                            padding: "20px",
                            background: getCrisisInfo(calculateDayCrisisScore(selectedDay)).bgColor,
                            borderRadius: "12px",
                            border: `2px solid ${getCrisisInfo(calculateDayCrisisScore(selectedDay)).color}`,
                          }}
                        >
                          <div style={{ fontSize: "14px", opacity: 0.6, marginBottom: "8px" }}>
                            Crisis Score
                          </div>
                          <div
                            style={{
                              fontSize: "32px",
                              fontWeight: 800,
                              color: getCrisisInfo(calculateDayCrisisScore(selectedDay)).color,
                            }}
                          >
                            {calculateDayCrisisScore(selectedDay).toFixed(2)}
                          </div>
                        </div>
                      </div>

                      {/* Sentiment Distribution */}
                      <div>
                        <h4
                          style={{
                            fontSize: "18px",
                            fontWeight: 700,
                            marginBottom: "16px",
                            opacity: 0.8,
                          }}
                        >
                          📊 Phân bố cảm xúc
                        </h4>

                        <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
                          {/* Positive */}
                          <div>
                            <div
                              style={{
                                display: "flex",
                                justifyContent: "space-between",
                                marginBottom: "8px",
                                fontSize: "14px",
                              }}
                            >
                              <span style={{ fontWeight: 600, color: "#2e7d32" }}>
                                😊 Tích cực
                              </span>
                              <span style={{ fontWeight: 700 }}>
                                {selectedDay.sentiment.positive.count} bài (
                                {selectedDay.sentiment.positive.percentage}%)
                              </span>
                            </div>
                            <div
                              style={{
                                width: "100%",
                                height: "24px",
                                background: "#e8f5e9",
                                borderRadius: "12px",
                                overflow: "hidden",
                              }}
                            >
                              <div
                                style={{
                                  width: `${selectedDay.sentiment.positive.percentage}%`,
                                  height: "100%",
                                  background: "linear-gradient(90deg, #66bb6a 0%, #43a047 100%)",
                                  transition: "width 0.5s ease",
                                }}
                              />
                            </div>
                          </div>

                          {/* Neutral */}
                          <div>
                            <div
                              style={{
                                display: "flex",
                                justifyContent: "space-between",
                                marginBottom: "8px",
                                fontSize: "14px",
                              }}
                            >
                              <span style={{ fontWeight: 600, color: "#757575" }}>
                                😐 Trung lập
                              </span>
                              <span style={{ fontWeight: 700 }}>
                                {selectedDay.sentiment.neutral.count} bài (
                                {selectedDay.sentiment.neutral.percentage}%)
                              </span>
                            </div>
                            <div
                              style={{
                                width: "100%",
                                height: "24px",
                                background: "#f5f5f5",
                                borderRadius: "12px",
                                overflow: "hidden",
                              }}
                            >
                              <div
                                style={{
                                  width: `${selectedDay.sentiment.neutral.percentage}%`,
                                  height: "100%",
                                  background: "linear-gradient(90deg, #bdbdbd 0%, #9e9e9e 100%)",
                                  transition: "width 0.5s ease",
                                }}
                              />
                            </div>
                          </div>

                          {/* Negative */}
                          <div>
                            <div
                              style={{
                                display: "flex",
                                justifyContent: "space-between",
                                marginBottom: "8px",
                                fontSize: "14px",
                              }}
                            >
                              <span style={{ fontWeight: 600, color: "#c62828" }}>
                                😞 Tiêu cực
                              </span>
                              <span style={{ fontWeight: 700 }}>
                                {selectedDay.sentiment.negative.count} bài (
                                {selectedDay.sentiment.negative.percentage}%)
                              </span>
                            </div>
                            <div
                              style={{
                                width: "100%",
                                height: "24px",
                                background: "#ffebee",
                                borderRadius: "12px",
                                overflow: "hidden",
                              }}
                            >
                              <div
                                style={{
                                  width: `${selectedDay.sentiment.negative.percentage}%`,
                                  height: "100%",
                                  background: "linear-gradient(90deg, #ef5350 0%, #d32f2f 100%)",
                                  transition: "width 0.5s ease",
                                }}
                              />
                            </div>
                          </div>
                        </div>
                      </div>

                      {/* Dominant Sentiment */}
                      <div
                        style={{
                          marginTop: "24px",
                          padding: "16px",
                          background: "rgba(0,0,0,0.05)",
                          borderRadius: "12px",
                          textAlign: "center",
                        }}
                      >
                        <div style={{ fontSize: "14px", opacity: 0.6, marginBottom: "8px" }}>
                          Cảm xúc chiếm ưu thế
                        </div>
                        <div style={{ fontSize: "20px", fontWeight: 700 }}>
                          {selectedDay.sentiment.positive.percentage > selectedDay.sentiment.negative.percentage &&
                            selectedDay.sentiment.positive.percentage > selectedDay.sentiment.neutral.percentage
                            ? "😊 Tích cực"
                            : selectedDay.sentiment.negative.percentage > selectedDay.sentiment.neutral.percentage
                              ? "😞 Tiêu cực"
                              : "😐 Trung lập"}
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* ===== 24H BLOCK ===== */}
                <div style={{ marginBottom: "48px" }}>
                  <h3
                    style={{
                      marginBottom: "20px",
                      fontSize: "24px",
                      fontWeight: 700,
                      borderBottom: "3px solid rgba(0,0,0,0.15)",
                      paddingBottom: "12px",
                    }}
                  >
                    🔥 24 giờ gần nhất
                  </h3>

                  {articles24h.length === 0 ? (
                    <div
                      style={{
                        padding: "32px",
                        borderRadius: "12px",
                        background: "rgba(255,255,255,0.5)",
                        opacity: 0.75,
                        textAlign: "center",
                        border: "2px dashed rgba(0,0,0,0.1)",
                      }}
                    >
                      Không có tin tức mới thuộc chủ đề{" "}
                      <strong>{topic.name}</strong> trong 24h qua.
                    </div>
                  ) : (
                    <>
                      <div style={{ display: "flex", flexDirection: "column", gap: "0" }}>
                        {current24hNews.map((news) => (
                          <NewsCard key={news.id} {...news} />
                        ))}
                      </div>
                      {renderPagination(currentPage24h, totalPages24h, handlePageChange24h)}
                    </>
                  )}
                </div>

                <hr
                  style={{
                    margin: "48px 0",
                    border: "none",
                    borderTop: "2px solid rgba(0,0,0,0.1)",
                  }}
                />

                {/* ===== HISTORY BLOCK ===== */}
                <div>
                  <h3
                    style={{
                      marginBottom: "20px",
                      fontSize: "24px",
                      fontWeight: 700,
                      borderBottom: "3px solid rgba(0,0,0,0.15)",
                      paddingBottom: "12px",
                    }}
                  >
                    📰 Bài viết trước đó
                  </h3>

                  {articlesHistory.length === 0 ? (
                    <div
                      style={{
                        padding: "32px",
                        textAlign: "center",
                        opacity: 0.6,
                      }}
                    >
                      Chưa có bài viết nào cho chủ đề này.
                    </div>
                  ) : (
                    <>
                      <div style={{ display: "flex", flexDirection: "column", gap: "0" }}>
                        {currentHistoryNews.map((news) => (
                          <NewsCard key={news.id} {...news} />
                        ))}
                      </div>
                      {renderPagination(currentPageHistory, totalPagesHistory, handlePageChangeHistory)}
                    </>
                  )}
                </div>
              </>
            )}
          </div>
        </div>
      </main>

      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 0.6; }
          50% { opacity: 0.8; }
        }
        
        @keyframes pulse-bar {
          0%, 100% { 
            transform: scaleY(1);
            box-shadow: 0 4px 12px rgba(211,47,47,0.3);
          }
          50% { 
            transform: scaleY(1.05);
            box-shadow: 0 6px 16px rgba(211,47,47,0.5);
          }
        }
      `}</style>

      <Footer />
    </div>
  );
};

export default TopicPage;
