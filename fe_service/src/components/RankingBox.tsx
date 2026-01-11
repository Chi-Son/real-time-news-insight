import React, { useEffect, useState } from "react";

interface Topic {
  topic_id: string;
  topic_name: string;
  score: number;
}

interface RankingApiResponse {
  data: Topic[];
  updated_at: number;
}

interface WebSocketData {
  type: string;
  data: Topic[];
  updated_at: number;
}

const RankingBox: React.FC = () => {
  const [topics, setTopics] = useState<Topic[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("http://localhost:8001/api/topics/ranking?limit=20")
      .then((res) => res.json())
      .then((data: RankingApiResponse) => setTopics(data.data))
      .catch((err) => console.error("Failed to fetch ranking", err))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    const ws = new WebSocket("ws://0.0.0.0:8000/ws/topics");

    ws.onmessage = (event) => {
      try {
        const msg: WebSocketData = JSON.parse(event.data);
        if (msg.type === "topic_score_update") {
          setTopics(msg.data.slice(0, 20));
        }
      } catch (err) {
        console.error("WebSocket parse error", err);
      }
    };

    ws.onerror = (err) => console.error("WebSocket error", err);
    return () => ws.close();
  }, []);

  return (
    <div className="p-4 bg-[#f4e4bc] border-2 border-[#5d4037] max-w-md font-sans text-[#3e2723] rounded-lg shadow-lg">
      <h2 className="text-2xl font-bold text-center border-b border-[#5d4037] pb-2 mb-4 uppercase">
        Top Topics (24h)
      </h2>

      {loading ? (
        <p className="text-center italic opacity-60">Loading ranking...</p>
      ) : topics.length === 0 ? (
        <p className="text-center italic opacity-60">
          No active topics in last 24h
        </p>
      ) : (
          <div className="overflow-y-auto max-h-[400px]">
            <table className="min-w-full border-collapse table-auto table-fixed">
              <thead>
                <tr className="bg-[#e0cfa0] sticky top-0">
                  <th className="text-left px-3 py-2 border-b border-[#a1887f] w-12">#</th>
                  <th className="text-left px-3 py-2 border-b border-[#a1887f]">Topic</th>
                  <th className="text-right px-3 py-2 border-b border-[#a1887f] w-20">Score</th>
                </tr>
              </thead>
              <tbody>
                {topics.map((topic, index) => (
                  <tr
                    key={topic.topic_id}
                    className="hover:bg-[#efdfb3] cursor-pointer"
                    onClick={() => window.location.href = `/topics/${topic.topic_id}`}
                  >
                    <td className="px-3 py-2 border-b border-[#d7c4a1] font-semibold">{index + 1}</td>
                    <td className="px-3 py-2 border-b border-[#d7c4a1] whitespace-nowrap truncate">{topic.topic_name}</td>
                    <td className="px-3 py-2 border-b border-[#d7c4a1] font-mono text-right">{topic.score.toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

      )}
    </div>
  );
};

export default RankingBox;
