type Props = {
  revenue: string;
  grossProfit: string;
};

export function ResultsGrid({ revenue, grossProfit }: Props) {
  const cell = { border: "1px solid #ddd", padding: "8px 10px" };
  const row = { display: "grid", gridTemplateColumns: "1fr 1fr" };

  return (
    <div
      role="table"
      aria-label="Results"
      style={{ border: "1px solid #ddd", borderRadius: 8, overflow: "hidden" }}
    >
      <div style={{ ...row, background: "#f7f7f7" }}>
        <div style={{ ...cell, fontWeight: 600 }}>Metric</div>
        <div style={{ ...cell, fontWeight: 600 }}>Value</div>
      </div>
      <div style={row}>
        <div style={cell}>Revenue</div>
        <div style={cell}>{revenue}</div>
      </div>
      <div style={row}>
        <div style={cell}>Gross Profit</div>
        <div style={cell}>{grossProfit}</div>
      </div>
    </div>
  );
}
