import React, { useState } from "react";
import NewsCard from "../components/NewsCard";
import SearchBar from "../components/SearchBar";

const Home: React.FC = () => {
  const [keyword, setKeyword] = useState("");

  // Mock data để test UI
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
    <div style={{ maxWidth: 800, margin: "0 auto", padding: 24 }}>
      <SearchBar onSearch={setKeyword} />

      {mockNews
        .filter((n) =>
          n.title.toLowerCase().includes(keyword.toLowerCase())
        )
        .map((news, idx) => (
          <NewsCard key={idx} {...news} />
        ))}
    </div>
  );
};

export default Home;
