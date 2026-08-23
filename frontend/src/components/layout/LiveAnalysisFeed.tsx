"use client";
import { motion, AnimatePresence } from "framer-motion";
import { useEffect, useRef } from "react";
import { CheckCircle, Info, AlertTriangle, Zap } from "lucide-react";

export interface LogEntry {
  id: string;
  type: "info" | "success" | "warning" | "error";
  message: string;
  timestamp: number;
}

interface LiveAnalysisFeedProps {
  logs: LogEntry[];
  maxHeight?: string;
}

export default function LiveAnalysisFeed({ logs, maxHeight = "200px" }: LiveAnalysisFeedProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs]);

  const getIcon = (type: string) => {
    switch (type) {
      case "success": return <CheckCircle size={12} className="text-theme-success" />;
      case "warning": return <AlertTriangle size={12} className="text-theme-warning" />;
      case "error": return <AlertTriangle size={12} className="text-theme-error" />;
      default: return <Info size={12} className="text-theme-accent" />;
    }
  };

  const getColor = (type: string) => {
    switch (type) {
      case "success": return "text-theme-success font-bold";
      case "warning": return "text-theme-warning";
      case "error": return "text-theme-error font-bold";
      default: return "text-theme-primary";
    }
  };

  return (
    <div className="bg-theme-surface rounded-lg border border-theme-border overflow-hidden">
      <div className="px-3 py-2 border-b border-theme-border flex items-center gap-2 bg-theme-surface/80 select-none">
        <Zap size={12} className="text-theme-accent" />
        <h4 className="text-[10px] text-theme-secondary uppercase tracking-wider font-bold font-mono">Live Analysis Feed</h4>
        {logs.length > 0 && (
          <motion.div
            animate={{ opacity: [0.5, 1, 0.5] }}
            transition={{ duration: 2, repeat: Infinity }}
            className="ml-auto w-2 h-2 rounded-full bg-theme-success"
          />
        )}
      </div>
      
      <div 
        ref={scrollRef}
        className="font-mono text-[11px] overflow-y-auto custom-scrollbar"
        style={{ maxHeight }}
      >
        <AnimatePresence initial={false}>
          {logs.length === 0 ? (
            <div className="p-3 text-theme-muted text-center font-mono">
              Waiting for analysis...
            </div>
          ) : (
            logs.map((log) => (
              <motion.div
                key={log.id}
                initial={{ opacity: 0, x: -20, height: 0 }}
                animate={{ opacity: 1, x: 0, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
                transition={{ duration: 0.2 }}
                className="px-3 py-1.5 border-b border-theme-border/50 hover:bg-theme-hover transition-colors"
              >
                <div className="flex items-start gap-2">
                  <span className="mt-0.5">{getIcon(log.type)}</span>
                  <span className={`flex-1 ${getColor(log.type)}`}>
                    {log.message}
                  </span>
                  <span className="text-theme-muted text-[9px] mt-0.5">
                    {new Date(log.timestamp).toLocaleTimeString()}
                  </span>
                </div>
              </motion.div>
            ))
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
