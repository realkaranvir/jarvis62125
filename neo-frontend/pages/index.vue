<template>
  <div class="flex flex-col items-center justify-end h-screen">
    <div
      class="mb-auto mt-4 font-thin flex flex-row items-center justify-center gap-2"
    >
      <p>
        {{ connectionStatus }}
      </p>
      <UIcon
        v-show="connectionStatus === serverStatus.CONNECTING"
        name="svg-spinners:8-dots-rotate"
        class="size-5 text-orange-500"
      />
      <UIcon
        v-show="connectionStatus === serverStatus.CONNECTED"
        name="material-symbols-light:stat-0-rounded"
        class="size-5 text-green-500"
      />
      <UTooltip
        :text="
          connectionStatus === serverStatus.REFUSED
            ? 'Server refused connection'
            : 'Is the server down?'
        "
      >
        <div>
          <UIcon
            v-show="
              connectionStatus === serverStatus.REFUSED ||
              connectionStatus === serverStatus.ERROR
            "
            name="material-symbols-light:warning"
            class="size-5 text-red-500"
          />
        </div>
      </UTooltip>
    </div>

    <div
      class="mt-auto mb-auto font-thin flex flex-col items-center justify-center text-center gap-2"
    >
      <p
        v-show="!gettingResponse"
        class="max-w-3/4 max-h-[50vh] text-xl break-words"
      >
        {{ response }}
      </p>
    </div>
    <p v-show="loadingPercent < 100" class="animate-pulse">{{ name }} is loading...</p>
    <p v-show="listening" class="text-sm text-gray-500">
        {{name}} is listening...
      </p>
    <UProgress v-show="loadingPercent != 100" v-model="loadingPercent" color="neutral" class="w-lg" />
    <UProgress v-show="gettingResponse" class="w-lg" />
    <UTextarea
      class="w-1/2 m-8"
      color="neutral"
      variant="soft"
      placeholder="Type something..."
      :maxrows="8"
      autoresize
      v-model="value"
      :disabled="connectionStatus !== serverStatus.CONNECTED"
      @keydown.enter="(event: KeyboardEvent) => { if (!event.shiftKey) handleEnter(event) }"
    />
  </div>
</template>

<script setup lang="ts">
import * as tts from '@diffusionstudio/vits-web';
const { MicVAD, utils } = await import("@ricky0123/vad-web");
const enum serverStatus {
  CONNECTING = "Connecting",
  CONNECTED = "Connected",
  REFUSED = "Connection Refused",
  ERROR = "Error Connecting",
}
const value = ref("");
const connectionStatus = ref(serverStatus.CONNECTING);
const gettingResponse = ref(false);
const history = ref([]);
const response = ref("");
const currentAudioBlob = ref<Blob | null>(null);
const listening = ref(false);
const loadingPercent = ref(0);
const localTTS = ref(false); // Set to true to use local TTS, false to use server TTS
let name = "J.A.R.V.I.S.";

onMounted(() => {
  handleConnect();
});

onMounted(async () => {
  // Only run this code in the browser
  if (process.client || typeof window !== "undefined") {
    try {
      const myvad = await MicVAD.new({
        onSpeechEnd: (audio) => {
          console.log("Speech Ended");
          console.log(audio);
          const wavBuffer = utils.encodeWAV(audio);
          const audioBlob = new Blob([wavBuffer], { type: "audio/wav" });
          currentAudioBlob.value = audioBlob;
        },
        positiveSpeechThreshold: 0.7,
      });
      myvad.start();
    } catch (error: any) {
      console.error(error);
    }
  }

  // Download the local TTS model just in case
  await tts.download('en_US-hfc_female-medium', (progress) => {
    console.log(`Downloading ${progress.url} - ${Math.round(progress.loaded * 100 / progress.total)}%`);
    loadingPercent.value = Math.round(progress.loaded * 100 / progress.total);
    if (loadingPercent.value === 100) {
      console.log("TTS model downloaded successfully.");
      listening.value = true;
    }
  });
});

