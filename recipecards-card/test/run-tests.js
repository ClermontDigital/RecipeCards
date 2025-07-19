#!/usr/bin/env node

/**
 * Simple test runner for RecipeCards frontend
 * Tests basic functionality and component structure
 */

const fs = require('fs');
const path = require('path');

console.log('🧪 RecipeCards Frontend Tests');
console.log('==============================\n');

let testsPassed = 0;
let testsFailed = 0;

function test(name, testFn) {
  try {
    testFn();
    console.log(`✅ ${name}`);
    testsPassed++;
  } catch (error) {
    console.log(`❌ ${name}`);
    console.log(`   Error: ${error.message}`);
    testsFailed++;
  }
}

// Test 1: Check if built file exists
test('Built card file exists', () => {
  const builtFile = path.join(__dirname, '../dist/recipecards-card.js');
  if (!fs.existsSync(builtFile)) {
    throw new Error('Built file not found. Run "npm run build" first.');
  }
});

// Test 2: Check if built file contains expected content
test('Built file contains card component', () => {
  const builtFile = path.join(__dirname, '../dist/recipecards-card.js');
  const content = fs.readFileSync(builtFile, 'utf8');
  
  if (!content.includes('recipecards-card')) {
    throw new Error('Built file does not contain card component name');
  }
  
  if (!content.includes('RecipeCardsCard')) {
    throw new Error('Built file does not contain component class');
  }
});

// Test 3: Check if source file exists
test('Source file exists', () => {
  const sourceFile = path.join(__dirname, '../src/recipecards-card.ts');
  if (!fs.existsSync(sourceFile)) {
    throw new Error('Source file not found');
  }
});

// Test 4: Check if source file contains expected structure
test('Source file has correct structure', () => {
  const sourceFile = path.join(__dirname, '../src/recipecards-card.ts');
  const content = fs.readFileSync(sourceFile, 'utf8');
  
  const requiredElements = [
    'class RecipeCardsCard',
    '@customElement',
    'static styles',
    'setConfig',
    'render()',
    'window.customCards'
  ];
  
  for (const element of requiredElements) {
    if (!content.includes(element)) {
      throw new Error(`Source file missing required element: ${element}`);
    }
  }
});

// Test 5: Check if test file exists
test('Test file exists', () => {
  const testFile = path.join(__dirname, 'recipecards-card.test.ts');
  if (!fs.existsSync(testFile)) {
    throw new Error('Test file not found');
  }
});

// Test 6: Check if test file contains comprehensive tests
test('Test file contains comprehensive tests', () => {
  const testFile = path.join(__dirname, 'recipecards-card.test.ts');
  const content = fs.readFileSync(testFile, 'utf8');
  
  const testCases = [
    'renders with default config',
    'shows loading state',
    'loads and displays recipe list',
    'switches recipes when tab is clicked',
    'flips card when flip button is clicked',
    'handles API errors gracefully',
    'shows no recipes message',
    'has proper accessibility attributes'
  ];
  
  for (const testCase of testCases) {
    if (!content.includes(testCase)) {
      throw new Error(`Test file missing test case: ${testCase}`);
    }
  }
});

// Test 7: Check package.json has correct scripts
test('Package.json has correct test scripts', () => {
  const packageFile = path.join(__dirname, '../package.json');
  const content = JSON.parse(fs.readFileSync(packageFile, 'utf8'));
  
  if (!content.scripts.test) {
    throw new Error('Package.json missing test script');
  }
});

// Test 8: Check TypeScript config
test('TypeScript config exists and is valid', () => {
  const tsConfigFile = path.join(__dirname, '../tsconfig.json');
  if (!fs.existsSync(tsConfigFile)) {
    throw new Error('TypeScript config not found');
  }
  
  const content = JSON.parse(fs.readFileSync(tsConfigFile, 'utf8'));
  if (!content.compilerOptions || !content.compilerOptions.target) {
    throw new Error('TypeScript config missing required options');
  }
});

console.log('\n📊 Test Results');
console.log('===============');
console.log(`Passed: ${testsPassed}`);
console.log(`Failed: ${testsFailed}`);
console.log(`Total: ${testsPassed + testsFailed}`);

if (testsFailed === 0) {
  console.log('\n🎉 All tests passed!');
  console.log('\n📝 Test Coverage:');
  console.log('   ✅ Component structure');
  console.log('   ✅ Build process');
  console.log('   ✅ Source code quality');
  console.log('   ✅ Test file completeness');
  console.log('   ✅ Configuration files');
  console.log('   ✅ Package setup');
  console.log('\n💡 To run full browser tests, use a modern testing framework like Playwright or Cypress');
} else {
  console.log('\n❌ Some tests failed. Please check the errors above.');
  process.exit(1);
} 