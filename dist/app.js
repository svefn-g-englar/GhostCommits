const $ = (selector, scope = document) => scope.querySelector(selector);
const $$ = (selector, scope = document) => [...scope.querySelectorAll(selector)];

const demo = {
  owner: "angular", repo: "angular.js", description: "AngularJS — HTML enhanced for web apps!", url: "https://github.com/angular/angular.js",
  archived: true, pushedAt: "2022-04-12T00:00:00Z", openIssues: 455, contributors: 1600, stars: 58900, forks: 28100,
  language: "JavaScript", license: "MIT", commits: [18,34,27,43,51,46,35,32,24,15,8,2], labels: ["2011","2012","2013","2014","2015","2016","2017","2018","2019","2020","2021","2022"], isDemo: true
};

let current = demo;
const compact = n => n > 999 ? `${(n / 1000).toFixed(n > 9999 ? 0 : 1)}k` : String(n ?? 0);
const dateFmt = value => new Intl.DateTimeFormat("en", { month: "short", year: "numeric" }).format(new Date(value));
const daysSince = value => Math.max(0, Math.floor((Date.now() - new Date(value).getTime()) / 86400000));
const escapeHtml = value => String(value ?? "").replace(/[&<>'"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;","'":"&#39;",'"':"&quot;"}[c]));

function parseRepo(value) {
  const clean = value.trim().replace(/\.git\/?$/, "").replace(/\/$/, "");
  const match = clean.match(/(?:https?:\/\/)?(?:www\.)?github\.com\/([^/]+)\/([^/?#]+)/i) || clean.match(/^([^/\s]+)\/([^/\s]+)$/);
  if (!match) throw new Error("Enter a public GitHub URL in the form github.com/owner/repository");
  return { owner: match[1], repo: match[2] };
}

function getTotalFromLink(response, fallback = 0) {
  const link = response.headers.get("link") || "";
  const last = link.match(/[?&]page=(\d+)>; rel="last"/);
  return last ? Number(last[1]) : fallback;
}

async function fetchGitHub(owner, repo) {
  const headers = { Accept: "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28" };
  const base = `https://api.github.com/repos/${encodeURIComponent(owner)}/${encodeURIComponent(repo)}`;
  const [infoRes, commitsRes, contributorsRes, languagesRes] = await Promise.all([
    fetch(base, { headers }), fetch(`${base}/commits?per_page=100`, { headers }), fetch(`${base}/contributors?anon=true&per_page=1`, { headers }), fetch(`${base}/languages`, { headers })
  ]);
  if (infoRes.status === 404) throw new Error("Repository not found. Check that it is public and the URL is correct.");
  if (infoRes.status === 403) throw new Error("GitHub's public API limit was reached. The demo case is still available.");
  if (!infoRes.ok) throw new Error(`GitHub returned ${infoRes.status}. Please try again shortly.`);
  const info = await infoRes.json();
  const commits = commitsRes.ok ? await commitsRes.json() : [];
  const languages = languagesRes.ok ? await languagesRes.json() : {};
  const buckets = new Map();
  commits.forEach(c => {
    const d = new Date(c.commit?.author?.date || c.commit?.committer?.date);
    if (!Number.isNaN(d.getTime())) { const key = `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,"0")}`; buckets.set(key,(buckets.get(key)||0)+1); }
  });
  const sorted = [...buckets.entries()].sort((a,b)=>a[0].localeCompare(b[0])).slice(-12);
  return {
    owner: info.owner.login, repo: info.name, description: info.description || "No repository description provided.", url: info.html_url,
    archived: info.archived, pushedAt: info.pushed_at || info.updated_at, openIssues: info.open_issues_count, contributors: getTotalFromLink(contributorsRes, contributorsRes.ok ? 1 : 0),
    stars: info.stargazers_count, forks: info.forks_count, language: info.language || Object.keys(languages)[0] || "Mixed", license: info.license?.spdx_id || "Unspecified",
    commits: sorted.length ? sorted.map(x=>x[1]) : [0], labels: sorted.length ? sorted.map(x=>dateFmt(`${x[0]}-01`)) : ["No sample"], isDemo: false
  };
}

function makeEvidence(data) {
  const inactive = daysSince(data.pushedAt);
  return [
    { id:"E-01", title: data.archived ? "Repository is archived" : "Repository remains unarchived", detail: data.archived ? "Owner-set, read-only state" : "No archival flag observed", url:data.url },
    { id:"E-02", title:`Last push: ${dateFmt(data.pushedAt)}`, detail:`${inactive.toLocaleString()} days since the last code signal`, url:`${data.url}/commits` },
    { id:"E-03", title:`${data.openIssues.toLocaleString()} open issues`, detail:"Public issue/PR count reported by GitHub", url:`${data.url}/issues` },
    { id:"E-04", title:`${data.language} · ${data.license}`, detail:"Primary language and declared license", url:data.url }
  ];
}

function makeFindings(data) {
  const inactive = daysSince(data.pushedAt);
  const inactivity = inactive > 730 ? "The development signal has been quiet for multiple years." : inactive > 180 ? "The development signal has slowed substantially." : "Recent activity suggests this project may still be maintained.";
  return [
    { tag:"LIFECYCLE", confidence:data.archived?"HIGH / 98%":"MEDIUM / 78%", title:data.archived?"The project is intentionally preserved":"Inactivity is not proof of abandonment", body:data.archived?"GitHub's archive flag is direct evidence that the repository is preserved in a read-only state. It does not, by itself, explain the maintainers' reasons.":`${inactivity} Without an explicit maintainer statement, the cause remains unknown.`, evidence:"E-01 · E-02" },
    { tag:"COMMUNITY", confidence:"HIGH / 91%", title:"Unresolved work remains visible", body:`The repository reports ${data.openIssues.toLocaleString()} open issues or pull requests. This is a backlog signal, not proof that every item is actionable or still relevant.`, evidence:"E-03" },
    { tag:"RECOVERY", confidence:"MEDIUM / 82%", title:"A revival should begin with verification", body:`The safest first move is to reproduce the project in an isolated ${data.language} environment, map supported versions, and validate a small issue before proposing broad changes.`, evidence:"E-02 · E-04" }
  ];
}

function makeRoadmap(data) {
  return [
    ["Preserve the evidence",`Fork the repository, record the current ${data.license} license state, and snapshot installation notes before changing anything.`,"30–45 min"],
    ["Reconstruct the toolchain",`Identify the last supported ${data.language} runtime and lockfile. Install only inside a disposable environment.`,"1–2 hours"],
    ["Prove one clean baseline","Run documented checks without executing unreviewed scripts; record failures and missing dependencies as new evidence.","1–3 hours"],
    ["Choose one bounded repair",`Triage the ${data.openIssues.toLocaleString()} open items and select a reproducible, well-scoped issue with a verifiable outcome.`,"1 hour"],
    ["Publish a revival brief","Share compatibility findings, risks, and the smallest useful contribution before attempting a larger modernization.","45 min"]
  ];
}

function renderMetrics(data) {
  const inactivity = daysSince(data.pushedAt);
  const values = [[inactivity.toLocaleString(),"DAYS SINCE PUSH",data.archived?"Archived signal":"Observed inactivity"],[compact(data.openIssues),"OPEN ITEMS","Issues + pull requests"],[compact(data.contributors),"CONTRIBUTORS","Public contributor estimate"],[compact(data.stars),"STARS","Community footprint"]];
  $("#metrics").innerHTML = values.map(v=>`<div class="metric"><span>${v[1]}</span><strong>${v[0]}</strong><small>${v[2]}</small></div>`).join("");
}

function renderChart(data) {
  const values = data.commits.length > 1 ? data.commits : [0,0];
  const W=720,H=250,P=30,max=Math.max(...values,1); const x=i=>P+i*(W-2*P)/(values.length-1); const y=v=>H-P-v*(H-2*P)/max;
  const line=values.map((v,i)=>`${i?"L":"M"}${x(i).toFixed(1)},${y(v).toFixed(1)}`).join(" ");
  const area=`${line} L${x(values.length-1)},${H-P} L${P},${H-P} Z`;
  const grid=[0,.25,.5,.75,1].map(t=>`<line class="chart-grid" x1="${P}" y1="${P+t*(H-2*P)}" x2="${W-P}" y2="${P+t*(H-2*P)}"/>`).join("");
  const labels=data.labels.map((label,i)=>i%Math.ceil(data.labels.length/6)===0?`<text class="chart-axis" x="${x(i)}" y="${H-6}" text-anchor="middle">${escapeHtml(label)}</text>`:"").join("");
  $("#timelineChart").innerHTML=`<svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="none"><defs><linearGradient id="chartFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#b9f66d" stop-opacity=".18"/><stop offset="1" stop-color="#b9f66d" stop-opacity="0"/></linearGradient></defs>${grid}<path class="chart-area" d="${area}"/><path class="chart-line" d="${line}"/>${values.map((v,i)=>`<circle class="chart-point" cx="${x(i)}" cy="${y(v)}" r="3"/>`).join("")}${labels}</svg>`;
  $("#chartCaption").textContent=data.isDemo?"Curated demonstration data · Run a live autopsy to replace it with a recent commit sample.":`Recent public commit sample across ${data.labels.length} active month${data.labels.length===1?"":"s"}. A sample is not the repository's complete history.`;
}

function render(data) {
  current=data; const evidence=makeEvidence(data), findings=makeFindings(data), roadmap=makeRoadmap(data);
  $("#reportLabel").textContent=data.isDemo?"CURATED DEMO · VALUES MAY CHANGE":"LIVE PUBLIC GITHUB DATA";
  $("#repoName").textContent=`${data.owner} / ${data.repo}`; $("#repoDescription").textContent=data.description; $("#githubLink").href=data.url;
  renderMetrics(data); renderChart(data); $("#evidenceCount").textContent=String(evidence.length).padStart(2,"0");
  $("#evidenceList").innerHTML=evidence.map(e=>`<a class="evidence-item" href="${e.url}" target="_blank" rel="noreferrer"><span class="evidence-id">${e.id}</span><span><strong>${escapeHtml(e.title)}</strong><small>${escapeHtml(e.detail)}</small></span><span>↗</span></a>`).join("");
  $("#findingsGrid").innerHTML=findings.map((f,i)=>`<article class="finding"><div class="finding-top"><span>0${i+1} / ${f.tag}</span><span class="confidence">${f.confidence}</span></div><h5>${escapeHtml(f.title)}</h5><p>${escapeHtml(f.body)}</p><div class="finding-evidence">SUPPORTED BY ${f.evidence}</div></article>`).join("");
  $("#roadmapSummary").textContent=`Five deliberately small steps for a safe first pass. No repository code is executed by GhostCommits.`;
  $("#roadmap").innerHTML=roadmap.map(r=>`<li><div><h5>${escapeHtml(r[0])}</h5><p>${escapeHtml(r[1])}</p></div><span class="effort">EST. <b>${r[2]}</b></span></li>`).join("");
}

function showToast(message) { const toast=$("#toast"); toast.textContent=message; toast.classList.add("show"); clearTimeout(showToast.t); showToast.t=setTimeout(()=>toast.classList.remove("show"),2800); }

async function analyze(event) {
  event.preventDefault(); let target;
  try { target=parseRepo($("#repoUrl").value); } catch(error) { showToast(error.message); return; }
  const shell=$("#analysisShell"), loading=$("#loadingState"), button=$("#inspectButton"); shell.hidden=true; loading.hidden=false; button.disabled=true;
  const messages=["Locating the last heartbeat…","Reading public repository signals…","Corroborating evidence records…","Building the resurrection blueprint…"]; let i=0;
  const timer=setInterval(()=>{$("#loadingMessage").textContent=messages[++i%messages.length]},650);
  try { const data=await fetchGitHub(target.owner,target.repo); render(data); showToast("Live case file reconstructed"); setTimeout(()=>document.querySelector("#investigation").scrollIntoView({behavior:"smooth"}),100); }
  catch(error) { render(demo); showToast(error.message); }
  finally { clearInterval(timer); loading.hidden=true; shell.hidden=false; button.disabled=false; }
}

function exportEpitaph() {
  const c=$("#epitaphCanvas"),ctx=c.getContext("2d"),inactive=daysSince(current.pushedAt);
  ctx.fillStyle="#090d0b";ctx.fillRect(0,0,c.width,c.height);ctx.strokeStyle="#2c3a30";ctx.lineWidth=2;ctx.strokeRect(54,54,c.width-108,c.height-108);
  ctx.fillStyle="#b9f66d";ctx.fillRect(54,54,14,160);ctx.font="500 24px DM Mono, monospace";ctx.fillText("GHOSTCOMMITS / DIGITAL EPITAPH",100,120);
  ctx.fillStyle="#edf2e9";ctx.font="600 76px Manrope, sans-serif";ctx.fillText(`${current.owner} /`,100,260);ctx.fillStyle="#b9f66d";ctx.font="italic 500 92px Georgia, serif";ctx.fillText(current.repo,100,355);
  ctx.fillStyle="#93a097";ctx.font="400 27px Manrope, sans-serif";wrap(ctx,current.description,100,435,1180,42);
  const stats=[[inactive.toLocaleString(),"DAYS SINCE LAST PUSH"],[current.openIssues.toLocaleString(),"OPEN ITEMS"],[compact(current.contributors),"CONTRIBUTORS"]];
  stats.forEach((s,i)=>{const x=100+i*455;ctx.fillStyle="#edf2e9";ctx.font="600 56px Manrope, sans-serif";ctx.fillText(s[0],x,650);ctx.fillStyle="#76837a";ctx.font="400 18px DM Mono, monospace";ctx.fillText(s[1],x,690)});
  ctx.fillStyle="#b9f66d";ctx.font="500 25px DM Mono, monospace";ctx.fillText(current.archived?"PRESERVED, NOT FORGOTTEN":"THE SIGNAL MAY YET RETURN",100,830);ctx.fillStyle="#76837a";ctx.font="400 18px DM Mono, monospace";ctx.fillText(`Evidence observed ${new Date().toISOString().slice(0,10)} · ghostcommits`,100,875);
  const a=document.createElement("a");a.download=`ghostcommits-${current.owner}-${current.repo}.png`;a.href=c.toDataURL("image/png");a.click();showToast("Epitaph exported as PNG");
}
function wrap(ctx,text,x,y,maxWidth,lineHeight){const words=String(text).split(" ");let line="";for(const word of words){const test=line+word+" ";if(ctx.measureText(test).width>maxWidth&&line){ctx.fillText(line,x,y);line=word+" ";y+=lineHeight}else line=test}ctx.fillText(line,x,y)}

$("#repoForm").addEventListener("submit",analyze);$("#exportButton").addEventListener("click",exportEpitaph);
$("#themeToggle").addEventListener("click",()=>{document.body.classList.toggle("light");localStorage.setItem("ghost-theme",document.body.classList.contains("light")?"light":"dark")});
$$('[role="tab"]').forEach(tab=>tab.addEventListener("click",()=>{ $$('[role="tab"]').forEach(t=>t.setAttribute("aria-selected",String(t===tab)));$$('[role="tabpanel"]').forEach(p=>p.hidden=p.id!==`${tab.dataset.tab}Panel`)}));
if(localStorage.getItem("ghost-theme")==="light")document.body.classList.add("light");render(demo);
