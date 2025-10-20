import { HealthStatus } from "@/types/conveyor";

interface DigitalTwinProps {
  status: HealthStatus;
}

const statusStyles = {
  healthy: {
    filter: "drop-shadow(0 0 8px hsl(var(--success)))",
    stroke: "hsl(var(--success))",
    animationPlayState: "running",
  },
  warning: {
    filter: "drop-shadow(0 0 8px hsl(var(--warning)))",
    stroke: "hsl(var(--warning))",
    animationPlayState: "running",
  },
  critical: {
    filter: "drop-shadow(0 0 8px hsl(var(--destructive)))",
    stroke: "hsl(var(--destructive))",
    animationPlayState: "paused",
  },
};

export function DigitalTwin({ status }: DigitalTwinProps) {
  const styles = statusStyles[status] || statusStyles.healthy;

  const animationStyle: React.CSSProperties = {
    animationPlayState: styles.animationPlayState,
  };

  const wheelStyle: React.CSSProperties = {
    ...animationStyle,
    animation: `spin 4s linear infinite`,
    transformOrigin: 'center',
  };

  const beltStyle: React.CSSProperties = {
    ...animationStyle,
    strokeDasharray: "20 20",
    animation: `belt-flow 1s linear infinite`,
  };

  return (
    <div className="p-4 border rounded-lg bg-card/80 flex justify-center items-center h-64">
      <svg
        width="100%"
        height="100%"
        viewBox="0 0 400 150"
        xmlns="http://www.w3.org/2000/svg"
        className="transition-all duration-500"
        style={{ filter: styles.filter }}
      >
        {/* Main Structure */}
        <g strokeWidth="4" stroke="hsl(var(--muted-foreground))" fill="none">
          {/* Belt */}
          <path
            d="M 50 50 H 350 Q 370 75 350 100 H 50 Q 30 75 50 50 Z"
            className="transition-all duration-500"
            stroke={styles.stroke}
            strokeWidth="6"
            style={beltStyle}
          />

          {/* Rollers */}
          <circle cx="50" cy="75" r="25" fill="hsl(var(--background))" />
          <circle cx="350" cy="75" r="25" fill="hsl(var(--background))" />
          <circle cx="150" cy="47" r="8" fill="hsl(var(--muted-foreground))" />
          <circle cx="250" cy="47" r="8" fill="hsl(var(--muted-foreground))" />
          <circle cx="150" cy="103" r="8" fill="hsl(var(--muted-foreground))" />
          <circle cx="250" cy="103" r="8" fill="hsl(var(--muted-foreground))" />

          {/* Motor */}
          <rect x="20" y="105" width="60" height="30" rx="5" fill="hsl(var(--card))" />
          <circle cx="75" cy="120" r="5" fill="hsl(var(--muted-foreground))" />
        </g>

        {/* Labels */}
        <text x="25" y="145" fontSize="10" fill="hsl(var(--muted-foreground))">Motor</text>
        <text x="330" y="40" fontSize="10" fill="hsl(var(--muted-foreground))">Drive</text>
      </svg>
    </div>
  );
}