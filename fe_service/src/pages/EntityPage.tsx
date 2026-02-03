import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { theme } from "../styles/theme";
import Header from "../components/Header";
import NewsCard from "../components/NewsCard";
import Footer from "../components/Footer";

type Entity = {
    entity_id: number;
    text: string;
    type: string;
};

type NewsItem = {
    id: number;
    title: string;
    published_at: string;
    source?: string;
    url: string;
    sentiment?: string;
    category?: string;
};

const EntityPage: React.FC = () => {
    const { entityId } = useParams<{ entityId: string }>();

    const [entity, setEntity] = useState<Entity | null>(null);
    const [articles24h, setArticles24h] = useState<NewsItem[]>([]);
    const [articlesHistory, setArticlesHistory] = useState<NewsItem[]>([]);
    const [loading, setLoading] = useState<boolean>(true);
    const [keyword, setKeyword] = useState("");
    const [currentPage24h, setCurrentPage24h] = useState(1);
    const [currentPageHistory, setCurrentPageHistory] = useState(1);
    const itemsPerPage = 5;

    useEffect(() => {
        const fetchEntityArticles = async () => {
            try {
                const res = await fetch(
                    `http://localhost:8001/api/entities/${entityId}`
                );
                const data = await res.json();

                setEntity(data.entity);
                setArticles24h(data.articles_24h || []);
                setArticlesHistory(data.articles_history || []);
            } catch (err) {
                console.error("Failed to fetch entity articles", err);
            } finally {
                setLoading(false);
            }
        };

        fetchEntityArticles();
    }, [entityId]);

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

    const getEntityTypeLabel = (type: string) => {
        const typeMap: Record<string, string> = {
            "PERSON": "Nhân vật",
            "ORGANIZATION": "Tổ chức",
            "LOCATION": "Địa điểm",
            "EVENT": "Sự kiện",
            "PRODUCT": "Sản phẩm",
            "OTHER": "Khác"
        };
        return typeMap[type] || type;
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
                                    Đang tải dữ liệu thực thể...
                                </div>
                            </div>
                        ) : !entity ? (
                            <div
                                style={{
                                    textAlign: "center",
                                    padding: "80px 20px",
                                    opacity: 0.6,
                                }}
                            >
                                <p style={{ fontSize: "18px" }}>Không tìm thấy thực thể.</p>
                            </div>
                        ) : (
                            <>
                                {/* Header Entity */}
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
                                    <div style={{ display: "flex", alignItems: "center", gap: "16px", marginBottom: "12px" }}>
                                        <h1
                                            style={{
                                                margin: 0,
                                                fontSize: "36px",
                                                fontWeight: 800,
                                                letterSpacing: "-1px",
                                                color: "#1976d2",
                                            }}
                                        >
                                            {entity.text}
                                        </h1>
                                        <span
                                            style={{
                                                padding: "6px 16px",
                                                background: "rgba(25, 118, 210, 0.12)",
                                                color: "#1976d2",
                                                borderRadius: "8px",
                                                fontSize: "13px",
                                                fontWeight: 700,
                                                textTransform: "uppercase",
                                                letterSpacing: "0.5px",
                                            }}
                                        >
                                            {getEntityTypeLabel(entity.type)}
                                        </span>
                                    </div>

                                    <p
                                        style={{
                                            opacity: 0.7,
                                            fontSize: "15px",
                                            margin: 0,
                                        }}
                                    >
                                        Thực thể được nhắc đến trong các bài viết tin tức
                                    </p>
                                </div>

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
                                            Không có tin tức mới về{" "}
                                            <strong>{entity.text}</strong> trong 24h qua.
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
                                            Chưa có bài viết nào về thực thể này.
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
      `}</style>

            <Footer />
        </div>
    );
};

export default EntityPage;
