import {
  DataProduct,
  Flight,
} from '../../pages/workspace/projects/Project';
import { NON_MAP_DATA_TYPES } from '../LayerPane/utils';

export type TemporalProduct = {
  dataProduct: DataProduct;
  flight: Flight;
};

export type TemporalStep = {
  date: string;
  /** Proportional offset (0-1) between the earliest and latest date. */
  position: number;
  products: TemporalProduct[];
};

/** Matched as a prefix so both "ortho" and "Orthomosaic" qualify. */
const PREFERRED_DATA_TYPE_PREFIX = 'ortho';

const DATA_TYPE_PALETTE = [
  '#3d5a80',
  '#2a9d8f',
  '#7c3aed',
  '#ca8a04',
  '#db2777',
  '#0891b2',
  '#65a30d',
  '#78350f',
];

/** data_type is free text on the backend, so casing varies ("dsm", "DSM"). */
export function normalizeDataType(dataType: string): string {
  return dataType.trim().toLowerCase();
}

export function isRasterDataProduct(dataProduct: DataProduct): boolean {
  return (
    !(NON_MAP_DATA_TYPES as readonly string[]).includes(
      normalizeDataType(dataProduct.data_type)
    ) && (dataProduct.stac_properties?.raster?.length ?? 0) > 0
  );
}

/** Date-only strings must parse as UTC; local time would shift the day. */
export function parseDateUTC(date: string): number {
  const [year, month, day] = date.split('-').map(Number);
  if (!year || !month || !day) return NaN;
  return Date.UTC(year, month - 1, day);
}

function compareDataTypes(a: string, b: string): number {
  const left = normalizeDataType(a);
  const right = normalizeDataType(b);
  if (left === right) return 0;
  const leftPreferred = left.startsWith(PREFERRED_DATA_TYPE_PREFIX);
  const rightPreferred = right.startsWith(PREFERRED_DATA_TYPE_PREFIX);
  if (leftPreferred !== rightPreferred) return leftPreferred ? -1 : 1;
  return left.localeCompare(right);
}

/**
 * Distinct raster data types across a project's flights. Derive this from the
 * unfiltered flights so marker colors stay stable while a filter is applied.
 */
export function getRasterDataTypes(flights: Flight[]): string[] {
  const dataTypes = new Map<string, string>();
  flights.forEach((flight) =>
    flight.data_products
      .filter(isRasterDataProduct)
      .forEach(({ data_type }) => {
        const key = normalizeDataType(data_type);
        if (!dataTypes.has(key)) dataTypes.set(key, data_type);
      })
  );
  return [...dataTypes.values()].sort(compareDataTypes);
}

export function getDataTypeColor(
  dataType: string,
  dataTypes: string[]
): string {
  const key = normalizeDataType(dataType);
  const index = dataTypes.findIndex(
    (candidate) => normalizeDataType(candidate) === key
  );
  return DATA_TYPE_PALETTE[
    (index < 0 ? 0 : index) % DATA_TYPE_PALETTE.length
  ];
}

/** The first product is a date's default selection and its lowest marker. */
export function sortTemporalProducts(
  products: TemporalProduct[]
): TemporalProduct[] {
  return [...products].sort((a, b) => {
    const typeDiff = compareDataTypes(
      a.dataProduct.data_type,
      b.dataProduct.data_type
    );
    if (typeDiff !== 0) return typeDiff;
    const nameDiff = (a.flight.name ?? '').localeCompare(b.flight.name ?? '');
    if (nameDiff !== 0) return nameDiff;
    return a.dataProduct.id.localeCompare(b.dataProduct.id);
  });
}

/** One step per acquisition date; flights sharing a date are merged. */
export function buildTemporalSteps(
  flights: Flight[],
  dataTypeFilter: string | null = null
): TemporalStep[] {
  const filterKey = dataTypeFilter ? normalizeDataType(dataTypeFilter) : null;
  const productsByDate = new Map<string, TemporalProduct[]>();

  flights.forEach((flight) => {
    const products = flight.data_products.filter(
      (dataProduct) =>
        isRasterDataProduct(dataProduct) &&
        (!filterKey || normalizeDataType(dataProduct.data_type) === filterKey)
    );
    if (!products.length) return;
    if (Number.isNaN(parseDateUTC(flight.acquisition_date))) return;

    const existing = productsByDate.get(flight.acquisition_date) ?? [];
    productsByDate.set(flight.acquisition_date, [
      ...existing,
      ...products.map((dataProduct) => ({ dataProduct, flight })),
    ]);
  });

  const dates = [...productsByDate.keys()].sort(
    (a, b) => parseDateUTC(a) - parseDateUTC(b)
  );
  if (!dates.length) return [];

  const earliest = parseDateUTC(dates[0]);
  const span = parseDateUTC(dates[dates.length - 1]) - earliest;

  return dates.map((date) => ({
    date,
    position: span > 0 ? (parseDateUTC(date) - earliest) / span : 0.5,
    products: sortTemporalProducts(productsByDate.get(date) ?? []),
  }));
}

export function hasTemporalData(flights: Flight[]): boolean {
  return buildTemporalSteps(flights).length > 1;
}

export function pickProductForStep(
  step: TemporalStep | null,
  preferredType: string | null = null
): TemporalProduct | null {
  if (!step || !step.products.length) return null;
  if (preferredType) {
    const key = normalizeDataType(preferredType);
    const preferred = step.products.find(
      ({ dataProduct }) => normalizeDataType(dataProduct.data_type) === key
    );
    if (preferred) return preferred;
  }
  return step.products[0];
}

export function nearestStepIndex(steps: TemporalStep[], date: string): number {
  if (!steps.length) return -1;

  const target = parseDateUTC(date);
  if (Number.isNaN(target)) return 0;

  let nearest = 0;
  let smallestDiff = Infinity;
  steps.forEach((step, index) => {
    const diff = Math.abs(parseDateUTC(step.date) - target);
    // Strict comparison keeps the earlier date when two are equidistant.
    if (diff < smallestDiff) {
      smallestDiff = diff;
      nearest = index;
    }
  });
  return nearest;
}
