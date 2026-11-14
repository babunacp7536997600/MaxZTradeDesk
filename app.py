import streamlit as st, pandas as pd, requests, feedparser, yfinance as yf
import plotly.graph_objects as go
import re
from io import StringIO
from urllib.parse import quote
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo
from concurrent.futures import ThreadPoolExecutor

st.set_page_config(page_title="Trader Dashboard", page_icon="📈", layout="wide", initial_sidebar_state="collapsed")

SEC = {"Bank": "^NSEBANK", "IT": "^CNXIT", "Auto": "^CNXAUTO", "Pharma": "^CNXPHARMA", "FMCG": "^CNXFMCG", "Metal": "^CNXMETAL",
       "Energy": "^CNXENERGY", "Realty": "^CNXREALTY", "Media": "^CNXMEDIA", "Infra": "^CNXINFRA", "PSE": "^CNXPSE"}
IX = {"^NSEI": "Nifty 50", "^BSESN": "Sensex", "^NSEBANK": "Bank Nifty", "^INDIAVIX": "India VIX"}
IDX = {**{k.upper(): v for k, v in SEC.items()}, **{"NIFTY " + k.upper(): v for k, v in SEC.items()},
       "NIFTY": "^NSEI", "NIFTY 50": "^NSEI", "SENSEX": "^BSESN", "BANKNIFTY": "^NSEBANK", "BANK NIFTY": "^NSEBANK"}
UNI = {
    "Largecap": "RELIANCE TCS HDFCBANK INFY ICICIBANK SBIN BHARTIARTL ITC LT HINDUNILVR AXISBANK MARUTI SUNPHARMA",
    "Midcap": "PERSISTENT POLYCAB COFORGE MPHASIS LUPIN AUROPHARMA FEDERALBNK GODREJPROP BHARATFORG CUMMINSIND VOLTAS ASTRAL",
    "Smallcap": "CDSL CAMS ANGELONE RADICO KARURVYSYA NATCOPHARM ZENSARTECH SONATSOFTW KFINTECH CASTROLIND",
    "F&O": "TATASTEEL JSWSTEEL HINDALCO ONGC NTPC POWERGRID COALINDIA BAJFINANCE ADANIPORTS DLF INDUSINDBK",
    "Banks & Finance": "HDFCBANK ICICIBANK SBIN KOTAKBANK AXISBANK BAJFINANCE BAJAJFINSV PNB BANKBARODA CHOLAFIN",
    "IT & Pharma": "TCS INFY WIPRO HCLTECH TECHM LTIM SUNPHARMA CIPLA DRREDDY DIVISLAB"}
MFU = {"Large Cap": ["Nippon India Large Cap", "Mirae Asset Large Cap", "HDFC Large Cap", "ICICI Prudential Large Cap"],
       "Mid Cap": ["HDFC Mid Cap", "Motilal Oswal Midcap", "Nippon India Growth Mid Cap", "Axis Midcap", "Kotak Midcap"],
       "Small Cap": ["Nippon India Small Cap", "SBI Small Cap", "Quant Small Cap", "Axis Small Cap", "HDFC Small Cap"],
       "Flexi Cap": ["Parag Parikh Flexi Cap", "HDFC Flexi Cap", "Kotak Flexicap", "UTI Flexi Cap"],
       "ELSS": ["Quant ELSS Tax Saver", "Mirae Asset ELSS Tax Saver", "SBI Long Term Equity", "Bandhan ELSS Tax Saver"],
       "Index (Nifty 50)": ["UTI Nifty 50 Index", "ICICI Prudential Nifty 50 Index", "SBI Nifty Index", "HDFC Index Fund NIFTY 50"]}
HOLD = {"Large Cap": "3-5 saal", "Mid Cap": "5+ saal", "Small Cap": "7+ saal", "Flexi Cap": "5+ saal",
        "ELSS": "3 saal lock-in, 5+ saal ideal", "Index (Nifty 50)": "5+ saal"}
