type BlendingModeType = 'average' | 'disabled' | 'min' | 'max' | 'mosaic';
type CameraType = 'single' | 'multi';
type QualityType = 'low' | 'medium' | 'high';

export interface MetashapeSettings {
  alignQuality: QualityType;
  backend: 'metashape';
  blendingMode: BlendingModeType;
  buildDepthQuality: QualityType;
  camera: CameraType;
  cullFaces: boolean;
  disclaimer: boolean;
  exportDEM: boolean;
  exportDEMResolution: number;
  exportOrtho: boolean;
  exportOrthoResolution: number;
  exportPointCloud: boolean;
  fillHoles: boolean;
  ghostingFilter: boolean;
  keyPoint: number;
  refineSeamlines: boolean;
  resolution: number;
  tiePoint: number;
}

type PCQualityType = 'lowest' | 'low' | 'medium' | 'high' | 'ultra';

export interface ODMSettings {
  backend: 'odm';
  disclaimer: boolean;
  orthoResolution: number;
  pcQuality: PCQualityType;
}

export type ImageProcessingJobProps = {
  initialCheck: boolean;
  jobId: string;
  progress: number;
  rawDataId: string;
};

export type RawDataProps = {
  id: string;
  status: string;
  original_filename: string;
  report?: string;
  url: string;
};

export type RawDataImageProcessingFormProps = {
  onSubmitJob: (settings: MetashapeSettings | ODMSettings) => void;
  toggleModal: () => void;
};
