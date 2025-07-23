<script setup lang="ts">
import { TresCanvas, useRenderLoop } from '@tresjs/core'
import { OrbitControls } from '@tresjs/cientos'
import { shallowRef } from 'vue'
import { Vector2 } from 'three'

const { onLoop } = useRenderLoop()

const sphereRef = shallowRef();
const jarvisSpeakingRef = shallowRef(false);
const sphereSizeRef = shallowRef(1.5);

let targetSphereSize = 1.5
let currentSphereSizeVelocity = 0;

window.addEventListener("va-start", () => {
    jarvisSpeakingRef.value = true;
    targetSphereSize = 3;
});
window.addEventListener("va-stop", () => {
    jarvisSpeakingRef.value = false;
    targetSphereSize = 1.5;
});

// Angular velocity and acceleration
const rotationVelocity = ref({ x: 0, y: 0 })
const rotationAcceleration = ref({ x: 0, y: 0 })

onLoop(({ delta }) => {
    // Add small random accelerations
    rotationAcceleration.value.x += (Math.random() - 0.5) * 0.0002
    rotationAcceleration.value.y += (Math.random() - 0.5) * 0.0002

    // Clamp acceleration to prevent spiraling out of control
    rotationAcceleration.value.x = Math.max(-0.01, Math.min(0.01, rotationAcceleration.value.x))
    rotationAcceleration.value.y = Math.max(-0.01, Math.min(0.01, rotationAcceleration.value.y))

    // Apply acceleration to velocity
    rotationVelocity.value.x += rotationAcceleration.value.x
    rotationVelocity.value.y += rotationAcceleration.value.y

    // Dampen the velocity a bit for smoothness
    rotationVelocity.value.x *= 0.98
    rotationVelocity.value.y *= 0.98

    // Rotate the sphere
    if (sphereRef.value) {
        sphereRef.value.rotation.x += rotationVelocity.value.x * delta
        sphereRef.value.rotation.y += rotationVelocity.value.y * delta
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
})

const uniforms = {
    uTime: { value: 0 },
    uAmplitude: { value: new Vector2(0.1, 0.1) },
    uFrequency: { value: new Vector2(20, 5) },
}

const fragmentShader = `
precision mediump float;
varying vec2 vUv;

void main() {
    gl_FragColor = vec4(1.0, vUv.y, 0.5, 1.0);
}
`

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

</script>

<template>
    <TresCanvas clear-color="#000000" render-mode="on-demand">
        <TresPerspectiveCamera :position="[5, 5, 5]" />
        <OrbitControls />

        <!-- Wireframe Sphere -->
        <TresMesh :position="[0, 0, 0]" ref="sphereRef">
        <TresSphereGeometry :args="[sphereSizeRef, 32, 32]" />
        <TresShaderMaterial :vertex-shader="vertexShader" :fragment-shader="fragmentShader" :uniforms="uniforms" :wireframe="true" />
        </TresMesh>
    </TresCanvas>
</template>

<style>
</style>  