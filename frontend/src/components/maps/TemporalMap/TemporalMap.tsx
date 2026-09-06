import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import Map, {
  MapRef,
  NavigationControl,
  ScaleControl,
} from 'react-map-gl/maplibre';

import ColorBarControl from '../ColorBarControl';
import ProjectBoundary from '../ProjectBoundary';
import ProjectRasterTiles from '../ProjectRasterTiles';
import TemporalFilterControl from './TemporalFilterControl';
import TemporalTimeline from './TemporalTimeline';

import { useInterval, useIsMobile } from '../../hooks';
import { useMapApiKeys } from '../MapApiKeysContext';
import { useMapContext } from '../MapContext';
import { useRasterSymbologyContext } from '../RasterSymbologyContext';
import { useRasterSymbologyInit } from '../useRasterSymbologyInit';

import { BBox } from '../Maps';
import {
  getMapboxSatelliteBasemapStyle,
  getWorldImageryTopoBasemapStyle,
} from '../styles/basemapStyles';
import { isSingleBand } from '../utils';
import {
  buildTemporalSteps,
  getRasterDataTypes,
  nearestStepIndex,
  pickProductForStep,
  TemporalProduct,
} from './utils';

const PLAYBACK_INTERVAL = 2000;

export default function TemporalMap() {
  const [dataTypeFilter, setDataTypeFilter] = useState<string | null>(null);
  const [requestedDate, setRequestedDate] = useState<string | null>(null);
  const [requestedProductId, setRequestedProductId] = useState<string | null>(
    null
  );
  const [preferredType, setPreferredType] = useState<string | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [activeProjectBBox, setActiveProjectBBox] = useState<BBox | null>(null);

  const mapRef = useRef<MapRef>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const { activeProject, flights } = useMapContext();
  const { mapboxAccessToken, maptilerApiKey } = useMapApiKeys();
  const { state: symbologyState } = useRasterSymbologyContext();
  const isMobile = useIsMobile();

  const dataTypes = useMemo(() => getRasterDataTypes(flights), [flights]);

  const steps = useMemo(
    () => buildTemporalSteps(flights, dataTypeFilter),
    [flights, dataTypeFilter]
  );

  const activeIndex = useMemo(() => {
    if (!steps.length) return -1;
    if (!requestedDate) return 0;
    const exact = steps.findIndex(({ date }) => date === requestedDate);
    return exact >= 0 ? exact : nearestStepIndex(steps, requestedDate);
  }, [steps, requestedDate]);

  const activeStep = activeIndex >= 0 ? steps[activeIndex] : null;

  const activeProduct = useMemo(() => {
    if (!activeStep) return null;
    const requested = activeStep.products.find(
      ({ dataProduct }) => dataProduct.id === requestedProductId
    );
    return (
      requested ??
      pickProductForStep(activeStep, dataTypeFilter ?? preferredType)
    );
  }, [activeStep, requestedProductId, dataTypeFilter, preferredType]);

  const activeDataProduct = activeProduct?.dataProduct ?? null;

  useRasterSymbologyInit(activeDataProduct);

  const goToIndex = useCallback(
    (index: number) => {
      if (!steps.length) return;
      const clamped = Math.min(Math.max(index, 0), steps.length - 1);
      setRequestedDate(steps[clamped].date);
      setRequestedProductId(null);
    },
    [steps]
  );

  const selectProduct = useCallback((product: TemporalProduct) => {
    setRequestedProductId(product.dataProduct.id);
    setPreferredType(product.dataProduct.data_type);
  }, []);

  const handleFilterChange = useCallback(
    (dataType: string | null) => {
      // Resolve the nearest surviving date so filtering renders once.
      const nextSteps = buildTemporalSteps(flights, dataType);
      const nextIndex = activeStep
        ? nearestStepIndex(nextSteps, activeStep.date)
        : -1;
      setRequestedDate(nextIndex >= 0 ? nextSteps[nextIndex].date : null);
      setRequestedProductId(null);
      setDataTypeFilter(dataType);
      setIsPlaying(false);
    },
    [flights, activeStep]
  );

  const togglePlay = useCallback(() => setIsPlaying((prev) => !prev), []);

  useEffect(() => {
    setDataTypeFilter(null);
    setRequestedDate(null);
    setRequestedProductId(null);
    setPreferredType(null);
    setIsPlaying(false);
    setActiveProjectBBox(null);
  }, [activeProject?.id]);

  useInterval(
    () => {
      if (activeIndex >= steps.length - 1) {
        setIsPlaying(false);
      } else {
        goToIndex(activeIndex + 1);
      }
    },
    isPlaying && steps.length > 1 ? PLAYBACK_INTERVAL : null
  );

  const handleTogglePlay = useCallback(() => {
    if (!isPlaying && activeIndex >= steps.length - 1) {
      goToIndex(0);
    }
    togglePlay();
  }, [isPlaying, activeIndex, steps.length, goToIndex, togglePlay]);

  const mapStyle = useMemo(() => {
    return mapboxAccessToken
      ? getMapboxSatelliteBasemapStyle(mapboxAccessToken)
      : getWorldImageryTopoBasemapStyle(maptilerApiKey);
  }, [mapboxAccessToken, maptilerApiKey]);

  // The layer pane collapses on entry and can be reopened, so the container
  // resizes after MapLibre measures it. A stale transform renders the map
  // anchored to the left of the container.
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const observer = new ResizeObserver(() => mapRef.current?.resize());
    observer.observe(container);
    return () => observer.disconnect();
  }, []);

  return (
    <div ref={containerRef} className="relative h-full overflow-hidden">
      <Map
        ref={mapRef}
        initialViewState={{
          longitude: -86.9138040788386,
          latitude: 40.428655143949925,
          zoom: 8,
        }}
        style={{ width: '100%', height: '100%' }}
        mapboxAccessToken={mapboxAccessToken || undefined}
        mapStyle={mapStyle}
        maxZoom={25}
      >
        {activeProject && (
          <ProjectBoundary setActiveProjectBBox={setActiveProjectBBox} />
        )}

        {activeProject &&
          activeDataProduct &&
          symbologyState[activeDataProduct.id]?.isLoaded && (
            <ProjectRasterTiles
              key={activeDataProduct.id}
              boundingBox={
                activeDataProduct.bbox || activeProjectBBox || undefined
              }
              dataProduct={activeDataProduct}
            />
          )}

        {/* Overlaps the timeline on narrow viewports */}
        {activeProject &&
          activeDataProduct &&
          isSingleBand(activeDataProduct) &&
          !isMobile && (
            <ColorBarControl
              dataProduct={activeDataProduct}
              projectId={activeProject.id}
            />
          )}

        <NavigationControl />
        <ScaleControl />
      </Map>

      {dataTypes.length > 1 && (
        <TemporalFilterControl
          dataTypes={dataTypes}
          value={dataTypeFilter}
          onChange={handleFilterChange}
        />
      )}

      <TemporalTimeline
        steps={steps}
        activeIndex={activeIndex}
        activeProductId={activeDataProduct?.id ?? null}
        dataTypes={dataTypes}
        isPlaying={isPlaying}
        onGoToIndex={goToIndex}
        onSelectProduct={selectProduct}
        onTogglePlay={handleTogglePlay}
      />
    </div>
  );
}
