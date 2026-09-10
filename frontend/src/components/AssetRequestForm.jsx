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
            Requester email <span aria-hidden="true">*</span>
          </label>
          <input
            {...fieldProps('requester_email')}
            type="email"
            autoComplete="email"
            maxLength={254}
            required
            placeholder="you@company.com"
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
          <h2>What do you need?</h2>
          <p>Choose your asset and tell us how it will help.</p>
        </div>
      </div>
      <div className="field">
        <label htmlFor="asset_type">
          Asset type <span aria-hidden="true">*</span>
        </label>
        <select {...fieldProps('asset_type')} required>
          <option value="">Select an asset</option>
          {ASSET_TYPES.map((asset) => (
            <option key={asset}>{asset}</option>
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
          rows={5}
          maxLength={1000}
          required
          placeholder="Tell us why you need this asset, including any issue with your current equipment."
        />
        <div className="field-hint">
          <span>
            {errors.reason ? (
              <span className="field-error" id="reason-error">
                {errors.reason}
              </span>
            ) : (
              'A little context helps IT understand your request. Minimum 10 meaningful characters.'
            )}
          </span>
          <span>
            {meaningfulCharacterCount(values.reason)} meaningful · {values.reason.length}/1000 total
          </span>
        </div>
      </div>
      {error && (
        <div className="notice error" role="alert">
          {error}
        </div>
      )}
      <div className="form-footer">
        <span>All fields are required.</span>
        <button className="button primary" disabled={submitting}>
          {submitting ? 'Saving your request…' : 'Submit IT Asset Request'}{' '}
          <span aria-hidden="true">↗</span>
        </button>
      </div>
    </form>
  );
}
