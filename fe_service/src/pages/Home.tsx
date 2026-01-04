import React, { useState } from "react";
import { theme } from "../styles/theme";
import Header from "../components/Header";
import NewsCard from "../components/NewsCard";
import RankingBox from "../components/RankingBox";

type NewsItem = {
  title: string;
  content: string;
  source?: string;
  url: string;
};

const Home: React.FC = () => {
  const [keyword, setKeyword] = useState("");

  const mockNews: NewsItem[] = [
    {
      title: "Lạm phát tháng 11 tăng mạnh",
      content:
        "Lạm phát trong tháng 11 ghi nhận mức tăng cao nhất trong vòng 2 năm qua.",
      source: "VnExpress",
      url: "https://vnexpress.net",
    },
    {
      title: "Thị trường chứng khoán biến động",
      content:
        "Thị trường chứng khoán hôm nay biến động mạnh do ảnh hưởng từ thị trường quốc tế.",
      source: "CafeF",
      url: "https://cafef.vn",
    },
  ];

  const filtered = mockNews.filter((n) =>
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
          padding: "32px 16px",
          gap: "24px", // khoảng cách giữa RankingBox và NewsCard
        }}
      >
        {/* Cột trái: RankingBox */}
        <div style={{ flex: "0 0 320px" }}>
          <RankingBox />
        </div>

        {/* Cột phải: NewsCard */}
        <div style={{ flex: 1 }}>
          {filtered.map((news, idx) => (
            <div
              key={idx}
              style={{ marginLeft: "16px", marginBottom: "16px" }} // lệch sang phải + khoảng cách
            >
              <NewsCard {...news} />
            </div>
          ))}
        </div>
      </main>
    </div>
  );
};

export default Home;