POS = "surge gain rally profit beat record order win upgrade buy growth jump rise strong dividend bonus approval boost".split()
NEG = "fall drop loss miss downgrade sell fraud probe penalty ban cut weak plunge crash default warning decline slump".split()
SHORT = "result q1 q2 q3 q4 earnings rbi policy fii dii".split()
MID = "order merger acquisition approval launch capex deal stake".split()


# ---------- indicators & analysis ----------
def ind(df):
    c = df.Close; d = c.diff()
    for n in (20, 50, 200): df[f"S{n}"] = c.rolling(n).mean()
    g = d.clip(lower=0).ewm(alpha=1 / 14).mean(); l = (-d.clip(upper=0)).ewm(alpha=1 / 14).mean()
    df["RSI"] = 100 - 100 / (1 + g / l)
    df["MACD"] = c.ewm(span=12).mean() - c.ewm(span=26).mean(); df["SIG"] = df.MACD.ewm(span=9).mean()
    tr = pd.concat([df.High - df.Low, (df.High - c.shift()).abs(), (df.Low - c.shift()).abs()], axis=1).max(axis=1)
    df["ATR"] = tr.ewm(alpha=1 / 14).mean()
    return df


def pattern(df):
    a, b = df.iloc[-2], df.iloc[-1]
    body = abs(b.Close - b.Open); rng = b.High - b.Low + 1e-9
    lo = min(b.Open, b.Close) - b.Low; up = b.High - max(b.Open, b.Close)
    if body < 0.1 * rng: return "Doji (indecision): agli candle ka wait karo"
    if lo > 2 * body and up < body: return "Hammer: support par ho to bullish reversal, entry candle high ke upar"
    if up > 2 * body and lo < body: return "Shooting star: resistance par ho to bearish, exit/short candle low ke neeche"
    if b.Close > b.Open and a.Close < a.Open and b.Close > a.Open and b.Open < a.Close: return "Bullish engulfing: entry iski high ke upar, SL iski low ke neeche"
    if b.Close < b.Open and a.Close > a.Open and b.Close < a.Open and b.Open > a.Close: return "Bearish engulfing: exit ya short iski low ke neeche"
    if b.Close >= df.High.iloc[-21:-1].max(): return "20-din breakout: volume confirm ho to entry, retest par safe"
    if b.Close <= df.Low.iloc[-21:-1].min(): return "20-din breakdown: naya buy avoid"
    return "Koi clear pattern nahi: trend ke saath chalo"


def analyze(df):
    df = ind(df.copy()); r = df.iloc[-1]; C = df.Close; c = r.Close; a = r.ATR; l200 = pd.notna(r.S200)
    sc = (20 if c > r.S50 else -20) + (15 if c > r.S20 else -15) + (15 if r.MACD > r.SIG else -15) + (15 if c > C.iloc[-22] else -15)
    sc += (20 if r.S50 > r.S200 else -20) if l200 else 0
    sc += 15 if 45 < r.RSI < 70 else -15 if r.RSI < 40 else -5 if r.RSI >= 75 else 0
    sig = "BUY" if sc >= 40 else "SELL" if sc <= -40 else "HOLD"
    sd = 1 if sc >= 0 else -1; side = "LONG" if sd == 1 else "SHORT/AVOID"
    f = lambda m: round(c - sd * m * a, 2); t = lambda m: round(c + sd * m * a, 2)
    e1 = round(r.High if sd == 1 else r.Low, 2); e = round(c, 2)
    plan = pd.DataFrame([
        ["Intraday", side, e1, round(e1 - sd * .5 * a, 2), round(e1 + sd * a, 2), "0.5 ATR step", "Usi din, 3:15 PM tak"],
        ["Swing", side, e, f(1.5), t(3), "10-din low/high", "5-15 din"],
        ["Positional", side, e, f(2.5), t(6), "SMA50 close", "1-3 mahine"],
        ["Long-term", side, e, round(r.S200, 2) if sd == 1 and l200 else f(4), t(12), "SMA200 close", "6+ mahine"]],
        columns=["Style", "Side", "Entry", "Stop-loss", "Target", "Trailing SL", "Hold"])
    v = C.pct_change().tail(60).std()
    k = lambda *b: sum(1 if x else -1 for x in b)
    s1 = k(r.MACD > r.SIG, c > C.iloc[-2], r.RSI > 50); s5 = k(c > r.S20, c > C.iloc[-6], r.MACD > 0)
    s21 = k(c > r.S50, c > C.iloc[-22], r.S20 > r.S50); s63 = k(l200 and r.S50 > r.S200, c > C.iloc[-64], c > r.S50)
    lab = lambda x: "Bullish 🟢" if x >= 2 else "Bearish 🔴" if x <= -2 else "Sideways ⚪"
    out = pd.DataFrame([[n, lab(s), f"{c * (1 - v * d ** .5):,.1f} – {c * (1 + v * d ** .5):,.1f}"]
                        for n, s, d in [("1 Day", s1, 1), ("1 Week", s5, 5), ("1 Month", s21, 21), ("3 Months", s63, 63)]],
                       columns=["Horizon", "Bias", "Likely range (±1σ)"])
    return {"price": c, "chg": (c / C.iloc[-2] - 1) * 100, "score": sc, "signal": sig, "rsi": r.RSI,
            "pattern": pattern(df), "plan": plan, "outlook": out}


