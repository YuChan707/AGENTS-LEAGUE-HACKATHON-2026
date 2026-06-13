import { useCallback, useEffect, useRef } from "react";
import { useStore } from "./store";

const WS_BASE =
  (typeof process !== "undefined" && process.env.NEXT_PUBLIC_WS_URL) ||
  "ws://localhost:8000";

// Module-level singleton so all components share one connection
let _ws: WebSocket | null = null;

export function useWebSocket() {
  const { sessionConfig, setConnected, setSessionId, addEvent } = useStore();
  const configRef = useRef(sessionConfig);
  useEffect(() => { configRef.current = sessionConfig; }, [sessionConfig]);

  const connect = useCallback(() => {
    if (
      _ws &&
      (_ws.readyState === WebSocket.CONNECTING ||
        _ws.readyState === WebSocket.OPEN)
    ) return;

    _ws = new WebSocket(`${WS_BASE}/ws/stream`);

    _ws.onopen = () => {
      setConnected(true);
      _ws!.send(
        JSON.stringify({
          type: "init",
          persona: configRef.current.personaType,
          region: configRef.current.region,
          focus_area: configRef.current.focusArea,
        })
      );
    };

    _ws.onmessage = (e) => {
      try {
        const msg = JSON.parse(e.data as string);
        if (msg.type === "session_ready") {
          setSessionId(msg.session_id);
          return;
        }
        if (msg.agent && msg.payload) {
          addEvent(msg.agent, msg.payload);
        }
      } catch {
        // ignore malformed frames
      }
    };

    _ws.onclose = () => {
      setConnected(false);
      _ws = null;
    };

    _ws.onerror = () => {
      setConnected(false);
    };
  }, [setConnected, setSessionId, addEvent]);

  const disconnect = useCallback(() => {
    _ws?.close();
    _ws = null;
    setConnected(false);
  }, [setConnected]);

  const sendTranscript = useCallback((text: string) => {
    if (_ws?.readyState === WebSocket.OPEN) {
      _ws.send(JSON.stringify({ type: "transcript_chunk", text }));
    }
  }, []);

  const sendFrame = useCallback((imageBase64: string) => {
    if (_ws?.readyState === WebSocket.OPEN) {
      _ws.send(JSON.stringify({ type: "video_frame", image_base64: imageBase64 }));
    }
  }, []);

  useEffect(() => {
    return () => { /* intentionally leave singleton alive across component mounts */ };
  }, []);

  return { connect, disconnect, sendTranscript, sendFrame };
}
