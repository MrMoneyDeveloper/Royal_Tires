import { useRef, useState } from 'react';
import {
  ASSET_TYPES,
  meaningfulCharacterCount,
  validateRequest,
} from '../helpers/validation.js';

const initialValues = {
  requester_name: '',
  requester_email: '',
  asset_type: '',
  reason: '',
};

export default function AssetRequestForm({ onSubmit, submitting, error }) {
  const [values, setValues] = useState(initialValues);
  const [errors, setErrors] = useState({});
  const form = useRef(null);

  function change(event) {
    const { name, value } = event.target;
    setValues((current) => ({ ...current, [name]: value }));
    setErrors((current) => ({ ...current, [name]: undefined }));
  }

  function submit(event) {
    event.preventDefault();
    if (submitting) return;
    const nextErrors = validateRequest(values);
    setErrors(nextErrors);
    if (Object.keys(nextErrors).length) {
      form.current.elements[Object.keys(nextErrors)[0]].focus();
      return;
    }
    onSubmit(
      Object.fromEntries(
        Object.entries(values).map(([key, value]) => [key, value.trim()]),
      ),
    );
  }

  function fieldProps(name) {
    return {
      id: name,
      name,
      value: values[name],
      onChange: change,
      'aria-invalid': Boolean(errors[name]),
      'aria-describedby': errors[name] ? `${name}-error` : undefined,
    };
  }

  return (
    <form ref={form} onSubmit={submit} noValidate>
      <div className="section-title">
        <span className="step">01</span>
        <div>
          <h2>Your details</h2>
          <p>Let the IT team know who the equipment is for.</p>
        </div>
      </div>
      <div className="field-grid">
        <div className="field">
          <label htmlFor="requester_name">
            Requester name <span aria-hidden="true">*</span>
          </label>
          <input
            {...fieldProps('requester_name')}
            autoComplete="name"
            maxLength={100}
            required
            placeholder="Your full name"
          />
          {errors.requester_name && (
            <p className="field-error" id="requester_name-error">
              {errors.requester_name}
            </p>
          )}
        </div>
        <div className="field">
          <label htmlFor="requester_email">
            Email address <span aria-hidden="true">*</span>
          </label>
          <input
            {...fieldProps('requester_email')}
            type="email"
            autoComplete="email"
            maxLength={254}
            required
            placeholder="name@royaltyres.co.za"
          />
          {errors.requester_email && (
            <p className="field-error" id="requester_email-error">
              {errors.requester_email}
            </p>
          )}
        </div>
      </div>

      <div className="section-title separated">
        <span className="step">02</span>
        <div>
          <h2>Equipment request</h2>
          <p>Choose the asset and tell IT why it is needed.</p>
        </div>
      </div>
      <div className="field">
        <label htmlFor="asset_type">
          Asset type <span aria-hidden="true">*</span>
        </label>
        <select {...fieldProps('asset_type')} required>
          <option value="">Choose an asset</option>
          {ASSET_TYPES.map((asset) => (
            <option key={asset} value={asset}>
              {asset}
            </option>
          ))}
        </select>
        {errors.asset_type && (
          <p className="field-error" id="asset_type-error">
            {errors.asset_type}
          </p>
        )}
      </div>
      <div className="field">
        <label htmlFor="reason">
          Business reason <span aria-hidden="true">*</span>
        </label>
        <textarea
          {...fieldProps('reason')}
          maxLength={1000}
          required
          placeholder="Explain what the equipment is needed for and any urgency."
        />
        <div className="field-hint">
          <span>Minimum 10 non-whitespace characters</span>
          <span>{meaningfulCharacterCount(values.reason)}/10 meaningful</span>
        </div>
        {errors.reason && (
          <p className="field-error" id="reason-error">
            {errors.reason}
          </p>
        )}
      </div>

      {error && (
        <p className="notice error" role="alert">
          {error}
        </p>
      )}
      <div className="form-footer">
        <span>Required fields are marked *</span>
        <button type="submit" className="button primary" disabled={submitting}>
          {submitting ? 'Submitting…' : 'Submit request'}{' '}
          <span aria-hidden="true">→</span>
        </button>
      </div>
    </form>
  );
}