# ---------- data fetchers ----------
@st.cache_data(ttl=300)
def hist(s):
    for x in ([s, s[:-3] + ".BO"] if s.endswith(".NS") else [s]):
        try:
            d = yf.Ticker(x).history(period="2y")
            if len(d) > 80: return x, d
        except Exception:
            pass
    return s, None


@st.cache_data(ttl=3600)
def info(s):
    try: return yf.Ticker(s).info or {}
    except Exception: return {}


def resolve(q):
    k = q.strip().upper()
    if k in IDX: return IDX[k]
    if k.startswith("^") or "." in k: return k
    if " " not in k: return k + ".NS"
    try:
        r = [x["symbol"] for x in yf.Search(q, max_results=8).quotes if x["symbol"].endswith((".NS", ".BO"))]
        return r[0] if r else k.replace(" ", "") + ".NS"
    except Exception:
        return k.replace(" ", "") + ".NS"


@st.cache_data(ttl=900)
def scan(cat):
    t = [x + ".NS" for x in UNI[cat].split()]
    d = yf.download(t, period="1y", group_by="ticker", progress=False, threads=True)
    out = []
    for x in t:
        try:
            df = d[x].dropna()
            if len(df) > 120: out.append({"Stock": x[:-3], **analyze(df)})
        except Exception:
            pass
    return sorted(out, key=lambda z: -z["score"])


@st.cache_data(ttl=300)
def idx():
    return yf.download(list(IX), period="5d", progress=False)["Close"].ffill()


@st.cache_data(ttl=600)
def sectors():
    d = yf.download(list(SEC.values()), period="6mo", progress=False)["Close"].dropna(axis=1, how="all").ffill()
    inv = {v: k for k, v in SEC.items()}
    rows = [{"Sector": inv[c], **{lb: round((d[c].iloc[-1] / d[c].iloc[-1 - n] - 1) * 100, 2)
                                  for n, lb in [(1, "1D %"), (5, "1W %"), (21, "1M %"), (63, "3M %")]}} for c in d.columns]
    return pd.DataFrame(rows).sort_values("1M %", ascending=False)


@st.cache_data(ttl=600)
def nse(path):
    h = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)", "Accept": "application/json", "Referer": "https://www.nseindia.com/"}
    s = requests.Session(); s.get("https://www.nseindia.com", headers=h, timeout=10)
    return s.get("https://www.nseindia.com/api/" + path, headers=h, timeout=10).json()


