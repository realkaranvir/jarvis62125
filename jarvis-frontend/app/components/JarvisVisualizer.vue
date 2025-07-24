<script setup lang="ts">
import { BloomPmndrs, EffectComposerPmndrs, GlitchPmndrs, ScanlinePmndrs } from '@tresjs/post-processing'
import { TresCanvas, useRenderLoop } from '@tresjs/core'
import { OrbitControls } from '@tresjs/cientos'
import { shallowRef } from 'vue'
import { Vector2, NoToneMapping } from 'three'
import { Pane } from 'tweakpane'

const { onLoop } = useRenderLoop()

// Sphere Refs
const sphereRef = shallowRef();
const sphereSizeRef = shallowRef(2);
const sphereXPosRef = shallowRef(0);

// Constants
const glitchDelays = new Vector2(10, 100);
const glitchDurations = new Vector2(0.2, 0.4);

const state = reactive({
    red: 1.0,
    blue: 0.5,
    wireframe: true,
    radius: 0.85,
    intensity: 8.0,
    luminanceThreshold: 0.3,
    luminanceSmoothing: 0.3,
});

const customContainer = document.createElement("div");
document.body.appendChild(customContainer)

customContainer.classList.add('fixed', 'bottom-0', 'left-0', 'z-50');

const pane = new Pane({container: customContainer});

// Color
pane.addBinding(state, 'red', { min: 0.00, max: 1.00, step: 0.05 }).on('change', (ev) => {
    uniforms.uRed.value = ev.value
});
pane.addBinding(state, 'blue', { min: 0.00, max: 1.00, step: 0.05 }).on('change', (ev) => {
    uniforms.uBlue.value = ev.value
});

// Wireframe
pane.addBinding(state, 'wireframe');

// Bloom
const bloomSettings = pane.addFolder({
    title: 'Bloom',
    expanded: false
});
bloomSettings.addBinding(state, "radius", { min: 0.00, max: 1.00, step: 0.05 });
bloomSettings.addBinding(state, "intensity", { min: 0.00, max: 10.00, step: 1.00 });
bloomSettings.addBinding(state, "luminanceThreshold", { min: 0.00, max: 1.00, step: 0.10 });
bloomSettings.addBinding(state, "luminanceSmoothing", { min: 0.00, max: 1.00, step: 0.10 });

let targetSphereSize = 2
let currentSphereSizeVelocity = 0;

window.addEventListener("va-start", () => {
    targetSphereSize = 3;
});
window.addEventListener("va-stop", () => {
    targetSphereSize = 2;
});

let targetSphereXPos = 0;
let currentXVelocity = 0;

window.addEventListener("chat-non-empty", () => {
    targetSphereXPos = -6;
});

window.addEventListener("chat-empty", () => {
    targetSphereXPos = 0;
});

// Angular velocity and acceleration
const rotationVelocity = ref({ x: 0, y: 0, z: 0 })
const rotationAcceleration = ref({ x: 0, y: 0, z: 0 })

onLoop(({ delta }) => {
    // Add small random accelerations
    rotationAcceleration.value.x += (Math.random() - 0.5) * 0.0002
    rotationAcceleration.value.y += (Math.random() - 0.5) * 0.0002
    rotationAcceleration.value.z += (Math.random() - 0.5) * 0.0002

    // Clamp acceleration to prevent spiraling out of control
    rotationAcceleration.value.x = Math.max(-0.01, Math.min(0.01, rotationAcceleration.value.x))
    rotationAcceleration.value.y = Math.max(-0.01, Math.min(0.01, rotationAcceleration.value.y))
    rotationAcceleration.value.z = Math.max(-0.01, Math.min(0.01, rotationAcceleration.value.z))

    // Apply acceleration to velocity
    rotationVelocity.value.x += rotationAcceleration.value.x
    rotationVelocity.value.y += rotationAcceleration.value.y
    rotationVelocity.value.z += rotationAcceleration.value.z

    // Dampen the velocity a bit for smoothness
    rotationVelocity.value.x *= 0.98
    rotationVelocity.value.y *= 0.98
    rotationVelocity.value.z *= 0.98

    // Rotate the sphere
    if (sphereRef.value) {
        sphereRef.value.rotation.x += rotationVelocity.value.x * delta
        sphereRef.value.rotation.y += rotationVelocity.value.y * delta
        sphereRef.value.rotation.z += rotationVelocity.value.z * delta
    }

    // Sphere scaling
    const stiffness = 20
    const damping = 5
    const currentSize = sphereSizeRef.value
    const displacement = targetSphereSize - currentSize
    const springForce = displacement * stiffness
    const dampingForce = -currentSphereSizeVelocity * damping

    const acceleration = springForce + dampingForce
    currentSphereSizeVelocity += acceleration * delta
    sphereSizeRef.value += currentSphereSizeVelocity * delta

    // Sphere position
    // Sphere X Position Spring
    const xStiffness = 20;
    const xDamping = 5;
    const xDisplacement = targetSphereXPos - sphereXPosRef.value;
    const xSpringForce = xDisplacement * xStiffness;
    const xDampingForce = -currentXVelocity * xDamping;

    const xAcceleration = xSpringForce + xDampingForce;
    currentXVelocity += xAcceleration * delta;
    sphereXPosRef.value += currentXVelocity * delta;

    if (sphereRef.value) {
        sphereRef.value.position.x = sphereXPosRef.value;
    }
})

const uniforms = {
    uTime: { value: 0 },
    uAmplitude: { value: new Vector2(0.1, 0.1) },
    uFrequency: { value: new Vector2(20, 5) },
    uRed: { value: state.red },
    uBlue: { value: state.blue },
}

const vertexShader = `
uniform vec2 uAmplitude;
uniform vec2 uFrequency;
uniform float uTime;

varying vec2 vUv;

void main() {
    vec4 modelPosition = modelMatrix * vec4(position, 1.0);
    modelPosition.y += sin(modelPosition.x * uFrequency.x - uTime) * uAmplitude.x;
    modelPosition.x += cos(modelPosition.y * uFrequency.y - uTime) * uAmplitude.y;

    vec4 viewPosition = viewMatrix * modelPosition;
    gl_Position = projectionMatrix * viewPosition;
    vUv = uv;
}
`

const fragmentShader = `
precision mediump float;
varying vec2 vUv;
uniform float uRed;
uniform float uBlue;

void main() {
    gl_FragColor = vec4(uRed, vUv.y, uBlue, 1.0);
}
`

</script>

<template>
    <TresCanvas clear-color="#000000" :tone-mapping="NoToneMapping">
        <TresPerspectiveCamera :position="[5, 0, 7]" />
        <OrbitControls />

        <!-- Wireframe Sphere -->
        <TresMesh :position="[0, 0, 0]" ref="sphereRef">
        <TresSphereGeometry :args="[sphereSizeRef, 32, 32]" />
        <TresShaderMaterial :vertex-shader="vertexShader" :fragment-shader="fragmentShader" :uniforms="uniforms" :wireframe="state.wireframe" />
        </TresMesh>
        <Suspense>
            <EffectComposerPmndrs>
                <BloomPmndrs
                    :radius="state.radius"
                    :intensity="state.intensity"
                    :luminance-threshold="state.luminanceThreshold"
                    :luminance-smoothing="state.luminanceSmoothing"
                    mipmap-blur
                />
                <GlitchPmndrs 
                    :delay="glitchDelays"
                    :duration="glitchDurations"
                />
            </EffectComposerPmndrs>
        </Suspense>
    </TresCanvas>
</template>