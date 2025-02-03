import axios, { AxiosResponse, isAxiosError } from 'axios';
import { FeatureCollection, Point } from 'geojson';
import { useEffect } from 'react';

import { useMapContext } from './MapContext';

export default function ProjectLoader() {
  const { projectGeojsonDispatch, projectGeojsonLoadedDispatch } =
    useMapContext();

  const geojsonUrl = `${
    import.meta.env.VITE_API_V1_STR
  }/projects?include_all=${false}&format=geojson`;

  useEffect(() => {
    const fetchGeojson = async () => {
      try {
        const response: AxiosResponse<FeatureCollection<Point>> =
          await axios.get(geojsonUrl);
        // Only set if project features returned
        if (response.data?.features.length > 0) {
          projectGeojsonDispatch({ type: 'set', payload: response.data });
          projectGeojsonLoadedDispatch({ type: 'set', payload: true });
        }
      } catch (error) {
        // Clear any previously set data
        projectGeojsonDispatch({ type: 'set', payload: null });
        projectGeojsonLoadedDispatch({ type: 'set', payload: false });
        if (isAxiosError(error)) {
          // Axios-specific error handling
          const status = error.response?.status || 500;
          const message = error.response?.data?.message || error.message;

          throw {
            status,
            message: `Failed to load project geojson: ${message}`,
          };
        } else {
          // Generic error handling
          throw {
            status: 500,
            message: 'An unexpected error occurred.',
          };
        }
      }
    };
    fetchGeojson();
  }, []);

  return null;
}