@st.cache_data(ttl=600)
def news(q):
    try:
        e = feedparser.parse("https://news.google.com/rss/search?q=" + quote(q) + "&hl=en-IN&gl=IN&ceid=IN:en").entries[:15]
        return [(x.title, x.link, x.get("source", {}).get("title", ""), x.get("published", "")[:22]) for x in e]
    except Exception:
        return []


def show_news(q, n=8):
    items = news(q)[:n]
    if not items: st.info("Abhi news nahi mili. Refresh dabao.")
    for t, l, s, p in items:
        w = t.lower(); a = sum(k in w for k in POS); b = sum(k in w for k in NEG)
        tag = "🟢 Positive" if a > b else "🔴 Negative" if b > a else "⚪ Neutral"
        hz = "1-5 din" if any(k in w for k in SHORT) else "1-3 mahine" if any(k in w for k in MID) else "1-4 hafte"
        tip = ("dip par buy ya breakout entry, SL swing-low ke neeche" if a > b else
               "naya buy avoid, holding par trailing SL, F&O me pullback par short" if b > a else "price action confirm hone tak wait")
        t2 = t.replace("[", "(").replace("]", ")").replace("$", "\\$")
        st.markdown(f"**[{t2}]({l})**  \n{s} · {p} · {tag} · asar: {hz}  \n_Strategy: {tip}_")


# ---------- mutual funds ----------
def _find(q):
    try: return [(x["schemeCode"], x["schemeName"]) for x in requests.get("https://api.mfapi.in/mf/search", params={"q": q}, timeout=15).json()]
    except Exception: return []


def _nav(c):
    j = requests.get(f"https://api.mfapi.in/mf/{c}", timeout=20).json()
    d = pd.DataFrame(j["data"]); d.index = pd.to_datetime(d["date"], format="%d-%m-%Y")
    return j["meta"].get("scheme_category", ""), pd.to_numeric(d["nav"], errors="coerce").dropna().sort_index()


mf_find = st.cache_data(ttl=3600)(_find)
mf_nav = st.cache_data(ttl=3600)(_nav)


def mf_stats(s):
    r = {}
    for n, k in [(21, "1M"), (63, "3M"), (126, "6M"), (252, "1Y")]:
        if len(s) > n: r[k] = round((s.iloc[-1] / s.iloc[-1 - n] - 1) * 100, 1)
    if len(s) > 756: r["3Y CAGR"] = round(((s.iloc[-1] / s.iloc[-757]) ** (1 / 3) - 1) * 100, 1)
    r["Vol %"] = round(s.pct_change().std() * 252 ** .5 * 100, 1); r["MaxDD %"] = round((s / s.cummax() - 1).min() * 100, 1)
    r["Trend"] = "Up 🟢" if s.iloc[-1] > s.tail(50).mean() else "Down 🔴"
    return r


@st.cache_data(ttl=3600)
def mf_pick(cat):
    def one(n):
        try:
            m = [x for x in _find(n) if "direct" in x[1].lower() and "growth" in x[1].lower()
                 and not any(k in x[1].lower() for k in ("idcw", "dividend", "bonus"))]
            return {"Fund": m[0][1][:60], **mf_stats(_nav(m[0][0])[1])} if m else None
        except Exception:
            return None
    with ThreadPoolExecutor(6) as ex:
        return pd.DataFrame([r for r in ex.map(one, MFU[cat]) if r])


def show_mf(q):
    res = mf_find(q)[:40]
    if not res: st.warning("Koi fund nahi mila. Fund house + category likho (jaise: Parag Parikh Flexi Cap)."); return
    res.sort(key=lambda x: ("direct" not in x[1].lower(), "growth" not in x[1].lower()))
    names = dict(res)
    code = st.selectbox("Fund chuno", [x[0] for x in res], format_func=lambda c: names[c])
    cat, s = mf_nav(code); stt = mf_stats(s)
    st.subheader(names[code]); st.caption(cat)
    st.line_chart(s.tail(756)); st.dataframe(pd.DataFrame([stt]), hide_index=True)
    st.info(("SIP/holding jaari rakho ✅" if stt["Trend"].startswith("Up") else "Naya lumpsum rok ke SIP jaari rakho ⚠️") + " · Hold: 3-5+ saal")
    show_news(names[code].split(" - ")[0] + " mutual fund", 5)


