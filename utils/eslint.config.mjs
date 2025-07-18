// eslint.config.js
export default [
    {
      files: ["**/*.js"],
      languageOptions: {
        ecmaVersion: "latest",
        sourceType: "module"
      },
      rules: {
        semi: "error",
        quotes: ["error", "double"],
        "no-unused-vars": "warn",
        "no-console": "off"
      }
    }
  ];
  