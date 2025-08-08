<template>
  <div class="flex flex-col items-center max-h-screen box-border">
    <div class="flex items-center justify-center p-4 gap-4 box-border w-screen absolute top-0 z-1000 ">
      <UButton :icon="micModeOn ? 'mdi-light:microphone' : 'mdi-light:microphone-off'" color="neutral" size="xl" variant="ghost" @click="() => { toggleMic() }" />
      <UButton :icon="speakerOn ? 'mdi-light:volume' : 'mdi-light:volume-off'" color="neutral" size="xl" variant="ghost" @click="() => { toggleSpeaker() }" />
      <UButton color="neutral" size="xl" variant="ghost" @click="() => { clearHistory() }">Clear History</UButton>
      <UButton color="neutral" size="xl" variant="ghost" @click="() => { insertTestResponse() }">Insert Test Response</UButton>
      <UInput variant="ghost" v-model="backendUrl" placeholder="https://backendurl.com/..." size="xl"/>
      <UIcon v-show="loading" name="mdi-light:loading" class="animate-spin size-6"/>
    </div>
    <div class="flex justify-center items-end box-border w-screen h-screen">
      <div class="h-full w-full">
        <JarvisVisualizer />
      </div>

      <!-- Right side: Chat content (conditionally shown) -->
      <transition
        name="fade-slide"
        mode="out-in"
        appear
      >
        <div
          v-if="response.length > 0"
          class="w-1/2 h-[80%] overflow-y-auto scroll-smooth px-8 box-border absolute top-1/2 transform -translate-y-1/2 right-0"
          ref="scrollContainer"
        >
          <div
            v-for="(item, index) in response"
            :key="index"
            :class="[
              'flex',
              'mb-16',
              item.role === 'User' ? 'justify-end text-right' : 'justify-start'
            ]"
          >
            <p class="max-w-3/4 text-white">
              {{ item.text }}
            </p>
          </div>
        </div>
      </transition>
    </div>
  </div>
</template>

<script setup lang="js">
import { ref, nextTick, watchEffect } from 'vue'
import { getTestResponse } from "../composables/Utils";
const { MicVAD, utils } = await import("@ricky0123/vad-web");
let audio = null;
const micModeOn = ref(false);
const speakerOn = ref(false);
const response = ref([]);
const backendUrl = ref("http://localhost:5002");
const scrollContainer = ref(null)
const loading = ref(false);
let myvad = null;

watchEffect(() => {
  if (response.value.length === 0) {
    window.dispatchEvent(new Event('chat-empty'));
  } else {
    window.dispatchEvent(new Event('chat-non-empty'));
  }
});

const clearHistory = () => {
  response.value = [];
}

const insertTestResponse = () => {
  response.value.push(getTestResponse());
}

const scrollToBottom = () => {
  const el = scrollContainer.value
  if (el) {
    el.scrollTop = el.scrollHeight
  }
}

const toggleMic = () => {
  if (micModeOn.value) {
    turnOffMic();
  } else {
    turnOnMic();
  }
  micModeOn.value = !micModeOn.value;
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
        if (!micModeOn.value) { return; }
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
    window.dispatchEvent(new Event('va-start'));
    audio.src = "data:audio/wav;base64," + base64Wav;
    audio.playbackRate = 1.0;

    await new Promise((resolve, reject) => {
      audio.addEventListener("ended", resolve);
      audio.addEventListener("error", reject);
      audio.play().catch(reject);
    });
    window.dispatchEvent(new Event('va-stop'));
  } catch (error) {
    console.error("Error playing audio:", error);
    window.dispatchEvent(new Event('va-stop'));
  }
};

const getTextResponseFromAudio = async (audioBlob) => {
  loading.value = true;
  turnOffMic();
  const formData = new FormData();
  if (audioBlob) {
    formData.append("file", audioBlob, "audio.wav");
  } else {
    console.error("No audio blob available to submit.");
    myvad.start();
    loading.value = false;
    return;
  }

  formData.append("session_id", ""); // TODO: Replace with actual session ID
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
    loading.value = false;

    if (speakerOn.value && data.response.tts_wav) {
      const wav = data.response.tts_wav;
      await playAudio(wav);
    }
    if (micModeOn.value) {
      turnOnMic();
    }

  } catch (error) {
    console.error(`Error: ${error}`);
    if (micModeOn.value) {
      turnOnMic();
    }
    loading.value = false;
    return;
  }
}
</script>


<style>
.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: opacity 0.8s ease, transform 0.8s ease;
}
.fade-slide-enter-from,
.fade-slide-leave-to {
  opacity: 0;
  transform: translateX(100px);
}
.fade-slide-enter-to,
.fade-slide-leave-from {
  opacity: 1;
  transform: translateX(0);
}
</style>