def show_stock(q):
    s, df = hist(resolve(q))
    if df is None:
        st.error("Symbol nahi mila. NSE symbol likho (jaise RELIANCE, TCS) ya index (NIFTY, PHARMA)."); return
    a = analyze(df); d = ind(df.copy()).tail(180); ix = s.startswith("^")
    nm = q.upper() if ix else (info(s).get("shortName") or s)
    st.subheader(f"{nm} ({s})")
    m = st.columns(3)
    m[0].metric("Price", f"{a['price']:,.2f}", f"{a['chg']:.2f}%")
    m[1].metric("Signal", a["signal"], f"score {a['score']}", delta_color="off")
    m[2].metric("RSI", f"{a['rsi']:.0f}")
    fig = go.Figure(go.Candlestick(x=d.index, open=d.Open, high=d.High, low=d.Low, close=d.Close, name="Price"))
    for n in (20, 50, 200): fig.add_scatter(x=d.index, y=d[f"S{n}"], name=f"SMA{n}", line=dict(width=1))
    fig.update_layout(height=380, margin=dict(l=0, r=0, t=10, b=0), xaxis_rangeslider_visible=False, legend=dict(orientation="h"))
    st.plotly_chart(fig)
    st.markdown("**Pattern:** " + a["pattern"])
    st.markdown("**Outlook** (volatility range, guarantee nahi)"); st.dataframe(a["outlook"], hide_index=True)
    st.markdown("**Trade plan**"); st.dataframe(a["plan"], hide_index=True)
    st.caption("Intraday entry = last candle high/low ka breakout. Short sirf F&O me; cash me SHORT = avoid/exit.")
    if not ix:
        i = info(s); g = lambda k, m=1: f"{i[k] * m:,.1f}" if i.get(k) is not None else "-"
        st.dataframe(pd.DataFrame([{"Sector": i.get("sector", "-"), "PE": g("trailingPE"), "P/B": g("priceToBook"),
                                    "ROE %": g("returnOnEquity", 100), "D/E": g("debtToEquity"), "MCap ₹Cr": g("marketCap", 1e-7)}]), hide_index=True)
    show_news(q + " India market" if ix else nm + " share NSE", 8)


# ---------- FII / FPI / DII flows (multi-source) ----------
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"}
FC = ["Date", "FII Buy", "FII Sell", "FII Net", "DII Buy", "DII Sell", "DII Net"]


def _clean(df):
    df = df.iloc[:, :7].copy(); df.columns = FC
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    for c in FC[1:]: df[c] = pd.to_numeric(df[c].astype(str).str.replace(r"[,+₹\s]", "", regex=True), errors="coerce")
    return df.dropna().sort_values("Date", ascending=False).reset_index(drop=True)


def _groww():
    h = requests.get("https://www.groww.in/fii-dii-data", headers=UA, timeout=15).text
    for t in pd.read_html(StringIO(h)):
        if t.shape[1] >= 7:
            d = _clean(t)
            if len(d) >= 5: return d
    raise ValueError("table nahi mili")


def _tape():
    x = requests.get("https://tapetide.com/fii-dii-data.md", headers=UA, timeout=15).text
    m = re.findall(r"\|\s*(\d{4}-\d{2}-\d{2})\s*\|((?:\s*-?[\d.]+\s*\|){6})", x)
    d = _clean(pd.DataFrame([[a] + re.findall(r"-?[\d.]+", b) for a, b in m]))
    if len(d) < 5: raise ValueError("rows nahi mili")
    return d


def _nse_df():
    f = pd.DataFrame(nse("fiidiiTradeReact")); f["k"] = f.category.str.strip().str.upper().str[:3]
    v = lambda k, c: float(str(f.loc[f.k == k, c].iloc[0]).replace(",", ""))
    return _clean(pd.DataFrame([[f.date.iloc[0]] + [v(k, c) for k in ("FII", "DII") for c in ("buyValue", "sellValue", "netValue")]]))


