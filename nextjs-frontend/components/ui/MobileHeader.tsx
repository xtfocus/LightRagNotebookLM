interface MobileHeaderProps {
  className?: string;
}

export function MobileHeader({ className = "" }: MobileHeaderProps) {
  return (
    <div className={`lg:hidden text-center mb-8 ${className}`}>
      <h1 className="text-3xl font-bold text-gray-900 mb-2">
        OpenStorm
      </h1>
      <p className="text-gray-600">
        Research anything
      </p>
    </div>
  );
} 