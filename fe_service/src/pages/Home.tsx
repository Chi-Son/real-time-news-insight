import React, { useState } from "react";
import NewsCard from "../components/NewsCard";
import { theme } from "../styles/theme";

const Home: React.FC = () => {
  const [keyword, setKeyword] = useState("");

  const mockNews = [
    {
      title: "Lạm phát tháng 11 tăng mạnh",
      content:
        "Lạm phát trong tháng 11 ghi nhận mức tăng cao nhất trong vòng 2 năm qua. Nguyên nhân chính đến từ giá năng lượng.",
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

  return (
    <main
      style={{
        display: "grid",
        gridTemplateColumns: "1fr 3fr 1fr",
        background: theme.colors.background,
        color: theme.colors.text,
        fontFamily: theme.fonts.body,
        minHeight: "100vh",
      }}
    >
      <div />
      <div style={{ padding: "24px" }}>
        {mockNews
          .filter((n) =>
            n.title.toLowerCase().includes(keyword.toLowerCase())
          )
          .map((news, idx) => (
            <NewsCard key={idx} {...news} />
          ))}
      </div>
      <div />
    </main>
  );
};

export default Home;
