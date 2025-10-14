import React, { createContext, useContext, useMemo, useReducer } from 'react';

type State = { active: boolean };

type Action = 
  | { type: 'ACTIVATE' }
  | { type: 'DEACTIVATE' }
  | { type: 'TOGGLE' };

function reducer(state: State, action: Action): State {
  switch (action.type) {
    case 'ACTIVATE':
      return { active: true };
    case 'DEACTIVATE':
      return { active: false };
    case 'TOGGLE':
      return { active: !state.active };
    default:
      return state;
  }
}

type Ctx = {
  active: boolean;
  activate: () => void;
  deactivate: () => void;
  toggle: () => void;
};

const AnnotationContext = createContext<Ctx | null>(null);

export function AnnotationProvider({ children }: {children: React.ReactNode }) {
  const [state, dispatch ] = useReducer(reducer, { active: false });

  const value = useMemo<Ctx>(
    () => ({
      active: state.active,
      activate: () => dispatch({ type: 'ACTIVATE' }),
      deactivate: () => dispatch({ type: 'DEACTIVATE' }),
      toggle: () => dispatch({ type: 'TOGGLE' }),
    }),
  [state.active]);

  return (
    <AnnotationContext.Provider value={value}>
      {children}
    </AnnotationContext.Provider>
  );
}

export function useAnnotationContext() {
  const ctx = useContext(AnnotationContext);
  if (!ctx) throw new Error('useAnnotationContext must be used within AnnotationProvider');
  return ctx;
}