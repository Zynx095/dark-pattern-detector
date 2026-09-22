import { Search, Upload, Loader2, ScanSearch } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";

export interface AnalyzerFormProps {
  url: string;
  onUrlChange: (url: string) => void;
  onAnalyzeUrl: (e: React.FormEvent) => void;
  file: File | null;
  onFileChange: (file: File | null) => void;
  onAnalyzeScreenshot: () => void;
  dragActive: boolean;
  onDragActiveChange: (active: boolean) => void;
  loading: boolean;
}

/**
 * Input card for the homepage: lets the user analyze either a pasted URL
 * or an uploaded checkout/subscription screenshot.
 */
export function AnalyzerForm({
  url,
  onUrlChange,
  onAnalyzeUrl,
  file,
  onFileChange,
  onAnalyzeScreenshot,
  dragActive,
  onDragActiveChange,
  loading,
}: AnalyzerFormProps) {
  function handleDrop(e: React.DragEvent<HTMLLabelElement>) {
    e.preventDefault();
    onDragActiveChange(false);
    const dropped = e.dataTransfer.files?.[0];
    if (dropped && dropped.type.startsWith("image/")) {
      onFileChange(dropped);
    }
  }

  return (
    <Card className="mb-8 border-slate-200 shadow-sm dark:border-slate-800">
      <CardContent className="pt-6 space-y-5">
        <form onSubmit={onAnalyzeUrl} className="flex flex-col gap-3 sm:flex-row">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="https://example.com/checkout"
              value={url}
              onChange={(e) => onUrlChange(e.target.value)}
              className="h-11 pl-9 text-base"
              disabled={loading}
            />
          </div>
          <Button type="submit" disabled={loading || !url.trim()} className="h-11 sm:w-44">
            {loading ? (
              <Loader2 className="size-4 animate-spin" />
            ) : (
              <>
                <ScanSearch className="size-4" />
                Analyze URL
              </>
            )}
          </Button>
        </form>

        <div className="flex items-center gap-3">
          <div className="h-px flex-1 bg-border" />
          <span className="text-xs text-muted-foreground">OR</span>
          <div className="h-px flex-1 bg-border" />
        </div>

        <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
          <label
            onDragOver={(e) => {
              e.preventDefault();
              onDragActiveChange(true);
            }}
            onDragLeave={() => onDragActiveChange(false)}
            onDrop={handleDrop}
            className={`flex flex-1 cursor-pointer items-center gap-2 rounded-lg border-2 border-dashed px-4 py-3.5 text-sm transition-all ${
              dragActive
                ? "border-emerald-500 bg-emerald-50 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300"
                : "border-slate-300 text-muted-foreground hover:border-slate-400 hover:bg-slate-50 dark:border-slate-700 dark:hover:bg-slate-900"
            }`}
          >
            <Upload className={`size-4 shrink-0 ${dragActive ? "animate-bounce" : ""}`} />
            <span className="truncate">
              {file
                ? file.name
                : dragActive
                ? "Drop the screenshot here"
                : "Drag & drop a checkout/subscription screenshot, or click to browse"}
            </span>
            <input
              type="file"
              accept="image/*"
              className="hidden"
              onChange={(e) => onFileChange(e.target.files?.[0] || null)}
              disabled={loading}
            />
          </label>
          <Button
            variant="secondary"
            onClick={onAnalyzeScreenshot}
            disabled={loading || !file}
            className="h-11 sm:w-44"
          >
            {loading ? <Loader2 className="size-4 animate-spin" /> : "Analyze Image"}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