@st.cache_data(ttl=900)
def flows():
    h = src = n = None
    for name, fn in (("Groww", _groww), ("Tapetide", _tape)):
        try: h, src = fn(), name; break
        except Exception: pass
    try:
        n = _nse_df(); n = n if len(n) else None
    except Exception: pass
    return h, src, n


def streak(s):
    n = 0
    for x in s:
        if x != 0 and (x > 0) == (s.iloc[0] > 0): n += 1
        else: break
    return ("buying" if s.iloc[0] > 0 else "selling"), n


def bias(f5, d5):
    if f5 > 0 and d5 > 0: return "🟢 Dono net buyers: bullish bias, dips par buy"
    if f5 < 0 and d5 < 0: return "🔴 Dono net sellers: bearish bias, naya long avoid"
    if f5 < 0: return "🟡 FII bech rahe, DII absorb kar rahe: market supported par upside capped, selective raho"
    return "🟡 FII khareed rahe, DII profit book kar rahe: FII-led move, trend follow karo, trailing SL rakho"


def show_flows():
    h, src, n = flows()
    if h is None and n is None:
        st.warning("FII/DII data kisi source se nahi mila (NSE, Groww, Tapetide). Refresh dabao ya official page dekho: nseindia.com/reports/fii-dii"); return
    if h is None: h, src = n, "NSE"
    L = h.iloc[0]; d = f"{L.Date:%d %b %Y}"
    if n is not None and h is not n:
        a = n.iloc[0]
        if a.Date == L.Date:
            ok = all(abs(a[k] - L[k]) <= max(5, .01 * abs(a[k])) for k in ("FII Net", "DII Net"))
            st.success(f"✅ NSE (official) aur {src} ka {d} ka data match karta hai") if ok else st.warning(f"⚠️ NSE aur {src} me fark: FII net NSE ₹{a['FII Net']:,.0f} Cr vs {src} ₹{L['FII Net']:,.0f} Cr. NSE ko sahi maano.")
        else:
            st.info(f"NSE latest: {a.Date:%d %b} · {src} latest: {L.Date:%d %b}")
    c = st.columns(2)
    c[0].metric(f"FII/FPI net · {d}", f"₹{L['FII Net']:,.0f} Cr"); c[1].metric(f"DII net · {d}", f"₹{L['DII Net']:,.0f} Cr")
    rows = [{"Period": lb, "FII Net": round(h.head(k)["FII Net"].sum()), "DII Net": round(h.head(k)["DII Net"].sum()),
             "Combined": round(h.head(k)[["FII Net", "DII Net"]].sum().sum())}
            for lb, k in (("1 Day", 1), ("1 Week", 5), ("1 Month", 21), (f"Last {len(h)} sessions", len(h))) if k <= len(h)]
    st.dataframe(pd.DataFrame(rows), hide_index=True)
    (fs, fd), (ds, dd) = streak(h["FII Net"]), streak(h["DII Net"])
    st.info(f"FII {fd} session se net {fs} · DII {dd} session se net {ds}")
    st.success(bias(h.head(5)["FII Net"].sum(), h.head(5)["DII Net"].sum()) + " (5-session flow, rule-based)")
    st.bar_chart(h.head(30).set_index("Date")[["FII Net", "DII Net"]].sort_index())
    st.dataframe(h.head(10).assign(Date=h.head(10).Date.dt.strftime("%d %b")), hide_index=True)
    st.caption(f"Source: {src} · exchange provisional cash data · ₹ Cr · final figures thode alag ho sakte hain")
    try:
        dl = nse("snapshot-capital-market-largedeal")
        for k, lb in (("BULK_DEALS_DATA", "Bulk deals"), ("BLOCK_DEALS_DATA", "Block deals")):
            z = pd.DataFrame(dl.get(k, []))
            if len(z):
                st.markdown(f"**{lb} (big players, stock-wise)**")
                st.dataframe(z[[c for c in ["date", "symbol", "clientName", "buySell", "qty", "watp"] if c in z]], hide_index=True)
    except Exception:
        st.caption("Bulk/block deals NSE se abhi nahi mile (NSE kabhi cloud servers ko block karta hai).")


