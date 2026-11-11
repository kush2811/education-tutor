import React from 'react';

interface ConceptDiagramProps {
  type: string;
}

export const ConceptDiagram: React.FC<ConceptDiagramProps> = ({ type }) => {
  const key = type.trim().toLowerCase();

  if (key === 'right_triangle') {
    return (
      <div className="my-3 max-w-sm rounded-2xl border border-slate-200 bg-white p-4 shadow-xs">
        <svg viewBox="0 0 320 210" className="w-full h-auto" role="img" aria-label="Right-angled triangle showing a, b, and hypotenuse c">
          <polygon
            points="60,35 60,155 255,155"
            fill="#f0fdf4"
            stroke="#059669"
            strokeWidth="2.5"
            strokeLinejoin="round"
          />
          {/* Right angle marker */}
          <polyline
            points="60,137 78,137 78,155"
            fill="none"
            stroke="#0f172a"
            strokeWidth="1.75"
          />
          <text x="84" y="149" fontSize="11" fill="#475569" fontWeight="600">
            90°
          </text>

          {/* Side labels */}
          <text x="36" y="100" fontSize="16" fill="#0f172a" fontWeight="700">
            a
          </text>
          <text x="152" y="177" fontSize="16" fill="#0f172a" fontWeight="700">
            b
          </text>
          <text x="165" y="84" fontSize="16" fill="#0369a1" fontWeight="700">
            c
          </text>
          <line x1="180" y1="79" x2="225" y2="79" stroke="#94a3b8" strokeWidth="1.2" strokeDasharray="3,2" />
          <text x="230" y="83" fontSize="11" fill="#475569" fontWeight="500">
            hypotenuse
          </text>

          {/* Vertex labels */}
          <text x="48" y="28" fontSize="11" fill="#64748b">A</text>
          <text x="260" y="160" fontSize="11" fill="#64748b">B</text>
          <text x="46" y="166" fontSize="11" fill="#64748b">C</text>
        </svg>
        <div className="mt-2 pt-2 border-t border-slate-100 text-center">
          <div className="text-sm font-bold text-emerald-700">a² + b² = c²</div>
          <div className="text-[11px] text-slate-500">
            a, b = legs &bull; c = hypotenuse (longest side, opposite 90°)
          </div>
        </div>
      </div>
    );
  }

  if (key === 'quadratic_parabola') {
    return (
      <div className="my-3 max-w-sm rounded-2xl border border-slate-200 bg-white p-4 shadow-xs">
        <svg viewBox="0 0 320 200" className="w-full h-auto" role="img" aria-label="Parabola graph showing roots on x-axis">
          {/* Axes */}
          <line x1="25" y1="135" x2="295" y2="135" stroke="#94a3b8" strokeWidth="1.5" />
          <line x1="160" y1="20" x2="160" y2="185" stroke="#94a3b8" strokeWidth="1.5" />
          <text x="285" y="128" fontSize="11" fill="#64748b">x</text>
          <text x="167" y="28" fontSize="11" fill="#64748b">y</text>

          {/* Parabola curve crossing x=100 and x=220 */}
          <path
            d="M 70 30 Q 160 225 250 30"
            fill="none"
            stroke="#0284c7"
            strokeWidth="2.5"
          />

          {/* Roots */}
          <circle cx="110" cy="135" r="4.5" fill="#e11d48" />
          <circle cx="210" cy="135" r="4.5" fill="#e11d48" />
          <text x="92" y="153" fontSize="11" fill="#e11d48" fontWeight="600">root 1</text>
          <text x="194" y="153" fontSize="11" fill="#e11d48" fontWeight="600">root 2</text>

          {/* Vertex */}
          <circle cx="160" cy="127" r="3.5" fill="#059669" />
          <text x="166" y="123" fontSize="10" fill="#059669">vertex</text>
        </svg>
        <div className="mt-2 pt-2 border-t border-slate-100 text-center text-[11px] text-slate-500">
          Roots are the x-intercepts where y = ax² + bx + c = 0
        </div>
      </div>
    );
  }

  if (key === 'conditional_probability_venn') {
    return (
      <div className="my-3 max-w-sm rounded-2xl border border-slate-200 bg-white p-4 shadow-xs">
        <svg viewBox="0 0 320 180" className="w-full h-auto" role="img" aria-label="Venn diagram of conditional probability P(A|B)">
          <rect x="15" y="15" width="290" height="150" rx="12" fill="#f8fafc" stroke="#cbd5e1" strokeWidth="1.5" />
          <text x="26" y="34" fontSize="11" fill="#64748b" fontWeight="600">Sample Space S</text>

          {/* Event A */}
          <circle cx="130" cy="95" r="48" fill="#bae6fd" fillOpacity="0.5" stroke="#0284c7" strokeWidth="2" />
          {/* Event B */}
          <circle cx="190" cy="95" r="48" fill="#a7f3d0" fillOpacity="0.55" stroke="#059669" strokeWidth="2" />

          <text x="96" y="99" fontSize="14" fill="#0369a1" fontWeight="700">A</text>
          <text x="215" y="99" fontSize="14" fill="#047857" fontWeight="700">B</text>
          <text x="148" y="99" fontSize="12" fill="#0f172a" fontWeight="700">A &cap; B</text>
        </svg>
        <div className="mt-2 pt-2 border-t border-slate-100 text-center text-[11px] text-slate-500">
          Knowing B occurred shrinks the space to circle B; P(A|B) is the fraction inside A &cap; B
        </div>
      </div>
    );
  }

  if (key === 'force_acceleration') {
    return (
      <div className="my-3 max-w-sm rounded-2xl border border-slate-200 bg-white p-4 shadow-xs">
        <svg viewBox="0 0 320 150" className="w-full h-auto" role="img" aria-label="Force acting on mass m producing acceleration a">
          <line x1="20" y1="115" x2="300" y2="115" stroke="#94a3b8" strokeWidth="2" />
          <rect x="115" y="55" width="70" height="60" rx="6" fill="#e0f2fe" stroke="#0284c7" strokeWidth="2" />
          <text x="144" y="90" fontSize="16" fill="#0369a1" fontWeight="700">m</text>

          {/* Force Arrow */}
          <line x1="40" y1="85" x2="108" y2="85" stroke="#e11d48" strokeWidth="3" />
          <polygon points="113,85 103,79 103,91" fill="#e11d48" />
          <text x="60" y="75" fontSize="13" fill="#e11d48" fontWeight="700">Force F</text>

          {/* Acceleration Arrow */}
          <line x1="200" y1="85" x2="275" y2="85" stroke="#059669" strokeWidth="2.5" strokeDasharray="5,3" />
          <polygon points="282,85 272,79 272,91" fill="#059669" />
          <text x="215" y="75" fontSize="12" fill="#059669" fontWeight="700">a = F / m</text>
        </svg>
      </div>
    );
  }

  if (key === 'ohms_law_circuit') {
    return (
      <div className="my-3 max-w-sm rounded-2xl border border-slate-200 bg-white p-4 shadow-xs">
        <svg viewBox="0 0 320 160" className="w-full h-auto" role="img" aria-label="Simple circuit with voltage V, current I, and resistor R">
          {/* Circuit Loop */}
          <rect x="65" y="35" width="190" height="90" rx="6" fill="none" stroke="#334155" strokeWidth="2" />
          {/* Voltage Source */}
          <rect x="52" y="65" width="26" height="30" fill="#ffffff" />
          <line x1="55" y1="74" x2="75" y2="74" stroke="#0284c7" strokeWidth="3" />
          <line x1="60" y1="85" x2="70" y2="85" stroke="#0284c7" strokeWidth="2" />
          <text x="28" y="84" fontSize="13" fill="#0284c7" fontWeight="700">V</text>

          {/* Resistor */}
          <rect x="242" y="60" width="26" height="40" fill="#ffffff" />
          <polyline
            points="255,60 263,66 247,73 263,80 247,87 263,94 255,100"
            fill="none"
            stroke="#e11d48"
            strokeWidth="2.2"
          />
          <text x="272" y="84" fontSize="13" fill="#e11d48" fontWeight="700">R</text>

          {/* Current Arrow */}
          <line x1="125" y1="35" x2="185" y2="35" stroke="#059669" strokeWidth="2.5" />
          <polygon points="192,35 182,30 182,40" fill="#059669" />
          <text x="148" y="25" fontSize="12" fill="#059669" fontWeight="700">I = V / R</text>
        </svg>
      </div>
    );
  }

  return null;
};
