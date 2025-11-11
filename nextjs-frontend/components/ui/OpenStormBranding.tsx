interface OpenStormBrandingProps {
  className?: string;
}

export function OpenStormBranding({ className = "" }: OpenStormBrandingProps) {
  const features = [
    { color: "bg-blue-500", text: "AI-powered research assistance" },
    { color: "bg-green-500", text: "Intelligent data analysis" },
    { color: "bg-purple-500", text: "Collaborative research tools" },
  ];

  return (
    <div className={`hidden lg:flex lg:w-1/2 bg-black text-white flex-col justify-center items-center p-12 ${className}`}>
      <div className="max-w-md text-center">
        <h1 className="text-5xl font-bold mb-6">
          OpenStorm
        </h1>
        <h2 className="text-2xl font-semibold mb-4">
          Research anything
        </h2>
        <p className="text-lg text-gray-300 mb-8">
          Discover, analyze, and explore with our powerful research platform
        </p>
        <div className="space-y-4">
          {features.map((feature, index) => (
            <div key={index} className="flex items-center justify-center space-x-3">
              <div className={`w-3 h-3 ${feature.color} rounded-full`}></div>
              <span className="text-gray-300">{feature.text}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
} 