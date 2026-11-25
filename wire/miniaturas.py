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
}
