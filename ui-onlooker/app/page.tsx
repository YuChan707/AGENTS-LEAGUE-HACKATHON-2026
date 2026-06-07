// Main dashboard page.
// Scaffold: compose SessionSetup + the agent/score/feed panels here, wired
// to the Zustand store and the WebSocket hook (see lib/).

export default function Page() {
  return (
    <main className="min-h-screen p-6">
      <h1 className="text-2xl font-semibold">OnLooker</h1>
      <p className="text-sm opacity-70">Dashboard scaffold — wire up panels here.</p>
    </main>
  );
}
