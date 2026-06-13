// FeedbackFeed — Displays feedback from different audience perspectives
"use client";

import { useStore, FeedbackPayload } from "@/lib/store";
import { AlertCircle, ThumbsUp, ThumbsDown, HelpCircle } from "lucide-react";

interface FeedbackItemProps {
  feedback: FeedbackPayload;
}

function FeedbackIcon({ type }: { type: string }) {
  switch (type) {
    case "constructive":
      return <ThumbsUp className="w-4 h-4 text-green-600" />;
    case "critical":
      return <AlertCircle className="w-4 h-4 text-red-600" />;
    case "skeptical":
      return <HelpCircle className="w-4 h-4 text-yellow-600" />;
    case "supportive":
      return <ThumbsUp className="w-4 h-4 text-blue-600" />;
    default:
      return <AlertCircle className="w-4 h-4 text-gray-600" />;
  }
}

function FeedbackItem({ feedback }: FeedbackItemProps) {
  return (
    <div
      className="fl-card p-3 mb-2 border-l-4"
      style={{
        borderColor:
          feedback.feedback_type === "critical"
            ? "#e11d48"
            : feedback.feedback_type === "skeptical"
              ? "#ea580c"
              : feedback.feedback_type === "constructive"
                ? "#16a34a"
                : "#2563eb",
      }}
    >
      <div className="flex items-start gap-2">
        <div className="mt-1">
          <FeedbackIcon type={feedback.feedback_type} />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="font-medium text-xs" style={{ color: "var(--color-btn-action)" }}>
              {feedback.location} — {feedback.group}
            </span>
            <span className="text-xs px-1.5 py-0.5 rounded bg-gray-200">
              Relevance: {feedback.relevance_score}/10
            </span>
          </div>

          <p className="text-xs mb-1" style={{ color: "var(--color-on-surface)" }}>
            <span className="font-medium">Main Concern:</span> {feedback.key_concern}
          </p>

          {feedback.cultural_note && (
            <p className="text-xs mb-1 p-1.5 bg-amber-50 rounded border border-amber-200">
              <span className="font-medium">Cultural Note:</span> {feedback.cultural_note}
            </p>
          )}

          <div className="text-xs bg-gray-50 p-1.5 rounded border border-gray-200 mb-1">
            <span className="font-medium">They would ask:</span> "{feedback.critical_question}"
          </div>

          <p className="text-xs mb-1">
            <span className="font-medium">Recommendation:</span> {feedback.recommendation}
          </p>

          <p className="text-xs" style={{ color: "var(--color-outline)" }}>
            <span className="font-medium">Values Alignment:</span> {feedback.alignment_with_values}
          </p>
        </div>
      </div>
    </div>
  );
}

export function FeedbackFeed() {
  const feedbacks = useStore((s) => s.feedbacks);

  if (!feedbacks || feedbacks.length === 0) {
    return (
      <div className="rounded border p-4 text-center" style={{ borderColor: "var(--color-outline-variant)" }}>
        <p className="text-xs opacity-60">Feedback from different perspectives will appear here</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-2 max-h-96 overflow-y-auto">
      {feedbacks.map((feedback, idx) => (
        <FeedbackItem key={idx} feedback={feedback} />
      ))}
    </div>
  );
}
