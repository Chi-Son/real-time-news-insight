import React from "react";

type NewsCardProps = {
  title: string;
  content: string;
  source?: string;
  url: string;
};

const NewsCard: React.FC<NewsCardProps> = ({
  title,
  content,
  source,
  url,
}) => {
  // Lấy câu đầu tiên (đơn giản theo dấu chấm)
  const firstSentence = content.split(".")[0] + ".";

  const handleClick = () => {
    window.open(url, "_blank", "noopener,noreferrer");
  };

  return (
    <div
      onClick={handleClick}
      style={{
        border: "1px solid #e5e7eb",
        borderRadius: 8,
        padding: 12,
        cursor: "pointer",
        marginBottom: 12,
      }}
    >
      <h3 style={{ margin: "0 0 8px 0" }}>{title}</h3>

      <p style={{ margin: "0 0 8px 0", color: "#374151" }}>
        {firstSentence}
      </p>

      {source && (
        <small style={{ color: "#6b7280" }}>
          Nguồn: {source}
        </small>
      )}
    </div>
  );
};

export default NewsCard;
