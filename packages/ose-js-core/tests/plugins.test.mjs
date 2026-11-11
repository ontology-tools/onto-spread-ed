import {test} from 'node:test';
import assert from 'node:assert/strict';
import {definePlugin, PLUGIN_API_VERSION, registry, setupPlugin} from '../dist/index.js';

test('plugin identity, context, override order and warnings', async () => {
    const original = {render() {}};
    const replacement = {render() {}};
    const plugin = {apiVersion: PLUGIN_API_VERSION, setup(ose) {
        assert.equal(ose.id, 'first');
        ose.release.addStageView('TEST_OVERRIDE', original);
    }};
    assert.equal(definePlugin(plugin), plugin);
    await setupPlugin('first', plugin);
    assert.equal(registry.stageView('TEST_OVERRIDE'), original);
    const warnings = [];
    const warn = console.warn;
    console.warn = message => warnings.push(message);
    try {
        await setupPlugin('second', definePlugin({apiVersion: 1, setup(ose) {
            ose.release.addStageView('TEST_OVERRIDE', replacement);
        }}));
    } finally {
        console.warn = warn;
    }
    assert.equal(registry.stageView('TEST_OVERRIDE'), replacement);
    assert.match(warnings[0], /first overridden by second/);
});

test('invalid versions and failed setup do not commit registrations', async () => {
    await assert.rejects(setupPlugin('invalid', {apiVersion: 2, setup() {
        assert.fail('setup must not run');
    }}), /Unsupported plugin API/);
    await assert.rejects(setupPlugin('broken', definePlugin({apiVersion: 1, async setup(ose) {
        ose.release.addStageView('TEST_ROLLBACK', {render() {}});
        throw new Error('broken setup');
    }})), /broken setup/);
    assert.equal(registry.stageView('TEST_ROLLBACK'), undefined);
    assert.equal(registry.stageView('UNKNOWN'), undefined);
});

test('stage view options are stored per registration and replaced by overrides', async () => {
    const view = {render() {}};
    assert.deepEqual(registry.stageViewOptions('TEST_OPTIONS'), {});
    await setupPlugin('options', definePlugin({apiVersion: 1, setup(ose) {
        ose.release.addStageView('TEST_OPTIONS', view, {showsDiagnostics: true});
        ose.release.addStageView('TEST_NO_OPTIONS', view);
    }}));
    assert.equal(registry.stageViewOptions('TEST_OPTIONS').showsDiagnostics, true);
    assert.deepEqual(registry.stageViewOptions('TEST_NO_OPTIONS'), {});

    const warn = console.warn;
    console.warn = () => {};
    try {
        await setupPlugin('options-override', definePlugin({apiVersion: 1, setup(ose) {
            ose.release.addStageView('TEST_OPTIONS', view);
        }}));
    } finally {
        console.warn = warn;
    }
    assert.deepEqual(registry.stageViewOptions('TEST_OPTIONS'), {});
});

test('stage view loaders remain lazy and resolve default exports', async () => {
    let loaded = false;
    const component = {render() {}};
    await setupPlugin('lazy', definePlugin({apiVersion: 1, setup(ose) {
        ose.release.addStageView('TEST_LAZY', async () => {
            loaded = true;
            return {default: component, [Symbol.toStringTag]: 'Module'};
        });
    }}));
    assert.equal(loaded, false);
    assert.equal(await registry.stageView('TEST_LAZY').__asyncLoader(), component);
    assert.equal(loaded, true);
});
