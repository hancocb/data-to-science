import clsx from 'clsx';
import { useEffect, useMemo, useRef, useState } from 'react';
import {
  ChevronLeftIcon,
  ChevronRightIcon,
  PauseIcon,
  PlayIcon,
} from '@heroicons/react/24/outline';

import { useIsMobile } from '../../hooks';
import { formatDate } from '../LayerPane/utils';
import { getDataTypeColor, TemporalProduct, TemporalStep } from './utils';

/** Constant box so the dot stays centered on the line as its size changes. */
const DOT_BOX = 24;
const MARKER = { desktop: 10, mobile: 14 };
const MARKER_GAP = { desktop: 8, mobile: 12 };
const LABEL_ROW = 16;
/** Track end inset, sized to fit a centered end label. */
const TRACK_INSET = 32;
/** Labels closer together than this are thinned out; the track never scrolls. */
const LABEL_SPACING = { compact: 54, withYear: 70 };

type TemporalTimelineProps = {
  steps: TemporalStep[];
  activeIndex: number;
  activeProductId: string | null;
  dataTypes: string[];
  isPlaying: boolean;
  onGoToIndex: (index: number) => void;
  onSelectProduct: (product: TemporalProduct) => void;
  onTogglePlay: () => void;
};

function formatShortDate(date: string, includeYear: boolean): string {
  return new Date(date).toLocaleDateString('en-us', {
    timeZone: 'UTC',
    month: 'short',
    day: 'numeric',
    ...(includeYear ? { year: '2-digit' } : {}),
  });
}

function stepOffset(position: number): string {
  return `calc(${TRACK_INSET}px + ${position} * (100% - ${TRACK_INSET * 2}px))`;
}

