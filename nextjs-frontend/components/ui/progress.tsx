import { CheckIcon, LoaderCircle } from "lucide-react";

// Utility to merge class names (Tailwind best practice)
function cn(...classes: (string | undefined | false | null)[]) {
  return classes.filter(Boolean).join(" ");
}

// Utility to truncate URLs in log messages
const truncateUrl = (url: string, maxLength: number = 40) => {
  if (!url) return "";
  if (url.length <= maxLength) return url;
  return url.substring(0, maxLength - 3) + "...";
};

export function Progress({
  logs,
}: {
  logs: {
    message: string;
    done: boolean;
  }[];
}) {
  if (!logs || logs.length === 0) {
    return null;
  }

  return (
    <div data-test-id="progress-steps">
      <div className="bg-[var(--background)] rounded-lg overflow-hidden text-sm py-2">
        {logs.map((log, index) => (
          <div
            key={index}
            data-test-id="progress-step-item"
            className={cn(
              "flex",
              log.done || index === logs.findIndex((l) => !l.done)
                ? ""
                : "opacity-50"
            )}
          >
            <div className="w-8">
              <div
                className="w-4 h-4 border border-[var(--border)] bg-white flex items-center justify-center rounded-full mt-[10px] ml-[12px]"
                data-test-id={log.done ? "progress-step-item_done" : "progress-step-item_loading"}
              >
                {log.done ? (
                  <CheckIcon className="w-3 h-3 text-[var(--primary)]" />
                ) : (
                  <LoaderCircle className="w-3 h-3 text-[var(--primary)] animate-spin" />
                )}
              </div>
              {index < logs.length - 1 && (
                <div className="h-full w-[1px] bg-[var(--border)] ml-[20px]"></div>
              )}
            </div>
            <div className="flex-1 flex justify-center py-2 pl-2 pr-4">
              <div className="flex-1 flex items-center text-xs">
                {log.message.replace(
                  /https?:\/\/[^\s]+/g, // Regex to match URLs
                  (url) => truncateUrl(url) // Replace with truncated URL
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
} 