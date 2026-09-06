import { useMemo } from 'react';
import { ClockIcon, MapIcon, ScaleIcon } from '@heroicons/react/24/outline';

import Checkbox from '../Checkbox';
import { useMapContext } from './MapContext';
import { hasTemporalData } from './TemporalMap/utils';

function classNames(...classes: string[]) {
  return classes.filter(Boolean).join(' ');
}

const TOOL_BUTTON_CLASSES =
  'h-11 w-11 md:h-8 md:w-8 flex items-center justify-center shadow-xs rounded-sm border-2 border-solid border-slate-500 p-1.5';

export default function MapToolbar() {
  const {
    activeMapTool,
    activeDataProductDispatch,
    activeMapToolDispatch,
    flights,
    tileScale,
    tileScaleDispatch,
  } = useMapContext();

  const temporalEnabled = useMemo(() => hasTemporalData(flights), [flights]);

  return (
    <fieldset className="border border-solid border-slate-300 p-1.5">
      <legend>Map Tools</legend>
      <div className="flex items-end justify-start gap-1.5">
        <div
          className={classNames(
            activeMapTool === 'map' ? 'bg-accent2' : '',
            TOOL_BUTTON_CLASSES,
            'cursor-pointer hover:shadow-xl'
          )}
          onClick={() => {
            activeDataProductDispatch({ type: 'clear', payload: null });
            activeMapToolDispatch({ type: 'set', payload: 'map' });
          }}
        >
          <MapIcon className="h-5 w-5 md:h-4 md:w-4" />
          <span className="sr-only">Map Tool</span>
        </div>
        <div
          className={classNames(
            activeMapTool === 'compare' ? 'bg-accent2' : '',
            TOOL_BUTTON_CLASSES,
            'cursor-pointer hover:shadow-xl'
          )}
          onClick={() => {
            activeDataProductDispatch({ type: 'clear', payload: null });
            activeMapToolDispatch({ type: 'set', payload: 'compare' });
          }}
        >
          <ScaleIcon className="h-5 w-5 md:h-4 md:w-4" />
          <span className="sr-only">Compare Tool</span>
        </div>
        <div
          className={classNames(
            activeMapTool === 'temporal' ? 'bg-accent2' : '',
            TOOL_BUTTON_CLASSES,
            temporalEnabled
              ? 'cursor-pointer hover:shadow-xl'
              : 'opacity-40 cursor-not-allowed'
          )}
          aria-disabled={!temporalEnabled}
          title={
            temporalEnabled
              ? 'Step through flight dates'
              : 'Requires raster data products on at least two flight dates'
          }
          onClick={() => {
            if (!temporalEnabled) return;
            activeDataProductDispatch({ type: 'clear', payload: null });
            activeMapToolDispatch({ type: 'set', payload: 'temporal' });
          }}
        >
          <ClockIcon className="h-5 w-5 md:h-4 md:w-4" />
          <span className="sr-only">Temporal Tool</span>
        </div>
        <div className="mt-4">
          <Checkbox
            id="scale-checkbox"
            name="scale"
            checked={tileScale === 4}
            onChange={(e) => {
              tileScaleDispatch({
                type: 'set',
                payload: e.currentTarget.checked ? 4 : 2,
              });
            }}
          />
          <label
            htmlFor="scale-checkbox"
            className="ms-2 text-sm font-medium text-gray-900"
            title="Increases tile resolution from 512x512 to 1024x1024"
          >
            Increase tile resolution
          </label>
        </div>
      </div>
    </fieldset>
  );
}