@st.cache_data(ttl=21600)
def fpi_sector():
    today = date.today(); ends = []
    for i in range(3):
        y, m = divmod(today.year * 12 + today.month - 1 - i, 12); m += 1
        ends += [date(y + (m == 12), m % 12 + 1, 1) - timedelta(days=1), date(y, m, 15)]
    for e in sorted([x for x in ends if x < today], reverse=True)[:4]:
        for tok in dict.fromkeys([e.strftime("%b"), e.strftime("%b").upper(), e.strftime("%B"), e.strftime("%B").upper()]):
            try:
                r = requests.get(f"https://www.fpi.nsdl.co.in/web/StaticReports/Fortnightly_Sector_wise_FII_Investment_Data/FIIInvestSector_{tok}{e.day:02d}{e.year}.html", headers=UA, timeout=6)
            except requests.RequestException:
                return None, [], None
            if r.status_code != 200 or "Sectors" not in r.text: continue
            try:
                t = max(pd.read_html(StringIO(r.text)), key=lambda x: x.shape[1])
                num = t.iloc[:, 2:].apply(lambda c: pd.to_numeric(c.astype(str).str.replace(",", ""), errors="coerce"))
                df = pd.DataFrame({"Sector": t.iloc[:, 1].astype(str), "Prev fortnight": num.iloc[:, 10],
                                   "Latest fortnight": num.iloc[:, 20], "AUC": num.iloc[:, 30]}).dropna()
                pr = list(dict.fromkeys(re.findall(r"Net Investment ([A-Za-z]+ \d{1,2}-\d{1,2}, \d{4})", r.text)))[:2]
                if len(df) > 10: return df, pr, e
            except Exception: pass
    return None, [], None


def show_fpi_sector():
    df, pr, e = fpi_sector()
    if df is None:
        st.caption("NSDL sector-wise FPI report abhi nahi mila. Official: fpi.nsdl.co.in → Statistics → Fortnightly Sector-wise."); return
    df = df[~df.Sector.isin(["Grand Total", "nan"])].copy()
    df["Bias"] = ["Accumulating 🟢" if a > 0 and b > 0 else "Distributing 🔴" if a < 0 and b < 0 else "Mixed ⚪"
                  for a, b in zip(df["Prev fortnight"], df["Latest fortnight"])]
    df = df.sort_values("Latest fortnight", ascending=False)
    st.caption("Equity net flow, ₹ Cr · Latest = " + (pr[-1] if pr else f"fortnight ending {e:%d %b %Y}") + (f" · Prev = {pr[0]}" if len(pr) > 1 else ""))
    st.dataframe(df, hide_index=True); st.bar_chart(df.set_index("Sector")["Latest fortnight"])
    st.success("Sabse zyada inflow: " + ", ".join(df.Sector.head(3)) + " | outflow: " + ", ".join(df.Sector.tail(3)))
    st.caption("NSDL ka official fortnightly data (depository-based) hai: daily NSE FII figures se alag aur 5-10 din late aata hai.")


