import { useEffect } from 'react';

import { DataProduct } from '../pages/workspace/projects/Project';
import { useRasterSymbologyContext } from './RasterSymbologyContext';
import {
  createDefaultMultibandSymbology,
  createDefaultSingleBandSymbology,
  isSingleBand,
} from './utils';

/**
 * ProjectRasterTiles renders nothing until the symbology context holds a
 * symbology and ready state for the raster. RasterSymbologySettings normally
 * does this, but only mounts inside an expanded DataProductCard, so tools that
 * render rasters outside the layer pane need it here.
 */
export function useRasterSymbologyInit(dataProduct: DataProduct | null): void {
  const { dispatch } = useRasterSymbologyContext();

  useEffect(() => {
    if (!dataProduct) return;

    const { id, stac_properties, user_style } = dataProduct;

    if (user_style) {
      // default opacity to 100 for older saved styles that are missing it
      dispatch({
        type: 'SET_SYMBOLOGY',
        rasterId: id,
        payload: { ...user_style, opacity: user_style.opacity ?? 100 },
      });
    } else if (isSingleBand(dataProduct)) {
      dispatch({
        type: 'SET_SYMBOLOGY',
        rasterId: id,
        payload: createDefaultSingleBandSymbology(stac_properties),
      });
    } else {
      dispatch({
        type: 'SET_SYMBOLOGY',
        rasterId: id,
        payload: createDefaultMultibandSymbology(stac_properties),
      });
    }

    dispatch({ type: 'SET_READY_STATE', rasterId: id, payload: true });
  }, [dataProduct, dispatch]);
}
