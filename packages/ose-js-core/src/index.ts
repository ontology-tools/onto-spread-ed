/**
 * @ontospreaded/js-core - Core TypeScript library for OntoSpreadEd
 * 
 * This package contains shared types, models, and utilities
 * used by the OntoSpreadEd web application and plugins.
 */

import ProgressIndicator from './release/ProgressIndicator.vue';

// Models and Types
export * from './model';
export * from './types';
export * from './diagnostic-data';
export * from './constants';

// Utilities
export * from './debounce';
export * from './filter';
export * from './messages';

// Components
export { ProgressIndicator };
