import React from "react";
import { theme } from "../styles/theme";

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
  const firstSentence = content.split(".")[0] + ".";

  return (
    <article
      onClick={() => window.open(url, "_blank")}
      style={{
        padding: "16px 0",
        borderBottom: `1px solid ${theme.colors.border}`,
        cursor: "pointer",
      }}
    >
      <h2 style={{ margin: "0 0 8px 0" }}>{title}</h2>
      <p style={{ margin: "0 0 6px 0", opacity: 0.9 }}>
        {firstSentence}
      </p>
      {source && (
        <small style={{ opacity: 0.7 }}>Nguồn: {source}</small>
      )}
    </article>
  );
};

export default NewsCard;
