import { AlertCircle, Info, AlertTriangle } from "lucide-react";

interface ErrorState {
  errors?: {
    [key: string]: string | string[];
  };
  server_validation_error?: string;
  server_error?: string;
}

interface EnhancedFormErrorProps {
  state: ErrorState | null | undefined;
  className?: string;
}

interface FieldErrorProps {
  state: ErrorState | null | undefined;
  field: string;
  className?: string;
}

export function EnhancedFormError({ state, className = "" }: EnhancedFormErrorProps) {
  if (!state) return null;

  const error = state.server_validation_error || state.server_error;
  if (!error) return null;

  // The error message has already been processed by the server action
  // So we can display it directly with appropriate styling
  const getIcon = () => {
    return <AlertCircle className="h-4 w-4" />;
  };

  const getContainerClasses = () => {
    const baseClasses = "flex items-start gap-2 p-3 rounded-md border";
    return `${baseClasses} bg-red-50 border-red-200 text-red-800 dark:bg-red-900/20 dark:border-red-800 dark:text-red-400`;
  };

  return (
    <div className={`${getContainerClasses()} ${className}`}>
      {getIcon()}
      <div className="flex-1">
        <p className="text-sm font-medium">{error}</p>
      </div>
    </div>
  );
}

export function EnhancedFieldError({ state, field, className = "" }: FieldErrorProps) {
  if (!state?.errors) return null;

  const error = state.errors[field];
  if (!error) return null;

  if (Array.isArray(error)) {
    return (
      <div className={`text-sm text-red-500 ${className}`}>
        <ul className="list-disc ml-4">
          {error.map((err) => (
            <li key={err}>{err}</li>
          ))}
        </ul>
      </div>
    );
  }

  return (
    <div className={`flex items-center gap-1 text-sm text-red-500 ${className}`}>
      <AlertCircle className="h-3 w-3" />
      <span>{error}</span>
    </div>
  );
} 