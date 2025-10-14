import '@watergis/maplibre-gl-terradraw/dist/maplibre-gl-terradraw.css';
import { useEffect, useRef } from 'react';
import { useMap } from 'react-map-gl/maplibre';
import { MaplibreTerradrawControl } from '@watergis/maplibre-gl-terradraw';

import { useAnnotationContext } from './contexts/AnnotationContext';

export default function DrawControl() {
  const { current: map } = useMap();
  const { active } = useAnnotationContext();
  const drawRef = useRef<any | null>(null);

  // 1) Create TerraDraw instance once
  useEffect(() => {
    if (!map || drawRef.current || !active) return;

    console.log('Creating TerraDraw instance');

    const draw = new MaplibreTerradrawControl({
      modes: [
        'point',
        'linestring',
        'polygon',
        'rectangle',
        'delete',
      ],
      open: true,
    });

    drawRef.current = draw;

    map.addControl(draw, 'top-left');

    return () => {
      map.removeControl(draw);
      drawRef.current = null;
    };
  }, [active, map]);

  // 2) React to context.active to start/stop draw
  useEffect(() => {
    const draw = drawRef.current;
    if (!draw) return;

    try {
      if (active) {
        draw.start?.();
      } else {
        draw.stop?.();
      }
    } catch (error) {
      console.error('Error starting/stopping draw:', error);
    }
  }, [active]);

  return null;
}
