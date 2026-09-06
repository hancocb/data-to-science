import clsx from 'clsx';

import { getDataTypeColor } from './utils';

type TemporalFilterControlProps = {
  dataTypes: string[];
  value: string | null;
  onChange: (dataType: string | null) => void;
};

export default function TemporalFilterControl({
  dataTypes,
  value,
  onChange,
}: TemporalFilterControlProps) {
  return (
    <div
      className={clsx(
        'absolute top-2 left-14 max-md:left-2 bg-gray-200 rounded-md shadow-md px-3 py-3 md:min-w-80',
        'max-md:px-2 max-md:py-2 max-md:max-w-[calc(100%-1rem)]'
      )}
      style={{ zIndex: 1001 }}
    >
      <div className="w-full flex flex-col gap-2">
        <select
          className="w-full px-8 max-md:pl-2 max-md:pr-6 max-md:text-xs font-semibold text-gray-600 text-center truncate border-2 border-gray-300 rounded-md bg-white"
          aria-label="Filter timeline by data type"
          name="temporalDataTypeFilter"
          value={value ?? ''}
          onChange={(event) => onChange(event.target.value || null)}
        >
          <option value="">All data types</option>
          {dataTypes.map((dataType) => (
            <option key={dataType} value={dataType}>
              {dataType.toUpperCase()}
            </option>
          ))}
        </select>
        {dataTypes.length > 1 && (
          <div className="max-md:hidden flex flex-wrap items-center gap-x-3 gap-y-1 text-xs font-semibold text-gray-600">
            {dataTypes.map((dataType) => (
              <span key={dataType} className="flex items-center gap-1">
                <span
                  className="h-2.5 w-2.5 rounded-sm"
                  style={{ backgroundColor: getDataTypeColor(dataType, dataTypes) }}
                />
                {dataType.toUpperCase()}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
