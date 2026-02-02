import { isAxiosError } from 'axios';
import { useState } from 'react';
import { FormProvider, SubmitHandler, useForm } from 'react-hook-form';
import * as Yup from 'yup';
import { yupResolver } from '@hookform/resolvers/yup';
import { Feature } from 'geojson';

import Alert, { Status } from '../Alert';
import { Button, OutlineButton } from '../Buttons';
import { InputField, TextAreaField } from '../FormFields';
import Modal from '../Modal';

import api from '../../api';

type AnnotationFormData = {
  description: string;
  tags: string;
};

const validationSchema = Yup.object({
  description: Yup.string()
    .min(1, 'Description is required')
    .required('Description is required'),
  tags: Yup.string().optional().default(''),
});

const defaultValues: AnnotationFormData = {
  description: '',
  tags: '',
};

interface AnnotationCreateModalProps {
  open: boolean;
  setOpen: React.Dispatch<React.SetStateAction<boolean>>;
  feature: Feature | null;
  projectId: string;
  flightId: string;
  dataProductId: string;
  onSuccess: () => void;
  onCancel: () => void;
}

export default function AnnotationCreateModal({
  open,
  setOpen,
  feature,
  projectId,
  flightId,
  dataProductId,
  onSuccess,
  onCancel,
}: AnnotationCreateModalProps) {
  const [status, setStatus] = useState<Status | null>(null);

  const methods = useForm<AnnotationFormData>({
    defaultValues,
    resolver: yupResolver(validationSchema),
  });

  const {
    formState: { isSubmitting },
    handleSubmit,
    reset,
  } = methods;

  const onSubmit: SubmitHandler<AnnotationFormData> = async (values) => {
    if (!feature) return;
    setStatus(null);

    const tags = values.tags
      ? values.tags
          .split(',')
          .map((t) => t.trim())
          .filter(Boolean)
      : [];

    try {
      await api.post(
        `/projects/${projectId}/flights/${flightId}/data_products/${dataProductId}/annotations`,
        {
          description: values.description,
          geom: feature,
          tags,
        }
      );
      reset();
      setStatus(null);
      setOpen(false);
      onSuccess();
    } catch (err) {
      if (isAxiosError(err)) {
        setStatus({
          type: 'error',
          msg: err.response?.data.detail || 'Unable to create annotation',
        });
      } else {
        setStatus({ type: 'error', msg: 'Unable to create annotation' });
      }
    }
  };

  const handleCancel = () => {
    reset();
    setStatus(null);
    setOpen(false);
    onCancel();
  };

  return (
    <Modal open={open} setOpen={() => handleCancel()}>
      <div className="my-8 mx-4">
        <div className="mx-4 my-2">
          <h2 className="text-lg font-bold mb-4">New Annotation</h2>
          <FormProvider {...methods}>
            <form
              className="flex flex-col gap-4"
              onSubmit={handleSubmit(onSubmit)}
            >
              <TextAreaField
                label="Description"
                name="description"
                placeholder="Describe this annotation..."
                rows={4}
              />
              <InputField
                label="Tags"
                name="tags"
                required={false}
                placeholder="e.g. erosion, field-edge, note"
              />
              <div className="flex items-center justify-between mt-4">
                <div className="w-36">
                  <OutlineButton size="sm" type="button" onClick={handleCancel}>
                    Cancel
                  </OutlineButton>
                </div>
                <div className="w-36">
                  <Button type="submit" size="sm" disabled={isSubmitting}>
                    {isSubmitting ? 'Saving...' : 'Save'}
                  </Button>
                </div>
              </div>
              {status && status.type && status.msg && (
                <Alert alertType={status.type}>{status.msg}</Alert>
              )}
            </form>
          </FormProvider>
        </div>
      </div>
    </Modal>
  );
}