# ---------- UI ----------
h1, h2 = st.columns([4, 1]); h1.title("📈 Trader Dashboard")
if h2.button("🔄 Refresh"): st.cache_data.clear(); st.rerun()
st.caption("Updated " + datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%d %b, %H:%M IST") + " · Free data me ~15 min delay ho sakta hai")
T = st.tabs(["🏠 Market", "🔍 Search", "🎯 Stocks", "💼 MF", "📰 News"])

with T[0]:
    try:
        x = idx()
        for i in (0, 2):
            for c, k in zip(st.columns(2), list(IX)[i:i + 2]):
                c.metric(IX[k], f"{x[k].iloc[-1]:,.0f}", f"{(x[k].iloc[-1] / x[k].iloc[-2] - 1) * 100:.2f}%")
    except Exception:
        st.warning("Index data nahi mila. Refresh dabao.")
    st.subheader("FII / FPI / DII · cash market")
    show_flows()
    st.subheader("FPI sector-wise flow (NSDL)")
    show_fpi_sector()
    st.caption("Stock-wise daily FII/DII/MF buy-sell public nahi hota; bulk/block deals se bade players ki stock-wise activity dikhti hai. Neeche sector momentum price-based proxy hai.")
    st.subheader("Sector momentum")
    try:
        sd = sectors(); st.dataframe(sd, hide_index=True); st.bar_chart(sd.set_index("Sector")["1M %"])
        st.success("Strong (1M): " + ", ".join(sd.Sector[:3]) + " | Weak: " + ", ".join(sd.Sector[-3:]))
    except Exception:
        st.warning("Sector data nahi mila. Refresh dabao.")

with T[1]:
    kind = st.radio("Type", ["Stock / Index / Sector", "Mutual Fund"], horizontal=True, label_visibility="collapsed")
    q = st.text_input("Search", placeholder="RELIANCE, NIFTY, NIFTY IT, PHARMA, Parag Parikh Flexi Cap", label_visibility="collapsed")
    if q: (show_stock if kind.startswith("Stock") else show_mf)(q)

with T[2]:
    c1, c2 = st.columns(2)
    cat = c1.selectbox("Category", list(UNI)); sty = c2.selectbox("Style", ["Intraday", "Swing", "Positional", "Long-term"])
    res = scan(cat)
    if not res:
        st.warning("Data nahi aaya. Refresh dabao ya thodi der baad try karo.")
    else:
        rows = []
        for z in res:
            p = z["plan"].set_index("Style").loc[sty]; o = z["outlook"].set_index("Horizon")["Bias"]
            rows.append({"Stock": z["Stock"], "Price": round(z["price"], 1), "Signal": z["signal"], "Score": z["score"], "RSI": round(z["rsi"]),
                         "Pattern": z["pattern"], "1W": o["1 Week"], "1M": o["1 Month"], "3M": o["3 Months"], "Side": p["Side"],
                         "Entry": p["Entry"], "SL": p["Stop-loss"], "Target": p["Target"], "Trail": p["Trailing SL"], "Hold": p["Hold"]})
        st.dataframe(pd.DataFrame(rows), hide_index=True)
        st.caption("Score +100 (strong up) se -100 (strong down). Sabse strong upar. Detail ke liye Search tab.")
        for z in res[:3]:
            with st.expander("📰 " + z["Stock"] + " news"): show_news(z["Stock"] + " share NSE", 4)

with T[3]:
    cat = st.selectbox("MF category", list(MFU))
    df = mf_pick(cat)
    if df.empty:
        st.warning("Data nahi mila. Refresh dabao.")
    else:
        st.dataframe(df.sort_values("1Y", ascending=False) if "1Y" in df else df, hide_index=True)
        st.caption(f"Suggested hold: {HOLD[cat]} · SIP best. Past returns future ki guarantee nahi.")
    st.caption("Fund-wise FII/DII buying live public nahi hota; AMCs monthly portfolio disclose karte hain.")
    show_news(cat + " mutual fund India", 4)

with T[4]:
    Q = {"Market": "Sensex Nifty stock market India", "FII/DII": "FII DII flows India stocks", "RBI & Economy": "RBI India economy inflation",
         "Global cues": "Wall Street US Fed crude oil markets", "Results": "India quarterly results earnings stocks"}
    show_news(Q[st.radio("Topic", list(Q), horizontal=True)], 15)

st.caption("⚠️ Signals indicator-based hain (RSI, MACD, SMA, ATR); ye SEBI-registered advice nahi hai aur profit ki guarantee nahi. Apna risk khud manage karo.")
