// Configurable logging utility
const LOG_LEVEL = process.env.NEXT_PUBLIC_LOG_LEVEL || 'info'; // 'debug', 'info', 'warn', 'error', 'none'
const ENABLE_LOGS = LOG_LEVEL !== 'none';

interface LogOptions {
  level?: 'debug' | 'info' | 'warn' | 'error';
  sendToServer?: boolean;
}

class Logger {
  private shouldLog(level: string): boolean {
    if (!ENABLE_LOGS) return false;
    
    const levels = ['debug', 'info', 'warn', 'error'];
    const currentLevelIndex = levels.indexOf(LOG_LEVEL);
    const messageLevelIndex = levels.indexOf(level);
    
    return messageLevelIndex >= currentLevelIndex;
  }

  private formatMessage(component: string, message: string, data?: any): string {
    const timestamp = new Date().toISOString();
    const formattedMessage = `[${component}] ${message}`;
    
    if (data) {
      return `${formattedMessage} - ${JSON.stringify(data)}`;
    }
    
    return formattedMessage;
  }

  private async sendToServer(component: string, message: string, data?: any) {
    try {
      await fetch('/api/logs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          component,
          message,
          data,
          timestamp: new Date().toISOString(),
          level: 'info'
        })
      });
    } catch (error) {
      // Silently fail - don't want logging to break the app
    }
  }

  debug(component: string, message: string, data?: any, options?: LogOptions) {
    if (!this.shouldLog('debug')) return;
    
    const formattedMessage = this.formatMessage(component, message, data);
    console.debug(formattedMessage);
    
    if (options?.sendToServer) {
      this.sendToServer(component, message, data);
    }
  }

  info(component: string, message: string, data?: any, options?: LogOptions) {
    if (!this.shouldLog('info')) return;
    
    const formattedMessage = this.formatMessage(component, message, data);
    console.info(formattedMessage);
    
    if (options?.sendToServer) {
      this.sendToServer(component, message, data);
    }
  }

  warn(component: string, message: string, data?: any, options?: LogOptions) {
    if (!this.shouldLog('warn')) return;
    
    const formattedMessage = this.formatMessage(component, message, data);
    console.warn(formattedMessage);
    
    if (options?.sendToServer) {
      this.sendToServer(component, message, data);
    }
  }

  error(component: string, message: string, data?: any, options?: LogOptions) {
    if (!this.shouldLog('error')) return;
    
    const formattedMessage = this.formatMessage(component, message, data);
    console.error(formattedMessage);
    
    if (options?.sendToServer) {
      this.sendToServer(component, message, data);
    }
  }
}

export const logger = new Logger(); 