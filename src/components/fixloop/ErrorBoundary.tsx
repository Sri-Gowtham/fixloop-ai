import React, { Component, type ReactNode } from "react";
import { FxButton } from "./Button";
import { Panel } from "./Panel";
import { TriangleAlert, RefreshCw, Home } from "lucide-react";
import { reportLovableError } from "@/lib/lovable-error-reporting";

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    // Update state so the next render will show the fallback UI.
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error("Uncaught error:", error, errorInfo);
    try {
      reportLovableError(error, { boundary: "react_error_boundary" });
    } catch (e) {
      console.error("Failed to report error", e);
    }
  }

  private handleRetry = () => {
    this.setState({ hasError: false, error: null });
    window.location.reload();
  };

  private handleGoHome = () => {
    window.location.href = "/";
  };

  public render() {
    if (this.state.hasError) {
      return (
        <div className="flex min-h-screen items-center justify-center bg-background p-4">
          <div className="w-full max-w-lg">
            <Panel
              title="System Error"
              subtitle="An unexpected error occurred in the application layer."
            >
              <div className="flex flex-col items-center justify-center py-6 text-center">
                <div className="h-16 w-16 rounded-full bg-critical/10 flex items-center justify-center mb-6 border border-critical/20">
                  <TriangleAlert className="h-8 w-8 text-critical" />
                </div>
                <h2 className="text-xl font-bold text-foreground mb-2">Application Crashed</h2>
                <p className="text-sm text-muted-foreground mb-6 max-w-sm">
                  We apologize for the interruption. The error has been securely logged and our
                  engineering team will investigate the root cause.
                </p>

                {this.state.error && (
                  <div className="w-full text-left bg-surface border border-border rounded-md p-4 mb-6 overflow-auto max-h-40">
                    <div className="text-[10px] uppercase tracking-wider text-muted-foreground font-semibold mb-2">
                      Stack Trace
                    </div>
                    <pre className="text-xs text-critical font-mono whitespace-pre-wrap">
                      {this.state.error.message}
                    </pre>
                  </div>
                )}

                <div className="flex items-center gap-3 w-full sm:w-auto">
                  <FxButton
                    variant="outline"
                    className="flex-1 sm:flex-none"
                    onClick={this.handleGoHome}
                  >
                    <Home className="mr-2 h-4 w-4" />
                    Dashboard
                  </FxButton>
                  <FxButton
                    variant="cyber"
                    className="flex-1 sm:flex-none"
                    onClick={this.handleRetry}
                  >
                    <RefreshCw className="mr-2 h-4 w-4" />
                    Reload App
                  </FxButton>
                </div>
              </div>
            </Panel>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
