import ConnectForm from './ConnectForm';

export const styles = {
  error: 'mt-1 text-red-500 text-sm',
  label: 'block text-sm text-gray-400 font-bold pt-2 pb-1',
  inputText:
    'focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-none border border-gray-400 rounded py-1 pl-4 pr-8 block w-full appearance-none',
  inputTextArea: 'w-full h-48 resize-none rounded',
};

type InputField = {
  label: string;
  name: string;
  placeholder?: string;
  required?: boolean;
  type?: string;
};

interface InputSelectField extends InputField {
  options: {
    label: string;
    value: string;
  }[];
}

export function InputField({
  label,
  name,
  placeholder = '',
  required = true,
  type = 'text',
}: InputField) {
  return (
    <ConnectForm>
      {({ formState: { errors }, register }) => (
        <div>
          <label className={styles.label}>
            {label}
            {required && '*'}
          </label>
          <input
            className={styles.inputText}
            type={type}
            placeholder={placeholder}
            {...register(name)}
            aria-invalid={errors[name] ? 'true' : 'false'}
          />
          {errors[name] && (
            <p role="alert" className={styles.error}>
              {errors[name].message}
            </p>
          )}
        </div>
      )}
    </ConnectForm>
  );
}

export function SelectField({
  label,
  name,
  options,
  required = true,
}: InputSelectField) {
  return (
    <ConnectForm>
      {({ formState: { errors }, register }) => (
        <div>
          <label className={styles.label}>
            {label}
            {required && '*'}
          </label>
          <select
            className={styles.inputText}
            {...register(name)}
            aria-invalid={errors[name] ? 'true' : 'false'}
          >
            <option value="">Select an option...</option>
            {options.map((opt, i) => (
              <option key={i} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
          {errors[name] && (
            <p role="alert" className={styles.error}>
              {errors[name].message}
            </p>
          )}
        </div>
      )}
    </ConnectForm>
  );
}

export function TextAreaField({
  label,
  name,
  placeholder = '',
  required = true,
}: InputField) {
  return (
    <ConnectForm>
      {({ formState: { errors }, register }) => (
        <div>
          <label className={styles.label}>
            {label}
            {required && '*'}
          </label>
          <textarea
            className={styles.inputTextArea}
            placeholder={placeholder}
            {...register(name)}
            aria-invalid={errors[name] ? 'true' : 'false'}
          />
          {errors[name] && (
            <p role="alert" className={styles.error}>
              {errors[name].message}
            </p>
          )}
        </div>
      )}
    </ConnectForm>
  );
}
