<template>
  <UContainer class="flex flex-col items-center h-screen">
    <UContainer class="flex justify-center p-4">
      <UButton :icon="micOn ? 'mdi-light:microphone' : 'mdi-light:microphone-off'" color="neutral" size="xl" variant="ghost" @click="() => { toggleMic() }" />
      <UButton :icon="speakerOn ? 'mdi-light:volume' : 'mdi-light:volume-off'" color="neutral" size="xl" variant="ghost" @click="() => { toggleSpeaker() }" />
      <UInput v-model="backendUrl" placeholder="https://backendurl.com/..." size="xl"/>
    </UContainer>
    <div class="w-full h-3/4 p-4 overflow-y-auto scroll-smooth" ref="scrollContainer">
      <div
        v-for="(item, index) in response"
        :key="index"
          :class="[
            'flex', 
            'p-2', 
            'mb-2',
            item.role === 'User' ? 'justify-end' : 'justify-start'  // Customize this based on role
          ]"
      >
        <div>
          <p class="w-3/4">
          {{ item.text }}
          </p>
        </div>
      </div>
    </div>
  </UContainer>
</template>

<script setup lang="js">
import { ref, nextTick } from 'vue'
const { MicVAD, utils } = await import("@ricky0123/vad-web");
let audio = null;
const micOn = ref(false);
const speakerOn = ref(false);
const response = ref([]);
const history = ref([]);
const backendUrl = ref("");
const scrollContainer = ref(null)
let myvad = null;

const scrollToBottom = () => {
  const el = scrollContainer.value
  if (el) {
    el.scrollTop = el.scrollHeight
  }
}

const toggleMic = () => {
  if (micOn.value) {
    turnOffMic();
  } else {
    turnOnMic();
  }
  micOn.value = !micOn.value;
}

const turnOffMic = () => {
  if (myvad) {
    myvad.destroy();
    myvad = null;
  }
}

const turnOnMic = () => {
  if (myvad) {
    turnOffMic();
  }
  startMicVAD();
}

const toggleSpeaker = () => {
  if (!audio) {
    audio = new Audio();
    audio.play().catch(() => { })
  }
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
    audio.src = "data:audio/wav;base64," + base64Wav;
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
  turnOffMic();
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
    const query = data.response.query;
    const llm_response = data.response.LLM_response;
    if (query && llm_response) {
      response.value.push({ role: "User", text: query });
      response.value.push({ role: "AI", text: llm_response });
      nextTick(() => {
        scrollToBottom()
      })
    }
    history.value = data.response.history;

    if (speakerOn.value) {
      const wav = data.response.tts_wav;
      await playAudio(wav);
    }
    turnOnMic();

  } catch (error) {
    console.error(`Error: ${error}`);
    turnOnMic();
    return;
  }
}

</script>
