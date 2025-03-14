import React from "react";

const InputField = ({
  label,
  type,
  value,
  onChange,
  required,
  name,
  showPassword,
  onTogglePassword,
}) => {
  const isPasswordField = [
    "password",
    "newPassword",
    "confirmPassword",
  ].includes(name);

  const getAutoCompleteValue = () => {
    switch (name) {
      case "email":
        return "email";
      case "username":
        return "username";
      case "password":
        return "current-password";
      case "newPassword":
      case "confirmPassword":
        return "new-password";
      default:
        return "off";
    }
  };

  return (
    <div className="mb-4 relative">
      <label
        htmlFor={name}
        className="block text-gray-600 dark:text-gray-300 font-medium mb-2"
      >
        {label} <span className="text-red-600">*</span>
      </label>

      <input
        id={name}
        type={type}
        name={name}
        value={value}
        onChange={onChange}
        required={required}
        autoComplete={getAutoCompleteValue()}
        className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400"
      />

      {isPasswordField && (
        <button
          type="button"
          className="absolute cursor-pointer right-3 top-[70%] transform -translate-y-1/2 text-gray-500 dark:text-gray-300"
          onClick={onTogglePassword}
        >
          {showPassword ? "Hide" : "Show"}
        </button>
      )}
    </div>
  );
};

export default InputField;
