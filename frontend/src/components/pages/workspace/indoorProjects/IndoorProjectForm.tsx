import { AxiosResponse, isAxiosError } from 'axios';
import React, { useEffect, useState } from 'react';
import { FormProvider, SubmitHandler, useForm } from 'react-hook-form';
import { useNavigate } from 'react-router-dom';
import * as Yup from 'yup';
import { yupResolver } from '@hookform/resolvers/yup';

import api from '../../../../api';
import Alert, { Status } from '../../../Alert';
import { Button } from '../../../Buttons';
import { InputField } from '../../../FormFields';

import { IndoorProjectAPIResponse } from './IndoorProject';

export type IndoorProjectFormInput = {
  title: string;
  description: string;
  startDate?: Date | string;
  endDate?: Date | string;
};

const defaultValues = {
  title: '',
  description: '',
  startDate: undefined,
  endDate: undefined,
};

export const validationSchema = Yup.object({
  title: Yup.string()
    .max(255, 'Must be less than 255 characters')
    .required('Title is required'),
  description: Yup.string()
    .max(300, 'Must be less than 300 characters')
    .required('Description is required'),
  startDate: Yup.mixed<Date | string>()
    .transform((value, originalValue) =>
      originalValue === '' ? undefined : value
    )
    .test('date-max', 'Start date must be before end date', function (value) {
      const { endDate } = this.parent;
      if (!value || !endDate) return true;
      const startDateObj = typeof value === 'string' ? new Date(value) : value;
      const endDateObj =
        typeof endDate === 'string' ? new Date(endDate) : endDate;
      return startDateObj <= endDateObj;
    })
    .optional(),
  endDate: Yup.mixed<Date | string>()
    .transform((value, originalValue) =>
      originalValue === '' ? undefined : value
    )
    .test('date-min', 'End date must be after start date', function (value) {
      const { startDate } = this.parent;
      if (!value || !startDate) return true;
      const endDateObj = typeof value === 'string' ? new Date(value) : value;
      const startDateObj =
        typeof startDate === 'string' ? new Date(startDate) : startDate;
      return endDateObj >= startDateObj;
    })
    .optional(),
});

export default function IndoorProjectForm({
  setModalOpen,
}: {
  setModalOpen: React.Dispatch<React.SetStateAction<boolean>>;
}) {
  const [status, setStatus] = useState<Status | null>(null);

  const navigate = useNavigate();

  const methods = useForm<IndoorProjectFormInput>({
    defaultValues,
    resolver: yupResolver(validationSchema),
    mode: 'onChange',
    reValidateMode: 'onChange',
  });

  const {
    formState: { isSubmitting },
    reset,
    handleSubmit,
    trigger,
  } = methods;

  const onSubmit: SubmitHandler<IndoorProjectFormInput> = async (values) => {
    try {
      const { title, description, startDate, endDate } = values;
      const payload = {
        title,
        description,
        start_date: startDate,
        end_date: endDate,
      };

      const response: AxiosResponse<IndoorProjectAPIResponse> = await api.post(
        `/indoor_projects`,
        payload
      );

      if (response && response.status == 201) {
        navigate(`/indoor_projects/${response.data.id}`);
        setModalOpen(false);
      } else {
        setStatus({ type: 'error', msg: 'Unable to create indoor project' });
      }
    } catch (err) {
      if (isAxiosError(err)) {
        setStatus({
          type: 'error',
          msg: err.response?.data.detail || 'Unable to create indoor project',
        });
      } else {
        setStatus({ type: 'error', msg: 'Unable to create indoor project' });
      }
    }
  };

  useEffect(() => {
    reset();
  }, []);

  return (
    <div className="my-8 mx-4">
      <div className="mx-4 my-2">
        <h1>New Indoor Project</h1>
        <FormProvider {...methods}>
          <form
            className="flex flex-col gap-4"
            onSubmit={handleSubmit(onSubmit)}
          >
            <InputField label="Title" name="title" />
            <InputField label="Description" name="description" />
            <InputField
              type="date"
              label="Start date"
              name="startDate"
              onChange={() => setTimeout(() => trigger('endDate'), 0)}
            />
            <InputField
              type="date"
              label="End date"
              name="endDate"
              onChange={() => setTimeout(() => trigger('startDate'), 0)}
            />
            <div className="mt-4 flex flex-col gap-2">
              <Button type="submit" disabled={isSubmitting}>
                {!isSubmitting ? 'Create' : 'Creating...'}
              </Button>
              {status && status.type && status.msg && (
                <Alert alertType={status.type}>{status.msg}</Alert>
              )}
            </div>
          </form>
        </FormProvider>
      </div>
    </div>
  );
}
