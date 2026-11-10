let MODE = 'beach', LAST = null;
const TZ = 'America/Los_Angeles';
// marine lat/lon sit slightly offshore so the wave model has an ocean grid cell
const BEACHES = [
  {name:'Santa Monica',      drive:'~16 mi · 35 min', lat:34.0095,lon:-118.4972, mlat:34.00, mlon:-118.55, face:250, shelter:1},
  {name:'Venice',            drive:'~14 mi · 30 min', lat:33.9850,lon:-118.4695, mlat:33.97, mlon:-118.53, face:250, shelter:1},
  {name:'Dockweiler',        drive:'~19 mi · 35 min', lat:33.9360,lon:-118.4430, mlat:33.93, mlon:-118.50, face:270, shelter:1},
  {name:'Manhattan Beach',   drive:'~20 mi · 40 min', lat:33.8847,lon:-118.4109, mlat:33.88, mlon:-118.47, face:270, shelter:1},
  {name:'Hermosa Beach',     drive:'~21 mi · 40 min', lat:33.8622,lon:-118.3995, mlat:33.85, mlon:-118.46, face:270, shelter:1},
  {name:'Redondo Beach',     drive:'~22 mi · 40 min', lat:33.8492,lon:-118.3884, mlat:33.84, mlon:-118.45, face:260, shelter:1},
  {name:'Cabrillo (San Pedro)',drive:'~25 mi · 40 min',lat:33.7080,lon:-118.2780, mlat:33.69, mlon:-118.30, face:180, shelter:0.5},
  {name:'Long Beach (Belmont Shore)',drive:'~24 mi · 35 min',lat:33.7570,lon:-118.1200, mlat:33.73, mlon:-118.13, face:180, shelter:0.3},
  {name:'Malibu (Surfrider)',drive:'~28 mi · 55 min', lat:34.0360,lon:-118.6780, mlat:34.00, mlon:-118.72, face:190, shelter:1},
];

const clamp = (x,a=0,b=100)=>Math.max(a,Math.min(b,x));
const lerp = (x,x0,x1,y0,y1)=>y0+(y1-y0)*clamp((x-x0)/(x1-x0),0,1);

// ---- scoring: each returns 0..100 ----
const S = {
  air:  t => t==null?null : t>=76&&t<=88?100 : t<76?lerp(t,55,76,0,100) : lerp(t,88,102,100,10),
  water:t => t==null?null : lerp(t,58,70,15,100),
  wave: h => h==null?null : h<=3?100 : h<=5?lerp(h,3,5,100,70) : h<=8?lerp(h,5,8,70,25) : lerp(h,8,12,25,0),
  wind: w => w==null?null : w<=8?100 : lerp(w,8,28,100,0),
  sky:  (cloud,pp) => cloud==null?null : clamp((100-cloud*0.6) - Math.max(0,(pp||0)-20)*1.0),
  uv:   u => u==null?null : u<=5?100 : u<=7?85 : u<=10?65 : 45,
  aqi:  a => a==null?null : a<=50?100 : a<=100?lerp(a,50,100,100,60) : a<=150?lerp(a,100,150,60,25) : lerp(a,150,200,25,0),
};
const surfWind = (w,dir,face) => {
  if(w==null) return null;
  if(dir==null) return S.wind(w);
  const comp = Math.cos((dir-face)*Math.PI/180); // +1 onshore, -1 offshore
  if(w<5) return 90;
  return comp<=0 ? (w<=15?100:lerp(w,15,30,100,50)) : lerp(w*comp,3,18,95,10);
};
function scoreSurf(h,b){
  const ht = (h.swell??h.wave)==null?null:(h.swell??h.wave)*(b.shelter??1);
  const per = h.period;
  const hs = ht==null?null: ht<=3?lerp(ht,0.5,3,8,70) : ht<=6?lerp(ht,3,4,70,100) : ht<=8?lerp(ht,6,8,100,80) : lerp(ht,8,14,80,15);
  const ps = per==null?null:lerp(per,5,14,10,100);
  const ws = surfWind(h.wind,h.wdir,b.face);
  const parts=[[hs,.4],[ps,.25],[ws,.35]].filter(x=>x[0]!=null);
  const wt=parts.reduce((a,x)=>a+x[1],0);
  return wt? parts.reduce((a,x)=>a+x[0]*x[1],0)/wt : null;
}
const WEIGHTS = {air:.20,water:.15,wave:.15,wind:.15,sky:.15,uv:.10,aqi:.10};

