import js from '@eslint/js';
import tseslint from '@typescript-eslint/eslint-plugin';

import eslintConfigPrettier from 'eslint-config-prettier';
import importPlugin from 'eslint-plugin-import';
import pluginPromise from 'eslint-plugin-promise';
import pluginReact from 'eslint-plugin-react';
import pluginReactHooks from 'eslint-plugin-react-hooks';
import globals from 'globals';

export default [
  {
    files: ['**/*.{js,mjs,cjs,ts,jsx,tsx}'],
    ignores: ['node_modules/*'],
  },
  {
    languageOptions: {
      parser: tseslint.parser,
      parserOptions: {
        project: ['./tsconfig.json'],
        tsconfigRootDir: '.',
        ecmaFeatures: {
          jsx: true,
        },
      },
      ecmaVersion: 'latest',
      globals: { ...globals.browser, ...globals.node },
    },
  },
  {
    settings: {
      react: {
        version: 'detect',
      },
    },
  },
  // Core ESLint recommended rules
  js.configs.recommended,

  // Import plugin rules for better import/export handling
  importPlugin.flatConfigs.recommended,

  // TypeScript-ESLint recommended rules
  tseslint.configs.recommended,

  // Promises best practices
  pluginPromise.configs['flat/recommended'],

  // React best practices and JSX runtime uses
  pluginReact.configs.flat.recommended,
  pluginReact.configs.flat['jsx-runtime'],

  // React Hooks best practices
  pluginReactHooks.configs.recommended,

  // Prettier integration: ensures no conflict between Prettier and ESLint rules
  eslintConfigPrettier,

  {
    rules: {
      'no-unused-vars': 'off',
      'react/react-in-jsx-scope': 'off',
      'react-hooks/exhaustive-deps': 'off',
      'react/display-name': 'off',
      'react/prop-types': 'off',
      'newline-before-return': 'error',

      // TypeScript-ESLint specific rules
      '@typescript-eslint/no-unused-vars': 'warn',
      '@typescript-eslint/no-expressions': 'off',
      '@typescript-eslint/no-explicit-any': 'off',
      '@typescript-eslint/no-empty-interface': 'off',
      '@typescript-eslint/ban-ts-comment': 'off',

      // Import plugin specific rules
      'import/no-unresolved': 'off',
      'import/no-named-as-default': 'off',
      'import/named': 'off',
      'import/no-named-as-default-member': 'off',

      // React specific rules
      'react/no-unescaped-entities': 'off',
      'react/no-unknown-property': 'off',
    },
  },
];
