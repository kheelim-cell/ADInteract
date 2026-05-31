import"./DsnmJJEf.js";import{aM as pt,ag as te,W as v,aR as d,b4 as h,af as t,bb as ut,aJ as ft,bf as Q,ad as xt,bg as bt,aX as D,b7 as G,aG as Nt,aL as gt}from"./DZw3CzZJ.js";import{a as _t,s as Zt}from"./1tbC218K.js";import{s as W}from"./DrNk6-25.js";import{b as n,d as Tt,h as x,i as St,e as ee,f as ae}from"./DYdvHkt6.js";import{i as O}from"./esggYe-A.js";import{s as Lt,c as re,e as Vt,i as Bt}from"./DWkWmUCR.js";import{p as H}from"./0TfH8zGS.js";import{c as Wt,k as Ht,j as It,e as se,f as Ut,q as oe,b as ie,g as ne,i as le,a as de,m as ce,l as pe,F as fe,T as ve,d as ue,p as me,u as Ft,r as ge}from"./BfOoc3Fz.js";import{s as he,b as xe}from"./sIPu7q3x.js";import{a as ht,g as kt,c as be,b as et,h as Yt,e as Gt,d as ye}from"./BGWJ93V5.js";import{P as Ot}from"./C2Y3_Ee9.js";import{G as zt}from"./B0y_GNzS.js";import{i as Rt,L as Et,G as Mt}from"./CpVtZ_C6.js";import{o as Dt}from"./QuEOonFV.js";import{b as jt}from"./BrC9WJ7c.js";import{g as we}from"./Cepz4cvy.js";import{d as Qt}from"./DLGEyEa8.js";import{s as _e}from"./CRJJ19w1.js";import{s as Le}from"./DbCGByZk.js";function At(o){const[e,r,i]=o.split("-");return new Date(Number(e),Number(r)-1,Number(i)).toLocaleDateString("en-GB",{day:"numeric",month:"short",year:"numeric"})}function ke(o,e,r){switch(o.dateRange){case"1m":return"Last 30 Days";case"3m":return"Last 3 Months";case"6m":return"Last 6 Months";case"12m":return"Last 12 Months";case"3y":return"Last 3 Years";case"ytd":return"Year to Date";default:return`${At(e)} – ${At(r)}`}}function Se(o){return o.project?o.project:o.district?o.district:o.saleType==="off-plan"?"Abu Dhabi — Off-Plan Market":o.saleType==="ready"?"Abu Dhabi — Ready Market":"Abu Dhabi Property Market"}function Me(o,e,r){const i=["ADInteract"];o.district&&i.push(o.district),o.project&&i.push(o.project),o.saleType!=="all"&&i.push(o.saleType==="off-plan"?"Off-Plan":"Ready"),o.propertyTypes.length&&i.push(o.propertyTypes.map(u=>u.charAt(0).toUpperCase()+u.slice(1)).join("+")),o.layouts.length&&i.push(o.layouts.map(u=>u.replace(/\s+/g,"")).join("+"));const s={"1m":"1M","3m":"3M","6m":"6M","12m":"12M","3y":"3Y",ytd:"YTD"};return i.push(o.dateRange&&s[o.dateRange]?s[o.dateRange]:`${At(e)} to ${At(r)}`),i.join(" - ")}function Ct(o,e){const r=Yt(o,e);if(r==null)return"";const i=r>=0;return`<span class="sg ${i?"up":"dn"}">${i?"▲":"▼"} ${Math.abs(r).toFixed(1)}% vs prior period</span>`}function qt(o){return`<span class="rnk${o===0?" r1":o===1?" r2":o===2?" r3":""}">${o+1}</span>`}const Ce=`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 200" style="height:72px;width:288px;flex-shrink:0;display:block">
  <defs>
    <linearGradient id="logobg" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#1e4d3a"/>
      <stop offset="100%" stop-color="#0d2318"/>
    </linearGradient>
    <linearGradient id="logogl" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="transparent"/>
      <stop offset="50%" stop-color="#C8A951" stop-opacity="0.85"/>
      <stop offset="100%" stop-color="transparent"/>
    </linearGradient>
  </defs>
  <rect width="800" height="200" fill="url(#logobg)"/>
  <rect width="800" height="2.5" fill="url(#logogl)"/>
  <rect x="24" y="24" width="152" height="152" rx="22" fill="rgba(255,255,255,0.06)" stroke="#C8A951" stroke-width="1.5" stroke-opacity="0.32"/>
  <path transform="translate(32,68) scale(1.7)" fill="#dfb83c"
    d="M0,38 L0,30 L5,30 L5,26 L10,26 L10,30 L11,30 L11,25 Q15.5,18 20,25 L20,30 L21,30
       L21,21 L23,21 L23,13 L25,3 L27,13 L27,21 L29,21 L29,17 L31,17 L31,7 L32,7 L32,2
       L32.5,0 L33,2 L33,7 L34,7 L34,17 L35,17 L35,21 L37,21 L37,13 L39.5,7 L42,13 L42,21
       L44,21 L44,16 L47,13 L50,16 L50,21 L52,21 L52,27 L57,27 L57,23 L64,23 L64,27 L72,27
       L72,31 L80,31 L80,38 Z"/>
  <text x="200" y="122" font-family="Montserrat,system-ui,-apple-system,sans-serif" font-size="76" fill="#dfb83c">
    <tspan font-weight="800" letter-spacing="-2">AD</tspan><tspan font-weight="300" font-style="italic" letter-spacing="-1">INTERACT</tspan>
  </text>
  <text x="202" y="154" font-family="Montserrat,system-ui,-apple-system,sans-serif"
        font-size="13.5" fill="rgba(200,169,81,0.75)" font-weight="600" letter-spacing="5">ABU DHABI PROPERTY TRANSACTIONS</text>
</svg>`;async function Pe(o){const{filters:e,dateStart:r,dateEnd:i,stats:s,topAreas:u,layoutSummary:l}=o;let g,c,a;if(e.project){const p=l.length>0?l:await Wt(e,r,i);g="Price by Bedroom Type",c='<th>#</th><th>Layout</th><th class="r">Transactions</th><th class="r">Median Price</th><th class="r">Median AED/sqft</th>',a=p.map((f,k)=>`<tr><td>${qt(k)}</td><td>${f.layout.charAt(0).toUpperCase()+f.layout.slice(1)}</td>
          <td class="r">${f.count.toLocaleString()}</td>
          <td class="r">${ht(f.medianPrice)}</td>
          <td class="r">${kt(f.medianRate)}</td></tr>`).join("")}else if(e.district){const p=await Ht(e,r,i,5);g=`Top Projects — ${e.district}`,c='<th>#</th><th>Project</th><th class="r">Transactions</th><th class="r">Median Price</th><th class="r">Median AED/sqft</th>',a=p.map((f,k)=>`<tr><td>${qt(k)}</td><td>${f.district}</td>
          <td class="r">${f.volume.toLocaleString()}</td>
          <td class="r">${ht(f.medianPrice)}</td>
          <td class="r">${kt(f.medianRate)}</td></tr>`).join("")}else{const p=(u.length>0?u:await It(e,r,i,5)).slice(0,5);g="Top Areas by Transaction Volume",c='<th>#</th><th>Area</th><th class="r">Transactions</th><th class="r">Median Price</th><th class="r">Median AED/sqft</th>',a=p.map((f,k)=>`<tr><td>${qt(k)}</td><td>${f.district}</td>
          <td class="r">${f.volume.toLocaleString()}</td>
          <td class="r">${ht(f.medianPrice)}</td>
          <td class="r">${kt(f.medianRate)}</td></tr>`).join("")}const y=await se(e,r,i),m=300,_=y.slice(0,m),w=y.length>m?`<p class="txnote">Showing first ${m} of ${y.length.toLocaleString()} transactions. Export the full dataset as CSV from adinteract.co.</p>`:"",L=e.project?"Community":"District",C=_.map(p=>{const f=p.sale_type==="off-plan"?'<span class="bd bop">Off-plan</span>':p.sale_type==="ready"?'<span class="bd brd">Ready</span>':`<span class="bd">${p.sale_type??""}</span>`,k=p.sale_sequence==="primary"?'<span class="bd bpr">Primary</span>':p.sale_sequence==="secondary"?'<span class="bd bsc">Secondary</span>':"",I=p.layout&&p.layout!=="unclassified"?p.layout.charAt(0).toUpperCase()+p.layout.slice(1):"-",J=e.project?p.community??p.district:p.district;return`<tr>
        <td>${be(p.sale_date)}</td>
        <td>${p.project_name||"Private"}</td>
        <td>${J||""}</td>
        <td class="r">${ht(p.price_aed)}</td>
        <td class="r">${p.rate_per_sqft?Math.round(p.rate_per_sqft).toLocaleString():"-"}</td>
        <td>${I}</td>
        <td class="r">${p.area_sqft?Math.round(p.area_sqft).toLocaleString():"-"}</td>
        <td class="c">${f}${k}</td>
      </tr>`}).join(""),j=Se(e),X=ke(e,r,i),$=Me(e,r,i),rt=new Date().toLocaleDateString("en-GB",{day:"numeric",month:"long",year:"numeric"}),M=[];e.saleType!=="all"&&M.push(e.saleType==="off-plan"?"Off-Plan":"Ready"),e.saleSequence!=="all"&&M.push(e.saleSequence==="primary"?"Primary":"Secondary"),e.propertyTypes.length&&M.push(...e.propertyTypes.map(p=>p.charAt(0).toUpperCase()+p.slice(1))),e.layouts.length&&M.push(...e.layouts);const V=M.length?`<span style="margin-left:8px">${M.map(p=>`<span class="fchip">${p}</span>`).join(" ")}</span>`:"",P=`<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>${$}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Montserrat:ital,wght@0,400;0,500;0,600;0,700;0,800;0,900;1,300&display=swap" rel="stylesheet">
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Montserrat',sans-serif;color:#111827;background:#fff;font-size:10.5px;line-height:1.45}
.pg{max-width:830px;margin:0 auto;padding:22px 26px}

/* ── Header ── */
.hdr{display:flex;justify-content:space-between;align-items:center;padding-bottom:14px;border-bottom:2px solid #C8A951;margin-bottom:16px;gap:16px}
.hdright{text-align:right;flex-shrink:0}
.rptitle{font-size:14px;font-weight:800;color:#111827}
.rpscope{font-size:9.5px;color:#6b7280;margin-top:3px}
.gen{font-size:9px;color:#9ca3af;margin-top:4px}
.fchip{display:inline-block;padding:1px 6px;border-radius:8px;font-size:8px;font-weight:600;background:#eff6ff;color:#1d4ed8;margin-left:3px}

/* ── Stats ── */
.sgrid{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-bottom:16px}
.sc{background:#f9fafb;border:1px solid #e5e7eb;border-radius:7px;padding:10px 12px}
.slbl{font-size:8px;font-weight:700;color:#9ca3af;text-transform:uppercase;letter-spacing:.5px;margin-bottom:3px}
.sval{font-size:13px;font-weight:800;color:#111827}
.sg{font-size:8.5px;display:block;margin-top:2px}
.up{color:#16a34a}.dn{color:#dc2626}

/* ── Section ── */
.sec{margin-bottom:16px}
.stitle{font-size:9.5px;font-weight:800;color:#1e4d3a;text-transform:uppercase;letter-spacing:.6px;margin-bottom:7px;padding-bottom:4px;border-bottom:1px solid #e5e7eb}

/* ── Tables ── */
table{width:100%;border-collapse:collapse}
thead tr{background:#f3f4f6}
th{padding:5px 6px;font-size:8px;font-weight:700;text-transform:uppercase;color:#6b7280;letter-spacing:.4px;text-align:left;font-family:'Montserrat',sans-serif}
td{padding:4px 6px;border-bottom:1px solid #f3f4f6;color:#374151;vertical-align:middle;font-family:'Montserrat',sans-serif}
tr:nth-child(even) td{background:#fafafa}
tr:last-child td{border-bottom:none}
.r{text-align:right}.c{text-align:center}

/* ── Rank circles ── */
.rnk{display:inline-flex;align-items:center;justify-content:center;width:17px;height:17px;border-radius:50%;background:#d1d5db;color:#374151;font-size:7.5px;font-weight:700}
.r1{background:#C8A951;color:#fff}
.r2{background:#71717a;color:#fff}
.r3{background:#78350f;color:#fff}

/* ── Badges ── */
.bd{display:inline-block;padding:1.5px 5px;border-radius:8px;font-size:7.5px;font-weight:700;margin:1px}
.bop{background:#eff6ff;color:#1d4ed8}
.brd{background:#f0fdf4;color:#15803d}
.bpr{background:#ecfdf5;color:#065f46}
.bsc{background:#faf5ff;color:#6d28d9}

/* ── Misc ── */
.txnote{font-size:9px;color:#6b7280;margin-bottom:5px}
.ftr{margin-top:18px;padding-top:9px;border-top:1px solid #e5e7eb;display:flex;justify-content:space-between}
.ftxt{font-size:8px;color:#9ca3af}

/* ── Print ── */
@media print{
  body{-webkit-print-color-adjust:exact;print-color-adjust:exact}
  @page{margin:10mm 12mm;size:A4}
  thead{display:table-header-group}
}
</style>
</head>
<body>
<div class="pg">

<!-- Header: official logo + report context -->
<div class="hdr">
  ${Ce}
  <div class="hdright">
    <div class="rptitle">${j}</div>
    <div class="rpscope">${X} &nbsp;·&nbsp; ADREC Transaction Data${V}</div>
    <div class="gen">Generated ${rt} &nbsp;·&nbsp; adinteract.co</div>
  </div>
</div>

<!-- Stats cards -->
<div class="sgrid">
  <div class="sc">
    <div class="slbl">Transactions</div>
    <div class="sval">${s.totalVolume.toLocaleString()}</div>
    ${Ct(s.totalVolume,s.prevTotalVolume)}
  </div>
  <div class="sc">
    <div class="slbl">Median Price</div>
    <div class="sval">${ht(s.medianPrice)}</div>
    ${Ct(s.medianPrice,s.prevMedianPrice)}
  </div>
  <div class="sc">
    <div class="slbl">Median AED / sqft</div>
    <div class="sval">${kt(s.medianRatePerSqft)}</div>
    ${Ct(s.medianRatePerSqft,s.prevMedianRatePerSqft)}
  </div>
  <div class="sc">
    <div class="slbl">Total Value</div>
    <div class="sval">${et(s.totalValue)} AED</div>
    ${Ct(s.totalValue,s.prevTotalValue)}
  </div>
</div>

<!-- Leaderboard -->
<div class="sec">
  <div class="stitle">${g}</div>
  <table>
    <thead><tr>${c}</tr></thead>
    <tbody>${a}</tbody>
  </table>
</div>

<!-- Transactions -->
<div class="sec">
  <div class="stitle">Transactions — ${y.length.toLocaleString()} in period</div>
  ${w}
  <table>
    <thead>
      <tr>
        <th>Date</th>
        <th>Project</th>
        <th>${L}</th>
        <th class="r">Price (AED)</th>
        <th class="r">AED/sqft</th>
        <th>Beds</th>
        <th class="r">Area (sqft)</th>
        <th class="c">Type · Sequence</th>
      </tr>
    </thead>
    <tbody>${C}</tbody>
  </table>
</div>

<!-- Footer -->
<div class="ftr">
  <span class="ftxt">Data source: Abu Dhabi Real Estate Centre (ADREC) &nbsp;·&nbsp; adinteract.co</span>
  <span class="ftxt">For informational purposes only. Not financial or investment advice.</span>
</div>

</div>
<script>window.onload = () => { window.print(); }<\/script>
</body>
</html>`,E=window.open("","_blank","width=980,height=760,scrollbars=yes");if(!E){alert("Please allow pop-ups for adinteract.co to open the PDF report.");return}E.document.write(P),E.document.close()}var Ae=x('<span class="inline-flex items-center gap-1 self-start px-2.5 py-1 rounded-full text-xs font-semibold bg-gray-50 text-gray-500 ring-1 ring-gray-200"><svg class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M5 12h14"></path></svg> </span>'),Te=St('<svg class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M4.5 19.5l15-15m0 0H8.25m11.25 0v11.25"></path></svg>'),Re=St('<svg class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M4.5 4.5l15 15m0 0V8.25m0 11.25H8.25"></path></svg>'),De=x("<span><!> </span>"),je=St('<svg class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M4.5 19.5l15-15m0 0H8.25m11.25 0v11.25"></path></svg>'),$e=St('<svg class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M4.5 4.5l15 15m0 0V8.25m0 11.25H8.25"></path></svg>'),ze=St('<svg class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M5 12h14"></path></svg>'),qe=x("<span><!> </span>"),Ee=x('<span class="text-xs text-navy/30 font-medium">No prior period data</span>'),Ve=x('<div class="stat-card flex flex-col gap-3"><span class="text-[10px] sm:text-[11px] font-semibold uppercase tracking-wider sm:tracking-widest text-navy/40"> </span> <p> </p> <div><!></div></div>');function Pt(o,e){pt(e,!0);const r=()=>_t(Ut,"$filters",i),[i,s]=Zt(),u=te("gated-locked");let l=Q(()=>u?.get()??!1),g=H(e,"currentRaw",3,0),c=H(e,"previousRaw",3,0);H(e,"previousValue",3,null);let a=Q(()=>Yt(g(),c())),y=Q(()=>t(a)!==null&&t(a)>0),m=Q(()=>t(a)!==null&&t(a)===0),_=Q(()=>c()>0&&r().dateRange!=="ytd"&&r().dateRange!=="custom");const w={"1m":"vs. last 1M","3m":"vs. last 3M","6m":"vs. last 6M","12m":"vs. last 12M","3y":"vs. last 3Y"};let L=Q(()=>t(_)?w[r().dateRange]??"":"");var C=Ve(),j=v(C),X=v(j,!0);d(j);var $=h(j,2),rt=v($,!0);d($);var M=h($,2),V=v(M);{var P=f=>{var k=Tt(),I=xt(k);{var J=K=>{var B=Ae(),R=h(v(B));d(B),ut(()=>W(R,` 0.0% flat · ${t(L)??""}`)),n(K,B)},nt=K=>{var B=De(),R=v(B);{var st=ot=>{var A=Te();n(ot,A)},yt=ot=>{var A=Re();n(ot,A)};O(R,ot=>{t(y)?ot(st):ot(yt,-1)})}var $t=h(R);d(B),ut(ot=>{Lt(B,1,`inline-flex items-center gap-1 self-start px-2.5 py-1 rounded-full text-xs font-semibold
                   ${t(y)?"bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200":"bg-red-50 text-red-700 ring-1 ring-red-200"}`),W($t,` ${ot??""} · ${t(L)??""}`)},[()=>Gt(t(a))]),n(K,B)};O(I,K=>{t(m)?K(J):K(nt,-1)})}n(f,k)},E=f=>{var k=qe(),I=v(k);{var J=R=>{var st=je();n(R,st)},nt=R=>{var st=$e();n(R,st)},K=R=>{var st=ze();n(R,st)};O(I,R=>{t(a)!==null&&t(a)>0?R(J):t(a)!==null&&t(a)<0?R(nt,1):R(K,-1)})}var B=h(I);d(k),ut(R=>{Lt(k,1,`inline-flex items-center gap-1 self-start px-2.5 py-1 rounded-full text-xs font-semibold
                 ${t(a)!==null&&t(a)>0?"bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200":t(a)!==null&&t(a)<0?"bg-red-50 text-red-700 ring-1 ring-red-200":"bg-gray-50 text-gray-500 ring-1 ring-gray-200"}`),W(B,` ${R??""}`)},[()=>t(a)!==null?Gt(t(a)):"—"]),n(f,k)},p=f=>{var k=Ee();n(f,k)};O(V,f=>{t(_)&&t(a)!==null?f(P):c()>0&&(r().dateRange==="ytd"||r().dateRange==="custom")?f(E,1):f(p,-1)})}d(M),d(C),ut(()=>{W(X,e.label),Lt($,1,`text-2xl sm:text-3xl font-bold text-navy leading-none${t(l)?" blur-[4px]":""}`),W(rt,e.value),Lt(M,1,re(t(l)?"blur-[3px]":""))}),n(o,C),ft(),s()}var Be=x('<div class="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4"><!> <!> <!> <!></div>');function Ne(o,e){pt(e,!0);var r=Be(),i=v(r);{let g=Q(()=>ye(e.stats.totalVolume));Pt(i,{label:"Transaction Volume",get value(){return t(g)},get currentRaw(){return e.stats.totalVolume},get previousRaw(){return e.stats.prevTotalVolume},get previousValue(){return e.stats.prevTotalVolume}})}var s=h(i,2);{let g=Q(()=>ht(e.stats.medianPrice));Pt(s,{label:"Median Price",get value(){return t(g)},get currentRaw(){return e.stats.medianPrice},get previousRaw(){return e.stats.prevMedianPrice},get previousValue(){return e.stats.prevMedianPrice}})}var u=h(s,2);{let g=Q(()=>kt(e.stats.medianRatePerSqft));Pt(u,{label:"Median Rate",get value(){return t(g)},get currentRaw(){return e.stats.medianRatePerSqft},get previousRaw(){return e.stats.prevMedianRatePerSqft},get previousValue(){return e.stats.prevMedianRatePerSqft}})}var l=h(u,2);{let g=Q(()=>et(e.stats.totalValue)+" AED");Pt(l,{label:"Total Value",get value(){return t(g)},get currentRaw(){return e.stats.totalValue},get previousRaw(){return e.stats.prevTotalValue},get previousValue(){return e.stats.prevTotalValue}})}d(r),n(o,r),ft()}var Fe=x('<div class="w-full h-72"></div>');function Ge(o,e){pt(e,!0);let r=H(e,"data",19,()=>[]),i=G(void 0),s;Dt(()=>{if(t(i)){s=Rt(t(i));const l=()=>s?.resize();return window.addEventListener("resize",l),()=>{window.removeEventListener("resize",l),s?.dispose()}}}),bt(()=>{if(s&&r()?.length){const l=r().map(a=>a.month),g=r().map(a=>a.medianPrice),c=r().map(a=>a.medianRate);s.setOption({textStyle:{fontFamily:"Manrope, system-ui, sans-serif"},tooltip:{trigger:"axis",backgroundColor:"#fff",borderColor:"#e5e7eb",borderWidth:1,textStyle:{color:"#374151",fontSize:12,fontFamily:"Manrope, system-ui, sans-serif"},formatter(a){let m=`<div class="font-medium mb-1">${a[0].axisValue}</div>`;for(const _ of a){const w=_.color,L=_.seriesName,C=L==="Median Price"?et(_.value)+" AED":et(_.value)+" AED/sqft";m+=`<div class="flex items-center gap-2"><span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:${w}"></span>${L}: <b>${C}</b></div>`}return m}},legend:{top:0,right:0,textStyle:{fontSize:12,color:"#6b7280"}},grid:{left:60,right:60,top:50,bottom:30},xAxis:{type:"category",data:l,axisLine:{lineStyle:{color:"#e5e7eb"}},axisTick:{show:!1},axisLabel:{color:"#9ca3af",fontSize:11,rotate:l.length>18?45:0}},yAxis:[{type:"value",name:"Price (AED)",nameTextStyle:{color:"#9ca3af",fontSize:11},axisLine:{show:!1},axisTick:{show:!1},splitLine:{lineStyle:{color:"#f3f4f6"}},axisLabel:{color:"#9ca3af",fontSize:11,formatter:a=>et(a)}},{type:"value",name:"AED/sqft",nameTextStyle:{color:"#9ca3af",fontSize:11},axisLine:{show:!1},axisTick:{show:!1},splitLine:{show:!1},axisLabel:{color:"#9ca3af",fontSize:11,formatter:a=>et(a)}}],series:[{name:"Median Price",type:"line",data:g,yAxisIndex:0,smooth:!0,symbol:"circle",symbolSize:4,lineStyle:{width:2.5,color:"#C8A951"},itemStyle:{color:"#C8A951"},areaStyle:{color:new Et(0,0,0,1,[{offset:0,color:"rgba(200,169,81,0.18)"},{offset:1,color:"rgba(200,169,81,0.01)"}])}},{name:"Median Rate/sqft",type:"line",data:c,yAxisIndex:1,smooth:!0,symbol:"circle",symbolSize:4,lineStyle:{width:2,color:"#1B4332",type:"dashed"},itemStyle:{color:"#1B4332"}}]})}});var u=Fe();jt(u,l=>D(i,l),()=>t(i)),n(o,u),ft()}var Oe=x('<div class="w-full h-72"></div>');function Ze(o,e){pt(e,!0);let r=H(e,"data",19,()=>[]),i=G(void 0),s;Dt(()=>{if(t(i)){s=Rt(t(i));const l=()=>s?.resize();return window.addEventListener("resize",l),()=>{window.removeEventListener("resize",l),s?.dispose()}}}),bt(()=>{if(s&&r()?.length){const l=r().map(a=>a.month),g=r().map(a=>a.offPlanVolume),c=r().map(a=>a.readyVolume);s.setOption({textStyle:{fontFamily:"Manrope, system-ui, sans-serif"},tooltip:{trigger:"axis",backgroundColor:"#fff",borderColor:"#e5e7eb",borderWidth:1,textStyle:{color:"#374151",fontSize:12,fontFamily:"Manrope, system-ui, sans-serif"},formatter(a){const y=a[0].axisValue;let m=0,_=`<div class="font-medium mb-1">${y}</div>`;for(const w of a)m+=w.value,_+=`<div class="flex items-center gap-2"><span style="display:inline-block;width:8px;height:8px;border-radius:2px;background:${w.color}"></span>${w.seriesName}: <b>${w.value.toLocaleString()}</b></div>`;return _+=`<div class="mt-1 pt-1 border-t border-gray-200 font-medium">Total: <b>${m.toLocaleString()}</b></div>`,_}},legend:{top:0,right:0,textStyle:{fontSize:12,color:"#6b7280"}},grid:{left:50,right:20,top:30,bottom:30},xAxis:{type:"category",data:l,axisLine:{lineStyle:{color:"#e5e7eb"}},axisTick:{show:!1},axisLabel:{color:"#9ca3af",fontSize:11,rotate:l.length>18?45:0}},yAxis:{type:"value",name:"Transactions",nameTextStyle:{color:"#9ca3af",fontSize:11},axisLine:{show:!1},axisTick:{show:!1},splitLine:{lineStyle:{color:"#f3f4f6"}},axisLabel:{color:"#9ca3af",fontSize:11}},series:[{name:"Off-plan",type:"bar",stack:"volume",data:g,barMaxWidth:28,itemStyle:{color:"#C8A951",borderRadius:[0,0,0,0]}},{name:"Ready",type:"bar",stack:"volume",data:c,barMaxWidth:28,itemStyle:{color:"#1B4332",borderRadius:[3,3,0,0]}}]})}});var u=Oe();jt(u,l=>D(i,l),()=>t(i)),n(o,u),ft()}var We=x('<div class="w-full h-72"></div>');function He(o,e){pt(e,!0);let r=H(e,"data",19,()=>[]),i=H(e,"clickable",3,!0),s=G(void 0),u;Dt(()=>{if(t(s)){u=Rt(t(s));const g=()=>u?.resize();return window.addEventListener("resize",g),()=>{window.removeEventListener("resize",g),u?.dispose()}}}),bt(()=>{if(u&&r()?.length){const g=[...r()].sort((m,_)=>m.volume-_.volume),c=g.map(m=>m.district),a=g.map(m=>m.volume),y=Math.max(280,g.length*32);t(s)&&(t(s).style.height=y+"px",u.resize()),u.setOption({textStyle:{fontFamily:"Manrope, system-ui, sans-serif"},tooltip:{trigger:"axis",axisPointer:{type:"shadow"},backgroundColor:"#fff",borderColor:"#e5e7eb",borderWidth:1,textStyle:{color:"#374151",fontSize:12,fontFamily:"Manrope, system-ui, sans-serif"},formatter(m){const _=m[0],w=g.find(L=>L.district===_.name);return w?`<div class="font-medium">${_.name}</div>
                    <div>Volume: <b>${w.volume.toLocaleString()}</b></div>
                    <div>Median Price: <b>${w.medianPrice.toLocaleString()} AED</b></div>
                    <div>Median Rate: <b>${w.medianRate.toLocaleString()} AED/sqft</b></div>`:""}},grid:{left:140,right:40,top:10,bottom:10},xAxis:{type:"value",name:"Transactions",nameTextStyle:{color:"#9ca3af",fontSize:11},axisLine:{show:!1},axisTick:{show:!1},splitLine:{lineStyle:{color:"#f3f4f6"}},axisLabel:{color:"#9ca3af",fontSize:11}},yAxis:{type:"category",data:c,axisLine:{lineStyle:{color:"#e5e7eb"}},axisTick:{show:!1},axisLabel:{color:"#374151",fontSize:11,width:120,overflow:"truncate"}},series:[{type:"bar",data:a,barMaxWidth:22,cursor:i()?"pointer":"default",itemStyle:{color:new Et(0,0,1,0,[{offset:0,color:"#1B4332"},{offset:1,color:"#C8A951"}]),borderRadius:[0,4,4,0]},emphasis:{itemStyle:{color:new Et(0,0,1,0,[{offset:0,color:"#2D6A4F"},{offset:1,color:"#dfb83c"}])}},label:{show:!0,position:"right",color:"#6b7280",fontSize:11,formatter:m=>m.value.toLocaleString()}}]}),u.off("click"),i()&&u.on("click",m=>{m.componentType==="series"&&we(`${Qt}/area/${encodeURIComponent(m.name)}`)})}});var l=We();jt(l,g=>D(s,g),()=>t(s)),n(o,l),ft()}var Ie=x('<div class="w-full h-72"></div>');function Ue(o,e){pt(e,!0);let r=H(e,"data",19,()=>[]),i=G(void 0),s;Dt(()=>{if(t(i)){s=Rt(t(i));const l=()=>s?.resize();return window.addEventListener("resize",l),()=>{window.removeEventListener("resize",l),s?.dispose()}}}),bt(()=>{if(s&&r()?.length){const l=r().map(c=>c.layout),g=r().map(c=>[c.min,c.q1,c.median,c.q3,c.max]);s.setOption({textStyle:{fontFamily:"Manrope, system-ui, sans-serif"},tooltip:{trigger:"item",backgroundColor:"#fff",borderColor:"#e5e7eb",borderWidth:1,textStyle:{color:"#374151",fontSize:12,fontFamily:"Manrope, system-ui, sans-serif"},formatter(c){const a=c.dataIndex,y=r()[a];return y?`<div class="font-medium mb-1">${y.layout}</div>
                    <div>Max: <b>${et(y.max)}</b></div>
                    <div>Q3: <b>${et(y.q3)}</b></div>
                    <div>Median: <b>${et(y.median)}</b></div>
                    <div>Q1: <b>${et(y.q1)}</b></div>
                    <div>Min: <b>${et(y.min)}</b></div>
                    <div class="mt-1 text-gray-400">${y.count.toLocaleString()} transactions</div>`:""}},grid:{left:70,right:30,top:20,bottom:40},xAxis:{type:"category",data:l,axisLine:{lineStyle:{color:"#e5e7eb"}},axisTick:{show:!1},axisLabel:{color:"#374151",fontSize:11}},yAxis:{type:"value",name:"AED/sqft",nameTextStyle:{color:"#9ca3af",fontSize:11},axisLine:{show:!1},axisTick:{show:!1},splitLine:{lineStyle:{color:"#f3f4f6"}},axisLabel:{color:"#9ca3af",fontSize:11,formatter:c=>et(c)}},series:[{type:"boxplot",data:g,itemStyle:{color:"#f6f3e8",borderColor:"#C8A951",borderWidth:1.5},boxWidth:["30%","50%"],emphasis:{itemStyle:{color:"#faf0ca",borderColor:"#0A1628",borderWidth:2}}}]})}});var u=Ie();jt(u,l=>D(i,l),()=>t(i)),n(o,u),ft()}var Ye=x('<div class="h-48 flex items-center justify-center"><p class="text-sm text-gray-400">No layout data for this period</p></div>'),Qe=x('<tr class="hover:bg-gray-50/50 transition-colors"><td class="py-2.5 pr-3 font-medium text-gray-900"> </td><td class="py-2.5 text-right tabular-nums text-gray-600"> </td><td class="py-2.5 text-right tabular-nums text-gray-700 whitespace-nowrap"> </td><td class="py-2.5 text-right tabular-nums font-semibold text-gray-900 whitespace-nowrap"> </td><td class="py-2.5 pl-3"><div class="w-full bg-gray-100 rounded-full h-1.5"><div class="bg-brand-400 h-1.5 rounded-full transition-all"></div></div></td></tr>'),Xe=x('<div class="overflow-x-auto"><table class="w-full text-sm"><thead><tr class="border-b border-gray-100"><th class="pb-2.5 text-left text-[10px] font-bold uppercase tracking-wider text-gray-400">Layout</th><th class="pb-2.5 text-right text-[10px] font-bold uppercase tracking-wider text-gray-400">Deals</th><th class="pb-2.5 text-right text-[10px] font-bold uppercase tracking-wider text-gray-400">Median Price</th><th class="pb-2.5 text-right text-[10px] font-bold uppercase tracking-wider text-gray-400">AED / sqft</th><th class="pb-2.5 w-20"></th></tr></thead><tbody class="divide-y divide-gray-50"></tbody></table></div>');function Je(o,e){pt(e,!0);let r=H(e,"data",19,()=>[]),i=Q(()=>Math.max(...r().map(a=>a.count),1));function s(a){return a&&a.charAt(0).toUpperCase()+a.slice(1)}var u=Tt(),l=xt(u);{var g=a=>{var y=Ye();n(a,y)},c=a=>{var y=Xe(),m=v(y),_=h(v(m));Vt(_,21,r,Bt,(w,L)=>{var C=Qe(),j=v(C),X=v(j,!0);d(j);var $=h(j),rt=v($,!0);d($);var M=h($),V=v(M,!0);d(M);var P=h(M),E=v(P,!0);d(P);var p=h(P),f=v(p),k=v(f);d(f),d(p),d(C),ut((I,J,nt,K,B)=>{W(X,I),W(rt,J),W(V,nt),W(E,K),_e(k,`width: ${B??""}%`)},[()=>s(t(L).layout),()=>t(L).count.toLocaleString(),()=>t(L).medianPrice?`AED ${Math.round(t(L).medianPrice).toLocaleString()}`:"—",()=>t(L).medianRate?Math.round(t(L).medianRate).toLocaleString():"—",()=>Math.round(t(L).count/t(i)*100)]),n(w,C)}),d(_),d(m),d(y),n(a,y)};O(l,a=>{r().length===0?a(g):a(c,-1)})}n(o,u),ft()}var Ke=x('<div class="h-48 flex items-center justify-center"><p class="text-sm text-gray-400">No comparable projects found in same district</p></div>'),ta=x('<a class="flex items-center gap-3 py-3 -mx-1 px-1 rounded-lg hover:bg-gray-50/80 transition-colors group"><span class="flex-shrink-0 w-5 h-5 rounded-full bg-gray-100 flex items-center justify-center text-[10px] font-bold text-gray-400 group-hover:bg-brand-100 group-hover:text-brand-600 transition-colors"></span> <div class="flex-1 min-w-0"><p class="text-sm font-medium text-gray-900 truncate group-hover:text-brand-700 transition-colors"> </p> <p class="text-xs text-gray-400"> </p></div> <div class="text-right flex-shrink-0"><p class="text-sm font-semibold text-gray-900 tabular-nums"> <span class="text-xs text-gray-400 font-normal">AED/sqft</span></p> <span> </span></div> <svg class="h-4 w-4 flex-shrink-0 text-gray-300 group-hover:text-brand-400 transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5"></path></svg></a>'),ea=x('<div class="divide-y divide-gray-50"></div>');function aa(o,e){pt(e,!0);let r=H(e,"data",19,()=>[]);function i(c){const a=Math.abs(c*100).toFixed(1);return`${c>=0?"+":"−"}${a}%`}var s=Tt(),u=xt(s);{var l=c=>{var a=Ke();n(c,a)},g=c=>{var a=ea();Vt(a,21,r,Bt,(y,m,_)=>{var w=ta(),L=v(w);L.textContent=_+1;var C=h(L,2),j=v(C),X=v(j,!0);d(j);var $=h(j,2),rt=v($);d($),d(C);var M=h(C,2),V=v(M),P=v(V);Nt(),d(V);var E=h(V,2),p=v(E,!0);d(E),d(M),Nt(2),d(w),ut((f,k,I,J)=>{Le(w,"href",`${Qt??""}/project/${f??""}`),W(X,t(m).project_name),W(rt,`${k??""} transactions`),W(P,`${I??""} `),Lt(E,1,`text-[11px] font-semibold tabular-nums ${t(m).rateDiff>=0?"text-emerald-600":"text-red-500"}`),W(p,J)},[()=>encodeURIComponent(t(m).project_name),()=>t(m).volume.toLocaleString(),()=>Math.round(t(m).medianRate).toLocaleString(),()=>i(t(m).rateDiff)]),n(y,w)}),d(a),n(c,a)};O(u,c=>{r().length===0?c(l):c(g,-1)})}n(o,s),ft()}var ra=x('<div class="stat-card animate-pulse"><div class="h-3 w-20 bg-gray-200 rounded mb-3"></div> <div class="h-7 w-28 bg-gray-200 rounded mb-2"></div> <div class="h-3 w-16 bg-gray-200 rounded"></div></div>'),sa=x('<div class="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4"></div>'),oa=x('<div class="mt-6 rounded-2xl border border-dashed border-gray-200 bg-white px-6 py-8 text-center"><div class="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-gray-100"><svg class="h-6 w-6 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 15.803 7.5 7.5 0 0 0 15.803 15.803z"></path></svg></div> <p class="mt-3 text-sm font-semibold text-gray-700">No transactions match these filters</p> <p class="mt-1 text-xs text-gray-400">Try broadening the date range or removing a filter</p> <button type="button" class="mt-4 inline-flex items-center gap-1.5 rounded-full px-5 py-2 text-xs font-semibold bg-brand-600 text-white hover:bg-brand-700 transition-colors">Clear all filters</button> <div class="mt-5 flex justify-center"><!></div></div>'),ia=x('<div class="h-64 flex items-center justify-center"><div class="animate-pulse text-gray-400 text-sm">Loading chart...</div></div>'),na=x('<div class="h-64 flex flex-col items-center justify-center gap-2 text-center"><svg class="h-8 w-8 text-gray-200" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 0 1 3 19.875v-6.75ZM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V8.625ZM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V4.125Z"></path></svg> <p class="text-sm text-gray-400">No data for current filters</p></div>'),la=x('<div class="h-64 flex items-center justify-center"><div class="animate-pulse text-gray-400 text-sm">Loading chart...</div></div>'),da=x('<div class="h-64 flex flex-col items-center justify-center gap-2 text-center"><svg class="h-8 w-8 text-gray-200" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 0 1 3 19.875v-6.75ZM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V8.625ZM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V4.125Z"></path></svg> <p class="text-sm text-gray-400">No data for current filters</p></div>'),ca=x('<div class="mt-8 grid grid-cols-1 lg:grid-cols-2 gap-6"><div class="chart-card"><h3 class="text-sm font-semibold text-navy mb-4">Median Price Trend</h3> <!></div> <div class="chart-card"><h3 class="text-sm font-semibold text-navy mb-4">Transaction Volume</h3> <!></div></div>'),pa=x('<div class="h-48 flex items-center justify-center"><div class="animate-pulse text-gray-400 text-sm">Loading...</div></div>'),fa=x('<div class="h-48 flex items-center justify-center"><div class="animate-pulse text-gray-400 text-sm">Loading...</div></div>'),va=x('<div class="chart-card"><h3 class="text-sm font-semibold text-navy mb-4">Comparable Projects</h3> <p class="text-xs text-gray-400 mb-4 -mt-2">Closest AED/sqft in the same district</p> <!></div> <div class="chart-card"><h3 class="text-sm font-semibold text-navy mb-4">Price by Layout</h3> <!></div>',1),ua=x('<div class="h-64 flex items-center justify-center"><div class="animate-pulse text-gray-400 text-sm">Loading chart...</div></div>'),ma=x('<div class="h-64 flex flex-col items-center justify-center gap-2 text-center"><svg class="h-8 w-8 text-gray-200" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 0 1 3 19.875v-6.75ZM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V8.625ZM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V4.125Z"></path></svg> <p class="text-sm text-gray-400">No data for current filters</p></div>'),ga=x('<div class="h-64 flex items-center justify-center"><div class="animate-pulse text-gray-400 text-sm">Loading chart...</div></div>'),ha=x('<div class="h-64 flex flex-col items-center justify-center gap-2 text-center"><svg class="h-8 w-8 text-gray-200" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 0 1 3 19.875v-6.75ZM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V8.625ZM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V4.125Z"></path></svg> <p class="text-sm text-gray-400">No data for current filters</p></div>'),xa=x('<div class="chart-card"><h3 class="text-sm font-semibold text-navy mb-4"> </h3> <!></div> <div class="chart-card"><h3 class="text-sm font-semibold text-navy mb-4">Price per Sqft by Layout</h3> <!></div>',1),ba=x('<div class="mt-8 grid grid-cols-1 lg:grid-cols-2 gap-6"><!></div>'),ya=x('<div class="max-w-7xl mx-auto px-4 sm:px-6 py-6"><!> <!> <div class="mt-6"><!></div> <!> <!> <div class="mt-8"><!></div> <!></div>');function Fa(o,e){pt(e,!0);const r=()=>_t(Ut,"$filters",l),i=()=>_t(ue,"$dateRangeMs",l),s=()=>_t(xe,"$dbReady",l),u=()=>_t(me,"$prevDateRange",l),[l,g]=Zt();let c=H(e,"topAreasLabel",3,"Top Areas by Volume"),a=H(e,"topAreasClickable",3,!0),y=H(e,"useTopProjects",3,!1),m=H(e,"projectName",3,""),_=Q(()=>!!m()),w=G(null),L=G(gt([])),C=G(gt([])),j=G(gt([])),X=G(gt([])),$=G(gt([])),rt=G(gt([])),M=G(0),V=G(!1),P=G(!1),E=G(!1);async function p(){if(!(!t(w)||t(E))){D(E,!0);try{await Pe({filters:r(),dateStart:i().start,dateEnd:i().end,stats:t(w),topAreas:t(C),layoutSummary:t(X)})}finally{D(E,!1)}}}let f=Q(()=>!t(V)&&!t(P)&&t(M)===0&&t(w)!==null);bt(()=>{s()&&oe().then(A=>he.set(A)).catch(()=>{})}),bt(()=>{const A=s(),N=r(),b=i(),U=u();if(!A)return;D(V,!0),D(P,!0);const lt=setTimeout(()=>{const tt=t(_)?Promise.resolve([]):y()?Ht(N,b.start,b.end):It(N,b.start,b.end),z=t(_)?ie(m(),b.start,b.end):tt,Y=t(_)?Wt(N,b.start,b.end):ne(N,b.start,b.end);Promise.all([le(N,b.start,b.end,U.start,U.end),de(N,b.start,b.end),tt,z,Y,ce(N,b.start,b.end),pe(N,b.start,b.end)]).then(([Z,it,dt,vt,ct,S,q])=>{D(w,Z,!0),D(L,it,!0),t(_)?(D($,vt,!0),D(X,ct,!0)):(D(C,dt,!0),D(j,ct,!0)),D(rt,S,!0),D(M,q,!0)}).finally(()=>{D(V,!1),D(P,!1)})},200);return()=>clearTimeout(lt)});var k=ya(),I=v(k);fe(I,{});var J=h(I,2);Ot(J,{get activeDistrict(){return r().district},onSelect:A=>Ft({district:A})});var nt=h(J,2),K=v(nt);zt(K,{children:(A,N)=>{var b=Tt(),U=xt(b);{var lt=z=>{var Y=sa();Vt(Y,20,()=>Array(4),Bt,(Z,it)=>{var dt=ra();n(Z,dt)}),d(Y),n(z,Y)},tt=z=>{Ne(z,{get stats(){return t(w)}})};O(U,z=>{t(V)&&!t(w)?z(lt):t(w)&&z(tt,1)})}n(A,b)},$$slots:{default:!0}}),d(nt);var B=h(nt,2);{var R=A=>{var N=oa(),b=h(v(N),6),U=h(b,2),lt=v(U);Ot(lt,{get activeDistrict(){return r().district},alwaysShow:!0,onSelect:tt=>Ft({district:tt})}),d(U),d(N),ae("click",b,function(...tt){ge?.apply(this,tt)}),n(A,N)};O(B,A=>{t(f)&&A(R)})}var st=h(B,2);zt(st,{children:(A,N)=>{var b=ca(),U=v(b),lt=h(v(U),2);{var tt=S=>{var q=ia();n(S,q)},z=S=>{var q=na();n(S,q)},Y=S=>{Mt(S,{children:(q,mt)=>{Ge(q,{get data(){return t(L)}})},$$slots:{default:!0}})};O(lt,S=>{t(P)&&t(L).length===0?S(tt):t(f)?S(z,1):S(Y,-1)})}d(U);var Z=h(U,2),it=h(v(Z),2);{var dt=S=>{var q=la();n(S,q)},vt=S=>{var q=da();n(S,q)},ct=S=>{Mt(S,{children:(q,mt)=>{Ze(q,{get data(){return t(L)}})},$$slots:{default:!0}})};O(it,S=>{t(P)&&t(L).length===0?S(dt):t(f)?S(vt,1):S(ct,-1)})}d(Z),d(b),n(A,b)},$$slots:{default:!0}});var yt=h(st,2),$t=v(yt);ve($t,{get transactions(){return t(rt)},get totalCount(){return t(M)},get loading(){return t(V)},onExportPdf:p,get exportingPdf(){return t(E)}}),d(yt);var ot=h(yt,2);zt(ot,{children:(A,N)=>{var b=ba(),U=v(b);{var lt=z=>{var Y=va(),Z=xt(Y),it=h(v(Z),4);{var dt=F=>{var wt=pa();n(F,wt)},vt=F=>{aa(F,{get data(){return t($)}})};O(it,F=>{t(P)&&t($).length===0?F(dt):F(vt,-1)})}d(Z);var ct=h(Z,2),S=h(v(ct),2);{var q=F=>{var wt=fa();n(F,wt)},mt=F=>{Je(F,{get data(){return t(X)}})};O(S,F=>{t(P)&&t(X).length===0?F(q):F(mt,-1)})}d(ct),n(z,Y)},tt=z=>{var Y=xa(),Z=xt(Y),it=v(Z),dt=v(it,!0);d(it);var vt=h(it,2);{var ct=T=>{var at=ua();n(T,at)},S=T=>{var at=ma();n(T,at)},q=T=>{Mt(T,{children:(at,Kt)=>{He(at,{get data(){return t(C)},get clickable(){return a()}})},$$slots:{default:!0}})};O(vt,T=>{t(P)&&t(C).length===0?T(ct):t(f)?T(S,1):T(q,-1)})}d(Z);var mt=h(Z,2),F=h(v(mt),2);{var wt=T=>{var at=ga();n(T,at)},Xt=T=>{var at=ha();n(T,at)},Jt=T=>{Mt(T,{children:(at,Kt)=>{Ue(at,{get data(){return t(j)}})},$$slots:{default:!0}})};O(F,T=>{t(P)&&t(j).length===0?T(wt):t(f)?T(Xt,1):T(Jt,-1)})}d(mt),ut(()=>W(dt,c())),n(z,Y)};O(U,z=>{t(_)?z(lt):z(tt,-1)})}d(b),n(A,b)},$$slots:{default:!0}}),d(k),n(o,k),ft(),g()}ee(["click"]);export{Fa as D};
