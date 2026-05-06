import { useEffect, useMemo, useState } from "react";

type StatusVariant = "default" | "ok" | "warn";

type StatusState = {
  text: string;
  variant: StatusVariant;
};

type LmsStrategyId = "foundations" | "balanced" | "intensive";

type StartSessionResponse = {
  session_id: string;
  source_type: "text" | "domain_link";
  first_question?: string;
  first_options: string[];
  source_summary: string;
  scan_status: "scanning" | "ready" | "failed";
  scan_progress: number;
  scan_message: string;
};

type QuestionTurnResponse = {
  status: "questioning" | "ready_for_generation";
  confidence_score: number;
  next_question?: string;
  next_options?: string[];
  allow_custom_answer?: boolean;
};

type LmsStrategyOption = {
  id: LmsStrategyId;
  title: string;
  subtitle: string;
  timeline_weeks: number;
  highlights: string[];
  roadmap_preview: Array<Record<string, string>>;
};

type PlanResponse = {
  session_id: string;
  source_summary: string;
  profile_preview: Record<string, string>;
  roadmap_preview: Array<Record<string, string>>;
  recommendations: string[];
  readiness_score: number;
  confidence_low: boolean;
  confidence_threshold: number;
  lms_strategy_options: LmsStrategyOption[];
  recommended_strategy_id: LmsStrategyId;
};

type ScanStatusResponse = {
  session_id: string;
  scan_status: "scanning" | "ready" | "failed";
  scan_progress: number;
  scan_message: string;
  source_summary: string;
  first_question?: string;
  first_options: string[];
};

type StepState = "pending" | "active" | "done";

/** Backend origin: build-time env, optional localStorage override for dev only (no UI). */
function resolveApiBase(): string {
  const fromEnv = import.meta.env.VITE_API_BASE_URL as string | undefined;
  if (fromEnv?.trim()) return fromEnv.trim().replace(/\/$/, "");
  try {
    const stored = window.localStorage.getItem("API_BASE_URL");
    if (stored?.trim()) return stored.trim().replace(/\/$/, "");
  } catch {
    /* ignore */
  }
  return "http://127.0.0.1:8000";
}

const OPTION_LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";

