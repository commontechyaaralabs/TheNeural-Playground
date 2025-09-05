interface LanguageOption {
  value: string;
  label: string;
}

interface LanguageSelectorProps {
  className?: string;
  options?: LanguageOption[];
  defaultValue?: string;
  onChange?: (value: string) => void;
}

const defaultOptions: LanguageOption[] = [
  { value: 'en', label: 'EN' },
  { value: 'es', label: 'ES' },
  { value: 'fr', label: 'FR' }
];

export default function LanguageSelector({ 
  className = '', 
  options = defaultOptions,
  defaultValue = 'en',
  onChange
}: LanguageSelectorProps) {
  return (
    <select 
      className={`bg-transparent text-white border border-[#bc6cd3]/40 rounded px-2 py-1 text-sm focus:outline-none focus:border-[#dcfc84] ${className}`}
      defaultValue={defaultValue}
      onChange={(e) => onChange?.(e.target.value)}
    >
      {options.map((option) => (
        <option 
          key={option.value} 
          value={option.value} 
          className="bg-[#1c1c1c] text-white"
        >
          {option.label}
        </option>
      ))}
    </select>
  );
}
