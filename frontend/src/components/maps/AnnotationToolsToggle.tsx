import { useEffect } from 'react';
import { FaDrawPolygon } from 'react-icons/fa6';

import { useAnnotationContext } from './contexts/AnnotationContext';
import { useMapContext } from './MapContext';

export default function AnnotationToolsToggle() {
  const { activeDataProduct } = useMapContext();
  const { active, toggle, deactivate } = useAnnotationContext();

  // Auto-deactivate annotation mode when activeDataProduct clears
  useEffect(() => {
    if (!activeDataProduct && active) {
      deactivate();
    }
  }, [activeDataProduct, active, deactivate]);

  // Only render when a data product is active
  if (!activeDataProduct) return null;

  return (
    <div className="absolute bottom-[5.75rem] right-2 m-2.5 z-10">
      <button
        type="button"
        className={`h-12 w-12 rounded-md shadow-md flex items-center justify-center focus:outline-hidden focus:ring-2 focus:ring-accent2 transition-colors ${
          active
            ? 'bg-accent2 text-white'
            : 'bg-white text-slate-600 hover:text-slate-800 hover:bg-slate-50'
        }`}
        aria-label={active ? 'Exit annotation mode' : 'Enter annotation mode'}
        aria-pressed={active}
        title="Annotation Tools"
        onClick={toggle}
      >
        <FaDrawPolygon className="h-5 w-5" />
      </button>
    </div>
  );
}