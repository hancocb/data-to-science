import { FeatureCollection, Point, Polygon } from 'geojson';

import {
  DataProduct,
  Flight,
  MapLayer,
  STACProperties,
} from '../pages/workspace/projects/Project';
import { SingleBandSymbology, MultibandSymbology } from './RasterSymbologyContext';

type Bounds = [number, number, number, number];

/**
 * Calculates bounding box for features in GeoJSON Feature Collection. Supports
 * Point or Polygon geometry types.
 * @param geojsonData Feature Collection of Point or Polygon Feautres.
 * @returns Bounding box array.
 */
function calculateBoundsFromGeoJSON(
  geojsonData: FeatureCollection<Point | Polygon>
): Bounds {
  const bounds: Bounds = geojsonData.features.reduce(
    (bounds, feature) => {
      const [minLng, minLat, maxLng, maxLat] = bounds;

      if (feature.geometry.type === 'Polygon') {
        // Flatten the coordinates array into single array of coordinates
        const coordinates = feature.geometry.coordinates.flat(Infinity) as number[];

        for (let i = 0; i < coordinates.length; i += 2) {
          const lng = coordinates[i];
          const lat = coordinates[i + 1];
          bounds[0] = Math.min(bounds[0], lng);
          bounds[1] = Math.min(bounds[1], lat);
          bounds[2] = Math.max(bounds[2], lng);
          bounds[3] = Math.max(bounds[3], lat);
        }

        return bounds;
      } else if (feature.geometry.type === 'Point') {
        const [lng, lat] = feature.geometry.coordinates;
        return [
          Math.min(minLng, lng),
          Math.min(minLat, lat),
          Math.max(maxLng, lng),
          Math.max(maxLat, lat),
        ];
      } else {
        throw new Error('Unable to calculate bounds for GeoJSON data');
      }
    },
    [Infinity, Infinity, -Infinity, -Infinity]
  );

  return bounds;
}

/**
 * Map API response with project vector layers to MapLayer[].
 * @param layers Vector layers returned from API response.
 * @returns Mapped vector layers.
 */
const mapApiResponseToLayers = (layers: MapLayer[]) =>
  layers.map((layer) => ({
    id: layer.layer_id,
    name: layer.layer_name,
    checked: false,
    type: layer.geom_type,
    color: '#ffde21',
    opacity: 100,
    signedUrl: layer.signed_url,
  }));

function getDefaultStyle(
  dataProduct: DataProduct
): SingleBandSymbology | MultibandSymbology {
  if (isSingleBand(dataProduct)) {
    const stats = dataProduct.stac_properties.raster[0].stats;
    return {
      colorRamp: 'rainbow',
      max: stats.maximum,
      meanStdDev: 2,
      min: stats.minimum,
      mode: 'minMax',
      userMin: stats.minimum,
      userMax: stats.maximum,
      opacity: 100,
    };
  } else {
    const raster = dataProduct.stac_properties.raster;
    return {
      mode: 'minMax',
      meanStdDev: 2,
      red: {
        idx: 1,
        min: raster[0].stats.minimum,
        max: raster[0].stats.maximum,
        userMin: raster[0].stats.minimum,
        userMax: raster[0].stats.maximum,
      },
      green: {
        idx: 2,
        min: raster[1].stats.minimum,
        max: raster[1].stats.maximum,
        userMin: raster[1].stats.minimum,
        userMax: raster[1].stats.maximum,
      },
      blue: {
        idx: 3,
        min: raster[2].stats.minimum,
        max: raster[2].stats.maximum,
        userMin: raster[2].stats.minimum,
        userMax: raster[2].stats.maximum,
      },
      opacity: 100,
    };
  }
}

function getHillshade(
  activeDataProduct: DataProduct,
  flights: Flight[]
): DataProduct | null {
  const dataProductName = activeDataProduct.data_type.toLowerCase();
  const filteredFlights = flights.filter(
    ({ id }) => id === activeDataProduct.flight_id
  );
  if (filteredFlights.length > 0 && filteredFlights[0].data_products.length > 1) {
    const dataProducts = filteredFlights[0].data_products;
    const dataProductHillshade = dataProducts.filter(
      (dataProduct) =>
        dataProduct.data_type.toLowerCase().split(' hs')[0] === dataProductName &&
        dataProduct.data_type.toLowerCase().split(' hs').length > 1
    );
    return dataProductHillshade.length > 0 ? dataProductHillshade[0] : null;
  } else {
    return null;
  }
}

/**
 * Returns true if data product has a single band.
 * @param dataProduct Active data product.
 * @returns True if single band, otherwise False.
 */
function isSingleBand(dataProduct: DataProduct): boolean {
  return dataProduct.stac_properties && dataProduct.stac_properties.raster.length === 1;
}

/**
 * Returns object with default symbology properties for a single-band data product.
 * @param stacProperties Data product band statistics.
 * @returns Default symbology.
 */
const createDefaultSingleBandSymbology = (
  stacProperties: STACProperties
): SingleBandSymbology => ({
  colorRamp: 'rainbow',
  meanStdDev: 2,
  mode: 'minMax',
  opacity: 100,
  min: stacProperties.raster[0].stats.minimum,
  max: stacProperties.raster[0].stats.maximum,
  userMin: stacProperties.raster[0].stats.minimum,
  userMax: stacProperties.raster[0].stats.maximum,
});