function scoreHour(h){
  const parts = {
    air:S.air(h.temp), water:S.water(h.sst), wave:S.wave(h.wave), wind:S.wind(h.wind),
    sky:S.sky(h.cloud,h.pop), uv:S.uv(h.uv), aqi:S.aqi(h.aqi),
  };
  let sum=0,wt=0;
  for(const k in parts){ if(parts[k]!=null){ sum+=parts[k]*WEIGHTS[k]; wt+=WEIGHTS[k]; } }
  return wt? sum/wt : null;
}
const avg = a => { a=a.filter(x=>x!=null); return a.length? a.reduce((s,x)=>s+x,0)/a.length : null; };

function surfLabel(s){
  if(s>=80) return 'Firing';
  if(s>=60) return 'Fun';
  if(s>=40) return 'Fair';
  if(s>=25) return 'Poor';
  return 'Flat/blown out';
}
function label(s){
  if(s>=85) return ['Epic beach day','var(--s-epic)'];
  if(s>=70) return ['Great','var(--s-great)'];
  if(s>=55) return ['Good','var(--s-good)'];
  if(s>=40) return ['Meh','var(--s-meh)'];
  return ['Skip it','var(--s-skip)'];
}

// ---- data fetching ----
const qs = o => Object.entries(o).map(([k,v])=>k+'='+encodeURIComponent(v)).join('&');
async function getJson(url){
  const r = await fetch(url); if(!r.ok) throw new Error(url.split('?')[0]+' '+r.status);
  return r.json();
}
const asArray = x => Array.isArray(x)?x:[x];

async function loadAll(){
  const lat = BEACHES.map(b=>b.lat).join(','), lon = BEACHES.map(b=>b.lon).join(',');
  const mlat = BEACHES.map(b=>b.mlat).join(','), mlon = BEACHES.map(b=>b.mlon).join(',');
  const common = {timezone:TZ, forecast_days:4};
  const [wx, marine, air] = await Promise.all([
    getJson('https://api.open-meteo.com/v1/forecast?'+qs({latitude:lat,longitude:lon,...common,
      hourly:'temperature_2m,cloud_cover,precipitation_probability,wind_speed_10m,wind_direction_10m,uv_index',
      temperature_unit:'fahrenheit',wind_speed_unit:'mph'})),
    getJson('https://marine-api.open-meteo.com/v1/marine?'+qs({latitude:mlat,longitude:mlon,...common,
      hourly:'wave_height,swell_wave_height,swell_wave_period,wave_period,sea_surface_temperature',length_unit:'imperial',temperature_unit:'fahrenheit'})).catch(()=>null),
    getJson('https://air-quality-api.open-meteo.com/v1/air-quality?'+qs({latitude:lat,longitude:lon,...common,
      hourly:'us_aqi,uv_index'})).catch(()=>null),
  ]);
  return BEACHES.map((b,i)=>{
    const w = asArray(wx)[i], m = marine&&asArray(marine)[i], a = air&&asArray(air)[i];
    const times = w.hourly.time;
    const hours = times.map((t,j)=>({
      t,
      temp:w.hourly.temperature_2m[j], cloud:w.hourly.cloud_cover[j], pop:w.hourly.precipitation_probability[j],
      wind:w.hourly.wind_speed_10m[j], wdir:w.hourly.wind_direction_10m[j],
      uv: a?.hourly?.uv_index?.[j] ?? w.hourly.uv_index?.[j],
      aqi:a?.hourly?.us_aqi?.[j],
      wave:m?.hourly?.wave_height?.[j], swell:m?.hourly?.swell_wave_height?.[j], period:(m?.hourly?.swell_wave_period?.[j] ?? m?.hourly?.wave_period?.[j]), sst:m?.hourly?.sea_surface_temperature?.[j],
    }));
    return {beach:b, hours};
  });
}

