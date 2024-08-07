import { Field, useFormikContext } from 'formik';

import HintText from '../../../../HintText';
import { SelectField } from '../../../../InputFields';

import { DataProduct } from '../../Project';
import { useProjectContext } from '../../ProjectContext';
import { ToolboxFields } from './ToolboxModal';

import { prepMapLayers } from '../../mapLayers/utils';

const EXGBandSelection = ({ dataProduct }: { dataProduct: DataProduct }) => {
  const bandOptions = dataProduct.stac_properties.eo.map((band, idx) => ({
    label: band.name,
    value: idx + 1,
  }));

  return (
    <div>
      <HintText>Select Red, Green, and Blue Bands</HintText>
      <div className="flex flex-row gap-4">
        <SelectField name="exgRed" label="Red Band" options={bandOptions} />
        <SelectField name="exgGreen" label="Green Band" options={bandOptions} />
        <SelectField name="exgBlue" label="Blue Band" options={bandOptions} />
      </div>
    </div>
  );
};

const NDVIBandSelection = ({ dataProduct }: { dataProduct: DataProduct }) => {
  const bandOptions = dataProduct.stac_properties.eo.map((band, idx) => ({
    label: band.name,
    value: idx + 1,
  }));

  return (
    <div>
      <HintText>Select Red and Near-Infrared Bands</HintText>
      <div className="flex flex-row gap-4">
        <SelectField name="ndviRed" label="Red Band" options={bandOptions} />
        <SelectField name="ndviNIR" label="NIR Band" options={bandOptions} />
      </div>
    </div>
  );
};

const RGBTools = ({ dataProduct }: { dataProduct: DataProduct }) => {
  const { values } = useFormikContext<ToolboxFields>();

  return (
    <ul>
      <li>
        <div className="flex flex-col gap-4">
          <div className="flex items-center">
            <Field id="exg-checkbox" type="checkbox" name="exg" />
            <label
              htmlFor="exg-checkbox"
              className="ms-2 text-sm font-medium text-gray-900"
            >
              Excess Green Vegetation Index (ExG)
            </label>
          </div>
          {values.exg ? <EXGBandSelection dataProduct={dataProduct} /> : null}
        </div>
      </li>
    </ul>
  );
};

const MultiSpectralTools = ({ dataProduct }: { dataProduct: DataProduct }) => {
  const { values } = useFormikContext<ToolboxFields>();

  return (
    <ul>
      <li>
        <div className="flex flex-col gap-4">
          <div className="flex items-center">
            <Field id="nvdi-checkbox" type="checkbox" name="ndvi" />
            <label
              htmlFor="nvdi-checkbox"
              className="ms-2 text-sm font-medium text-gray-900"
            >
              Normalized Difference Vegetation Index (NDVI)
            </label>
          </div>
          {values.ndvi ? <NDVIBandSelection dataProduct={dataProduct} /> : null}
        </div>
      </li>
    </ul>
  );
};

const LidarTools = () => {
  return (
    <ul>
      <li>
        <div className="flex flex-col gap-4">
          <div className="flex items-center">
            <Field id="chm-checkbox" type="checkbox" name="chm" disabled />
            <label
              htmlFor="chm-checkbox"
              className="ms-2 text-sm font-medium text-gray-900"
            >
              Canopy Height Model (CHM) <span className="italic">Coming soon</span>
            </label>
          </div>
        </div>
      </li>
    </ul>
  );
};

const ZonalStatisticTools = () => {
  const { values } = useFormikContext<ToolboxFields>();
  const { mapLayers } = useProjectContext();

  return (
    <ul>
      <li>
        <div className="flex flex-col gap-4">
          <div className="flex items-center">
            <Field id="zonal" type="checkbox" name="zonal" />
            <label htmlFor="zonal" className="ms-2 text-sm font-medium text-gray-900">
              Zonal Statistics
            </label>
          </div>
          {values.zonal && (
            <div>
              <span className="text-sm">Select Layer with Zonal Features:</span>
              {mapLayers &&
                prepMapLayers(mapLayers)
                  .filter(
                    ({ geomType }) =>
                      geomType.toLowerCase() === 'polygon' ||
                      geomType.toLowerCase() === 'multipolyon'
                  )
                  .map((layer) => (
                    <label
                      key={layer.id}
                      className="block text-sm text-gray-600 font-bold pb-1"
                    >
                      <Field type="radio" name="zonal_layer_id" value={layer.id} />
                      <span className="ml-2">{layer.name}</span>
                    </label>
                  ))}
            </div>
          )}
        </div>
      </li>
    </ul>
  );
};

export { RGBTools, MultiSpectralTools, LidarTools, ZonalStatisticTools };
