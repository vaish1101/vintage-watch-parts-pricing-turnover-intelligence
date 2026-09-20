const state={data:null,charts:[]};
const euro=new Intl.NumberFormat("en-IE",{style:"currency",currency:"EUR"});
const integer=new Intl.NumberFormat("en-IE",{maximumFractionDigits:0});

document.addEventListener("DOMContentLoaded",async()=>{
  try{
    const response=await fetch("./demo-data.json",{cache:"no-store"});
    if(!response.ok)throw new Error(`Data load failed (${response.status})`);
    state.data=await response.json();
    document.querySelector("#demo-notice span:last-child").textContent=state.data.metadata.notice;
    document.getElementById("header-freshness").textContent=`Snapshot ${formatDate(state.data.metadata.generated_at)}`;
    window.addEventListener("hashchange",route);route();
  }catch(error){document.getElementById("app").innerHTML=`<section class="error-state"><h2>Dashboard data could not be loaded</h2><p>${escapeHtml(error.message)}</p></section>`;}
});

function route(){
  destroyCharts();
  const hash=location.hash.replace(/^#/,"")||"portfolio";
  const [view,id]=hash.split("/");
  document.querySelectorAll("[data-nav]").forEach(link=>link.classList.toggle("active",link.dataset.nav===view));
  if(view==="inventory")renderInventory();else if(view==="item"&&id)renderItem(decodeURIComponent(id));else renderPortfolio();
  window.scrollTo({top:0,behavior:"instant"});if(window.lucide)window.lucide.createIcons();
}

function renderPortfolio(){
  const {portfolio,items,metadata}=state.data;
  const coverage=portfolio.priced_items/portfolio.eligible_items;
  const confidence=countBy(items.filter(x=>x.recommended_price!==null),"pricing_confidence");
  const basis=countBy(items,"pricing_basis");
  const turnover=countBy(items.filter(x=>x.recommended_price!==null),"turnover_method");
  document.getElementById("app").innerHTML=`
    <section class="page-heading"><div><div class="eyebrow">Public synthetic demo</div><h1>Portfolio intelligence</h1><p class="subtitle">A decision view for price coverage, evidence quality and expected selling velocity across a long tail spare parts portfolio.</p></div><span class="version-chip">Model ${escapeHtml(metadata.model_version)}</span></section>
    <section class="kpi-grid">
      ${kpi("Inventory parts",integer.format(portfolio.eligible_items),"Unique synthetic items","green")}
      ${kpi("Supported prices",integer.format(portfolio.priced_items),`${percent(coverage)} portfolio coverage`,"blue")}
      ${kpi("Portfolio value",euro.format(portfolio.recommended_portfolio_value),"Price x available stock","purple")}
      ${kpi("Stock units",integer.format(portfolio.stock_units),"Synthetic physical units","")}
      ${kpi("Historical support",integer.format(portfolio.historical_supported),"Direct sold evidence","green")}
      ${kpi("Abstained",integer.format(portfolio.abstained_items),"No unsupported price shown","red")}
    </section>
    <div class="section-title"><h2>Recommendation coverage</h2><p>Coverage is paired with explicit abstention where trusted evidence is insufficient.</p></div>
    <section class="coverage-panel"><div class="coverage-copy"><span class="eyebrow">Evidence-gated pricing</span><strong>${portfolio.priced_items} of ${portfolio.eligible_items}</strong><p>Items receive a recommendation only after candidate evidence passes deterministic identity and contradiction checks.</p><div class="progress"><span style="width:${coverage*100}%"></span></div></div><div class="basis-grid">${basisStat("Historical supported",basis.HISTORICAL_SUPPORTED||0,"Direct sold evidence drives price")}${basisStat("Active only",basis.ACTIVE_ONLY||0,"Calibrated asking-price fallback")}${basisStat("No recommendation",basis.NO_RECOMMENDATION||0,"Evidence gate did not pass")}</div></section>
    <section class="analytics-grid">${chartPanel("Pricing confidence","Priced items by final confidence","confidence-chart")}${chartPanel("Evidence basis","How each recommendation is supported","basis-chart")}${chartPanel("Turnover method","Direct observations and fallback hierarchy","turnover-chart")}</section>
    <div class="section-title"><h2>Decision ready inventory</h2><p>A sample of recommendations from the frozen synthetic contract.</p></div>${inventoryTable(items.slice(0,8),items.length)}
  `;
  requestAnimationFrame(()=>{
    state.charts.push(makeBarChart("confidence-chart",["High","Medium","Low"],[confidence.HIGH||0,confidence.MEDIUM||0,confidence.LOW||0],["#18865d","#a86916","#c43b3b"]));
    state.charts.push(makeDoughnut("basis-chart",["Historical","Active only","Abstained"],[basis.HISTORICAL_SUPPORTED||0,basis.ACTIVE_ONLY||0,basis.NO_RECOMMENDATION||0],["#18865d","#3168d9","#d4d0c8"]));
    state.charts.push(makeBarChart("turnover-chart",["Direct item","Comparable cohort","Portfolio prior"],[turnover.DIRECT_ITEM_HAZARD||0,turnover.COMPARABLE_COHORT_HAZARD||0,turnover.HIERARCHICAL_PORTFOLIO_PRIOR||0],["#7443d9","#3168d9","#a86916"]));
  });
}

function renderInventory(){
  const brands=[...new Set(state.data.items.map(x=>x.brand))].sort();
  document.getElementById("app").innerHTML=`
    <section class="page-heading"><div><div class="eyebrow">Evidence-level exploration</div><h1>Inventory pricing</h1><p class="subtitle">Search recommendations, inspect confidence and open an item to see its price and turnover trace.</p></div></section>
    <section class="toolbar">${field("Search",'<input id="search" type="search" placeholder="Brand, caliber, part or component">')}${field("Brand",`<select id="brand"><option value="">All brands</option>${brands.map(x=>`<option>${escapeHtml(x)}</option>`).join("")}</select>`)}${field("Pricing confidence",'<select id="confidence"><option value="">All confidence levels</option><option>HIGH</option><option>MEDIUM</option><option>LOW</option></select>')}${field("Turnover support",'<select id="turnover"><option value="">All turnover methods</option><option value="DIRECT_ITEM_HAZARD">Direct item</option><option value="COMPARABLE_COHORT_HAZARD">Comparable cohort</option><option value="NO_PRICE_RECOMMENDATION">Insufficient data</option></select>')}</section><div id="inventory-results"></div>`;
  ["search","brand","confidence","turnover"].forEach(id=>document.getElementById(id).addEventListener("input",updateInventory));updateInventory();
}

function updateInventory(){
  const query=document.getElementById("search").value.trim().toLowerCase();
  const brand=document.getElementById("brand").value,confidence=document.getElementById("confidence").value,turnover=document.getElementById("turnover").value;
  const filtered=state.data.items.filter(item=>{const haystack=`${item.brand} ${item.caliber} ${item.part_number} ${item.part_name}`.toLowerCase();return(!query||haystack.includes(query))&&(!brand||item.brand===brand)&&(!confidence||item.pricing_confidence===confidence)&&(!turnover||item.turnover_method===turnover)});
  document.getElementById("inventory-results").innerHTML=inventoryTable(filtered,state.data.items.length);
  document.querySelectorAll("tbody tr[data-id]").forEach(row=>row.addEventListener("click",()=>location.hash=`item/${encodeURIComponent(row.dataset.id)}`));
}

function renderItem(id){
  const item=state.data.items.find(row=>row.inventory_id===id);if(!item){document.getElementById("app").innerHTML='<section class="empty-state"><h2>Item not found</h2><a href="#inventory">Return to inventory</a></section>';return}
  const priced=item.recommended_price!==null;
  document.getElementById("app").innerHTML=`<a class="back-link" href="#inventory"><i data-lucide="arrow-left" aria-hidden="true"></i> Back to inventory</a><section class="detail-head"><div><div class="eyebrow">Synthetic inventory item</div><h1>${escapeHtml(item.brand)} ${escapeHtml(item.caliber)} ${escapeHtml(item.part_number)}</h1><p class="subtitle">${escapeHtml(item.part_name)}</p><div class="identity-tags"><span>Brand: ${escapeHtml(item.brand)}</span><span>Caliber: ${escapeHtml(item.caliber)}</span><span>Stock: ${item.stock_quantity} units</span></div></div><div class="recommendation"><small>${priced?"Recommended price":"Pricing decision"}</small><strong>${priced?euro.format(item.recommended_price):"Abstained"}</strong>${priced?`<div class="range">Range ${euro.format(item.lower_bound)} to ${euro.format(item.upper_bound)}</div><div style="margin-top:12px">${badge(item.pricing_confidence)}</div>`:`<div class="range">${reasonLabel(item.no_recommendation_reason)}</div>`}</div></section>${priced?detailContent(item):abstentionContent(item)}`;
}

function detailContent(item){return `<section class="detail-grid"><div class="panel"><div class="panel-heading"><h2>Pricing traceback</h2><p>Stored components from the authoritative synthetic contract.</p></div><div class="metric-list">${metricRow("Evidence basis",basisLabel(item.pricing_basis))}${metricRow("Historical market value",item.historical_value===null?"Not available":euro.format(item.historical_value))}${metricRow("Current market value",item.current_value===null?"Not available":euro.format(item.current_value))}${metricRow("Demand index",item.demand_index.toFixed(2))}${metricRow("Scarcity score",item.scarcity_score.toFixed(2))}${metricRow("Price trend",`${(item.price_trend*100).toFixed(1)}%`)}${metricRow("Final pricing confidence",item.pricing_confidence)}</div><div class="evidence-blocks"><div class="evidence-block"><strong>${item.active_evidence_count}</strong><span>Unique active listings</span></div><div class="evidence-block"><strong>${item.historical_evidence_count}</strong><span>Historical evidence records</span></div></div></div><div class="panel"><div class="panel-heading"><h2>Turnover intelligence</h2><p>Price confidence and selling time confidence answer different questions.</p></div><div class="metric-list">${metricRow("Method",turnoverLabel(item.turnover_method))}${metricRow("Confidence",item.turnover_confidence)}${metricRow("Median selling horizon",item.median_days_to_sale===null?"Insufficient sold evidence":`${item.median_days_to_sale} days`)}</div>${probability("Sale probability in 30 days",item.p_sale_30d)}${probability("Sale probability in 90 days",item.p_sale_90d)}<p class="subtitle" style="font-size:12px;margin-top:18px">Turnover is a directional exponential hazard estimate, not a guaranteed sale date.</p></div></section>`}
function abstentionContent(item){return `<section class="panel"><div class="panel-heading"><h2>Why no price is shown</h2><p>The system preserves uncertainty instead of substituting an unsupported portfolio average.</p></div><div class="abstention"><strong>${reasonLabel(item.no_recommendation_reason)}</strong><br>No trusted direct evidence passed the configured identity and quality gates for this synthetic item.</div><div class="evidence-blocks"><div class="evidence-block"><strong>${item.active_evidence_count}</strong><span>Accepted active listings</span></div><div class="evidence-block"><strong>${item.historical_evidence_count}</strong><span>Accepted historical records</span></div></div></section>`}

function inventoryTable(items,total){return `<section class="panel table-panel"><div class="table-meta"><span>${items.length} of ${total} items</span><span>Click a row for full traceback</span></div><div class="table-scroll"><table><thead><tr><th>Part</th><th>Stock</th><th>Recommended price</th><th>Pricing confidence</th><th>Evidence basis</th><th>Selling horizon</th></tr></thead><tbody>${items.length?items.map(item=>`<tr data-id="${escapeHtml(item.inventory_id)}"><td class="item-name"><strong>${escapeHtml(item.brand)} ${escapeHtml(item.caliber)} ${escapeHtml(item.part_number)}</strong><span>${escapeHtml(item.part_name)}</span></td><td>${item.stock_quantity}</td><td class="price">${item.recommended_price===null?'<span class="muted">No recommendation</span>':euro.format(item.recommended_price)}</td><td>${badge(item.pricing_confidence)}</td><td>${basisLabel(item.pricing_basis)}</td><td>${item.median_days_to_sale===null?'<span class="muted">Insufficient data</span>':`${item.median_days_to_sale} days`}</td></tr>`).join(""):'<tr><td colspan="6" class="empty-state">No items match these filters.</td></tr>'}</tbody></table></div></section>`}

function kpi(label,value,note,tone){return `<article class="kpi ${tone}"><small>${label}</small><strong>${value}</strong><span>${note}</span></article>`}function basisStat(label,value,note){return `<div class="basis-stat"><small>${label}</small><strong>${integer.format(value)}</strong><span class="muted">${note}</span></div>`}function chartPanel(title,subtitle,id){return `<article class="panel"><div class="panel-heading"><h3>${title}</h3><p>${subtitle}</p></div><div class="chart-wrap"><canvas id="${id}"></canvas></div></article>`}function field(label,control){return `<div class="field"><label>${label}</label>${control}</div>`}function metricRow(label,value){return `<div class="metric-row"><span>${label}</span><strong>${escapeHtml(String(value))}</strong></div>`}function probability(label,value){const pct=value===null?0:Math.round(value*100);return `<div class="probability"><div class="probability-line"><span>${label}</span><strong>${value===null?"Unavailable":`${pct}%`}</strong></div><div class="progress"><span style="width:${pct}%"></span></div></div>`}function badge(value){return `<span class="badge ${String(value).toLowerCase()}">${escapeHtml(value)}</span>`}
function percent(value){return `${(value*100).toFixed(1)}%`}function formatDate(value){return new Date(value).toLocaleDateString("en-GB",{day:"2-digit",month:"short",year:"numeric"})}function countBy(rows,key){return rows.reduce((out,row)=>{out[row[key]]=(out[row[key]]||0)+1;return out},{})}function basisLabel(value){return({HISTORICAL_SUPPORTED:"Historical supported",ACTIVE_ONLY:"Active only",NO_RECOMMENDATION:"No recommendation"})[value]||value}function turnoverLabel(value){return({DIRECT_ITEM_HAZARD:"Direct item hazard",COMPARABLE_COHORT_HAZARD:"Comparable cohort hazard",HIERARCHICAL_PORTFOLIO_PRIOR:"Portfolio prior",NO_PRICE_RECOMMENDATION:"No price recommendation"})[value]||value}function reasonLabel(value){return({NO_CANDIDATES:"No candidates retrieved",ALL_CANDIDATES_REJECTED:"All candidates contradicted the item identity",ONLY_LOW_CONFIDENCE_CANDIDATES:"Only low-confidence candidates were found",NO_TRUSTWORTHY_EVIDENCE:"No trustworthy evidence"})[value]||"Insufficient evidence"}
function makeBarChart(id,labels,values,colors){return new Chart(document.getElementById(id),{type:"bar",data:{labels,datasets:[{data:values,backgroundColor:colors,borderRadius:4,maxBarThickness:42}]},options:chartOptions(false)})}function makeDoughnut(id,labels,values,colors){return new Chart(document.getElementById(id),{type:"doughnut",data:{labels,datasets:[{data:values,backgroundColor:colors,borderColor:"#fff",borderWidth:3}]},options:chartOptions(true)})}function chartOptions(legend){return{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:legend,position:"bottom",labels:{boxWidth:10,usePointStyle:true,font:{family:"DM Sans",size:10}}}},scales:legend?{}:{x:{grid:{display:false}},y:{beginAtZero:true,grid:{color:"#efede8"},ticks:{precision:0}}}}}function destroyCharts(){state.charts.forEach(chart=>chart.destroy());state.charts=[]}function escapeHtml(value){return String(value).replace(/[&<>'"]/g,char=>({"&":"&amp;","<":"&lt;",">":"&gt;","'":"&#39;",'"':"&quot;"})[char])}
