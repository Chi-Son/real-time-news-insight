import React, { useState, useEffect } from "react";
import { theme } from "../styles/theme";
import Header from "../components/Header";
import NewsCard from "../components/NewsCard";
import RankingBox from "../components/RankingBox";

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

  // Fetch latest articles from API
  useEffect(() => {
    const fetchArticles = async () => {
      try {
        const res = await fetch(
          "http://localhost:8001/api/articles/latest?limit=20"
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

  // Filter by keyword
  const filtered = newsList.filter((n) =>
    n.title.toLowerCase().includes(keyword.toLowerCase())
  );

  return (
    <div
      style={{
        minHeight: "100vh",
        background: theme.colors.background,
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
            padding: "32px 16px",
          }}
        >
          <div
            style={{
              display: "flex",
              gap: "32px",
              maxWidth: "1200px", // tổng width tối đa để căn giữa
              width: "100%",
              flexWrap: "wrap",
              justifyContent: "center", // căn giữa nội dung bên trong
            }}
          >
            {/* Cột trái: RankingBox */}
            <div style={{ flex: "0 0 320px" }}>
              <RankingBox />
            </div>

            {/* Cột phải: NewsCard */}
            <div style={{ flex: "1 1 600px", minWidth: "320px" }}>
              {loading ? (
                <p>Đang tải bài viết...</p>
              ) : filtered.length === 0 ? (
                <p>Không có bài viết nào.</p>
              ) : (
                filtered.map((news) => (
                  <div key={news.id} style={{ marginBottom: "16px" }}>
                    <NewsCard {...news} />
                  </div>
                ))
              )}
            </div>
          </div>
        </main>


    </div>
  );
};

export default Home;
