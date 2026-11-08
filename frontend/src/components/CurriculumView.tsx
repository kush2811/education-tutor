import React from 'react';
import { BookOpen, ExternalLink, ShieldCheck } from 'lucide-react';

export const CurriculumView: React.FC = () => {
  const materials = [
    {
      id: 'ncert_m10',
      title: 'NCERT Class 10 Mathematics',
      author: 'National Council of Educational Research and Training (NCERT)',
      subject: 'Mathematics',
      license: 'Educational Fair Dealing / Public Education Portal',
      topics: ['Real Numbers', 'Polynomials', 'Quadratic Equations', 'Coordinate Geometry', 'Trigonometry'],
      link: 'https://ncert.nic.in/textbook.php'
    },
    {
      id: 'ncert_p11',
      title: 'NCERT Class 11 Physics (Part I & II)',
      author: 'NCERT',
      subject: 'Physics',
      license: 'Educational Fair Dealing / Public Education Portal',
      topics: ['Kinematics', 'Laws of Motion', 'Work, Energy & Power', 'Gravitation', 'Thermodynamics'],
      link: 'https://ncert.nic.in/textbook.php'
    },
    {
      id: 'openstax_calc1',
      title: 'OpenStax Calculus Volume 1',
      author: 'Rice University / OpenStax',
      subject: 'Calculus',
      license: 'Creative Commons Attribution 4.0 International (CC BY 4.0)',
      topics: ['Functions and Graphs', 'Limits', 'Derivatives', 'Applications of Derivatives', 'Integration'],
      link: 'https://openstax.org/details/books/calculus-volume-1'
    },
    {
      id: 'openstax_phys1',
      title: 'OpenStax University Physics Volume 1',
      author: 'Rice University / OpenStax',
      subject: 'Physics',
      license: 'Creative Commons Attribution 4.0 International (CC BY 4.0)',
      topics: ['Vectors', 'Motion along a Straight Line', 'Newtonian Mechanics', 'Conservation of Momentum'],
      link: 'https://openstax.org/details/books/university-physics-volume-1'
    }
  ];

  return (
    <div className="flex-1 overflow-y-auto p-8 bg-slate-50">
      <div className="max-w-5xl mx-auto space-y-6">
        <div>
          <h2 className="text-xl font-bold text-slate-900 flex items-center gap-2">
            <BookOpen className="w-5 h-5 text-sky-600" />
            Verified Educational Curriculum & Open Resources
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            All AI tutor knowledge retrieval and factual grounding in this platform strictly reference verified Open Educational Resources (OER) and official public curriculum textbooks under fair dealing.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {materials.map((item) => (
            <div
              key={item.id}
              className="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-sm flex flex-col justify-between hover:border-sky-300 transition-colors"
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[11px] font-bold px-2 py-0.5 rounded-md bg-sky-50 text-sky-700">
                    {item.subject}
                  </span>
                  <div className="flex items-center gap-1 text-[11px] text-emerald-600 font-medium">
                    <ShieldCheck className="w-3.5 h-3.5" />
                    <span>Verified OER</span>
                  </div>
                </div>

                <h3 className="font-bold text-base text-slate-800 leading-snug">{item.title}</h3>
                <p className="text-xs text-slate-400 mt-0.5">{item.author}</p>

                <div className="mt-4">
                  <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
                    Core Topics Covered
                  </span>
                  <div className="flex flex-wrap gap-1.5 mt-1.5">
                    {item.topics.map((t, idx) => (
                      <span
                        key={idx}
                        className="text-[11px] px-2 py-0.5 rounded-md bg-slate-100 text-slate-700"
                      >
                        {t}
                      </span>
                    ))}
                  </div>
                </div>
              </div>

              <div className="mt-5 pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
                <span className="text-[10px] text-slate-400 truncate max-w-[200px]" title={item.license}>
                  {item.license}
                </span>
                <a
                  href={item.link}
                  target="_blank"
                  rel="noreferrer"
                  className="flex items-center gap-1 text-sky-600 hover:text-sky-700 font-semibold"
                >
                  <span>Official Portal</span>
                  <ExternalLink className="w-3 h-3" />
                </a>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
