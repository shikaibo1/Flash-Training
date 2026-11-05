interface AudioVisualizerProps {
  isRecording: boolean;
  levels?: number[];
}

const AudioVisualizer = ({ isRecording, levels = [] }: AudioVisualizerProps) => {
  const bars = levels.length ? levels.map(v => Number.isFinite(v) ? Math.max(0, Math.min(v, 100)) : 0) : new Array<number>(30).fill(5);

  return (
    <div className="flex items-center justify-center gap-1 h-32 w-full bg-secondary/50 rounded-xl overflow-hidden p-6">
      {bars.map((height, index) => (
        <div
          key={index}
          className="w-1.5 md:w-2 bg-primary rounded-full transition-all duration-100 ease-in-out"
          style={{ height: `${height}%`, opacity: isRecording ? 0.8 : 0.3 }}
        />
      ))}
    </div>
  );
};

export default AudioVisualizer;
