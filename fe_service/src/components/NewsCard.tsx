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
  const firstSentence =
    content.split(".")[0] + (content.includes(".") ? "." : "");

  return (
    <article
      onClick={() => window.open(url, "_blank")}
      style={{
        padding: "18px 0",
        borderBottom: "1px solid rgba(0,0,0,0.15)",
        cursor: "pointer",
        fontFamily: theme.fonts.body,
      }}
    >
      <h3 style={{ margin: "0 0 6px 0" }}>{title}</h3>
      <p style={{ margin: "0 0 6px 0", opacity: 0.9 }}>
        {firstSentence}
      </p>
      {source && <small style={{ opacity: 0.7 }}>Nguồn: {source}</small>}
    </article>
  );
};

export default NewsCard;
