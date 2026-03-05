import fs from "fs";
import path from "path";

const LOG_DIR = path.resolve(process.cwd(), "logs");
const LOG_FILE = path.join(LOG_DIR, "app.log");
const ERROR_FILE = path.join(LOG_DIR, "error.log");

// Ensure logs directory exists
if (!fs.existsSync(LOG_DIR)) {
  fs.mkdirSync(LOG_DIR, { recursive: true });
}

type LogLevel = "INFO" | "WARN" | "ERROR" | "DEBUG";

function timestamp(): string {
  return new Date().toISOString();
}

function formatMessage(level: LogLevel, context: string, message: string, meta?: any): string {
  const base = `[${timestamp()}] [${level}] [${context}] ${message}`;
  if (meta) {
    const metaStr = meta instanceof Error
      ? `\n  Stack: ${meta.stack}`
      : `\n  Data: ${JSON.stringify(meta, null, 2)}`;
    return base + metaStr;
  }
  return base;
}

function writeToFile(file: string, line: string) {
  try {
    fs.appendFileSync(file, line + "\n");
  } catch {
    // Silently fail if file write fails (e.g. read-only FS on Render)
  }
}

export const logger = {
  info(context: string, message: string, meta?: any) {
    const line = formatMessage("INFO", context, message, meta);
    console.log(line);
    writeToFile(LOG_FILE, line);
  },

  warn(context: string, message: string, meta?: any) {
    const line = formatMessage("WARN", context, message, meta);
    console.warn(line);
    writeToFile(LOG_FILE, line);
  },

  error(context: string, message: string, error?: any) {
    const line = formatMessage("ERROR", context, message, error);
    console.error(line);
    writeToFile(LOG_FILE, line);
    writeToFile(ERROR_FILE, line);
  },

  debug(context: string, message: string, meta?: any) {
    if (process.env.NODE_ENV === "development" || process.env.DEBUG === "true") {
      const line = formatMessage("DEBUG", context, message, meta);
      console.log(line);
      writeToFile(LOG_FILE, line);
    }
  },

  /** Log an incoming HTTP request */
  request(method: string, url: string, statusCode: number, durationMs: number) {
    const line = `[${timestamp()}] [HTTP] ${method} ${url} → ${statusCode} (${durationMs}ms)`;
    console.log(line);
    writeToFile(LOG_FILE, line);
  },
};

export default logger;