// When we get a new audio blob, submit it to the server
watch(currentAudioBlob, (newValue, oldValue) => {
  if (listening.value == true) {
    submitAudio(newValue);
  }
});

// Submit audio to server, get transcription, and send query to server
async function submitAudio(audioBlob: Blob | null) {
  const formData = new FormData();
  if (audioBlob) {
    formData.append("file", audioBlob, "audio.wav");
  } else {
    console.error("No audio blob available to submit.");
    return;
  }
  formData.append("model", "Systran/faster-whisper-tiny.en");

  const res = await fetch("http://localhost:8000/v1/audio/transcriptions", {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    throw new Error("Transcription failed");
  }
  const data = await res.json();
  const transcription = data.text;

  // Needs to start with name for query to work
  // TODO: add check for name as first word if conversation isn't ongoing

  console.log("Transcription:", transcription);
  if (transcription.length < 1) {
    return;
  }
  // Set gettingResponse to true to show the loading state
  gettingResponse.value = true;
  // Send the query to the server
  try {
    const res = await sendQuery(transcription);
    response.value = res.response.LLM_response;
  } catch (error) {
    response.value = `${name} is malfunctioning.`;
  }

  gettingResponse.value = false;
}

// Check connection to the server
async function handleConnect() {
  try {
    const response = await fetch("http://127.0.0.1:5000/health", {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });
    const data = await response.json();
    if (data.status === "healthy") {
      connectionStatus.value = serverStatus.CONNECTED;
    } else {
      connectionStatus.value = serverStatus.REFUSED;
    }
  } catch (error) {
    connectionStatus.value = serverStatus.ERROR;
  }
}

// Send query to the server and update history
async function sendQuery(query: string) {
  listening.value = false;
  try {
    if (!query) {
      return;
    }
    if (query.trim() === "") {
      return;
    }
    const response = await fetch("http://127.0.0.1:5000/query", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ query: query, history: history.value }),
    });
    const res = await response.json();
    history.value = res.response.history.slice(
      Math.max(res.response.history.length - 10, 0),
      res.response.history.length
    );


    let wav: string | null = null;
    // Play the response using TTS
    if (localTTS.value == true) {
      let blob: Blob;
      blob = await tts.predict({
        text: res.response.LLM_response,
        voiceId: 'en_US-hfc_female-medium',
      });
      wav = URL.createObjectURL(blob)
    } else {
      // Use the TTS server to get the audio file
      wav = await getSpeechFileFromTTSServer(res.response.LLM_response);
    }

    const audio = new Audio();
    audio.src = wav;
    audio.playbackRate = 1.2;
    audio.play();
    audio.onended = () => {
      listening.value = true;
    };
    return res;
  } catch (error) {
    console.error("Error submitting data:", error);
  }
}

// Handle text input submission
async function handleEnter(event: KeyboardEvent) {
  // Prevent default behavior
  event.preventDefault();

  if (!value.value.trim()) {
    // If the input is empty, do nothing
    return;
  }
  const query = value.value;
  // Clear the input
  value.value = "";

  // Set gettingResponse to true to show the loading state
  gettingResponse.value = true;
  // Send the query to the server
  try {
    const res = await sendQuery(query);
    response.value = res.response.LLM_response;
  } catch (error) {
    response.value = `${name} is malfunctioning.`;
  }

  gettingResponse.value = false;
}

// Get speech file from TTS server
async function getSpeechFileFromTTSServer(text: string) {
  const params = new URLSearchParams({ text });

  const response = await fetch(`http://localhost:5008/?${params.toString()}`, {
    method: "GET",
  });

  if (!response.ok) {
    throw new Error(`Server error: ${response.status}`);
  }

  const blob = await response.blob(); // WAV file
  const url = URL.createObjectURL(blob);
  return url;
}
</script>
