import React from 'react';
import { Search } from 'lucide-react';
import { COUNTRIES } from '../data/countries';

const CountrySelect = ({ value, onChange, placeholder = "Select a country" }) => {
  return (
    <div className="country-select-wrapper">
      <div className="select-icon">
        <Search size={18} />
      </div>
      <select 
        value={value} 
        onChange={(e) => onChange(e.target.value)}
        className="country-select"
      >
        <option value="">{placeholder}</option>
        {COUNTRIES.map((country) => (
          <option key={country} value={country}>
            {country}
          </option>
        ))}
      </select>
    </div>
  );
};

export default CountrySelect;
