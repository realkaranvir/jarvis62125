<!-- components/SettingsPanel.vue -->
<template>
  <div class="flex flex-col gap-2 w-full max-w-64">
    <!-- Toggle Mic -->
    <UButton 
      :icon="micMuted ? 'i-lucide-mic-off' : 'i-lucide-mic'" 
      size="md" 
      color="primary" 
      variant="solid" 
      class="flex items-center justify-center"
      @click="micMuted = !micMuted" 
    />

    <!-- Toggle Speaker -->
    <UButton 
      :icon="speakerMuted ? 'i-lucide-volume-x' : 'i-lucide-volume-2'" 
      size="md" 
      color="primary" 
      variant="solid" 
      class="flex items-center justify-center"
      @click="speakerMuted = !speakerMuted" 
    />

    <!-- Select LLM -->
    <p>LLM</p>
    <USelect
      v-model="llm"
      :items="llmOptions"
      label="LLM Provider"
    />

    <!-- Select TTS Engine -->
    <p>TTS Engine</p>
    <USelect
      v-model="ttsEngine"
      :items="ttsOptions"
      label="TTS Engine"
    />

    <!-- Select TTS Voice -->
    <p>TTS Voice</p>
    <USelect
      v-model="ttsVoice"
      :items="voiceOptions"
      label="Voice"
    />

     <!-- Set Assistant Name -->
    <p>Assistant Name</p>
    <UInput
      v-model="assistantName"
      label="Assistant Name"
    />

    <!-- Set TTS Speed -->
    <p>TTS Speed</p>
    <UInputNumber
      v-model="ttsSpeed"
      :step=0.1
      :format-options="{
        style: 'percent'
      }"
      :max=2.0
      :min=0.1
    />

    <!-- Set Call Name Interval -->
    <p>Say Name Interval</p>
    <p class="text-xs">Seconds before you must say the assistant's name</p>
    <UInputNumber
      v-model="callNameInterval"
      :step=5
      :max=60
      :min=0
    />
  </div>
</template>

<script setup>
const {
  llm,
  ttsEngine,
  ttsVoice,
  ttsSpeed,
  assistantName,
  callNameInterval,
  micMuted,
  speakerMuted
} = useConfig()

const llmOptions = ['claude', 'ollama']
const ttsOptions = ['server', 'local']
const voiceOptions = ['jarvis', 'GLaDOS', 'female']

</script>