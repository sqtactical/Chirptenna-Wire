"""Miniaturas SVG de los tipos (para la galería de la web y del escritorio). Python puro; `currentColor` para la tinta."""

from __future__ import annotations

COBRE = "#c8892b"
_CAB = 'viewBox="0 0 120 60" width="120" height="60" role="img" fill="none" stroke-linecap="round" stroke-linejoin="round"'

MINIATURAS = {
    "dipolo": f'''<svg {_CAB}>
<line x1="10" y1="22" x2="53" y2="22" stroke="{COBRE}" stroke-width="3"/><line x1="67" y1="22" x2="110" y2="22" stroke="{COBRE}" stroke-width="3"/>
<rect x="53" y="17" width="14" height="10" rx="2" stroke="currentColor" stroke-width="1.4"/>
<line x1="60" y1="27" x2="60" y2="54" stroke="currentColor" stroke-width="2.6"/></svg>''',
    "jpole": f'''<svg {_CAB}>
<path d="M12 14 H108" stroke="{COBRE}" stroke-width="3"/><path d="M12 14 V34 H62" stroke="{COBRE}" stroke-width="3"/>
<circle cx="24" cy="14" r="1.8" stroke="currentColor" stroke-width="1.2"/><circle cx="24" cy="34" r="1.8" stroke="currentColor" stroke-width="1.2"/>
<line x1="24" y1="36" x2="24" y2="56" stroke="currentColor" stroke-width="2.6"/></svg>''',
    "manga": f'''<svg {_CAB}>
<line x1="8" y1="30" x2="64" y2="30" stroke="currentColor" stroke-width="2.6"/>
<rect x="26" y="24" width="38" height="12" rx="2" stroke="currentColor" stroke-width="1.4"/>
<line x1="64" y1="30" x2="112" y2="30" stroke="{COBRE}" stroke-width="3"/></svg>''',
    "coco": f'''<svg {_CAB}>
<line x1="6" y1="32" x2="16" y2="32" stroke="currentColor" stroke-width="2.4"/>
<rect x="16" y="27" width="20" height="10" rx="1.5" fill="currentColor" fill-opacity=".85" stroke="currentColor"/>
<rect x="38" y="27" width="20" height="10" rx="1.5" fill="currentColor" fill-opacity=".45" stroke="currentColor"/>
<rect x="60" y="27" width="20" height="10" rx="1.5" fill="currentColor" fill-opacity=".85" stroke="currentColor"/>
<rect x="82" y="27" width="20" height="10" rx="1.5" fill="currentColor" fill-opacity=".45" stroke="currentColor"/>
<line x1="102" y1="32" x2="114" y2="32" stroke="{COBRE}" stroke-width="3"/></svg>''',
    "jpole_koch": f'''<svg {_CAB}>
<path d="M12 12 V40 H64" stroke="{COBRE}" stroke-width="3"/>
<path d="M12 12 H50 L56 6 L62 12 L68 6 L74 12 L80 18 L86 12 L92 6 L98 12 L104 6 L110 12" stroke="{COBRE}" stroke-width="3"/>
<circle cx="24" cy="12" r="1.8" stroke="currentColor" stroke-width="1.2"/><circle cx="24" cy="40" r="1.8" stroke="currentColor" stroke-width="1.2"/>
<line x1="24" y1="42" x2="24" y2="57" stroke="currentColor" stroke-width="2.6"/></svg>''',
    "discone": f'''<svg {_CAB}>
<line x1="60" y1="14" x2="60" y2="20" stroke="currentColor" stroke-width="2.4"/>
<path d="M28 14 H92" stroke="{COBRE}" stroke-width="3"/><path d="M34 11 L60 14 L86 11" stroke="{COBRE}" stroke-width="2"/>
<path d="M60 20 L28 52 M60 20 L92 52 M60 20 L44 52 M60 20 L76 52" stroke="{COBRE}" stroke-width="2.4"/>
<path d="M26 52 H94" stroke="currentColor" stroke-width="1" stroke-dasharray="3 3"/></svg>''',
    "gp": f'''<svg {_CAB}>
<line x1="60" y1="8" x2="60" y2="32" stroke="{COBRE}" stroke-width="3"/>
<path d="M60 32 L28 52 M60 32 L92 52 M60 32 L44 54 M60 32 L76 54" stroke="{COBRE}" stroke-width="2.4"/>
<rect x="55" y="31" width="10" height="5" rx="1" stroke="currentColor" stroke-width="1.3"/></svg>''',
    "vinv": f'''<svg {_CAB}>
<path d="M60 10 L18 48 M60 10 L102 48" stroke="{COBRE}" stroke-width="3"/>
<rect x="55" y="7" width="10" height="6" rx="1.5" stroke="currentColor" stroke-width="1.3"/>
<line x1="60" y1="3" x2="60" y2="9" stroke="currentColor" stroke-width="2"/></svg>''',
    "yagi": f'''<svg {_CAB}>
<line x1="12" y1="30" x2="108" y2="30" stroke="currentColor" stroke-width="1.6"/>
<line x1="26" y1="8" x2="26" y2="52" stroke="{COBRE}" stroke-width="3"/>
<line x1="58" y1="14" x2="58" y2="46" stroke="{COBRE}" stroke-width="3"/><line x1="64" y1="14" x2="64" y2="46" stroke="{COBRE}" stroke-width="3"/>
<line x1="94" y1="18" x2="94" y2="42" stroke="{COBRE}" stroke-width="3"/></svg>''',
    "torniquete": f'''<svg {_CAB}>
<line x1="14" y1="30" x2="106" y2="30" stroke="{COBRE}" stroke-width="3"/>
<line x1="60" y1="6" x2="60" y2="54" stroke="{COBRE}" stroke-width="3" opacity=".6"/>
<circle cx="60" cy="30" r="5" stroke="currentColor" stroke-width="1.3" fill="none"/>
<path d="M65 30 Q80 14 90 14" stroke="currentColor" stroke-width="1.2" stroke-dasharray="3 3"/></svg>''',
    "batwing": f'''<svg {_CAB}>
<path d="M54 30 L14 12 M54 30 L14 30 M54 30 L14 48 M14 12 V48" stroke="{COBRE}" stroke-width="2.6"/>
<path d="M66 30 L106 12 M66 30 L106 30 M66 30 L106 48 M106 12 V48" stroke="{COBRE}" stroke-width="2.6"/>
<rect x="54" y="26" width="12" height="8" rx="1.5" stroke="currentColor" stroke-width="1.3"/></svg>''',
    "efhw": f'''<svg {_CAB}>
<line x1="6" y1="52" x2="114" y2="52" stroke="currentColor" stroke-width="1" stroke-dasharray="3 3"/>
<line x1="22" y1="52" x2="22" y2="16" stroke="currentColor" stroke-width="1.6"/><line x1="106" y1="52" x2="106" y2="16" stroke="currentColor" stroke-width="1.6"/>
<line x1="22" y1="20" x2="106" y2="20" stroke="{COBRE}" stroke-width="3"/><line x1="22" y1="20" x2="12" y2="20" stroke="{COBRE}" stroke-width="2"/>
<rect x="16" y="22" width="12" height="8" rx="1.5" stroke="currentColor" stroke-width="1.3"/>
<path d="M22 30 V48" stroke="currentColor" stroke-width="1.4" stroke-dasharray="3 2"/></svg>''',
    "dipolo_hf": f'''<svg {_CAB}>
<line x1="6" y1="54" x2="114" y2="54" stroke="currentColor" stroke-width="1" stroke-dasharray="3 3"/>
<line x1="60" y1="54" x2="60" y2="26" stroke="currentColor" stroke-width="1.6"/>
<line x1="10" y1="22" x2="110" y2="22" stroke="{COBRE}" stroke-width="3"/><rect x="55" y="18" width="10" height="8" rx="1.5" stroke="currentColor" stroke-width="1.3"/></svg>''',
    "vinv_hf": f'''<svg {_CAB}>
<line x1="6" y1="54" x2="114" y2="54" stroke="currentColor" stroke-width="1" stroke-dasharray="3 3"/>
<line x1="60" y1="54" x2="60" y2="10" stroke="currentColor" stroke-width="1.6"/>
<path d="M60 12 L16 40 M60 12 L104 40" stroke="{COBRE}" stroke-width="3"/></svg>''',
    "abanico": f'''<svg {_CAB}>
<line x1="6" y1="54" x2="114" y2="54" stroke="currentColor" stroke-width="1" stroke-dasharray="3 3"/>
<line x1="60" y1="54" x2="60" y2="26" stroke="currentColor" stroke-width="1.6"/>
<line x1="8" y1="18" x2="112" y2="18" stroke="{COBRE}" stroke-width="2.6"/><line x1="26" y1="24" x2="94" y2="24" stroke="{COBRE}" stroke-width="2.6"/>
<line x1="40" y1="30" x2="80" y2="30" stroke="{COBRE}" stroke-width="2.6"/></svg>''',
    "trampas": f'''<svg {_CAB}>
<line x1="6" y1="54" x2="114" y2="54" stroke="currentColor" stroke-width="1" stroke-dasharray="3 3"/>
<line x1="60" y1="54" x2="60" y2="28" stroke="currentColor" stroke-width="1.6"/>
<line x1="10" y1="22" x2="110" y2="22" stroke="{COBRE}" stroke-width="3"/>
<rect x="30" y="17" width="8" height="10" rx="1.5" stroke="currentColor" stroke-width="1.4" fill="none"/><rect x="82" y="17" width="8" height="10" rx="1.5" stroke="currentColor" stroke-width="1.4" fill="none"/></svg>''',
    "g5rv": f'''<svg {_CAB}>
<line x1="6" y1="54" x2="114" y2="54" stroke="currentColor" stroke-width="1" stroke-dasharray="3 3"/>
<line x1="8" y1="14" x2="112" y2="14" stroke="{COBRE}" stroke-width="3"/>
<path d="M59 15 V46 M61 15 V46" stroke="{COBRE}" stroke-width="1.4"/><rect x="54" y="46" width="12" height="6" rx="1.5" stroke="currentColor" stroke-width="1.3" fill="none"/></svg>''',
    "biconica": f'''<svg {_CAB}>
<path d="M60 30 L36 6 M60 30 L84 6 M60 30 L48 6 M60 30 L72 6" stroke="{COBRE}" stroke-width="2.4"/>
<path d="M60 30 L36 54 M60 30 L84 54 M60 30 L48 54 M60 30 L72 54" stroke="{COBRE}" stroke-width="2.4"/>
<circle cx="60" cy="30" r="2.2" stroke="currentColor" stroke-width="1.3"/></svg>''',
}
