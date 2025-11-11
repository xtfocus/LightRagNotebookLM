import { Check, X } from "lucide-react";

interface PasswordRequirement {
  id: string;
  text: string;
  regex: RegExp;
}

const requirements: PasswordRequirement[] = [
  {
    id: "length",
    text: "At least 8 characters",
    regex: /.{8,}/
  },
  {
    id: "uppercase", 
    text: "At least one uppercase letter",
    regex: /[A-Z]/
  },
  {
    id: "special",
    text: "At least one special character",
    regex: /[!@#$%^&*(),.?":{}|<>]/
  }
];

export function PasswordRequirements() {
  return (
    <div className="space-y-2">
      <p className="text-xs text-gray-600 dark:text-gray-400 font-medium">
        Password requirements:
      </p>
      <div className="space-y-1">
        {requirements.map((requirement) => (
          <div key={requirement.id} className="flex items-center gap-2">
            <div className="flex items-center justify-center w-4 h-4">
              <div className="w-1.5 h-1.5 rounded-full bg-gray-400 dark:bg-gray-500" />
            </div>
            <span className="text-xs text-gray-600 dark:text-gray-400">
              {requirement.text}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
} 