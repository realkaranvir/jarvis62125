<template>
  <UContainer class="flex justify-center p-4">
    <UDrawer>
      <UButton label="Settings" color="neutral" variant="subtle" trailing-icon="mdi-light:chevron-up" />
      <template #content>
        <UContainer class="flex justify-center items-center min-h-64">
          <UButton :icon="micOn ? 'mdi-light:microphone' : 'mdi-light:microphone-off'" color="neutral" size="xl" variant="ghost" @click="() => { toggleMic() }" />
          <UButton :icon="speakerOn ? 'mdi-light:volume' : 'mdi-light:volume-off'" color="neutral" size="xl" variant="ghost" @click="() => { toggleSpeaker() }" />
          <UInput v-model="backendUrl" />
        </UContainer>
      </template>
    </UDrawer>
  </UContainer>
</template>

<script setup lang="js">
const { MicVAD, utils } = await import("@ricky0123/vad-web");
const micOn = ref(false);
const speakerOn = ref(false);
const response = ref([]);
const history = ref([]);
const backendUrl = ref("");
let myvad = null;

const toggleMic = () => {
  if (micOn.value) {
    if (myvad) {
      myvad.destroy();
      myvad = null;
    }
  } else {
    startMicVAD();
  }
  micOn.value = !micOn.value;
}

const toggleSpeaker = () => {
  speakerOn.value = !speakerOn.value;
}

const startMicVAD = async () => {
  try {
    myvad = await MicVAD.new({
      onSpeechEnd: (audio) => {
        const wavBuffer = utils.encodeWAV(audio);
        const audioBlob = new Blob([wavBuffer], { type: "audio/wav" });
        getTextResponseFromAudio(audioBlob);
      },
      positiveSpeechThreshold: 0.7,
    });
    myvad.start();
  } catch (error) {
    console.error(error);
  }
}

const playAudio = async (base64Wav) => {
  try {
    const audio = new Audio("data:audio/wav;base64," + base64Wav);
    audio.playbackRate = 1.10;

    await new Promise((resolve, reject) => {
      audio.addEventListener("ended", resolve);
      audio.addEventListener("error", reject);
      audio.play().catch(reject);
    });
  } catch (error) {
    console.error("Error playing audio:", error);
  }
};

const getTextResponseFromAudio = async (audioBlob) => {
  myvad.pause();

  const formData = new FormData();
  if (audioBlob) {
    formData.append("file", audioBlob, "audio.wav");
  } else {
    console.error("No audio blob available to submit.");
    myvad.start();
    return;
  }

  formData.append("history", JSON.stringify(history.value));
  formData.append("use_tts", speakerOn.value ? "true" : "false");

  try {
    const res = await fetch(`${backendUrl.value}/proxy/audio-query`, {
      method: "POST",
      body: formData,
    });
    const data = await res.json();
    response.value = data.response.LLM_response;
    history.value = data.response.history;

    if (speakerOn.value) {
      const wav = data.response.tts_wav;
      await playAudio(wav);
    }

    myvad.start();
  } catch (error) {
    console.error(`Error: ${error}`);
    myvad.start();
    return;
  }
}

</script>