export default function TemporalTimeline({
  steps,
  activeIndex,
  activeProductId,
  dataTypes,
  isPlaying,
  onGoToIndex,
  onSelectProduct,
  onTogglePlay,
}: TemporalTimelineProps) {
  const trackRef = useRef<HTMLDivElement>(null);
  const [trackWidth, setTrackWidth] = useState(0);
  const isMobile = useIsMobile();

  const marker = isMobile ? MARKER.mobile : MARKER.desktop;
  const markerGap = isMobile ? MARKER_GAP.mobile : MARKER_GAP.desktop;

  const activeStep = steps[activeIndex] ?? null;
  const activeProduct =
    activeStep?.products.find(
      ({ dataProduct }) => dataProduct.id === activeProductId
    ) ?? null;

  const spansYears = useMemo(() => {
    if (steps.length < 2) return false;
    const firstYear = steps[0].date.slice(0, 4);
    return steps.some((step) => step.date.slice(0, 4) !== firstYear);
  }, [steps]);

  const trackHeight = useMemo(() => {
    const tallestStack = steps.reduce(
      (tallest, step) => Math.max(tallest, step.products.length),
      0
    );
    // Headroom keeps the enlarged active marker and its ring inside the track.
    return (
      LABEL_ROW + DOT_BOX + tallestStack * (marker + markerGap) + markerGap
    );
  }, [steps, marker, markerGap]);

  // Measured width decides how many labels fit without overlapping.
  useEffect(() => {
    const track = trackRef.current;
    if (!track) return;

    setTrackWidth(track.getBoundingClientRect().width);
    const observer = new ResizeObserver(([entry]) =>
      setTrackWidth(entry.contentRect.width)
    );
    observer.observe(track);
    return () => observer.disconnect();
  }, []);

  // Label every date with room for one, prioritising the active date and ends.
  const labelledSteps = useMemo(() => {
    if (!steps.length) return new Set<number>();
    if (trackWidth <= 0) {
      return new Set(
        [activeIndex, 0, steps.length - 1].filter((index) => index >= 0)
      );
    }

    const spacing = spansYears
      ? LABEL_SPACING.withYear
      : LABEL_SPACING.compact;
    const usable = Math.max(trackWidth - TRACK_INSET * 2, 0);
    const offsetOf = (index: number) =>
      TRACK_INSET + steps[index].position * usable;

    const accepted: number[] = [];
    const candidates = [
      activeIndex,
      0,
      steps.length - 1,
      ...steps.map((_, index) => index),
    ];
    candidates.forEach((index) => {
      if (index < 0 || index >= steps.length) return;
      if (accepted.includes(index)) return;
      const offset = offsetOf(index);
      const clears = accepted.every(
        (other) => Math.abs(offsetOf(other) - offset) >= spacing
      );
      if (clears) accepted.push(index);
    });
    return new Set(accepted);
  }, [steps, trackWidth, activeIndex, spansYears]);

  const handleKeyDown = (event: React.KeyboardEvent<HTMLDivElement>) => {
    if (!steps.length) return;

    switch (event.key) {
      case 'ArrowLeft':
        event.preventDefault();
        onGoToIndex(activeIndex - 1);
        break;
      case 'ArrowRight':
        event.preventDefault();
        onGoToIndex(activeIndex + 1);
        break;
      case 'Home':
        event.preventDefault();
        onGoToIndex(0);
        break;
      case 'End':
        event.preventDefault();
        onGoToIndex(steps.length - 1);
        break;
      case ' ':
        // Only when the track itself has focus, so Space still activates a
        // focused dot or marker button.
        if (event.target === event.currentTarget) {
          event.preventDefault();
          onTogglePlay();
        }
        break;
    }
  };

  const canStep = steps.length > 1;

  return (
    <div
      className="absolute bottom-12 left-1/2 -translate-x-1/2 w-[min(calc(100%-10rem),56rem)] max-md:bottom-4 max-md:w-[calc(100%-1rem)]"
      style={{ zIndex: 1001 }}
    >
      <div className="bg-white/90 rounded-md shadow-md px-3 py-2 text-slate-600">
        {!steps.length ? (
          <p className="text-sm text-center py-2">
            No raster data products available for this project.
          </p>
        ) : (
          <>
            <div className="flex items-center justify-between gap-2 text-sm">
              <span className="font-semibold truncate">
                {activeStep ? formatDate(activeStep.date) : ''}
              </span>
              <span className="flex items-center gap-2 min-w-0">
                {activeProduct && (
                  <span className="truncate">
                    {activeProduct.dataProduct.data_type.toUpperCase()}
                    {' · '}
                    {activeProduct.flight.name || activeProduct.flight.sensor}
                  </span>
                )}
                <span className="whitespace-nowrap text-slate-500">
                  {activeIndex + 1} of {steps.length}
                </span>
              </span>
            </div>

            <div className="flex items-end gap-1">
              <button
                type="button"
                className="px-2 py-1 rounded-md font-semibold border-2 shadow-md transition-colors bg-white border-gray-300 text-gray-600 hover:bg-gray-100 disabled:opacity-40 disabled:cursor-not-allowed"
                onClick={() => onGoToIndex(activeIndex - 1)}
                disabled={!canStep || activeIndex <= 0}
                title="Previous date"
                aria-label="Previous date"
              >
                <ChevronLeftIcon className="h-4 w-4" />
              </button>
              <button
                type="button"
                className={clsx(
                  'px-2 py-1 rounded-md font-semibold border-2 shadow-md transition-colors disabled:opacity-40 disabled:cursor-not-allowed',
                  isPlaying
                    ? 'bg-accent2 border-accent2 text-white'
                    : 'bg-white border-gray-300 text-gray-600 hover:bg-gray-100'
                )}
                onClick={onTogglePlay}
                disabled={!canStep}
                title={isPlaying ? 'Pause' : 'Play through dates'}
                aria-label={isPlaying ? 'Pause' : 'Play through dates'}
              >
                {isPlaying ? (
                  <PauseIcon className="h-4 w-4" />
                ) : (
                  <PlayIcon className="h-4 w-4" />
                )}
              </button>

              <div
                className="flex-1 min-w-0 rounded focus:outline-hidden focus:ring-2 focus:ring-accent2"
                role="group"
                aria-label="Flight timeline"
                tabIndex={0}
                onKeyDown={handleKeyDown}
              >
                <div
                  ref={trackRef}
                  className="relative"
                  style={{ height: trackHeight }}
                >
                  <div
                    className="absolute h-0.5 rounded bg-slate-400"
                    style={{
                      left: TRACK_INSET,
                      right: TRACK_INSET,
                      bottom: LABEL_ROW + DOT_BOX / 2 - 1,
                    }}
                  />

                  {steps.map((step, index) => {
                    const isActiveStep = index === activeIndex;

                    return (
                      <div key={step.date}>
                        <div
                          className="absolute flex flex-col-reverse items-center -translate-x-1/2"
                          style={{
                            left: stepOffset(step.position),
                            bottom: LABEL_ROW,
                            zIndex: isActiveStep ? 2 : 1,
                          }}
                        >
                          <button
                            type="button"
                            className="group relative flex items-center justify-center max-md:before:absolute max-md:before:content-[''] max-md:before:inset-[-0.625rem]"
                            style={{ height: DOT_BOX, width: DOT_BOX }}
                            onClick={() => onGoToIndex(index)}
                            title={formatDate(step.date)}
                            aria-label={`${formatDate(step.date)}, ${
                              step.products.length
                            } data product${
                              step.products.length === 1 ? '' : 's'
                            }`}
                            aria-current={isActiveStep ? 'date' : undefined}
                          >
                            <span
                              className={clsx(
                                'rounded-full bg-white transition-all',
                                isActiveStep
                                  ? 'h-5 w-5 border-[3px] border-accent2 shadow-md'
                                  : 'h-3.5 w-3.5 border-2 border-slate-500 group-hover:border-accent2'
                              )}
                            />
                          </button>

                          {step.products.map((product) => {
                            const isActiveProduct =
                              isActiveStep &&
                              product.dataProduct.id === activeProductId;
                            const label = `${product.dataProduct.data_type.toUpperCase()} · ${
                              product.flight.name || product.flight.sensor
                            }`;

                            return (
                              <button
                                key={product.dataProduct.id}
                                type="button"
                                className="flex items-center justify-center"
                                style={{
                                  height: marker + markerGap,
                                  width: marker + markerGap,
                                }}
                                onClick={() => {
                                  if (!isActiveStep) onGoToIndex(index);
                                  onSelectProduct(product);
                                }}
                                title={label}
                                aria-label={label}
                                aria-pressed={isActiveProduct}
                              >
                                <span
                                  className={clsx(
                                    'rounded-sm transition-all',
                                    isActiveProduct
                                      ? 'opacity-100 ring-2 ring-accent2 ring-offset-1 scale-125'
                                      : 'opacity-60 hover:opacity-100'
                                  )}
                                  style={{
                                    height: marker,
                                    width: marker,
                                    backgroundColor: getDataTypeColor(
                                      product.dataProduct.data_type,
                                      dataTypes
                                    ),
                                  }}
                                />
                              </button>
                            );
                          })}
                        </div>

                        {labelledSteps.has(index) && (
                          <span
                            className={clsx(
                              // w-max stops the label being squeezed, and
                              // overflowing, at the track's right edge.
                              'absolute bottom-0 w-max -translate-x-1/2 text-[10px] whitespace-nowrap',
                              isActiveStep
                                ? 'font-semibold text-slate-700'
                                : 'text-slate-500'
                            )}
                            style={{ left: stepOffset(step.position) }}
                          >
                            {formatShortDate(step.date, spansYears)}
                          </span>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>

              <button
                type="button"
                className="px-2 py-1 rounded-md font-semibold border-2 shadow-md transition-colors bg-white border-gray-300 text-gray-600 hover:bg-gray-100 disabled:opacity-40 disabled:cursor-not-allowed"
                onClick={() => onGoToIndex(activeIndex + 1)}
                disabled={!canStep || activeIndex >= steps.length - 1}
                title="Next date"
                aria-label="Next date"
              >
                <ChevronRightIcon className="h-4 w-4" />
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
