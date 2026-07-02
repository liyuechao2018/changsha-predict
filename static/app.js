const form = document.querySelector("#predictionForm");
const result = document.querySelector("#result");
const scoreInput = document.querySelector("#score");
const rankInput = document.querySelector("#rank");
const rankingHint = document.querySelector("#rankingHint");

const groupTitles = {
  reach: "冲",
  target: "稳",
  safety: "保",
};

scoreInput.addEventListener("input", async () => {
  const score = Number(scoreInput.value);
  if (!scoreInput.value) {
    setRankingHint("自动换算使用2026不含指标生一分一段表；推荐仍以位次为准。");
    return;
  }
  if (!Number.isInteger(score)) {
    setRankingHint("请输入整数分数。", true);
    return;
  }

  try {
    const response = await fetch(`${getBasePath()}/api/rankings/lookup?year=2026&score=${score}`);
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || "位次查询失败");
    }
    if (!data.found) {
      setRankingHint(data.message || "当前分数暂未覆盖，请手动填写位次。", true);
      return;
    }
    rankInput.value = data.rank;
    setRankingHint(`${score}分对应不含指标生累计位次约 ${Number(data.rank).toLocaleString()} 名。`);
  } catch (error) {
    setRankingHint(error.message, true);
  }
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!rankInput.value) {
    result.classList.remove("hidden");
    result.innerHTML = `<div class="notice error">请填写位次；如果只填分数，请确认该分数已被一分一段表覆盖并自动带出位次。</div>`;
    return;
  }
  result.classList.remove("hidden");
  result.innerHTML = `<div class="notice">正在预测...</div>`;

  const payload = {
    year: 2026,
    score: scoreInput.value ? Number(scoreInput.value) : null,
    rank: Number(rankInput.value),
    qualityLevel: document.querySelector("#qualityLevel").value,
  };

  try {
    const response = await fetch(`${getBasePath()}/api/predictions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || "预测失败");
    }
    renderResult(data);
  } catch (error) {
    result.innerHTML = `<div class="notice error">${escapeHtml(error.message)}</div>`;
  }
});

function getBasePath() {
  const path = window.location.pathname;
  return path.startsWith("/predict") ? "/predict" : "";
}

function setRankingHint(message, warning = false) {
  rankingHint.textContent = message;
  rankingHint.classList.toggle("warning", warning);
}

function renderResult(data) {
  const student = data.student;
  const cards = Object.entries(data.groups)
    .map(([key, schools]) => renderGroup(key, schools))
    .join("");

  result.innerHTML = `
    <section class="student">
      <div>
        <span>成绩</span>
        <strong>${student.score}</strong>
      </div>
      <div>
        <span>今年位次</span>
        <strong>${student.rank.toLocaleString()}</strong>
      </div>
      <div>
        <span>预测</span>
        <strong>${escapeHtml(student.summary)}</strong>
      </div>
      <p>${escapeHtml(student.rankSource)}</p>
    </section>
    ${cards}
  `;
}

function renderGroup(key, schools) {
  const content = schools.length
    ? schools.map(renderSchool).join("")
    : `<div class="empty">暂无匹配学校</div>`;
  return `
    <section class="group">
      <h2>${groupTitles[key]}</h2>
      <div class="school-grid">${content}</div>
    </section>
  `;
}

function renderSchool(school) {
  const scoreLabel = school.isNewSchool ? "2026预估线" : "2025分数线";
  const rankLabel = school.isNewSchool ? "2026预估位次" : "2025位次";
  const planLabel = school.isNewSchool ? "首年预估学位" : "招生计划";
  return `
    <article class="school-card">
      <header>
        <div>
          <h3>${escapeHtml(school.schoolName)}</h3>
          <span>${escapeHtml(school.tier || "未分梯队")} · ${batchLabel(school.admissionBatch)}</span>
        </div>
        <strong>${school.probability}%</strong>
      </header>
      <div class="stars">${"★".repeat(school.stars)}${"☆".repeat(5 - school.stars)}</div>
      <dl>
        <div><dt>${scoreLabel}</dt><dd>${formatValue(school.admissionScore)}</dd></div>
        <div><dt>${rankLabel}</dt><dd>${school.admissionRank.toLocaleString()}</dd></div>
        <div><dt>2026参考</dt><dd>${school.adjustedAdmissionRank.toLocaleString()}</dd></div>
        <div><dt>${planLabel}</dt><dd>${formatValue(school.enrollmentPlan)}</dd></div>
        <div><dt>位次差</dt><dd>${formatGap(school.rankGap)}</dd></div>
        <div><dt>对标依据</dt><dd>${formatValue(school.benchmark || school.tier)}</dd></div>
      </dl>
      ${renderAdjustment(school)}
      <p>${escapeHtml(school.reason)}</p>
    </article>
  `;
}

function renderAdjustment(school) {
  if (!school.structureAdjustment) return "";
  return `<div class="adjustment">结构修正 +${school.structureAdjustment.toLocaleString()} 名</div>`;
}

function formatGap(gap) {
  if (gap > 0) return `靠后 ${gap.toLocaleString()}`;
  if (gap < 0) return `领先 ${Math.abs(gap).toLocaleString()}`;
  return "持平";
}

function batchLabel(batch) {
  return batch === "first" ? "第一批次" : "第二批次";
}

function formatValue(value) {
  if (value === null || value === undefined || value === "") return "待公布";
  if (typeof value === "number") return value.toLocaleString();
  return escapeHtml(value);
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}
