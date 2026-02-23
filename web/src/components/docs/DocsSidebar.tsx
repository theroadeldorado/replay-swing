'use client';

import { useEffect, useState } from 'react';
import type { DocSection } from '@/data/docs';

export default function DocsSidebar({ sections }: { sections: DocSection[] }) {
  const [activeId, setActiveId] = useState<string>(sections[0]?.id ?? '');

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            setActiveId(entry.target.id);
          }
        }
      },
      { rootMargin: '-80px 0px -60% 0px', threshold: 0 }
    );

    for (const section of sections) {
      const el = document.getElementById(section.id);
      if (el) observer.observe(el);
    }

    return () => observer.disconnect();
  }, [sections]);

  return (
    <nav className="sticky top-24 max-h-[calc(100vh-8rem)] overflow-y-auto pr-4 -mr-4">
      <p className="text-xs font-semibold text-bronze/60 uppercase tracking-wider mb-3">
        On this page
      </p>
      <ul className="space-y-1">
        {sections.map((section) => (
          <li key={section.id}>
            <a
              href={`#${section.id}`}
              className={`block text-sm py-1.5 px-3 rounded-lg transition-colors ${
                activeId === section.id
                  ? 'bg-cream text-espresso font-medium border border-sand/60'
                  : 'text-bronze hover:text-espresso hover:bg-cream/50'
              }`}
            >
              {section.title}
            </a>
          </li>
        ))}
      </ul>
    </nav>
  );
}