// ---- aggregation ----
function nowLocal(){
  const p = Object.fromEntries(new Intl.DateTimeFormat('en-CA',{timeZone:TZ,hour12:false,year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit'}).formatToParts(new Date()).map(x=>[x.type,x.value]));
  return {date:`${p.year}-${p.month}-${p.day}`, hour:+p.hour % 24};
}
const hourOf = t => +t.slice(11,13), dateOf = t => t.slice(0,10);

function summarize(data, now){
  const {hours} = data;
  const days = [...new Set(hours.map(h=>dateOf(h.t)))];
  const daySummaries = days.map(d=>{
    let beachHrs = hours.filter(h=>dateOf(h.t)===d && hourOf(h.t)>=10 && hourOf(h.t)<=17);
    if(d===now.date){ const left = beachHrs.filter(h=>hourOf(h.t)>=now.hour); if(left.length) beachHrs = left; }
    beachHrs = beachHrs.map(h=>({...h,score:scoreHour(h),surf:scoreSurf(h,data.beach)}));
    const best = beachHrs.filter(h=>h.score!=null).sort((a,b)=>b.score-a.score)[0];
    const bestSurf = beachHrs.filter(h=>h.surf!=null).sort((a,b)=>b.surf-a.surf)[0];
    return {date:d, score:avg(beachHrs.map(h=>h.score)), surf:avg(beachHrs.map(h=>h.surf)), best, bestSurf, hrs:beachHrs};
  });
  const today = daySummaries.find(d=>d.date===now.date) || daySummaries[0];
  const cur = hours.find(h=>dateOf(h.t)===now.date && hourOf(h.t)===now.hour) || today.hrs[0];
  const stat = k => avg(today.hrs.map(h=>h[k]));
  return {
    score: today.score, best: today.best, surf: today.surf, bestSurf: today.bestSurf, days: daySummaries, cur,
    avg:{swell:avg(today.hrs.map(h=>h.swell??h.wave)), period:avg(today.hrs.map(h=>h.period)), temp:stat('temp'), sst:stat('sst'), wave:stat('wave'), wind:stat('wind'), pop:Math.max(...today.hrs.map(h=>h.pop||0)), aqi:stat('aqi')},
    maxUv: Math.max(...today.hrs.map(h=>h.uv||0)),
  };
}

// ---- tides (NOAA, LA Outer Harbor) ----
async function loadTides(){
  const d = new Date(); const pad=n=>String(n).padStart(2,'0');
  const ymd = `${d.getFullYear()}${pad(d.getMonth()+1)}${pad(d.getDate())}`;
  const j = await getJson('https://api.tidesandcurrents.noaa.gov/api/prod/datagetter?'+qs({
    product:'predictions',datum:'MLLW',station:'9410660',begin_date:ymd,range:48,interval:'hilo',
    units:'english',time_zone:'lst_ldt',format:'json'}));
  return j.predictions||[];
}
function renderTides(preds){
  const el = document.getElementById('tide');
  if(!preds.length) return;
  const now = new Date();
  const upcoming = preds.filter(p=>new Date(p.t.replace(' ','T'))>=now).slice(0,4);
  el.innerHTML = '<div>🌙 <b>Tides (LA Harbor):</b> '+upcoming.map(p=>{
    const t = new Date(p.t.replace(' ','T')).toLocaleTimeString([], {hour:'numeric',minute:'2-digit'});
    return `${p.type==='H'?'High':'Low'} ${(+p.v).toFixed(1)} ft at ${t}`;
  }).join(' · ')+'</div>';
  el.hidden = false;
}

// ---- rendering ----
const f = (x,d=0,u='') => x==null||isNaN(x)?'—':x.toFixed(d)+u;
const hr12 = h => (h%12||12)+(h<12?'am':'pm');
const dow = d => new Date(d+'T12:00:00').toLocaleDateString([], {weekday:'short'});

function uvLabel(u){ return u>=11?'Extreme':u>=8?'Very high':u>=6?'High':u>=3?'Moderate':'Low'; }

function render(results){
  const now = nowLocal();
  const rows = results.map(r=>({...r, sum:summarize(r,now)}))
    
    .sort((a,b)=>{const k=MODE==='surf'?'surf':'score';return (b.sum[k]??-1)-(a.sum[k]??-1);});
  const html = rows.map((r,i)=>{
    const s = r.sum, sc = s.score, [lab,col] = sc==null?['No data','var(--mute)']:label(sc);
    const warns = [];
    if(s.maxUv>=8) warns.push(`☀️ UV peaks at ${f(s.maxUv,0)} (${uvLabel(s.maxUv)}) — sunscreen & shade.`);
    if(s.avg.wave>=6) warns.push('🌊 Big surf — dangerous currents likely, swim near lifeguards.');
    if(s.avg.aqi>100) warns.push('😷 Poor air quality.');
    if(s.avg.pop>=40) warns.push('🌧️ Rain chance '+s.avg.pop+'%.');
    if(s.avg.sst!=null && s.avg.sst<62) warns.push('🥶 Cold water — wetsuit weather.');
    const sf = s.surf, sfCol = sf==null?'var(--mute)':label(sf)[1];
    return `<article class="card">
      <span class="rank">#${i+1}</span>
      <h3>${r.beach.name}</h3><div class="drive">🚗 ${r.beach.drive} from USC</div>
      <div class="top">
        <div class="ring" style="--p:${sc??0};--c:${col}"><span>${sc==null?'–':Math.round(sc)}</span></div>
        <div><div class="label" style="color:${col}">${lab}</div>
        <div class="best">${s.best?`Best around ${hr12(hourOf(s.best.t))} (${Math.round(s.best.score)})`:''}</div></div>
      </div>
      <div class="surf"><span class="pill" style="background:${sfCol}">🏄 Surf ${sf==null?'–':Math.round(sf)}</span>
        <span><b>${sf==null?'No data':surfLabel(sf)}</b> · ${f(s.avg.swell,1,' ft')} @ ${f(s.avg.period,0,'s')}${s.bestSurf?` · best ${hr12(hourOf(s.bestSurf.t))}`:''}</span></div>
      ${warns.map(w=>`<div class="warn">${w}</div>`).join('')}
      <div class="stats">
        <div>Air <b>${f(s.avg.temp,0,'°F')}</b></div><div>Water <b>${f(s.avg.sst,0,'°F')}</b></div>
        <div>Waves <b>${f(s.avg.wave,1,' ft')}</b></div><div>Wind <b>${f(s.avg.wind,0,' mph')}</b></div>
        <div>UV max <b>${f(s.maxUv,0)}</b></div><div>AQI <b>${f(s.avg.aqi,0)}</b></div>
      </div>
      <div class="days">${s.days.map(d=>{
        const [,c]=d.score==null?['','var(--mute)']:label(d.score);
        return `<div class="day" style="background:${c}">${dow(d.date)}<b>${d.score==null?'–':Math.round(d.score)}</b></div>`;}).join('')}</div>
    </article>`;
  }).join('');
  document.getElementById('cards').innerHTML = html;
}

async function run(){
  const status = document.getElementById('status');
  status.textContent = 'Loading…';
  try{
    const results = await loadAll();
    LAST = results; render(results);
    status.textContent = 'Updated '+new Date().toLocaleTimeString([], {hour:'numeric',minute:'2-digit'})+' · scores = today\'s beach hours';
  }catch(e){
    document.getElementById('cards').innerHTML = `<div class="err">Couldn't load conditions (${e.message}). Check your connection and hit Refresh.</div>`;
    status.textContent = 'Error';
  }
  loadTides().then(renderTides).catch(()=>{});
}
document.querySelectorAll('[data-mode]').forEach(b=>b.addEventListener('click',()=>{
  MODE=b.dataset.mode; document.querySelectorAll('[data-mode]').forEach(x=>x.classList.toggle('on',x===b)); if(LAST) render(LAST);
}));
document.getElementById('refresh').addEventListener('click', run);
if(typeof document!=='undefined' && !globalThis.__TEST__) { run(); setInterval(run, 15*60*1000); }