/**
 * Returns object with default symbology properties for a 3-band data product.
 * @param stacProperties Data product band statistics.
 * @returns Default symbology.
 */
const createDefaultMultibandSymbology = (
  stacProperties: STACProperties
): MultibandSymbology => {
  const createColorChannel = (idx: number) => ({
    idx,
    min: stacProperties.raster[idx - 1].stats.minimum,
    max: stacProperties.raster[idx - 1].stats.maximum,
    userMin: stacProperties.raster[idx - 1].stats.minimum,
    userMax: stacProperties.raster[idx - 1].stats.maximum,
  });

  return {
    meanStdDev: 2,
    mode: 'minMax',
    opacity: 100,
    red: createColorChannel(1),
    green: createColorChannel(2),
    blue: createColorChannel(3),
  };
};

/**
 * Returns default min/max values for single band raster.
 * @param stacProps STAC metadata for raster band.
 * @param symbology Current symbology settings.
 * @returns Min/max values for single band.
 */
const getSingleBandMinMax = (
  stacProps: STACProperties,
  symbology: SingleBandSymbology
): [number, number] => {
  const defaultMinMax: [number, number] = [0, 255];

  switch (symbology.mode) {
    case 'minMax':
      if (symbology.min === undefined || symbology.max === undefined) {
        console.warn(
          'Min and max raster props missing, falling back to default min/max.'
        );
        return defaultMinMax;
      }
      return [symbology.min, symbology.max];

    case 'userDefined':
      if (symbology.userMin === undefined || symbology.userMax === undefined) {
        console.warn(
          'User defined min and max props missing, falling back to default min/max.'
        );
        return defaultMinMax;
      }
      return [symbology.userMin, symbology.userMax];

    case 'meanStdDev':
      const stats = stacProps.raster?.[0]?.stats;
      if (!stats || stats.mean === undefined || stats.stddev === undefined) {
        console.warn('Stats missing, falling back to default min/max.');
        return defaultMinMax;
      }
      const deviation = stats.stddev * symbology.meanStdDev;
      return [stats.mean - deviation, stats.mean + deviation];

    default:
      console.warn(`Unexpected symbology mode: ${symbology.mode}`);
      return defaultMinMax;
  }
};

/**
 * Returns default min/max values for multiband raster.
 * @param stacProps STAC metadata for raster bands.
 * @param symbology Current symbology settings.
 * @returns Min/max values for each band.
 */
const getMultibandMinMax = (
  stacProps: STACProperties,
  symbology: MultibandSymbology
): [[number, number], [number, number], [number, number]] => {
  const defaultMinMax: [[number, number], [number, number], [number, number]] = [
    [0, 255],
    [0, 255],
    [0, 255],
  ];

  const validateBands = (key: 'min' | 'max' | 'userMin' | 'userMax') =>
    ['red', 'green', 'blue'].every((band) => symbology[band]?.[key] !== undefined);

  const getStats = (index: number) => stacProps.raster?.[index - 1]?.stats;

  switch (symbology.mode) {
    case 'minMax':
      if (!validateBands('min') || !validateBands('max')) {
        console.warn(
          'Min and max raster props missing for at least one band, falling back to default min/max.'
        );
        return defaultMinMax;
      } else {
        return [
          [symbology.red.min, symbology.red.max],
          [symbology.green.min, symbology.green.max],
          [symbology.blue.min, symbology.blue.max],
        ];
      }

    case 'userDefined':
      if (!validateBands('userMin') || !validateBands('userMax')) {
        console.warn(
          'User defined min and max props missing for at least one band, falling back to default min/max.'
        );
        return defaultMinMax;
      } else {
        return [
          [symbology.red.userMin, symbology.red.userMax],
          [symbology.green.userMin, symbology.green.userMax],
          [symbology.blue.userMin, symbology.blue.userMax],
        ];
      }

    case 'meanStdDev':
      // verify we have a band index for RGB
      if (
        !['red', 'green', 'blue'].every((band) => symbology[band]?.idx !== undefined)
      ) {
        console.warn(
          'Missing index for at least one band, falling back to default min/max.'
        );
        return defaultMinMax;
      } else {
        const stats = ['red', 'green', 'blue'].map((band) =>
          getStats(symbology[band].idx)
        );

        // verify we have a mean, std. dev. for each band and a meanStdDev mult factor
        if (
          stats.some((s) => !s || s.mean === undefined || s.stddev === undefined) ||
          symbology.meanStdDev === undefined
        ) {
          console.warn(
            'Stats missing for at least one band, falling back to default min/max.'
          );
          return defaultMinMax;
        }

        return stats.map((stat) => {
          const deviation = stat.stddev * symbology.meanStdDev;
          return [stat.mean - deviation, stat.mean + deviation];
        }) as [[number, number], [number, number], [number, number]];
      }

    default:
      return defaultMinMax;
  }
};

export {
  calculateBoundsFromGeoJSON,
  createDefaultSingleBandSymbology,
  createDefaultMultibandSymbology,
  getDefaultStyle,
  getHillshade,
  getSingleBandMinMax,
  getMultibandMinMax,
  isSingleBand,
  mapApiResponseToLayers,
};