function App() {
  const [sourceType, setSourceType] = useState<"text" | "domain_link">("domain_link");
  const [domainInput, setDomainInput] = useState<string>(
    "https://developer.mozilla.org/en-US/docs/Web/JavaScript",
  );
  const [textInput, setTextInput] = useState<string>(
    "I want an LMS platform for onboarding full-stack web developers with practical projects.",
  );
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [sourceSummary, setSourceSummary] = useState<string>("-");
  const [currentQuestion, setCurrentQuestion] = useState<string>("No question yet.");
  const [currentOptions, setCurrentOptions] = useState<string[]>([]);
  const [selectedOption, setSelectedOption] = useState<string>("");
  const [customAnswer, setCustomAnswer] = useState<string>("");
  const [questionStatus, setQuestionStatus] = useState<string>("Status: waiting for session");
  const [output, setOutput] = useState<string>("No LMS generated yet.");
  const [plan, setPlan] = useState<PlanResponse | null>(null);
  const [selectedStrategyId, setSelectedStrategyId] = useState<LmsStrategyId>("balanced");
  const [status, setStatus] = useState<StatusState>({ text: "Idle", variant: "default" });
  const [ready, setReady] = useState<boolean>(false);
  const [busy, setBusy] = useState<boolean>(false);
  const [error, setError] = useState<string>("");
  const [scanStep, setScanStep] = useState<string>("");
  const [scanProgress, setScanProgress] = useState<number>(0);
  const [planLoading, setPlanLoading] = useState<boolean>(false);
  const [lastAppliedStrategy, setLastAppliedStrategy] = useState<LmsStrategyId | null>(null);

  const canAnswer = !!sessionId && !busy;
  const canGenerate = !!sessionId && ready && !busy;

  const stepStates: StepState[] = useMemo(() => {
    const message = (scanStep || "").toLowerCase();
    let activeIndex = 0;
    if (message.includes("scanning domain") || message.includes("analyzing text")) activeIndex = 1;
    else if (message.includes("building interview")) activeIndex = 2;
    else if (status.text === "Interview Active" || ready) activeIndex = 3;
    else if (
      message.includes("validating") ||
      message.includes("processing") ||
      message.includes("submitting")
    )
      activeIndex = 0;

    if (status.text === "Interview Active" || ready) {
      return ["done", "done", "done", "active"];
    }
    return [0, 1, 2, 3].map((idx) => {
      if (idx < activeIndex) return "done";
      if (idx === activeIndex) return "active";
      return "pending";
    });
  }, [scanStep, status.text, ready]);

  const statusPillClass = useMemo(() => {
    if (status.variant === "ok") return "status-pill ok";
    if (status.variant === "warn") return "status-pill warn";
    return "status-pill";
  }, [status.variant]);

  async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
    const response = await fetch(`${resolveApiBase()}${path}`, {
      headers: { "Content-Type": "application/json" },
      ...options,
    });
    if (!response.ok) {
      const raw = await response.text();
      throw new Error(raw || `Request failed: ${response.status}`);
    }
    return (await response.json()) as T;
  }

  async function loadPlan(sid: string): Promise<PlanResponse> {
    setPlanLoading(true);
    try {
      const data = await api<PlanResponse>(`/api/session/${sid}/plan`);
      setPlan(data);
      setSelectedStrategyId(data.recommended_strategy_id);
      return data;
    } finally {
      setPlanLoading(false);
    }
  }

  useEffect(() => {
    if (!ready || !sessionId) return;
    let cancelled = false;
    void (async () => {
      try {
        await loadPlan(sessionId);
      } catch {
        if (!cancelled) {
          setPlan(null);
          setPlanLoading(false);
        }
      }
    })();
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps -- reload plan when interview completes
  }, [ready, sessionId]);

  async function startInterview(): Promise<void> {
    setError("");
    setStatus({ text: "Starting", variant: "warn" });
    setBusy(true);
    setScanStep("Submitting source...");
    setScanProgress(0);
    setPlan(null);
    setLastAppliedStrategy(null);
    try {
      const sourceValue = sourceType === "domain_link" ? domainInput.trim() : textInput.trim();
      const data = await api<StartSessionResponse>("/api/session/start", {
        method: "POST",
        body: JSON.stringify({
          source_type: sourceType,
          source_value: sourceValue,
        }),
      });
      setSessionId(data.session_id);
      setOutput("No LMS generated yet.");
      setReady(false);
      setSelectedOption("");
      setCustomAnswer("");

      let scanStatus: ScanStatusResponse = {
        session_id: data.session_id,
        scan_status: data.scan_status,
        scan_progress: data.scan_progress,
        scan_message: data.scan_message,
        source_summary: data.source_summary,
        first_question: data.first_question,
        first_options: data.first_options || [],
      };
      let guard = 0;
      while (scanStatus.scan_status === "scanning" && guard < 45) {
        setScanStep(scanStatus.scan_message || "Scanning...");
        setScanProgress(scanStatus.scan_progress || 0);
        await new Promise((resolve) => window.setTimeout(resolve, 900));
        scanStatus = await api<ScanStatusResponse>(`/api/session/${data.session_id}/scan-status`);
        guard += 1;
      }

      if (scanStatus.scan_status === "failed") {
        throw new Error("Failed to scan and prepare interview from provided source.");
      }
      if (scanStatus.scan_status !== "ready") {
        throw new Error("Scan took too long. Please retry.");
      }

      setSourceSummary(scanStatus.source_summary || "-");
      setCurrentQuestion(scanStatus.first_question || "No question returned.");
      setCurrentOptions(scanStatus.first_options || []);
      setQuestionStatus("Status: questioning");
      setStatus({ text: "Interview Active", variant: "ok" });
      setScanStep("");
      setScanProgress(100);
    } catch (err) {
      setStatus({ text: "Error", variant: "default" });
      setError(err instanceof Error ? err.message : String(err));
      setScanStep("");
      setScanProgress(0);
    } finally {
      setBusy(false);
    }
  }

  function resetAll(): void {
    setSessionId(null);
    setSourceSummary("-");
    setCurrentQuestion("No question yet.");
    setQuestionStatus("Status: waiting for session");
    setOutput("No LMS generated yet.");
    setPlan(null);
    setReady(false);
    setBusy(false);
    setCurrentOptions([]);
    setSelectedOption("");
    setCustomAnswer("");
    setScanStep("");
    setScanProgress(0);
    setError("");
    setPlanLoading(false);
    setSelectedStrategyId("balanced");
    setLastAppliedStrategy(null);
    setStatus({ text: "Idle", variant: "default" });
  }

  async function submitAnswerWithValue(answer: string): Promise<void> {
    if (!sessionId || busy) return;
    const cleaned = answer.trim();
    if (!cleaned) {
      setError("Please select an option or enter your own answer.");
      return;
    }

    setError("");
    setBusy(true);
    try {
      const data = await api<QuestionTurnResponse>(`/api/session/${sessionId}/answer`, {
        method: "POST",
        body: JSON.stringify({ answer: cleaned }),
      });
      setQuestionStatus(`Status: ${data.status}, confidence: ${data.confidence_score}`);
      if (data.status === "questioning") {
        setCurrentQuestion(data.next_question || "-");
        setCurrentOptions(data.next_options || []);
        setSelectedOption("");
        setCustomAnswer("");
        setStatus({ text: "Interview Active", variant: "ok" });
      } else {
        setCurrentQuestion("Interview complete. Choose your LMS path, then generate.");
        setCurrentOptions([]);
        setSelectedOption("");
        setCustomAnswer("");
        setReady(true);
        setStatus({ text: "Ready To Generate", variant: "ok" });
      }
    } catch (err) {
      setStatus({ text: "Error", variant: "default" });
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  async function submitAnswer(): Promise<void> {
    if (!canAnswer) return;
    const cleaned =
      selectedOption === "__other__" ? customAnswer.trim() : selectedOption.trim();
    await submitAnswerWithValue(cleaned);
  }

  function onSelectMcqOption(option: string): void {
    if (!sessionId || busy || ready) return;
    setSelectedOption(option);
    void submitAnswerWithValue(option);
  }

  function onSelectOther(): void {
    if (!sessionId || busy || ready) return;
    setSelectedOption("__other__");
  }

  async function previewPlan(): Promise<void> {
    if (!sessionId || busy) return;
    setError("");
    setStatus({ text: "Preparing Plan", variant: "warn" });
    setBusy(true);
    try {
      const data = await loadPlan(sessionId);
      setOutput(JSON.stringify(data, null, 2));
      setStatus({ text: "Plan Ready", variant: "ok" });
    } catch (err) {
      setStatus({ text: "Error", variant: "default" });
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  async function generateLms(): Promise<void> {
    if (!canGenerate) return;
    setError("");
    setStatus({ text: "Generating", variant: "warn" });
    setBusy(true);
    try {
      const data = await api<Record<string, unknown>>(`/api/session/${sessionId}/generate-lms`, {
        method: "POST",
        body: JSON.stringify({ strategy_id: selectedStrategyId }),
      });
      setOutput(JSON.stringify(data, null, 2));
      const applied = data.applied_strategy as LmsStrategyId | undefined;
      if (applied) setLastAppliedStrategy(applied);
      setStatus({ text: "LMS Generated", variant: "ok" });
    } catch (err) {
      setStatus({ text: "Error", variant: "default" });
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="app-shell">
      <header className="hero">
        <div className="hero-copy">
          <div className="eyebrow">Adaptive learning</div>
          <h1 className="title">Design an LMS from any domain, in minutes.</h1>
          <p className="subtitle">
            Paste a page URL (we scan it) or a short text brief (we analyze it), run a quick adaptive
            interview, then pick one of three curriculum paths before we generate your roadmap.
          </p>
        </div>
        <div className={statusPillClass}>{status.text}</div>
      </header>

      <div className="layout">
        <section className="glass panel">
          <div className="panel-head">
            <h2 className="section-title">Workflow</h2>
            <span className="step-num">Source · Interview · Build</span>
          </div>

          <div className="step">
            <label className="field-label">1 · Source</label>
            <div className="segmented">
              <button
                type="button"
                className={sourceType === "domain_link" ? "active" : ""}
                onClick={() => setSourceType("domain_link")}
                disabled={busy}
              >
                Domain link
              </button>
              <button
                type="button"
                className={sourceType === "text" ? "active" : ""}
                onClick={() => setSourceType("text")}
                disabled={busy}
              >
                Text brief
              </button>
            </div>
            {sourceType === "domain_link" ? (
              <>
                <label className="field-label" htmlFor="domainInput">
                  URL to scan
                </label>
                <input
                  id="domainInput"
                  className="input"
                  value={domainInput}
                  onChange={(e) => setDomainInput(e.target.value)}
                  disabled={busy}
                />
              </>
            ) : (
              <>
                <label className="field-label" htmlFor="textInput">
                  Describe the LMS you need
                </label>
                <textarea
                  id="textInput"
                  rows={5}
                  value={textInput}
                  onChange={(e) => setTextInput(e.target.value)}
                  disabled={busy}
                />
              </>
            )}
            <div className="btn-row">
              <button type="button" className="btn btn-primary" disabled={busy} onClick={startInterview}>
                Start interview
              </button>
              <button type="button" className="btn btn-secondary" onClick={resetAll}>
                Reset
              </button>
            </div>
            {busy ? (
              <>
                <div className="scan-progress">
                  <span className="dot-loader" />
                  <span>
                    {scanStep || "Working..."} ({scanProgress}%)
                  </span>
                </div>
                <div className="scan-steps">
                  {["Validate source", "Scan content", "Build context", "Interview ready"].map(
                    (label, idx) => (
                      <div className={`scan-step ${stepStates[idx]}`} key={label}>
                        <span className="scan-step-dot">{idx + 1}</span>
                        <span>{label}</span>
                      </div>
                    ),
                  )}
                </div>
              </>
            ) : null}
            <div className="meta-grid">
              <div>
                Session <code>{sessionId || "—"}</code>
              </div>
              {sessionId ? (
                <div className="context-preview">
                  <strong>Scanned context</strong>
                  {sourceSummary}
                </div>
              ) : (
                <p className="muted">Start an interview to see detected context from your URL or brief.</p>
              )}
            </div>
          </div>

          <div className="step">
            <label className="field-label">2 · AI interview</label>
            <div className="question-kicker">Current question</div>
            <div className="question-box">{currentQuestion}</div>
            {currentOptions.length > 0 && !ready ? (
              <>
                <div className="options">
                  {currentOptions.map((option, idx) => (
                    <label className="option-card" key={`mcq-${idx}-${option.slice(0, 40)}`}>
                      <input
                        className="sr-only"
                        type="radio"
                        name="mcq-option"
                        checked={selectedOption === option}
                        onChange={() => onSelectMcqOption(option)}
                        disabled={busy || !sessionId}
                      />
                      <span className="option-badge" aria-hidden>
                        {OPTION_LETTERS[idx] ?? idx + 1}
                      </span>
                      <span className="option-label">{option}</span>
                    </label>
                  ))}
                  <label className="option-card is-other">
                    <input
                      className="sr-only"
                      type="radio"
                      name="mcq-option"
                      checked={selectedOption === "__other__"}
                      onChange={onSelectOther}
                      disabled={busy || !sessionId}
                    />
                    <span className="option-badge" aria-hidden>
                      +
                    </span>
                    <span className="option-label">Other — write your own</span>
                  </label>
                </div>
                {selectedOption === "__other__" ? (
                  <>
                    <label className="field-label" htmlFor="customAnswer">
                      Custom answer
                    </label>
                    <input
                      id="customAnswer"
                      className="input"
                      placeholder="Type your answer, then submit"
                      value={customAnswer}
                      onChange={(e) => setCustomAnswer(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter") {
                          e.preventDefault();
                          void submitAnswer();
                        }
                      }}
                    />
                    <div className="btn-row">
                      <button
                        type="button"
                        className="btn btn-primary"
                        disabled={!canAnswer || !customAnswer.trim()}
                        onClick={() => void submitAnswer()}
                      >
                        Submit custom answer
                      </button>
                    </div>
                  </>
                ) : (
                  <div className="hint-tap">
                    Tap a lettered choice to answer instantly — no separate submit step.
                  </div>
                )}
              </>
            ) : null}
            <p className="muted" style={{ marginTop: 10 }}>
              {questionStatus}
            </p>
          </div>

          <div className="step">
            <label className="field-label">3 · LMS path and build</label>
            {ready && plan?.confidence_low ? (
              <div className="confidence-banner">
                <div>
                  <strong>Confidence is below {plan.confidence_threshold}</strong>
                  Compare the three paths below. We default to the recommended card, but you can override
                  before generating.
                </div>
              </div>
            ) : null}

            {ready && plan?.lms_strategy_options?.length ? (
              <div className="strategy-grid">
                {plan.lms_strategy_options.map((opt) => (
                  <button
                    key={opt.id}
                    type="button"
                    className={`strategy-card ${selectedStrategyId === opt.id ? "selected" : ""}`}
                    onClick={() => setSelectedStrategyId(opt.id)}
                  >
                    {plan.recommended_strategy_id === opt.id ? (
                      <span className="badge-rec">Recommended</span>
                    ) : null}
                    <div className="weeks">{opt.timeline_weeks} weeks</div>
                    <h4>{opt.title}</h4>
                    <p>{opt.subtitle}</p>
                    <ul>
                      {opt.highlights.map((h) => (
                        <li key={h}>{h}</li>
                      ))}
                    </ul>
                  </button>
                ))}
              </div>
            ) : ready && planLoading ? (
              <p className="muted">Loading path previews…</p>
            ) : ready ? (
              <p className="muted">Path previews will appear momentarily, or tap Refresh plan.</p>
            ) : (
              <p className="muted">Finish the interview to choose foundations, balanced, or intensive.</p>
            )}

            <div className="btn-row">
              <button
                type="button"
                className="btn btn-secondary"
                disabled={!canGenerate || planLoading}
                onClick={previewPlan}
              >
                Refresh plan
              </button>
              <button type="button" className="btn btn-primary" disabled={!canGenerate} onClick={generateLms}>
                Generate LMS
              </button>
            </div>
            {lastAppliedStrategy ? (
              <p className="muted" style={{ marginTop: 10 }}>
                Last build used: <strong>{lastAppliedStrategy}</strong> track.
              </p>
            ) : null}
          </div>

          {error ? <p className="error">{error}</p> : null}
        </section>

        <section className="glass panel output-panel">
          <div className="panel-head">
            <h2 className="section-title">Output</h2>
            <span className="step-num">Live</span>
          </div>

          {plan ? (
            <div className="plan-summary">
              <div>
                <strong>Readiness</strong> {plan.readiness_score}{" "}
                {plan.confidence_low ? <span className="muted">(below threshold)</span> : null}
              </div>
              <p className="muted" style={{ marginTop: 8 }}>
                {plan.source_summary.slice(0, 220)}
                {plan.source_summary.length > 220 ? "…" : ""}
              </p>
              <p style={{ margin: "12px 0 4px" }}>
                <strong>Profile</strong>
              </p>
              <ul>
                {Object.entries(plan.profile_preview).map(([key, value]) => (
                  <li key={key}>
                    {key}: {value}
                  </li>
                ))}
              </ul>
              <p style={{ margin: "12px 0 4px" }}>
                <strong>Roadmap</strong> ({selectedStrategyId})
              </p>
              <ul>
                {(plan.lms_strategy_options.find((o) => o.id === selectedStrategyId)?.roadmap_preview ||
                  plan.roadmap_preview
                ).map((item, idx) => (
                  <li key={`${item.module}-${idx}`}>
                    {item.module} ({item.hours}h) — {item.focus}
                  </li>
                ))}
              </ul>
            </div>
          ) : null}

          <p className="output-title">JSON</p>
          <pre className="code-block">{output}</pre>
        </section>
      </div>
    </div>
  );
}

export default App;
