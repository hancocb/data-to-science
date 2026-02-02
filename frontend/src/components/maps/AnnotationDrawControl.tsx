import '@watergis/maplibre-gl-terradraw/dist/maplibre-gl-terradraw.css';
import { useEffect, useRef, useState } from 'react';
import { useMap } from 'react-map-gl/maplibre';
import { MaplibreTerradrawControl } from '@watergis/maplibre-gl-terradraw';
import { Feature } from 'geojson';

import AnnotationCreateModal from './AnnotationCreateModal';

interface AnnotationDrawControlProps {
  projectId: string;
  flightId: string;
  dataProductId: string;
}

export default function AnnotationDrawControl({
  projectId,
  flightId,
  dataProductId,
}: AnnotationDrawControlProps) {
  const { current: map } = useMap();
  const drawRef = useRef<MaplibreTerradrawControl | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [drawnFeature, setDrawnFeature] = useState<Feature | null>(null);
  const [drawnFeatureId, setDrawnFeatureId] = useState<string | number | null>(
    null
  );

  useEffect(() => {
    if (!map || drawRef.current || !containerRef.current) return;

    const draw = new MaplibreTerradrawControl({
      modes: ['point', 'linestring', 'polygon', 'rectangle', 'delete'],
      open: true,
    });

    drawRef.current = draw;

    // Manually call onAdd to get the control DOM element,
    // then mount it in our own container instead of a MapLibre control slot.
    // This lets us position the toolbar inline next to the toggle button.
    const controlElement = draw.onAdd(map.getMap());
    containerRef.current.appendChild(controlElement);

    const terraDraw = draw.getTerraDrawInstance();
    const handleFinish = (
      id: string | number,
      context: { mode: string; action: string }
    ) => {
      if (context.mode === 'delete') return;

      const feature = terraDraw?.getSnapshotFeature(id);
      if (feature) {
        const { mode: _mode, ...restProperties } = feature.properties || {};
        const cleanFeature: Feature = {
          type: 'Feature',
          geometry: feature.geometry,
          properties: restProperties,
        };
        setDrawnFeature(cleanFeature);
        setDrawnFeatureId(id);
        setModalOpen(true);
      }
    };
    terraDraw?.on('finish', handleFinish);

    return () => {
      terraDraw?.off('finish', handleFinish);
      if (drawRef.current) {
        drawRef.current.onRemove();
        drawRef.current = null;
      }
    };
  }, [map]);

  const removeDrawnFeature = () => {
    try {
      const terraDraw = drawRef.current?.getTerraDrawInstance();
      if (terraDraw && drawnFeatureId !== null) {
        terraDraw.removeFeatures([drawnFeatureId]);
      }
    } catch {
      // Feature may already have been removed
    }
    setDrawnFeature(null);
    setDrawnFeatureId(null);
  };

  const handleAnnotationSuccess = () => {
    removeDrawnFeature();
  };

  const handleAnnotationCancel = () => {
    removeDrawnFeature();
  };

  return (
    <>
      <div ref={containerRef} />
      <AnnotationCreateModal
        open={modalOpen}
        setOpen={setModalOpen}
        feature={drawnFeature}
        projectId={projectId}
        flightId={flightId}
        dataProductId={dataProductId}
        onSuccess={handleAnnotationSuccess}
        onCancel={handleAnnotationCancel}
      />
    </>
  );
}