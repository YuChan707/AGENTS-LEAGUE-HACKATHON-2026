// WebSocket hook + event routing.
// Scaffold: connects to NEXT_PUBLIC_WS_URL, parses incoming agent messages,
// and routes them into the Zustand store. Fill in connection lifecycle and
// the event -> store mapping.

import { useEffect } from "react";

export function useWebSocket(url?: string) {
  useEffect(() => {
    if (!url) return;
    // const ws = new WebSocket(url);
    // ws.onmessage = (e) => route(JSON.parse(e.data));
    // return () => ws.close();
  }, [url]);
}
