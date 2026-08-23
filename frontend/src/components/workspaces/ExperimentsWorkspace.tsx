"use client";
import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { FlaskConical, Play, Award, Zap, AlertTriangle, CheckCircle } from "lucide-react";
import type { LogEntry } from "@/components/layout/LiveAnalysisFeed";

interface ExperimentsWorkspaceProps {
  onLog: (type: LogEntry["type"], message: string) => void;
}

interface IndividualRun {
  type: string;
  input: string;
  expected: string;
  output: string;
  success: boolean;
  time_ms: number;
  depth: number;
  steps: string[];
}

interface ExperimentResult {
  accuracy: number;
  average_time_ms: number;
  total_runs: number;
  successful_runs: number;
  depth_breakdown: Record<string, { accuracy: number; total: number; success: number }>;
  individual_runs: IndividualRun[];
}

export default function ExperimentsWorkspace({ onLog }: ExperimentsWorkspaceProps) {
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<ExperimentResult | null>(null);

  const runEvaluation = async () => {
    setRunning(true);
    setResult(null);
    onLog("info", "Starting scientific evaluation run...");
    
    try {
      const res = await fetch("/api/experiments/run", { method: "POST" });
      if (!res.ok) throw new Error(`API error: ${res.status}`);
      const data = await res.json();
      setResult(data);
      onLog("success", `Evaluation complete! Accuracy: ${data.accuracy}%, Avg Time: ${data.average_time_ms}ms`);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Unknown error";
      onLog("error", `Evaluation failed: ${msg}`);
    } finally {
      setRunning(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      className="h-full flex flex-col gap-6 overflow-y-auto pr-2 custom-scrollbar"
    >
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3 select-none">
          <div className="w-10 h-10 rounded-lg bg-theme-gradient flex items-center justify-center shadow-lg shadow-theme-accent/15">
            <FlaskConical size={20} className="text-white" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-theme-primary">Scientific Evaluation</h2>
            <p className="text-xs text-theme-secondary">Measure decoding framework accuracy, speed, and reliability</p>
          </div>
        </div>

        <motion.button
          onClick={runEvaluation}
          disabled={running}
          whileHover={{ scale: running ? 1 : 1.02 }}
          whileTap={{ scale: running ? 1 : 0.98 }}
          className="px-5 py-2.5 rounded-lg bg-theme-gradient hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed text-white text-xs font-mono font-bold transition-all flex items-center gap-2 shadow-lg shadow-theme-accent/15"
        >
          {running ? (
            <>
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full"
              />
              Running Suite...
            </>
          ) : (
            <>
              <Play size={14} fill="white" />
              Run Evaluation Suite
            </>
          )}
        </motion.button>
      </div>

      <AnimatePresence mode="wait">
        {!result && !running && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="flex-1 flex flex-col items-center justify-center p-12 border border-dashed border-theme-border rounded-xl bg-theme-surface/30 select-none"
          >
            <FlaskConical size={48} className="text-theme-muted mb-4 animate-pulse" />
            <p className="text-sm font-mono text-theme-secondary text-center max-w-md">
              Trigger a benchmark run to evaluate the multi-layer BFS solver against the ground-truth forensic dataset.
            </p>
          </motion.div>
        )}

        {running && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex-1 flex flex-col items-center justify-center p-12 select-none"
          >
            <div className="relative w-20 h-20 mb-4">
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                className="absolute inset-0 border-4 border-theme-accent/20 border-t-theme-accent rounded-full"
              />
              <motion.div
                animate={{ rotate: -360 }}
                transition={{ duration: 1.5, repeat: Infinity, ease: "linear" }}
                className="absolute inset-2 border-4 border-theme-border/20 border-t-theme-border rounded-full"
              />
            </div>
            <p className="text-xs font-mono text-theme-secondary tracking-wider uppercase animate-pulse">
              Executing decoders over dataset...
            </p>
          </motion.div>
        )}

        {result && !running && (
          <motion.div
            initial={{ opacity: 0, scale: 0.98 }}
            animate={{ opacity: 1, scale: 1 }}
            className="space-y-6"
          >
            {/* Overview Stats */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 select-none">
              <div className="p-5 bg-theme-surface border border-theme-border rounded-xl flex items-center justify-between">
                <div>
                  <span className="text-[10px] font-mono uppercase text-theme-secondary">Overall Accuracy</span>
                  <h3 className="text-2xl font-bold text-theme-success font-mono mt-1">{result.accuracy}%</h3>
                </div>
                <div className="p-3 bg-theme-success/10 border border-theme-success/20 text-theme-success rounded-lg">
                  <Award size={20} />
                </div>
              </div>

              <div className="p-5 bg-theme-surface border border-theme-border rounded-xl flex items-center justify-between">
                <div>
                  <span className="text-[10px] font-mono uppercase text-theme-secondary">Average Speed</span>
                  <h3 className="text-2xl font-bold text-theme-accent font-mono mt-1">{result.average_time_ms} ms</h3>
                </div>
                <div className="p-3 bg-theme-accent/10 border border-theme-accent/20 text-theme-accent rounded-lg">
                  <Zap size={20} />
                </div>
              </div>

              <div className="p-5 bg-theme-surface border border-theme-border rounded-xl flex items-center justify-between">
                <div>
                  <span className="text-[10px] font-mono uppercase text-theme-secondary">Total Run Count</span>
                  <h3 className="text-2xl font-bold text-theme-primary font-mono mt-1">{result.total_runs}</h3>
                </div>
                <div className="p-3 bg-theme-hover border border-theme-border text-theme-primary rounded-lg">
                  <FlaskConical size={20} />
                </div>
              </div>

              <div className="p-5 bg-theme-surface border border-theme-border rounded-xl flex items-center justify-between">
                <div>
                  <span className="text-[10px] font-mono uppercase text-theme-secondary">Success Rate</span>
                  <h3 className="text-2xl font-bold text-theme-accent font-mono mt-1">
                    {result.successful_runs}/{result.total_runs}
                  </h3>
                </div>
                <div className="p-3 bg-theme-accent/10 border border-theme-accent/20 text-theme-accent rounded-lg">
                  <CheckCircle size={20} />
                </div>
              </div>
            </div>

            {/* Depth Breakdowns */}
            <div className="p-6 bg-theme-surface border border-theme-border rounded-xl space-y-4 select-none">
              <h3 className="text-sm font-mono text-theme-secondary uppercase tracking-wider">Accuracy by Path Complexity</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {Object.entries(result.depth_breakdown).map(([depth, stats]) => (
                  <div key={depth} className="p-4 bg-theme-card border border-theme-border rounded-xl space-y-3">
                    <div className="flex justify-between text-xs font-mono">
                      <span className="text-theme-primary font-bold">{depth}</span>
                      <span className="text-theme-accent font-bold">{stats.accuracy}%</span>
                    </div>
                    {/* Progress Bar */}
                    <div className="h-2 bg-theme-input rounded-full overflow-hidden">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${stats.accuracy}%` }}
                        transition={{ duration: 0.8 }}
                        className="h-full bg-theme-accent"
                      />
                    </div>
                    <div className="flex justify-between text-[10px] font-mono text-theme-muted">
                      <span>Total Cases: {stats.total}</span>
                      <span>Passed: {stats.success}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Individual Runs */}
            <div className="p-6 bg-theme-surface border border-theme-border rounded-xl space-y-4">
              <h3 className="text-sm font-mono text-theme-secondary uppercase tracking-wider select-none">Test Suite Run Details</h3>
              <div className="overflow-x-auto custom-scrollbar">
                <table className="w-full text-left border-collapse text-xs font-mono">
                  <thead>
                    <tr className="border-b border-theme-border text-theme-secondary">
                      <th className="pb-3 pr-4 font-bold uppercase text-[10px]">Test Case Type</th>
                      <th className="pb-3 pr-4 font-bold uppercase text-[10px]">Input Preview</th>
                      <th className="pb-3 pr-4 font-bold uppercase text-[10px]">Target Output</th>
                      <th className="pb-3 pr-4 font-bold uppercase text-[10px]">Actual Result</th>
                      <th className="pb-3 pr-4 font-bold uppercase text-[10px]">Path</th>
                      <th className="pb-3 pr-4 font-bold uppercase text-[10px]">Speed</th>
                      <th className="pb-3 font-bold uppercase text-[10px]">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-theme-border/50">
                    {result.individual_runs.map((run, idx) => (
                      <tr key={idx} className="hover:bg-theme-hover transition-colors">
                        <td className="py-3 pr-4 font-bold text-theme-primary capitalize">{run.type.replace("_", " ")}</td>
                        <td className="py-3 pr-4 text-theme-secondary max-w-[150px] truncate break-all">{run.input}</td>
                        <td className="py-3 pr-4 text-theme-secondary max-w-[150px] truncate break-all">{run.expected}</td>
                        <td className="py-3 pr-4 text-theme-primary max-w-[150px] truncate break-all">{run.output}</td>
                        <td className="py-3 pr-4">
                          {run.steps.length > 0 ? (
                            <span className="bg-theme-accent/10 border border-theme-accent/20 px-2 py-0.5 rounded text-[10px] text-theme-accent font-bold">
                              {run.steps.join(" → ")}
                            </span>
                          ) : (
                            <span className="text-theme-muted font-mono">N/A</span>
                          )}
                        </td>
                        <td className="py-3 pr-4 text-theme-secondary">{run.time_ms} ms</td>
                        <td className="py-3">
                          {run.success ? (
                            <span className="text-theme-success font-bold flex items-center gap-1 font-mono">
                              <CheckCircle size={12} /> PASS
                            </span>
                          ) : (
                            <span className="text-theme-error font-bold flex items-center gap-1 font-mono">
                              <AlertTriangle size={12} /> FAIL
                            </span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
