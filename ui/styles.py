# ! Layout for the calculator card and the history panel.

from __future__ import annotations

import streamlit as st

LIGHT = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@500;600;700;800&family=JetBrains+Mono:wght@500;600&display=swap');
:root{
--page:#eef2f8;--card:#ffffff;--ink:#121722;--muted:#8b95a8;--faint:#a0a8b8;
--key:#ffffff;--key-2:#f4f6fb;--key-text:#1c2230;--fn:#5c6578;
--op-bg:#eef1fb;--op-bg-2:#e4e9f8;--op-text:#4f46e5;
--ac-bg:#fff1f3;--ac-bg-2:#fde4e8;--ac-text:#f04b5d;
--eq1:#5b6ef5;--eq2:#22d3ee;
--chip:#b7becc;--chip-on:#6d5efc;--chip-on-bg:#ece8ff;
--screen1:#fbfcff;--screen2:#eef1fb;--screen-line:#e6ebf4;
--border:#e6ebf3;--line:#e8edf4;
--shadow:0 18px 50px rgba(40,60,110,.10);
--key-shadow:inset 0 1px 0 rgba(255,255,255,.9),0 1px 1px rgba(28,40,80,.04),0 8px 16px rgba(28,40,80,.06);
--tab:#f3f5f9;--tab-ink:#98a0b3;--tab-on:#ffffff;--tab-on-ink:#2c3344;
--angle:#eef1f6;
--accent:#4f46e5;--accent2:#06b6d4;--danger:#ff6b81;
--font:'Inter',system-ui,sans-serif;
--mono:'JetBrains Mono',ui-monospace,monospace;
}
html,body{background:var(--page)!important}
.stApp{
background:
radial-gradient(900px 420px at 12% -8%,rgba(79,70,229,.16),transparent 60%),
radial-gradient(700px 380px at 96% 0%,rgba(34,211,238,.18),transparent 55%),
var(--page)!important;
font-family:var(--font);color:var(--ink);-webkit-font-smoothing:antialiased}
header[data-testid="stHeader"],[data-testid="stToolbar"],[data-testid="stDecoration"],
[data-testid="stStatusWidget"],[data-testid="stSidebar"],[data-testid="stSidebarCollapsedControl"],
#MainMenu,footer,.stDeployButton{display:none!important}
[data-stale="true"]{opacity:1!important}
.stMainBlockContainer,.block-container{max-width:780px!important;padding:28px 16px 36px!important}
.stMainBlockContainer>div[data-testid="stVerticalBlock"],.block-container>div[data-testid="stVerticalBlock"]{gap:0!important}
.st-key-kb_listener,.st-key-kb_listener iframe{position:absolute!important;width:0!important;height:0!important;overflow:hidden!important;border:0!important;opacity:0;pointer-events:none}
.st-key-shell{gap:0!important}
.st-key-workspace{display:grid!important;grid-template-columns:minmax(0,420px) minmax(180px,280px);gap:16px!important;
align-items:stretch;justify-content:center;flex-direction:unset!important}
.st-key-calc,.st-key-history{background:var(--card);border:1px solid var(--border);border-radius:28px;
box-shadow:var(--shadow);min-width:0}
.st-key-calc{padding:16px 14px 14px;gap:0!important}
.st-key-history{padding:18px 16px 16px;gap:0!important}
.st-key-calc [data-testid="stMarkdownContainer"],.st-key-history [data-testid="stMarkdownContainer"]{font-family:var(--font)}
.st-key-topbar{display:grid!important;grid-template-columns:minmax(0,1fr) auto auto;align-items:center;gap:8px!important;
margin-bottom:12px;flex-direction:unset!important}
.px-brand{display:flex;align-items:center;gap:10px;min-width:0}
.px-logo{width:36px;height:36px;flex:0 0 auto;display:flex;align-items:center;justify-content:center;border-radius:12px;
background:linear-gradient(135deg,#4f46e5,#22d3ee);color:#fff;font-weight:800;font-size:1.15rem;
box-shadow:0 6px 14px rgba(79,70,229,.28)}
.px-name{font-size:.98rem;font-weight:800;letter-spacing:-.03em;line-height:1.05}
.px-tag{margin-top:1px;font-size:.66rem;font-weight:600;color:var(--muted);white-space:nowrap}
.st-key-angles{display:flex!important;flex-direction:row!important;align-items:center;gap:0!important;padding:3px;background:var(--angle);border-radius:999px}
.st-key-angles>div,.st-key-theme__on,.st-key-theme__off{width:auto!important}
.px-screen{display:flex;flex-direction:column;min-height:188px;margin-bottom:16px;padding:12px 16px 14px;border-radius:22px;
background:linear-gradient(180deg,var(--screen1),var(--screen2));border:1px solid var(--screen-line)}
.px-chips{display:flex;justify-content:flex-end;gap:10px}
.px-chip{font-size:.68rem;font-weight:700;letter-spacing:.04em;color:var(--chip)}
.px-chip.on{color:var(--chip-on)}
.px-readout{margin-top:auto;text-align:right}
.px-math{min-height:72px;display:flex;align-items:center;justify-content:flex-end;overflow-x:auto;
font-size:28px;line-height:1.25;color:var(--ink);padding:6px 0 2px}
.px-math.err,.px-value.err{color:var(--danger)}
.m-row{display:inline-flex;align-items:center;justify-content:center}
.m-var{font-style:italic;font-family:Georgia,'Times New Roman',serif;padding:0 .02em}
.m-frac{display:inline-flex;flex-direction:column;align-items:stretch;margin:0 .12em;line-height:1.15;font-size:.92em}
.m-num,.m-den,.m-dtop,.m-dbot,.m-limtop,.m-limbot,.m-hi,.m-lo{display:flex;justify-content:center;padding:0 .32em}
.m-bar{height:0;border-top:1.7px solid currentColor;margin:.06em 0}
.m-pow{display:inline-flex;align-items:flex-start}
.m-exp,.m-dord{font-size:.62em;line-height:1}
.m-exp{transform:translateY(-.38em)}
.m-dord{transform:translateY(-.12em)}
.m-root{display:inline-grid;grid-template-columns:auto auto;grid-template-rows:auto auto;align-items:end;margin:0 .06em}
.m-deg{grid-column:1;grid-row:1;font-size:.68em;line-height:1;justify-self:end;align-self:end;transform:translate(.05em,.15em)}
.m-surd{grid-column:1;grid-row:2;font-size:1.45em;line-height:.8;align-self:center;padding-right:.04em}
.m-rad{grid-column:2;grid-row:2;padding:0;display:flex;align-items:center}
.m-fn,.m-group,.m-diff,.m-int,.m-limblk,.m-sumblk{display:inline-flex;align-items:center}
.m-fname{font-style:normal;margin-right:.04em}
.m-paren{padding:0 .02em}
.m-dfrac,.m-icol,.m-scol,.m-limcol{display:inline-flex;flex-direction:column;align-items:center;margin-right:.12em}
.m-dfrac{font-size:.78em;align-items:stretch}
.m-d{font-style:italic;font-family:Georgia,'Times New Roman',serif}
.m-isym{font-size:1.65em;line-height:.72}
.m-sigma{font-size:1.4em;line-height:.75}
.m-limword{font-style:italic;font-family:Georgia,'Times New Roman',serif;font-size:.78em;font-weight:650;line-height:1}
.m-limto,.m-dx,.m-hi,.m-lo,.m-limtop,.m-limbot{font-size:.62em}
.m-dx{font-style:italic;margin-left:.12em;font-size:.78em}
.m-caret{display:inline-block;width:2px;height:1.05em;margin:0 1px;border-radius:1px;background:currentColor;align-self:center;flex:0 0 auto;animation:px-blink 1.05s steps(1) infinite}
.m-box{display:inline-flex;align-items:center;justify-content:center;min-width:1.25em;min-height:1.32em;
padding:.08em .34em;margin:.05em .07em;border:1.5px dashed rgba(71,84,110,.8);border-radius:4px;
background:#fff;color:#1c2230;box-sizing:border-box;cursor:text;white-space:nowrap;vertical-align:middle}
.m-box.m-live{border-color:#4338ca;background:#fff}
.m-box .m-caret{background:#1c2230}
.m-box .m-op{color:#4f46e5}
.px-math.err .m-box{color:var(--danger)}
.px-math.err .m-box .m-caret{background:var(--danger)}
.m-sub{display:inline-flex;align-items:flex-end}
.m-idx{font-size:.62em;line-height:1;transform:translateY(.28em)}
.px-math .m-row,.px-math .m-atom{cursor:text}
.m-op{margin:0 .08em;color:var(--accent);font-weight:650}
.px-value{display:flex;align-items:center;justify-content:flex-end;flex-wrap:wrap;margin-top:2px;font-family:var(--font);
font-size:48px;font-weight:750;letter-spacing:-.04em;line-height:1.05;font-variant-numeric:tabular-nums;color:var(--ink)}
.px-value.sm{font-size:32px}.px-value.xs{font-size:22px}.px-value.xxs{font-size:16px;line-height:1.3;text-align:right}
@keyframes px-blink{50%{opacity:0}}
.st-key-tabrow{display:flex!important;flex-direction:row!important;align-items:center;justify-content:space-between;gap:10px!important;margin:14px 0 12px}
.st-key-tabrow>div{width:auto!important;flex:0 0 auto!important}
.st-key-shifts{display:flex!important;flex-direction:row!important;align-items:center;gap:6px!important}
.st-key-shifts>div{width:auto!important;flex:0 0 auto!important}
.st-key-tabs{display:flex!important;flex-direction:row!important;align-items:center;gap:2px!important;padding:3px;background:var(--tab);border-radius:999px}
.st-key-tabs>div{width:auto!important}
.st-key-angles button,.st-key-tabs button,.st-key-theme__on button,.st-key-theme__off button,
[class*="st-key-mode_2nd"] button,[class*="st-key-mode_hyp"] button,[class*="st-key-hist__"] button{
min-height:28px;padding:4px 7px!important;border:0!important;border-radius:999px!important;box-shadow:none!important;
background:transparent!important;color:var(--tab-ink)!important;font-family:var(--font)!important;font-size:.72rem!important;font-weight:700!important}
.st-key-tabs button{padding:4px 6px!important;font-size:.64rem!important}
.st-key-angles [class*="__on"] button,.st-key-tabs [class*="__on"] button{background:var(--tab-on)!important;color:var(--tab-on-ink)!important;
box-shadow:0 1px 3px rgba(20,30,60,.12)!important}
.st-key-theme__on button,.st-key-theme__off button{width:34px!important;height:34px!important;min-height:34px;padding:0!important;
background:#fff!important;border:1px solid var(--border)!important;color:#667085!important;font-size:1rem!important}
[class*="st-key-mode_2nd__on"] button,[class*="st-key-mode_hyp__on"] button,[class*="st-key-hist__on"] button{background:#6d5efc!important;color:#fff!important}
[class*="st-key-mode_2nd__off"] button,[class*="st-key-mode_hyp__off"] button{background:#fff!important;border:1px solid var(--border)!important;color:#98a2b4!important}
.st-key-funcs,.st-key-funcs3,.st-key-mem,.st-key-pad{display:grid!important;flex-direction:unset!important;gap:8px!important}
.st-key-funcs{grid-template-columns:repeat(6,minmax(0,1fr));margin-bottom:8px}
.st-key-mem{grid-template-columns:repeat(6,minmax(0,1fr));margin-bottom:8px}
.st-key-funcs3{grid-template-columns:repeat(3,minmax(0,1fr));margin-bottom:8px}
.st-key-pad{grid-template-columns:repeat(4,minmax(0,1fr));padding-top:10px;border-top:1px solid var(--line)}
.st-key-funcs>div,.st-key-funcs3>div,.st-key-mem>div,.st-key-pad>div{min-width:0;width:auto!important}
.st-key-funcs button,.st-key-funcs3 button,.st-key-mem button,.st-key-pad button{
width:100%!important;min-height:46px;padding:6px 2px!important;display:flex!important;align-items:center;justify-content:center;
font-family:var(--font)!important;font-weight:650!important;line-height:1!important;color:var(--key-text)!important;
background:linear-gradient(180deg,var(--key),var(--key-2))!important;border:1px solid rgba(255,255,255,.6)!important;
border-radius:14px!important;box-shadow:var(--key-shadow)!important;cursor:pointer;user-select:none;
transition:transform .12s ease,box-shadow .12s ease}
.st-key-funcs button p,.st-key-funcs3 button p,.st-key-mem button p,.st-key-pad button p,
.st-key-funcs button div,.st-key-funcs3 button div,.st-key-mem button div,.st-key-pad button div{margin:0!important;font:inherit!important;color:inherit!important}
.st-key-funcs button,.st-key-funcs3 button,.st-key-mem button{min-height:40px;font-size:.78rem!important;font-weight:600!important;color:var(--fn)!important}
.st-key-pad button{min-height:58px;font-size:1.35rem!important;border-radius:16px!important}
.st-key-funcs button:hover,.st-key-funcs3 button:hover,.st-key-mem button:hover,.st-key-pad button:hover{transform:translateY(-1px)}
.st-key-funcs button:active,.st-key-funcs3 button:active,.st-key-mem button:active,.st-key-pad button:active{transform:scale(.95)}
.st-key-funcs button:focus,.st-key-funcs3 button:focus,.st-key-pad button:focus,.st-key-angles button:focus,.st-key-tabs button:focus,
.st-key-theme__on button:focus,.st-key-theme__off button:focus,[class*="st-key-mode_2nd"] button:focus,[class*="st-key-mode_hyp"] button:focus,
.st-key-hist_clear button:focus{outline:none!important}
.st-key-funcs button:focus-visible,.st-key-funcs3 button:focus-visible,.st-key-pad button:focus-visible,.st-key-angles button:focus-visible,
.st-key-tabs button:focus-visible,[class*="st-key-mode_2nd"] button:focus-visible,[class*="st-key-mode_hyp"] button:focus-visible{
outline:2px solid var(--accent)!important;outline-offset:2px}
[class*="st-key-op_"] button,[class*="st-key-paren_"] button{background:linear-gradient(180deg,var(--op-bg),var(--op-bg-2))!important;color:var(--op-text)!important}
[class*="st-key-clr_"] button{background:linear-gradient(180deg,var(--ac-bg),var(--ac-bg-2))!important;color:var(--ac-text)!important;font-size:1.05rem!important;font-weight:800!important}
[class*="st-key-eq_"] button{background:linear-gradient(180deg,var(--eq1),var(--eq2))!important;color:#fff!important;border:0!important;
box-shadow:0 10px 18px rgba(79,70,229,.32)!important;font-size:1.5rem!important}
[class*="st-key-del_"] button{font-family:"Segoe UI Symbol","Segoe UI",sans-serif!important;font-size:1.15rem!important;color:#8b93a7!important}
.st-key-histhead{display:grid!important;grid-template-columns:1fr auto;align-items:center;margin-bottom:12px;flex-direction:unset!important}
.st-key-histtools{display:flex!important;flex-direction:row!important;align-items:center;gap:4px!important;width:auto!important}
.st-key-histtools>div{width:auto!important}
.px-htitle{font-size:.74rem;font-weight:800;letter-spacing:.08em;color:var(--muted)}
.st-key-hist_clear button,.st-key-copy_result button{min-height:32px;padding:0 6px!important;background:transparent!important;border:0!important;box-shadow:none!important;
color:var(--accent)!important;font-family:var(--font)!important;font-size:.92rem!important;font-weight:700!important}
.px-empty{padding:36px 8px;text-align:center;color:var(--muted);font-weight:600}
.st-key-hlist{display:flex!important;flex-direction:column!important;gap:8px!important}
.st-key-hlist>div{width:100%!important}
.st-key-hlist button{
width:100%!important;height:auto!important;min-height:48px;padding:10px 14px!important;
display:flex!important;align-items:center;justify-content:flex-end;
background:var(--card)!important;border:1px solid var(--border)!important;border-radius:16px!important;
box-shadow:none!important;color:var(--ink)!important;cursor:pointer}
.st-key-hlist button:hover{border-color:#c9d2e4!important;transform:none}
.st-key-hlist button p{margin:0!important;width:100%;text-align:right!important;
font-family:var(--mono)!important;font-size:.92rem!important;font-weight:600!important;
line-height:1.35!important;color:var(--ink)!important}
.px-foot{margin-top:18px;text-align:center}
.px-keys{font-size:.78rem;font-weight:600;color:var(--muted)}
.px-credit{margin-top:4px;font-size:.84rem;font-weight:700;color:var(--fn)}
@media (max-width:640px){
.st-key-workspace{grid-template-columns:minmax(0,420px)!important}
.st-key-history{display:none!important}
.stMainBlockContainer,.block-container{padding:16px 10px 24px!important}
}
@media (max-width:420px){
.px-value{font-size:40px}
.st-key-pad button{min-height:52px;font-size:1.2rem!important}
.st-key-tabs button{padding:4px 7px!important}
}
@media (prefers-reduced-motion:reduce){
*,*::before,*::after{animation:none!important;transition:none!important}
.st-key-funcs button:hover,.st-key-funcs3 button:hover,.st-key-mem button:hover,.st-key-pad button:hover,.st-key-funcs button:active,.st-key-funcs3 button:active,.st-key-mem button:active,.st-key-pad button:active{transform:none}
}
"""

DARK = """
:root{
--page:#07090f;--card:rgba(16,20,30,.78);--ink:#eef1f8;--muted:#8590a6;--faint:#8590a6;
--key:#161b27;--key-2:#121722;--key-text:#eef1f8;--fn:#c5cbe0;
--op-bg:#23283f;--op-bg-2:#1c2236;--op-text:#a5b4fc;
--ac-bg:#3a2430;--ac-bg-2:#2c1b24;--ac-text:#ff6b81;
--eq1:#7c83ff;--eq2:#22d3ee;
--chip:#8590a6;--chip-on:#c4baff;--chip-on-bg:transparent;
--screen1:#121826;--screen2:#0d121c;--screen-line:#232b3b;
--border:#232b3b;--line:#232b3b;
--shadow:0 18px 50px rgba(0,0,0,.35);
--key-shadow:inset 0 1px 0 rgba(255,255,255,.06),0 8px 16px rgba(0,0,0,.25);
--tab:#121722;--tab-ink:#8590a6;--tab-on:#232b3b;--tab-on-ink:#eef1f8;
--angle:#121722;
--accent:#7c83ff;--accent2:#22d3ee;--danger:#ff6b81}
.st-key-calc,.st-key-history{backdrop-filter:blur(18px)}
.st-key-theme__on button,.st-key-theme__off button,[class*="st-key-mode_2nd__off"] button,[class*="st-key-mode_hyp__off"] button{
background:var(--key)!important;border-color:var(--border)!important;color:var(--ink)!important}
.st-key-hlist button{background:rgba(22,27,39,.72)!important}
"""

_HISTORY_OPEN = "@media (max-width:640px){.st-key-history{display:flex!important}}"


# ! Inject the theme. A second rule shows History under the keypad on a phone.
def inject_css(theme: str, history_open: bool) -> None:
    css = LIGHT + (DARK if theme == "dark" else "")
    if history_open:
        css += _HISTORY_OPEN
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
