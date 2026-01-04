import React, { useEffect, useState } from 'react';

interface Topic {
  topic_id: string;
  score: number;
}

interface WebSocketData {
  type: string;
  data: Topic[];
  updated_at: number;
}

const RankingBox: React.FC = () => {
  const [topics, setTopics] = useState<Topic[]>([]);

  useEffect(() => {
    // URL WebSocket backend của bạn
    const ws = new WebSocket('ws://localhost:8000/ws/topics');

    ws.onmessage = (event) => {
      try {
        const response: WebSocketData = JSON.parse(event.data);
        if (response.type === 'topic_score_update') {
          setTopics(response.data.slice(0, 20)); // top 20
        }
      } catch (err) {
        console.error('Failed to parse WebSocket message', err);
      }
    };

    ws.onerror = (error) => console.error('WebSocket Error:', error);

    return () => ws.close();
  }, []);

  return (
    <div className="p-4 bg-[#f4e4bc] border-2 border-[#5d4037] max-w-md font-sans text-[#3e2723]">
      <h2 className="text-2xl font-bold text-center border-b border-[#5d4037] pb-2 mb-2 uppercase">
        Top Topics
      </h2>

      <div className="space-y-2 max-h-[400px] overflow-y-auto">
        {topics.length > 0 ? (
          topics.map((topic, index) => (
            <div
              key={topic.topic_id}
              className="flex justify-between border-b border-[#a1887f] py-1 px-2"
            >
              <span className="font-semibold">{topic.topic_id}</span>
              <span className="font-mono">{topic.score.toFixed(2)}</span>
            </div>
          ))
        ) : (
          <p className="text-center italic opacity-60">Waiting for topics...</p>
        )}
      </div>
    </div>
  );
};

export default RankingBox;
