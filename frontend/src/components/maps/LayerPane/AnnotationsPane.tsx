import { Button } from '../../Buttons';

import { useAnnotationContext } from '../contexts/AnnotationContext';

const AnnotationInstructions = () => (
  <p className="mt-2 text-sm text-gray-500">
    Use the draw tools in the top left corner of the map to create an
    annotation.
  </p>
);

export default function AnnotationsPane() {
  const { active, toggle } = useAnnotationContext();

  return (
    <fieldset className="border border-solid border-slate-300 p-2">
      <legend className="block text-sm text-gray-400 font-semibold pt-1 pb-1">
        Annotations
      </legend>
      <Button size="sm" onClick={toggle} icon="plus">
        {active ? 'Exit Annotation' : 'Start Annotation'}
      </Button>
      {active && <AnnotationInstructions />}
    </fieldset>
  );
}
