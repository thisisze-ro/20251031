const formatPercent = (value, digits = 2) => `${(value * 100).toFixed(digits)}%`;

const formatWeight = (value) => `${(value * 100).toFixed(1)}%`;

document.addEventListener("DOMContentLoaded", async () => {
  const tableBody = document.querySelector("[data-asset-table]");
  const tickersEl = document.querySelector("[data-tickers]");
  const observationsEl = document.querySelector("[data-observations]");
  const rawRowsEl = document.querySelector("[data-raw-rows]");
  const detailCard = document.querySelector("[data-selection]");
  const chartEl = document.getElementById("frontier-chart");

  try {
    const response = await fetch("frontier-data.json");
    if (!response.ok) {
      throw new Error(`데이터를 불러오지 못했습니다: ${response.status}`);
    }
    const payload = await response.json();
    const { metadata, assets, portfolios, efficient_frontier: frontier } = payload;

    tickersEl.textContent = metadata.tickers.length.toString();
    observationsEl.textContent = metadata.observations.toLocaleString();
    rawRowsEl.textContent = metadata.raw_rows.toLocaleString();

    tableBody.innerHTML = "";
    assets.forEach((asset) => {
      const row = document.createElement("tr");
      row.innerHTML = `
        <td>${asset.ticker}</td>
        <td>${formatPercent(asset.expected_return)}</td>
        <td>${formatPercent(asset.risk)}</td>
      `;
      tableBody.appendChild(row);
    });

    const allPortfolioTrace = {
      x: portfolios.map((p) => p.risk * 100),
      y: portfolios.map((p) => p.expected_return * 100),
      text: portfolios.map((p) =>
        Object.entries(p.weights)
          .map(([ticker, weight]) => `${ticker}: ${formatWeight(weight)}`)
          .join("<br />")
      ),
      customdata: portfolios.map((p) => ({
        weights: p.weights,
        expected_return: p.expected_return,
        risk: p.risk,
        label: "가능 조합",
      })),
      mode: "markers",
      name: "가능 조합",
      marker: {
        color: "rgba(148, 163, 184, 0.6)",
        size: 6,
      },
      hovertemplate: "위험: %{x:.2f}%<br>수익률: %{y:.2f}%<extra></extra>",
    };

    const frontierTrace = {
      x: frontier.map((p) => p.risk * 100),
      y: frontier.map((p) => p.expected_return * 100),
      text: frontier.map((p) =>
        Object.entries(p.weights)
          .map(([ticker, weight]) => `${ticker}: ${formatWeight(weight)}`)
          .join("<br />")
      ),
      customdata: frontier.map((p) => ({
        weights: p.weights,
        expected_return: p.expected_return,
        risk: p.risk,
        label: "효율적 경계",
      })),
      mode: "lines+markers",
      name: "효율적 경계",
      line: {
        color: "#4c1d95",
        width: 3,
      },
      marker: {
        size: 8,
        color: "#7c3aed",
      },
      hovertemplate: "위험: %{x:.2f}%<br>수익률: %{y:.2f}%<extra></extra>",
    };

    const assetTrace = {
      x: assets.map((asset) => asset.risk * 100),
      y: assets.map((asset) => asset.expected_return * 100),
      text: assets.map((asset) => asset.ticker),
      customdata: assets.map((asset) => ({
        weights: { [asset.ticker]: 1 },
        expected_return: asset.expected_return,
        risk: asset.risk,
        label: "단일 자산",
      })),
      mode: "markers",
      name: "단일 자산",
      marker: {
        color: "#ef4444",
        size: 10,
        symbol: "diamond",
      },
      hovertemplate: "%{text}<br>위험: %{x:.2f}%<br>수익률: %{y:.2f}%<extra></extra>",
    };

    const layout = {
      margin: { l: 60, r: 30, t: 20, b: 60 },
      xaxis: {
        title: "위험 (표준편차, %)",
        zeroline: false,
      },
      yaxis: {
        title: "기대 수익률 (%, 일간)",
        zeroline: false,
      },
      legend: {
        orientation: "h",
        y: -0.2,
      },
      hovermode: "closest",
    };

    const config = {
      responsive: true,
      displaylogo: false,
      locale: "ko",
    };

    await Plotly.newPlot(chartEl, [allPortfolioTrace, frontierTrace, assetTrace], layout, config);

    chartEl.on("plotly_click", (eventData) => {
      const point = eventData.points?.[0];
      if (!point) {
        return;
      }
      const data = point.customdata;
      if (!data) {
        return;
      }
      renderDetail(detailCard, data);
    });
  } catch (error) {
    console.error(error);
    if (tableBody) {
      tableBody.innerHTML = `<tr><td colspan="3" class="table-placeholder">데이터를 불러오지 못했습니다.</td></tr>`;
    }
    if (detailCard) {
      detailCard.innerHTML = `
        <h3>포트폴리오 세부 정보</h3>
        <p>데이터 로딩에 실패했습니다. 페이지를 새로고침해 주세요.</p>
      `;
    }
  }
});

function renderDetail(container, data) {
  if (!container) {
    return;
  }
  const weightList = Object.entries(data.weights)
    .map(([ticker, weight]) => `<li><strong>${ticker}</strong>: ${formatWeight(weight)}</li>`)
    .join("");

  container.innerHTML = `
    <h3>${data.label}</h3>
    <p><strong>기대 수익률:</strong> ${formatPercent(data.expected_return, 3)}</p>
    <p><strong>위험:</strong> ${formatPercent(data.risk, 3)}</p>
    <h4>자산 비중</h4>
    <ul>${weightList}</ul>
  `;
}
