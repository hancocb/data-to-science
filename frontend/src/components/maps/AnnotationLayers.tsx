import { useMemo, useEffect, useRef } from 'react';
import { Layer, Source, useMap } from 'react-map-gl/maplibre';

import { getAnnotationLayer } from './layerProps';
import {
  Annotation,
  useAnnotationContext,
  defaultAnnotationStyle,
} from './contexts/AnnotationContext';
import { formatArea, formatLength } from './LayerPane/utils';

function getMeasurement(annotation: Annotation): string | null {
  const geomType = annotation.geom.geometry?.type;
  if (geomType === 'LineString') return formatLength(annotation.geom);
  if (geomType === 'Polygon') return formatArea(annotation.geom);
  return null;
}

export default function AnnotationLayers() {
  const { annotations, checkedIds, styles, visible } = useAnnotationContext();
  const { current: map } = useMap();
  const previousIdsRef = useRef<Set<string>>(new Set());

  // Clean up layers that were unchecked or removed
  useEffect(() => {
    if (!map) return;

    const mapInstance = map.getMap();

    const currentIds = new Set(
      annotations
        .filter((a) => checkedIds.has(a.id))
        .map((a) => `annotation-${a.id}`)
    );

    // Find sources that were removed
    const removedIds = Array.from(previousIdsRef.current).filter(
      (id) => !currentIds.has(id)
    );

    removedIds.forEach((sourceId) => {
      // Remove label layer
      const labelLayerId = `${sourceId}-label`;
      if (mapInstance.getLayer(labelLayerId)) {
        mapInstance.removeLayer(labelLayerId);
      }

      // Remove border layer (for polygon annotations)
      const borderLayerId = `${sourceId}-border`;
      if (mapInstance.getLayer(borderLayerId)) {
        mapInstance.removeLayer(borderLayerId);
      }

      // Remove main layer
      if (mapInstance.getLayer(sourceId)) {
        mapInstance.removeLayer(sourceId);
      }

      // Remove source last
      if (mapInstance.getSource(sourceId)) {
        mapInstance.removeSource(sourceId);
      }
    });

    previousIdsRef.current = currentIds;
  }, [annotations, checkedIds, map]);

  const enrichedAnnotations = useMemo(
    () =>
      annotations
        .filter((a) => checkedIds.has(a.id))
        .map((annotation) => {
          const measurement = getMeasurement(annotation);
          const data = measurement
            ? {
                ...annotation.geom,
                properties: {
                  ...annotation.geom.properties,
                  measurement,
                },
              }
            : annotation.geom;
          return { annotation, data };
        }),
    [annotations, checkedIds]
  );

  if (!visible) return null;

  return enrichedAnnotations.map(({ annotation, data }) => {
    const sourceId = `annotation-${annotation.id}`;
    const geomType = annotation.geom.geometry?.type || 'Point';
    const style = styles[annotation.id] || defaultAnnotationStyle;
    const layerProps = getAnnotationLayer(annotation.id, geomType, style);
    const renderLayer = (props: React.ComponentProps<typeof Layer>) => (
      <Layer key={props.id} {...props} />
    );

    return (
      <Source key={sourceId} id={sourceId} type="geojson" data={data}>
        {Array.isArray(layerProps)
          ? layerProps.map(renderLayer)
          : renderLayer(layerProps)}
      </Source>
    );
  });
}
